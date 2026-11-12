"""Dense depth for one frame by testing candidate depths against nearby keyframes (a plane sweep).

Each pixel's candidate depths are projected into the keyframes. The cost of a candidate is the
Census distance between the pixel and where it lands; semi-global matching then smooths the costs
along four scan lines. The cheapest candidate wins; its margin over the next cheapest sets
confidence.
"""

import cv2
import numpy as np

from sitescan.types import Camera, MeasuredDepth

SCALE = 0.5
PLANE_STEP_PX = 1.0
MIN_PLANES = 16
MAX_PLANES = 128
NEAR_M = 0.3
FAR_M = 10.0
PRIOR_BAND = 0.3
CENSUS_RADIUS = 2
P1 = 1.0
P2 = 6.0
FULL_CONFIDENCE_MARGIN = 0.6


def shrink(grey: np.ndarray, camera: Camera, scale: float) -> tuple[np.ndarray, Camera]:
    """The image and its camera resized by `scale`, keeping pixel centres aligned."""
    width, height = round(camera.width * scale), round(camera.height * scale)
    sx, sy = width / camera.width, height / camera.height
    small = Camera(
        camera.fx * sx,
        camera.fy * sy,
        (camera.cx + 0.5) * sx - 0.5,
        (camera.cy + 0.5) * sy - 0.5,
        width,
        height,
    )
    return cv2.resize(grey, (width, height), interpolation=cv2.INTER_AREA), small


def census(grey: np.ndarray, radius: int = CENSUS_RADIUS) -> np.ndarray:
    """Per-pixel bit codes: a bit per neighbour in the window, set where darker than the centre."""
    height, width = grey.shape
    padded = np.pad(grey, radius, mode="edge")
    codes = np.zeros((height, width), np.uint64)
    bit = 0
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy == 0 and dx == 0:
                continue
            neighbour = padded[
                radius + dy : radius + dy + height, radius + dx : radius + dx + width
            ]
            codes |= (neighbour < grey).astype(np.uint64) << np.uint64(bit)
            bit += 1
    return codes


def plane_count(camera: Camera, references, pose, prior=None, *, band: float = PRIOR_BAND) -> int:
    """Candidates needed for neighbouring ones to land about one pixel apart in the widest keyframe.

    Disparity is focal length x baseline x inverse depth, so the inverse-depth range searched sets
    the count. With a prior the range is widest at its near pixels (5th percentile). The count is
    kept between 16 and 128.
    """
    baseline = max(np.linalg.norm(p[:3, 3] - pose[:3, 3]) for _, _, p in references)
    if prior is None or not np.any(np.isfinite(prior) & (prior > 0)):
        inverse_range = 1.0 / NEAR_M - 1.0 / FAR_M
    else:
        near = np.percentile(prior[np.isfinite(prior) & (prior > 0)], 5)
        inverse_range = (np.exp(band) - np.exp(-band)) / near
    needed = int(np.ceil(camera.fx * baseline * inverse_range / PLANE_STEP_PX))
    return int(np.clip(needed, MIN_PLANES, MAX_PLANES))


def candidate_depths(
    shape, prior=None, *, planes=MIN_PLANES, near_m=NEAR_M, far_m=FAR_M, band=PRIOR_BAND
):
    """planes x H x W candidate depths, nearest first.

    Without a prior, every pixel tests the same depths, evenly spaced in inverse depth between near
    and far. With one, pixels with a valid prior test depths within exp(+-band) of it instead.
    """
    depths = 1.0 / np.linspace(1.0 / near_m, 1.0 / far_m, planes)
    volume = np.repeat(depths[:, None, None], shape[0] * shape[1], axis=1).reshape(planes, *shape)
    if prior is not None:
        good = np.isfinite(prior) & (prior > 0)
        volume[:, good] = prior[good][None, :] * np.exp(np.linspace(-band, band, planes))[:, None]
    return volume.astype(np.float32)


def matching_costs(grey, camera: Camera, pose, references, depths: np.ndarray) -> np.ndarray:
    """planes x H x W mean Census distance to the keyframes; NaN where no keyframe sees it."""
    codes = census(grey)
    rows, cols = np.mgrid[0 : camera.height, 0 : camera.width]
    rays = np.stack(
        [(cols - camera.cx) / camera.fx, (rows - camera.cy) / camera.fy, np.ones(rows.shape)]
    )
    total = np.zeros(depths.shape, np.float32)
    seen = np.zeros(depths.shape, np.float32)
    for reference_grey, reference, reference_pose in references:
        reference_codes = census(reference_grey)
        moved = np.linalg.inv(reference_pose) @ pose
        turned = np.einsum("ij,jhw->ihw", moved[:3, :3], rays)
        for k in range(len(depths)):
            x, y, z = turned * depths[k] + moved[:3, 3, None, None]
            with np.errstate(divide="ignore", invalid="ignore"):
                col = np.rint(reference.fx * x / z + reference.cx)
                row = np.rint(reference.fy * y / z + reference.cy)
            inside = (
                (z > 0)
                & (col >= 0)
                & (col < reference.width)
                & (row >= 0)
                & (row < reference.height)
            )
            landed = reference_codes[
                np.where(inside, row, 0).astype(int), np.where(inside, col, 0).astype(int)
            ]
            total[k] += np.where(inside, np.bitwise_count(codes ^ landed), 0)
            seen[k] += inside
    with np.errstate(invalid="ignore", divide="ignore"):
        return total / seen


