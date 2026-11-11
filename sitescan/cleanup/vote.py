"""Weighted surface support and free-space evidence from depth views."""

import numpy as np

VOTE_MARGIN_M = 0.08
VOTE_MARGIN_SHARE = 0.05
VOTE_FAR_M = 8.0
MIN_POINT_DEPTH_M = 0.1
MIN_VOTE_DEPTH_M = 0.5


def measurements(points: np.ndarray, views):
    """Per-view camera depths and measured depths at rounded colour pixels.

    Each view supplies a camera_from_world projection matrix, intrinsics and depth.
    Missing, behind-camera and out-of-image observations have zero measured depth.
    """
    for camera_from_world, (fx, fy, cx, cy), depth in views:
        height, width = depth.shape
        camera = points @ camera_from_world[:3, :3].T + camera_from_world[:3, 3]
        z = camera[:, 2]
        ahead = z > MIN_POINT_DEPTH_M
        denominator = np.where(ahead, z, 1.0)
        cols = np.round(camera[:, 0] / denominator * fx + cx).astype(int)
        rows = np.round(camera[:, 1] / denominator * fy + cy).astype(int)
        inside = ahead & (cols >= 0) & (cols < width) & (rows >= 0) & (rows < height)
        measured = np.zeros(len(points))
        measured[inside] = depth[rows[inside], cols[inside]]
        yield z, measured


def vote_tallies(
    points: np.ndarray,
    views,
    *,
    margin_m: float = VOTE_MARGIN_M,
    margin_share: float = VOTE_MARGIN_SHARE,
    min_depth_m: float = MIN_VOTE_DEPTH_M,
) -> tuple[np.ndarray, np.ndarray]:
    """Weighted support and see-through opposition for each point, in input order."""
    support = np.zeros(len(points))
    against = np.zeros(len(points))
    for z, measured in measurements(points, views):
        seen = measured > 0
        margin = np.maximum(margin_m, margin_share * measured)
        weight = 1.0 / np.maximum(measured, min_depth_m) ** 2
        support += np.where(seen & (np.abs(z - measured) <= margin), weight, 0.0)
        against += np.where(seen & (z < measured - margin), weight, 0.0)
    return support, against


def visibility_vote(points: np.ndarray, views) -> np.ndarray:
    """Keep points with support at least equal to see-through opposition."""
    support, against = vote_tallies(points, views)
    return support >= against
