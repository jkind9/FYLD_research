"""Rejected per-frame masks and near-depth fusion weighting."""

import cv2
import numpy as np

EDGE_JUMP = 0.05
MAX_VIEW_ANGLE_DEG = 75.0
NORMAL_STEP = 2
NEAR_FIRST_BANDS = ((0.0, 1.0, 16), (1.0, 2.0, 4), (2.0, 3.0, 2), (3.0, np.inf, 1))


def edge_mask(depth: np.ndarray, jump: float = EDGE_JUMP) -> np.ndarray:
    """A mask of local depth jumps relative to each pixel's depth."""
    d = depth.astype(np.float32)
    kernel = np.ones((3, 3), np.uint8)
    return (depth > 0) & (cv2.dilate(d, kernel) - cv2.erode(d, kernel) > jump * depth)


def view_angle_mask(
    depth: np.ndarray,
    intrinsics,
    max_angle_deg: float = MAX_VIEW_ANGLE_DEG,
    step: int = NORMAL_STEP,
) -> np.ndarray:
    """A mask of surface pixels seen beyond the allowed angle from their normal."""
    fx, fy, cx, cy = intrinsics
    height, width = depth.shape
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    camera_points = np.dstack(((cols - cx) / fx * depth, (rows - cy) / fy * depth, depth))
    across = np.roll(camera_points, -step, axis=1) - np.roll(camera_points, step, axis=1)
    down = np.roll(camera_points, -step, axis=0) - np.roll(camera_points, step, axis=0)
    normals = np.cross(across, down)
    cosine = np.abs((normals * camera_points).sum(-1)) / (
        np.linalg.norm(normals, axis=-1) * np.linalg.norm(camera_points, axis=-1) + 1e-12
    )
    mask = (depth > 0) & (cosine < np.cos(np.radians(max_angle_deg)))
    mask[:step], mask[-step:], mask[:, :step], mask[:, -step:] = (False, False, False, False)
    return mask


def near_first_passes(depth: np.ndarray, bands=NEAR_FIRST_BANDS) -> list[tuple[np.ndarray, int]]:
    """Depth bands and repeat counts for the rejected near-first fusion trial."""
    result = []
    for near_m, far_m, repeats in bands:
        keep = (depth > 0) & (depth >= near_m) & (depth < far_m)
        if keep.any():
            result.append((np.where(keep, depth, 0.0), repeats))
    return result
