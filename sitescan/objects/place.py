"""Where a detected object sits: the median of the measured surface inside its box."""

import numpy as np

from sitescan.types import Camera


def box_pixels(shape: tuple[int, int], xyxy) -> np.ndarray:
    """Pixels whose centres fall inside the box."""
    x1, y1, x2, y2 = xyxy
    v, u = np.indices(shape)
    return (u + 0.5 >= x1) & (u + 0.5 < x2) & (v + 0.5 >= y1) & (v + 0.5 < y2)


def box_position(
    depth: np.ndarray, valid: np.ndarray, camera: Camera, xyxy, world_from_camera: np.ndarray
) -> np.ndarray | None:
    """World position of the coordinate-wise median of the box's valid surface points.

    The box also covers background, so this is a visible-surface sample, not the object's centre.
    None when no pixel in the box has valid depth.
    """
    v, u = np.nonzero(valid & box_pixels(depth.shape, xyxy))
    if not len(v):
        return None
    z = depth[v, u]
    points = np.column_stack(((u - camera.cx) * z / camera.fx, (v - camera.cy) * z / camera.fy, z))
    median = np.median(points, axis=0)
    return median @ world_from_camera[:3, :3].T + world_from_camera[:3, 3]
