"""Task45 Part B: how much detection boxes jitter on stationary objects.

Poses are camera-to-world (T_wc), as in TUM ground truth. Colour pixels are
back-projected and projected with colour-time poses; the depth-time pose is used
only to move the depth map to colour time. A steady offset cannot be seen by
these measures; Part A measures placement accuracy. Values that cannot be
computed are None with a reason.
"""

import itertools
import math
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation, Slerp  # type: ignore[import-untyped]

from experiments.shared.contracts import Calibration
from experiments.shared.geometry import backproject, project, transform_points

from .placement import box_slices

MAX_POSE_GAP_S = 0.02
MIN_VALID_PIXELS = 20
MIN_VALID_FRACTION = 0.25
MAX_DEPTH_SPREAD = 0.2
MIN_TRACK = 5
JUMP_LIMIT = 2.0


def interpolate_pose(
    times: NDArray, poses: Sequence[NDArray], t: float, max_gap: float = MAX_POSE_GAP_S
) -> NDArray:
    """Linear position and slerp rotation between the two bracketing rows."""
    times = np.asarray(times, dtype=float)
    if t < times[0] or t > times[-1]:
        raise ValueError(f"time {t} outside the motion-capture range")
    right = int(np.searchsorted(times, t, side="left"))
    if times[right] == t:
        return np.array(poses[right], dtype=float)
    left = right - 1
    if times[right] - times[left] > max_gap:
        raise ValueError(
            f"motion-capture gap {times[right] - times[left]:.3f} s at {t}"
        )
    share = (t - times[left]) / (times[right] - times[left])
    rotations = Rotation.from_matrix([poses[left][:3, :3], poses[right][:3, :3]])
    matrix = np.eye(4)
    matrix[:3, :3] = Slerp([0.0, 1.0], rotations)([share]).as_matrix()[0]
    matrix[:3, 3] = (1 - share) * poses[left][:3, 3] + share * poses[right][:3, 3]
    return matrix


def depth_to_colour_time(
    depth: NDArray,
    valid: NDArray,
    camera: Calibration,
    depth_pose: NDArray,
    colour_pose: NDArray,
) -> tuple[NDArray, NDArray]:
    """Move every valid depth sample into the colour-time camera; nearest depth wins."""
    points, _ = backproject(depth, valid, camera)
    moved = transform_points(points, np.linalg.inv(colour_pose) @ depth_pose)
    moved = moved[moved[:, 2] > 0]
    pixels = np.rint(project(moved, camera)).astype(int)
    inside = (
        (pixels[:, 0] >= 0)
        & (pixels[:, 0] < camera.width)
        & (pixels[:, 1] >= 0)
        & (pixels[:, 1] < camera.height)
    )
    pixels, z = pixels[inside], moved[inside, 2]
    flat = np.full(camera.width * camera.height, np.inf)
    np.minimum.at(flat, pixels[:, 1] * camera.width + pixels[:, 0], z)
    result = flat.reshape(camera.height, camera.width)
    filled = np.isfinite(result)
    return np.where(filled, result, np.nan), filled


def centre_depth(depth: NDArray, valid: NDArray, xyxy: Sequence[float]) -> dict:
    """Median depth over the central half of the box, with quality flags."""
    x1, y1, x2, y2 = map(float, xyxy)
    quarter_w, quarter_h = (x2 - x1) / 4, (y2 - y1) / 4
    height, width = depth.shape
    window = box_slices(
        [x1 + quarter_w, y1 + quarter_h, x2 - quarter_w, y2 - quarter_h],
        width=width,
        height=height,
    )
    values = depth[window][valid[window]]
    size = depth[window].size
    if not len(values):
        return {
            "median": None,
            "valid_pixels": 0,
            "valid_fraction": 0.0,
            "spread": None,
            "flag_sparse": True,
            "flag_spread": False,
            "reason": "no valid depth in the central half",
        }
    median = float(np.median(values))
    spread = float(np.subtract(*np.percentile(values, [75, 25])) / median)
    fraction = len(values) / size
    return {
        "median": median,
        "valid_pixels": len(values),
        "valid_fraction": fraction,
        "spread": spread,
        "flag_sparse": len(values) < MIN_VALID_PIXELS or fraction < MIN_VALID_FRACTION,
        "flag_spread": spread > MAX_DEPTH_SPREAD,
        "reason": None,
    }


def backproject_pixel(
    u: float, v: float, z: float, camera: Calibration, pose: NDArray
) -> NDArray:
    point = np.array(
        [[(u - camera.cx) * z / camera.fx, (v - camera.cy) * z / camera.fy, z]]
    )
    return transform_points(point, pose)[0]


def project_world(
    point: NDArray, camera: Calibration, pose: NDArray
) -> tuple[float, float]:
    local = transform_points(
        np.asarray(point, dtype=float).reshape(1, 3), np.linalg.inv(pose)
    )
    u, v = project(local, camera)[0]
    return float(u), float(v)


