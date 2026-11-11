"""Measured camera-plane distances projected onto the colour image."""

import numpy as np

from sitescan.types import ArcoreDepth, Camera

MIN_CONFIDENCE = 128
MAX_DEPTH_AGE_S = 0.1


def depth_targets(
    depth: ArcoreDepth, camera: Camera, *, min_confidence: int = MIN_CONFIDENCE
) -> tuple[np.ndarray, np.ndarray]:
    """Colour pixels and measured depths from confident ARCore depth pixels."""
    rows, cols = np.nonzero((depth.depth_m > 0) & (depth.confidence >= min_confidence))
    raw = depth.camera
    uv = np.c_[
        camera.cx + camera.fx * (cols - raw.cx) / raw.fx,
        camera.cy + camera.fy * (rows - raw.cy) / raw.fy,
    ]
    inside = (
        (uv[:, 0] >= 0) & (uv[:, 0] < camera.width) & (uv[:, 1] >= 0) & (uv[:, 1] < camera.height)
    )
    return uv[inside], depth.depth_m[rows, cols][inside].astype(np.float64)


def point_targets(
    points_world: np.ndarray, points_pixel: np.ndarray, world_from_camera: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray]:
    """Recorded pixels and camera-plane metres for tracked points in front of the camera."""
    if world_from_camera is None or not len(points_world):
        return np.zeros((0, 2)), np.zeros(0)
    camera_from_world = np.linalg.inv(world_from_camera)
    metres = points_world @ camera_from_world[2, :3] + camera_from_world[2, 3]
    keep = metres > 0
    return points_pixel[keep], metres[keep]


def fresh_depth(depth_t_ns: int, camera_t_ns: int, *, max_age_s: float = MAX_DEPTH_AGE_S) -> bool:
    """Whether measured depth is no more than the allowed age behind the camera frame."""
    return camera_t_ns - depth_t_ns <= max_age_s * 1e9
