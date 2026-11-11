"""One size per processed frame for learned depth, from ARCore's raw depth, else its tracked points, else the last size.

The size multiplies the model's depth (median of target / model at matched pixels, Task72's rule).
"""

from __future__ import annotations

import numpy as np

from sitescan import scale
from sitescan.scale.fit import MIN_DEPTH_PIXELS, MIN_POINTS
from sitescan.scale.fit import fit_one as _fit
from sitescan.scale.targets import MIN_CONFIDENCE  # noqa: F401
from sitescan.types import ArcoreDepth, Camera

from .stream import session_v1


def depth_targets(depth: session_v1.Depth, image_k, image_size) -> tuple[np.ndarray, np.ndarray]:
    """Measured targets adapted from the wire depth record."""
    height, width = depth.depth_m.shape
    raw = ArcoreDepth(depth.t_ns, depth.depth_m, depth.confidence,
                      Camera(*depth.intrinsics, width, height))
    return scale.depth_targets(raw, Camera(*image_k, *image_size))


def point_targets(frame: session_v1.Frame) -> tuple[np.ndarray, np.ndarray]:
    """Tracked targets adapted from a wire camera pose."""
    pose = None if frame.pose is None else session_v1.world_from_camera_cv(frame.pose)
    return scale.point_targets(frame.points_world, frame.points_pixel, pose)


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