def scan(costs: np.ndarray, p1: float, p2: float) -> np.ndarray:
    """Semi-global path costs along the last axis: a step of one candidate costs p1, a jump p2."""
    out = np.empty_like(costs)
    previous = costs[:, :, 0]
    out[:, :, 0] = previous
    edge = np.full((1, costs.shape[1]), np.inf, costs.dtype)
    for x in range(1, costs.shape[2]):
        best = previous.min(axis=0)
        step = np.minimum(np.vstack([edge, previous[:-1]]), np.vstack([previous[1:], edge])) + p1
        previous = costs[:, :, x] + np.minimum(np.minimum(previous, step), best + p2) - best
        out[:, :, x] = previous
    return out


def aggregate(costs: np.ndarray, p1: float = P1, p2: float = P2) -> np.ndarray:
    """Sum of path costs from left, right, top and bottom."""
    across = np.ascontiguousarray(costs.transpose(0, 2, 1))
    return (
        scan(costs, p1, p2)
        + scan(costs[..., ::-1], p1, p2)[..., ::-1]
        + (scan(across, p1, p2) + scan(across[..., ::-1], p1, p2)[..., ::-1]).transpose(0, 2, 1)
    )


def best_depth(aggregated: np.ndarray, depths: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(depth, confidence 0-255): the cheapest candidate, refined between its neighbours.

    Confidence grows with the margin of the second-cheapest candidate that is not a neighbour.
    It is zero at the first and last candidates, where the true depth may lie outside the range.
    """
    count = len(depths)
    k = aggregated.argmin(axis=0)[None]
    best = np.take_along_axis(aggregated, k, 0)[0]
    below = np.take_along_axis(aggregated, np.maximum(k - 1, 0), 0)[0]
    above = np.take_along_axis(aggregated, np.minimum(k + 1, count - 1), 0)[0]
    others = aggregated.copy()
    for offset in (-1, 0, 1):
        np.put_along_axis(others, np.clip(k + offset, 0, count - 1), np.inf, 0)
    margin = 1.0 - best / np.maximum(others.min(axis=0), 1e-6)
    curve = below - 2 * best + above
    offset = np.clip(
        np.divide(below - above, 2 * curve, out=np.zeros_like(curve), where=curve > 0), -0.5, 0.5
    )
    inverse = 1.0 / depths
    at = np.take_along_axis(inverse, k, 0)[0]
    toward = np.take_along_axis(inverse, np.clip(k + np.sign(offset).astype(int), 0, count - 1), 0)[
        0
    ]
    depth = 1.0 / (at + np.abs(offset) * (toward - at))
    inner = (k[0] > 0) & (k[0] < count - 1)
    confidence = np.where(inner, np.clip(margin / FULL_CONFIDENCE_MARGIN, 0, 1) * 255, 0)
    return depth.astype(np.float32), confidence.astype(np.uint8)


def sweep_depth(
    grey, camera: Camera, pose, references, *, t_ns: int = 0, prior=None, scale: float = SCALE
) -> MeasuredDepth:
    """Depth and confidence for a frame from one or more keyframes, at `scale` of the image size.

    `references` are (grey, Camera, world_from_camera) for each keyframe. `prior` is an optional
    full-size depth in metres, such as scaled learned depth, to search around.
    """
    small, small_camera = shrink(grey, camera, scale)
    shrunk = [(*shrink(g, c, scale), p) for g, c, p in references]
    if prior is not None:
        prior = cv2.resize(
            prior.astype(np.float32),
            (small_camera.width, small_camera.height),
            interpolation=cv2.INTER_NEAREST,
        )
    planes = plane_count(small_camera, shrunk, pose, prior)
    depths = candidate_depths(small.shape, prior, planes=planes)
    costs = matching_costs(small, small_camera, pose, shrunk, depths)
    no_evidence = (
        CENSUS_RADIUS * (CENSUS_RADIUS + 1) * 2
    )  # half the bits: what an unrelated pixel scores
    depth, confidence = best_depth(aggregate(np.where(np.isnan(costs), no_evidence, costs)), depths)
    return MeasuredDepth(
        t_ns,
        np.where(confidence > 0, depth, 0).astype(np.float32),
        confidence,
        small_camera,
        "sweep",
    )
