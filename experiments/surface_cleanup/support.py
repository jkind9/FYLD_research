"""Observation-count and viewing-angle experiments used by the cleanup tuner."""

import numpy as np

from sitescan.cleanup.vote import VOTE_MARGIN_M, VOTE_MARGIN_SHARE
from sitescan.cleanup.vote import measurements as _measurements

MEASURED_M = 2.5
WIDE_ANGLE_DEG = 3.0


def views_measuring(points: np.ndarray, views) -> np.ndarray:
    """The number of views measuring each point within the adopted vote margin."""
    seen_counts = np.zeros(len(points), int)
    for camera_depth, view_depth in _measurements(points, views):
        seen_counts += _agrees(camera_depth, view_depth)
    return seen_counts


def wide_support(
    points: np.ndarray, views, measured_m: float = MEASURED_M, angle_deg: float = WIDE_ANGLE_DEG
) -> np.ndarray:
    """A mask of near-measured points or far points supported from separate viewing spots."""
    nearest, second_widest = spot_evidence(points, views)
    return (nearest < measured_m) | (second_widest >= angle_deg)


def spot_evidence(points: np.ndarray, views) -> tuple[np.ndarray, np.ndarray]:
    """Nearest measured depth and second-widest viewing angle for each point."""
    first_ray, angles_deg = (np.zeros((len(points), 3)), np.zeros((len(points), 2)))
    near_depth_m = np.full(len(points), np.inf)
    for (camera_from_world, _, _), (z, measured) in zip(views, _measurements(points, views)):
        agrees = _agrees(z, measured)
        near_depth_m[agrees] = np.minimum(near_depth_m[agrees], measured[agrees])
        indices = np.flatnonzero(agrees)
        rays = -camera_from_world[:3, :3].T @ camera_from_world[:3, 3] - points[indices]
        rays /= np.linalg.norm(rays, axis=1, keepdims=True)
        unseen = ~first_ray[indices].any(1)
        first_ray[indices[unseen]] = rays[unseen]
        angle = np.where(
            unseen,
            0.0,
            np.degrees(np.arccos(np.clip((rays * first_ray[indices]).sum(1), -1.0, 1.0))),
        )
        top_angle_deg, second_angle_deg = (angles_deg[indices, 0], angles_deg[indices, 1])
        angles_deg[indices, 1] = np.maximum(second_angle_deg, np.minimum(top_angle_deg, angle))
        angles_deg[indices, 0] = np.maximum(top_angle_deg, angle)
    return (near_depth_m, angles_deg[:, 1])


def _agrees(z: np.ndarray, measured: np.ndarray) -> np.ndarray:
    """The view measured the point at its depth, within the vote margin."""
    return (measured > 0) & (
        np.abs(z - measured) <= np.maximum(VOTE_MARGIN_M, VOTE_MARGIN_SHARE * measured)
    )
