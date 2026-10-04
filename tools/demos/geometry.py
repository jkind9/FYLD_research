"""Geometry for demo pages: depth back-projection, voxel fusion, normals, splats, top-down grids.

These are presentation steps on already exported depth and poses. They do not change or
replace any experiment result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Intrinsics:
    """Pinhole calibration in pixels for the image size the depth was recorded at."""

    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float


def backproject(depth_m: np.ndarray, k: Intrinsics, stride: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Return camera-frame points (N, 3) and their (row, col) pixels for valid depth.

    Camera frame: x right, y down, z forward, metres. Depth is distance along z.
    Invalid depth must already be zero or non-finite.
    """
    if depth_m.shape != (k.height, k.width):
        raise ValueError(f"depth shape {depth_m.shape} does not match calibration {(k.height, k.width)}")
    rows, cols = np.mgrid[0:k.height:stride, 0:k.width:stride]
    z = depth_m[rows, cols]
    valid = np.isfinite(z) & (z > 0)
    rows, cols, z = rows[valid], cols[valid], z[valid]
    x = (cols - k.cx) * z / k.fx
    y = (rows - k.cy) * z / k.fy
    return np.stack([x, y, z], axis=1), np.stack([rows, cols], axis=1)


def depth_edges(depth_m: np.ndarray, relative_jump: float) -> np.ndarray:
    """Mask pixels next to a depth jump larger than relative_jump times their depth.

    These "flying pixels" sit between foreground and background and smear surfaces.
    """
    z = np.where(np.isfinite(depth_m), depth_m, 0.0)
    edge = np.zeros(z.shape, dtype=bool)
    for dy, dx in ((0, 1), (1, 0)):
        a = z[: z.shape[0] - dy, : z.shape[1] - dx]
        b = z[dy:, dx:]
        jump = np.abs(a - b) > relative_jump * np.maximum(a, b)
        jump &= (a > 0) & (b > 0)
        edge[: z.shape[0] - dy, : z.shape[1] - dx] |= jump
        edge[dy:, dx:] |= jump
    return edge


def camera_normals(depth_m: np.ndarray, k: Intrinsics) -> np.ndarray:
    """Per-pixel surface normals in the camera frame (H, W, 3); zeros where undefined.

    Normals come from the cross product of neighbouring back-projected points and are
    flipped to face the camera.
    """
    rows, cols = np.mgrid[0:k.height, 0:k.width]
    z = np.where(np.isfinite(depth_m), depth_m, 0.0)
    pts = np.stack([(cols - k.cx) * z / k.fx, (rows - k.cy) * z / k.fy, z], axis=2)
    du = np.zeros_like(pts)
    dv = np.zeros_like(pts)
    du[:, 1:-1] = pts[:, 2:] - pts[:, :-2]
    dv[1:-1, :] = pts[2:, :] - pts[:-2, :]
    n = np.cross(du, dv)
    length = np.linalg.norm(n, axis=2, keepdims=True)
    ok = (length[..., 0] > 0) & (z > 0)
    ok[:, [0, -1]] = False
    ok[[0, -1], :] = False
    n = np.where(ok[..., None], n / np.maximum(length, 1e-12), 0.0)
    facing = np.sum(n * pts, axis=2) > 0
    n[facing] *= -1.0
    return n


def to_world(points_cam: np.ndarray, t_world_camera: np.ndarray) -> np.ndarray:
    """Apply a 4x4 camera-to-world transform to (N, 3) points."""
    t = np.asarray(t_world_camera, dtype=float)
    if t.shape != (4, 4):
        raise ValueError("pose must be a 4x4 camera-to-world matrix")
    return points_cam @ t[:3, :3].T + t[:3, 3]


def voxel_fuse(points: np.ndarray, colours: np.ndarray, normals: np.ndarray, voxel_m: float,
               min_count: int = 1) -> dict[str, np.ndarray]:
    """Average points, colours and normals that fall in the same voxel.

    Returns positions (M, 3), colours (M, 3) uint8, unit normals (M, 3) and the number of
    samples per voxel. Voxels with fewer than min_count samples are dropped, which removes
    isolated noise seen only once.
    """
    if voxel_m <= 0:
        raise ValueError("voxel size must be positive")
    if not (len(points) == len(colours) == len(normals)):
        raise ValueError("points, colours and normals must have the same length")
    keys = np.floor(points / voxel_m).astype(np.int64)
    _, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.reshape(-1)
    m = len(counts)
    pos = np.zeros((m, 3))
    col = np.zeros((m, 3))
    nrm = np.zeros((m, 3))
    np.add.at(pos, inverse, points)
    np.add.at(col, inverse, colours.astype(float))
    np.add.at(nrm, inverse, normals)
    pos /= counts[:, None]
    col /= counts[:, None]
    length = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.where(length > 1e-9, nrm / np.maximum(length, 1e-12), np.array([0.0, 0.0, 1.0]))
    keep = counts >= min_count
    return {
        "positions": pos[keep],
        "colours": np.clip(np.rint(col[keep]), 0, 255).astype(np.uint8),
        "normals": nrm[keep],
        "counts": counts[keep],
    }


