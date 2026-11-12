"""Measured scale targets for one frame, chosen by name. Both pipelines read the same names.

| Name | Targets |
|---|---|
| arcore_depth | ARCore's confident raw depth |
| tracked_points | The tracker's 3D points carried in the record (ARCore's today) |
| sparse | Features triangulated against earlier keyframes, weighted by their depth error |
| dense | Plane-sweep depth between keyframes, searched around the sparse-scaled learned depth |
"""

import numpy as np

from sitescan import scale, session
from sitescan.scale.fit import MIN_DEPTH_PIXELS, MIN_POINTS
from sitescan.triangulate import SparseDepth
from sitescan.types import MeasuredDepth

SOURCES = ("arcore_depth", "tracked_points", "sparse", "dense")
TRIANGULATED = ("sparse", "dense")
MINIMUM = {
    "arcore_depth": MIN_DEPTH_PIXELS,
    "tracked_points": MIN_POINTS,
    "sparse": MIN_POINTS,
    "dense": MIN_DEPTH_PIXELS,
}
TOO_FEW = {
    "arcore_depth": "too_few_depth_pixels",
    "tracked_points": "too_few_tracked_points",
    "sparse": "too_few_sparse_points",
    "dense": "too_few_dense_pixels",
}
FITS = ("grid", "power")


def scale_targets(
    source: str,
    frame,
    pose: np.ndarray | None,
    sparse: SparseDepth | None = None,
    dense: MeasuredDepth | None = None,
) -> tuple | None:
    """(colour pixels, metres, weights or None) from a named source; None if the frame lacks it."""
    if source == "arcore_depth":
        if frame.depth is None:
            return None
        return (
            *scale.depth_targets(session.arcore_depth(frame.depth), session.camera(frame)),
            None,
        )
    if source == "tracked_points":
        return (*scale.point_targets(frame.points_world, frame.points_pixel, pose), None)
    if source == "sparse":
        if sparse is None:
            return None
        return sparse.uv, sparse.depth_m, scale.target_weights(sparse.depth_m, sparse.sigma_m)
    if source == "dense":
        return None if dense is None else (*scale.depth_targets(dense, session.camera(frame)), None)
    raise ValueError(f"unknown scale source {source!r}; choose from {SOURCES}")


def sweep_prior(
    learned: np.ndarray, valid: np.ndarray, sparse: SparseDepth | None
) -> np.ndarray | None:
    """Learned depth times the sparse points' scale, where the plane sweep searches; or None."""
    if sparse is None:
        return None
    fitted = scale.fit_one(
        learned,
        valid,
        sparse.uv,
        sparse.depth_m,
        MIN_POINTS,
        scale.target_weights(sparse.depth_m, sparse.sigma_m),
    )
    return None if fitted is None else np.where(valid, learned * fitted, np.nan)


def fit_scale(fit: str, learned, valid, uv, metres, weight, minimum: int) -> np.ndarray | None:
    """Per-pixel scale from the named fit: "grid" (8 x 6 cell medians) or "power" (by distance)."""
    if fit == "grid":
        return scale.fit_grid(learned, valid, uv, metres, minimum=minimum, weight=weight)
    if fit == "power":
        return scale.fit_power(learned, valid, uv, metres, weight, minimum=minimum)
    raise ValueError(f"unknown scale fit {fit!r}; choose from {FITS}")
