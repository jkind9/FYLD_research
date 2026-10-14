"""One size per processed frame for learned depth, from ARCore's raw depth, else its tracked points, else the last size.

The size multiplies the model's depth (median of target / model at matched pixels, Task72's rule).
"""

from __future__ import annotations

import importlib

import numpy as np

from .stream import session_v1

dense = importlib.import_module("experiments.sfm.src.dense")

MIN_CONFIDENCE = 128  # Google's suggested cut-off for raw depth confidence (0-255)
MIN_DEPTH_PIXELS = 50  # learning chapter 2: about 50 good points per frame are enough
MIN_POINTS = 20  # Task72's minimum tracked points per frame


def depth_targets(depth: session_v1.Depth, image_k, image_size) -> tuple[np.ndarray, np.ndarray]:
    """Confident raw depth pixels as (image pixel u, v) and depth in metres along the camera axis.

    The depth image has its own field of view and intrinsics, so each pixel goes back to a 3D
    camera point and forward into the sent image.
    """
    y, x = np.nonzero((depth.depth_m > 0) & (depth.confidence >= MIN_CONFIDENCE))
    fx, fy, cx, cy = depth.intrinsics
    fxi, fyi, cxi, cyi = image_k
    uv = np.c_[cxi + fxi * (x - cx) / fx, cyi + fyi * (y - cy) / fy]
    inside = (uv[:, 0] >= 0) & (uv[:, 0] < image_size[0]) & (uv[:, 1] >= 0) & (uv[:, 1] < image_size[1])
    return uv[inside], depth.depth_m[y, x][inside].astype(np.float64)


def point_targets(frame: session_v1.Frame) -> tuple[np.ndarray, np.ndarray]:
    """Tracked points in front of the camera as (pixel, depth along the camera axis)."""
    if frame.pose is None or not len(frame.point_ids):
        return np.zeros((0, 2)), np.zeros(0)
    camera_from_world = np.linalg.inv(session_v1.world_from_camera(frame.pose))
    z = -(frame.points_world @ camera_from_world[2, :3] + camera_from_world[2, 3])
    keep = z > 0
    return frame.points_pixel[keep], z[keep]


def _fit(model: np.ndarray, valid: np.ndarray, uv: np.ndarray, target: np.ndarray, minimum: int) -> float | None:
    h, w = model.shape
    cols, rows = np.clip(uv[:, 0].astype(int), 0, w - 1), np.clip(uv[:, 1].astype(int), 0, h - 1)
    keep = valid[rows, cols]
    if keep.sum() < minimum:
        return None
    fitted = dense.fit_size(model[rows, cols][keep], target[keep])
    return None if fitted is None else fitted[0]


def frame_size(model: np.ndarray, valid: np.ndarray, frame: session_v1.Frame,
               previous: float | None) -> tuple[float | None, str]:
    """(size, where it came from): arcore_depth, tracked_points, previous or none."""
    if frame.depth is not None:
        size = _fit(model, valid, *depth_targets(frame.depth, frame.intrinsics, frame.image_size), MIN_DEPTH_PIXELS)
        if size is not None:
            return size, "arcore_depth"
    size = _fit(model, valid, *point_targets(frame), MIN_POINTS)
    if size is not None:
        return size, "tracked_points"
    return (previous, "previous") if previous is not None else (None, "none")