def surfel_covariance(normals: np.ndarray, tangent_sigma: np.ndarray, normal_sigma: np.ndarray) -> np.ndarray:
    """3D covariance of flat Gaussians: wide in the tangent plane, thin along the normal.

    Sigma = s_t^2 (I - n n^T) + s_n^2 n n^T. Returns the 6 upper-triangle entries
    (xx, xy, xz, yy, yz, zz) per Gaussian.
    """
    n = normals / np.linalg.norm(normals, axis=1, keepdims=True)
    st2 = np.broadcast_to(np.asarray(tangent_sigma, float), (len(n),)).reshape(-1, 1, 1) ** 2
    sn2 = np.broadcast_to(np.asarray(normal_sigma, float), (len(n),)).reshape(-1, 1, 1) ** 2
    nn = n[:, :, None] * n[:, None, :]
    cov = st2 * (np.eye(3)[None] - nn) + sn2 * nn
    return np.stack([cov[:, 0, 0], cov[:, 0, 1], cov[:, 0, 2], cov[:, 1, 1], cov[:, 1, 2], cov[:, 2, 2]], axis=1)


def render_points(points: np.ndarray, colours: np.ndarray, t_world_camera: np.ndarray, k: Intrinsics,
                  radius_px: int, background: tuple[int, int, int]) -> np.ndarray:
    """Draw world points into the image of a recorded camera, nearest point winning per pixel.

    A simple z-buffer used for still thumbnails; each point covers a small square.
    """
    t = np.asarray(t_world_camera, float)
    cam = (points - t[:3, 3]) @ t[:3, :3]
    front = cam[:, 2] > 0.05
    cam, col = cam[front], colours[front]
    u = np.rint(k.fx * cam[:, 0] / cam[:, 2] + k.cx).astype(int)
    v = np.rint(k.fy * cam[:, 1] / cam[:, 2] + k.cy).astype(int)
    image = np.empty((k.height, k.width, 3), np.uint8)
    image[:] = background
    zbuf = np.full((k.height, k.width), np.inf)
    order = np.argsort(-cam[:, 2])
    for dy in range(-radius_px, radius_px + 1):
        for dx in range(-radius_px, radius_px + 1):
            uu, vv = u[order] + dx, v[order] + dy
            ok = (uu >= 0) & (uu < k.width) & (vv >= 0) & (vv < k.height)
            z = cam[order, 2][ok]
            closer = z < zbuf[vv[ok], uu[ok]]
            zbuf[vv[ok][closer], uu[ok][closer]] = z[closer]
            image[vv[ok][closer], uu[ok][closer]] = col[order][ok][closer]
    return image


def top_down_grid(points: np.ndarray, colours: np.ndarray, up_axis: int, cell_m: float,
                  height_range: tuple[float, float]) -> dict[str, np.ndarray | float]:
    """Project points onto the ground plane, keeping the highest point per cell.

    Returns height (H, W) with NaN where unseen, colour (H, W, 3), an observed mask, sample
    counts and the grid origin in the two ground axes. Points outside height_range are
    ignored so a ceiling cannot hide the floor.
    """
    ground = [a for a in range(3) if a != up_axis]
    h = points[:, up_axis]
    keep = (h >= height_range[0]) & (h <= height_range[1])
    p, c, h = points[keep], colours[keep], h[keep]
    if len(p) == 0:
        raise ValueError("no points inside the height range")
    g = p[:, ground]
    origin = g.min(axis=0)
    ij = np.floor((g - origin) / cell_m).astype(np.int64)
    width, height = ij.max(axis=0) + 1
    order = np.argsort(h, kind="stable")
    flat = ij[order, 1] * width + ij[order, 0]
    best = np.full(width * height, -1, dtype=np.int64)
    best[flat] = order
    counts = np.bincount(ij[:, 1] * width + ij[:, 0], minlength=width * height)
    observed = best >= 0
    height_map = np.full(width * height, np.nan)
    height_map[observed] = h[best[observed]]
    colour_map = np.zeros((width * height, 3), dtype=np.uint8)
    colour_map[observed] = c[best[observed]]
    return {
        "height": height_map.reshape(height, width),
        "colour": colour_map.reshape(height, width, 3),
        "observed": observed.reshape(height, width),
        "counts": counts.reshape(height, width),
        "origin": origin,
        "cell_m": cell_m,
    }