def link(previous: Sequence[dict], current: Sequence[dict], gate: float = 0.5) -> dict:
    """One-to-one same-class links by smallest distance within gate x previous diagonal.

    Only current detections with depth (`linkable`, default True) can be linked.
    Each previous detection left unlinked gets an outcome from the nearest
    same-class current detection: `no_depth` (found again within the gate but
    without depth), `claimed` (a nearby box was already assigned to another
    track), `jump` (one-to-one assignment beyond the gate but within two
    diagonals), or `gone`.
    """
    candidates = [
        (math.dist(before["predicted"], after["centre"]), i, j)
        for i, before in enumerate(previous)
        for j, after in enumerate(current)
        if before["label"] == after["label"]
    ]
    used_previous, used_current, links = set(), set(), []
    for distance, i, j in sorted(candidates):
        if (
            i in used_previous
            or j in used_current
            or not current[j].get("linkable", True)
            or distance > gate * previous[i]["diagonal"]
        ):
            continue
        links.append((i, j))
        used_previous.add(i)
        used_current.add(j)
    unlinked = []
    jump_candidates = []
    for i, before in enumerate(previous):
        if i in used_previous:
            continue
        same_class = sorted((d, j) for d, a, j in candidates if a == i)
        nearest, nearest_index = same_class[0] if same_class else (None, None)
        if nearest is None or nearest > JUMP_LIMIT * before["diagonal"]:
            outcome = "gone"
        elif nearest <= gate * before["diagonal"]:
            nearest_detection = current[nearest_index]
            if not nearest_detection.get("linkable", True):
                outcome = "no_depth"
            elif nearest_index in used_current:
                outcome = "claimed"
            else:
                outcome = "gone"
        else:
            outcome = "gone"
            jump_candidates.extend(
                (distance, i, j)
                for distance, j in same_class
                if j not in used_current
                and distance <= JUMP_LIMIT * before["diagonal"]
            )
        unlinked.append(
            {"index": i, "nearest_px": nearest, "outcome": outcome}
        )
    assigned_jumps = set()
    for distance, i, j in sorted(jump_candidates):
        if i in assigned_jumps or j in used_current:
            continue
        row = next(item for item in unlinked if item["index"] == i)
        if row["outcome"] == "gone":
            row["outcome"] = "jump"
            row["nearest_px"] = distance
            assigned_jumps.add(i)
            used_current.add(j)
    return {"links": sorted(links), "unlinked": unlinked}


def _unavailable(reason: str) -> dict:
    return {"sx": None, "sy": None, "radial_rms": None, "n": 0, "reason": reason}


def _spread(residuals: NDArray) -> dict:
    sx, sy = np.std(residuals, axis=0, ddof=1)
    return {
        "sx": float(sx),
        "sy": float(sy),
        "radial_rms": float(
            math.sqrt(
                np.mean(np.sum((residuals - residuals.mean(axis=0)) ** 2, axis=1))
            )
        ),
        "n": len(residuals),
        "reason": None,
    }


def windowed_jitter(
    track: Sequence[dict], camera: Calibration, half_window: int | None = 5
) -> dict:
    """Residual of each detection against the median world point of nearby frames.

    `half_window=None` anchors on the whole track (reported for comparison only;
    it counts slow drift as jitter).
    """
    if len(track) < MIN_TRACK:
        return _unavailable(f"track shorter than {MIN_TRACK} frames")
    indices = np.array([frame["index"] for frame in track])
    worlds = np.array([frame["world"] for frame in track])
    residuals = []
    for frame in track:
        near = (
            np.ones(len(track), dtype=bool)
            if half_window is None
            else np.abs(indices - frame["index"]) <= half_window
        )
        anchor = np.median(worlds[near], axis=0)
        expected = project_world(anchor, camera, frame["pose"])
        residuals.append(np.subtract(frame["centre"], expected))
    return _spread(np.array(residuals))


def _lag1(series: NDArray) -> float | None:
    if len(series) < 3 or np.std(series) == 0:
        return None
    return float(np.corrcoef(series[:-1], series[1:])[0, 1])


def pairwise_jitter(track: Sequence[dict], camera: Calibration) -> dict:
    """Frame-to-frame residuals between consecutive linked frames, std / sqrt(2)."""
    if len(track) < MIN_TRACK:
        return {
            **_unavailable(f"track shorter than {MIN_TRACK} frames"),
            "lag1_x": None,
            "lag1_y": None,
        }
    residuals = np.array(
        [
            np.subtract(
                after["centre"], project_world(before["world"], camera, after["pose"])
            )
            for before, after in itertools.pairwise(track)
            if after["index"] == before["index"] + 1
        ]
    )
    if len(residuals) < MIN_TRACK - 1:
        return {
            **_unavailable("too few consecutive frame pairs"),
            "lag1_x": None,
            "lag1_y": None,
        }
    result = _spread(residuals)
    return {
        **result,
        "sx": result["sx"] / math.sqrt(2),
        "sy": result["sy"] / math.sqrt(2),
        "radial_rms": result["radial_rms"] / math.sqrt(2),
        "lag1_x": _lag1(residuals[:, 0]),
        "lag1_y": _lag1(residuals[:, 1]),
    }


def bootstrap_interval(
    values: Sequence[float], *, seed: int, resamples: int = 1000
) -> tuple[float, float]:
    """2.5-97.5 percentile of the mean over whole-track resamples."""
    array = np.asarray(values, dtype=float)
    generator = np.random.default_rng(seed)
    means = generator.choice(array, size=(resamples, len(array)), replace=True).mean(
        axis=1
    )
    low, high = np.percentile(means, [2.5, 97.5])
    return float(low), float(high)
