"""Low-resolution depth prompts for Prompt Depth Anything, built from a frame's SfM points."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.spatial import QhullError

MIN_POINTS = 4  # a triangulation needs a triangle plus one more


def largest_model(rows: list[dict]) -> int:
    """ID of the SfM model that placed the most frames."""
    ids = [row["model_id"] for row in rows if row["model_id"] is not None]
    return max(set(ids), key=ids.count)


def frame_points(rows: list[dict], xyz: np.ndarray, observations: dict[str, np.ndarray], keep_point: np.ndarray,
                 k: int, *, size: float, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    """Pixels and depth in metres of frame k's kept SfM points that lie in front of the camera and in the image."""
    mask = (observations["frame_index"] == k) & keep_point[observations["point_index"]]
    world_from_camera = np.array(rows[k]["T_world_camera"])
    camera = (xyz[observations["point_index"][mask]] - world_from_camera[:3, 3]) @ world_from_camera[:3, :3]
    uv = observations["uv"][mask]
    inside = (camera[:, 2] > 0) & (uv[:, 0] >= 0) & (uv[:, 1] >= 0) & (uv[:, 0] < width) & (uv[:, 1] < height)
    return uv[inside], camera[inside, 2] * size


def prompt_map(uv: np.ndarray, depth_m: np.ndarray, image_hw: tuple[int, int], grid_hw: tuple[int, int],
               fill: str) -> np.ndarray | None:
    """Grid of depth in metres filled between points; None when there are too few points to fill it.

    The model rescales its output by the prompt's smallest and largest value, so the grid must hold
    real depth everywhere (zeros would set the smallest value to 0).
    """
    if len(depth_m) < MIN_POINTS:
        return None
    rows = (np.arange(grid_hw[0]) + 0.5) * image_hw[0] / grid_hw[0]
    columns = (np.arange(grid_hw[1]) + 0.5) * image_hw[1] / grid_hw[1]
    x, y = np.meshgrid(columns, rows)
    nearest = NearestNDInterpolator(uv, depth_m)
    if fill == "nearest":
        return nearest(x, y).astype(np.float32)
    try:
        filled = LinearNDInterpolator(uv, depth_m)(x, y)
    except QhullError:
        return None
    return np.where(np.isnan(filled), nearest(x, y), filled).astype(np.float32)
