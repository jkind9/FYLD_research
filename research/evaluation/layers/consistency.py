"""How far apart two frames' surfaces sit once both are placed in the world.

When depth is scaled differently in each frame, the same wall lands at a different distance
from each camera, and the point cloud shows it several times along the viewing direction.
`surface_gap` puts that in metres: it moves frame B's points into frame A's camera with the
two camera-to-world poses and compares them with frame A's own depth along A's view axis.
It reads saved depth and poses only; no reference enters it.
"""

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from experiments.shared.contracts import Calibration, Pose
from experiments.shared.geometry import backproject, transform_points

# Points closer than this to camera A are not projected (they would explode in u, v).
MIN_PROJECTED_DEPTH_M = 0.05

DepthLoader = Callable[[int], tuple[NDArray, NDArray]]


def surface_gap(
    depth_a: NDArray,
    valid_a: NDArray,
    pose_a: Pose,
    camera_a: Calibration,
    depth_b: NDArray,
    valid_b: NDArray,
    pose_b: Pose,
    camera_b: Calibration,
) -> dict[str, Any]:
    """Median signed and absolute depth difference (B minus A) where both frames see a surface.

    B's points are rounded to A's nearest pixel; where several land on one pixel only the
    nearest counts, so a surface hidden behind another is not compared. `overlap` is the
    share of B's valid pixels that land on a valid A pixel. No overlap gives None gaps.
    """
    points_b, _ = backproject(depth_b, valid_b, camera_b)
    b_to_a = np.linalg.inv(pose_a.matrix) @ pose_b.matrix
    in_a = transform_points(points_b, b_to_a) if len(points_b) else points_b
    in_a = in_a[in_a[:, 2] > MIN_PROJECTED_DEPTH_M]
    u = np.round(camera_a.fx * in_a[:, 0] / in_a[:, 2] + camera_a.cx).astype(np.int64)
    v = np.round(camera_a.fy * in_a[:, 1] / in_a[:, 2] + camera_a.cy).astype(np.int64)
    inside = (u >= 0) & (u < camera_a.width) & (v >= 0) & (v < camera_a.height)
    u, v, z = u[inside], v[inside], in_a[inside, 2]
    nearest = _nearest_per_pixel(v * camera_a.width + u, z)
    u, v, z = u[nearest], v[nearest], z[nearest]
    seen = valid_a[v, u]
    differences = z[seen] - depth_a[v[seen], u[seen]]
    total = int(np.count_nonzero(valid_b))
    if differences.size == 0:
        return {"median_signed_m": None, "median_abs_m": None, "overlap": 0.0, "pixels": 0}
    return {
        "median_signed_m": float(np.median(differences)),
        "median_abs_m": float(np.median(np.abs(differences))),
        "overlap": differences.size / total,
        "pixels": int(differences.size),
    }


def _nearest_per_pixel(pixel: NDArray, depth: NDArray) -> NDArray:
    """Indices of the nearest point for each distinct pixel (a z-buffer)."""
    order = np.lexsort((depth, pixel))
    _, first = np.unique(pixel[order], return_index=True)
    return order[first]


def gap_by_lag(
    load_depth: DepthLoader,
    poses: Sequence[Pose],
    cameras: Sequence[Calibration],
    lags: Sequence[int],
) -> dict[int, list[dict[str, Any] | None]]:
    """For each lag, one entry per frame: its gap to the frame `lag` earlier, or None.

    None means there is no earlier frame, or the two frames are in different tracking
    worlds or segments (their coordinates are unrelated). `load_depth(index)` returns
    (depth, valid); each frame is read once and only the last max(lags)+1 are kept.
    """
    if not lags or any(type(lag) is not int or lag < 1 for lag in lags):
        raise ValueError("Every lag must be a positive whole number of frames")
    if len(poses) != len(cameras):
        raise ValueError("Each frame needs one pose and one calibration")
    keep = max(lags) + 1
    loaded: dict[int, tuple[NDArray, NDArray]] = {}
    series: dict[int, list[dict[str, Any] | None]] = {lag: [] for lag in lags}
    for index, pose in enumerate(poses):
        loaded[index] = load_depth(index)
        loaded.pop(index - keep, None)
        for lag in lags:
            earlier = index - lag
            if earlier < 0 or _origin(poses[earlier]) != _origin(pose):
                series[lag].append(None)
                continue
            series[lag].append(
                surface_gap(*loaded[earlier], poses[earlier], cameras[earlier], *loaded[index], pose, cameras[index])
            )
    return series


def _origin(pose: Pose) -> tuple[str, str]:
    return pose.world_id, pose.segment_id


def median_gap(series: Sequence[dict[str, Any] | None], field: str = "median_abs_m") -> float | None:
    """Median of one field over the frames that have a value; None when none do."""
    values = [entry[field] for entry in series if entry is not None and entry.get(field) is not None]
    return float(np.median(values)) if values else None
