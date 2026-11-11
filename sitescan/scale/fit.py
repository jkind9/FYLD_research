"""Median scale fits shared by the live and room pipelines."""

import cv2
import numpy as np

CELLS = (8, 6)
MIN_DEPTH_PIXELS = 50
MIN_CELL_PIXELS = 20
MIN_POINTS = 20


def fit_ratio(model_depth: np.ndarray, target_depth: np.ndarray) -> float | None:
    """Median target-to-learned ratio from at least two positive, finite depth pairs."""
    good = (
        np.isfinite(model_depth)
        & np.isfinite(target_depth)
        & (model_depth > 0)
        & (target_depth > 0)
    )
    if np.count_nonzero(good) < 2:
        return None
    return float(np.median(target_depth[good] / model_depth[good]))


def fit_one(
    model: np.ndarray,
    valid: np.ndarray,
    uv: np.ndarray,
    target: np.ndarray,
    minimum: int = MIN_DEPTH_PIXELS,
) -> float | None:
    """One median scale for a frame, or None without enough valid target pixels."""
    height, width = model.shape
    cols = np.clip(uv[:, 0].astype(int), 0, width - 1)
    rows = np.clip(uv[:, 1].astype(int), 0, height - 1)
    keep = valid[rows, cols]
    if np.count_nonzero(keep) < minimum:
        return None
    return fit_ratio(model[rows, cols][keep], target[keep])


def cell_index(uv: np.ndarray, image_size, cells: tuple[int, int] = CELLS) -> np.ndarray:
    """Row-major grid cell IDs for colour pixels, clipped to the image bounds."""
    width, height = image_size
    nx, ny = cells
    cols = np.clip(uv[:, 0].astype(int), 0, width - 1)
    rows = np.clip(uv[:, 1].astype(int), 0, height - 1)
    return np.minimum(rows * ny // height, ny - 1) * nx + np.minimum(cols * nx // width, nx - 1)


def fit_grid(
    model: np.ndarray,
    valid: np.ndarray,
    uv: np.ndarray,
    target: np.ndarray,
    cells: tuple[int, int] = CELLS,
    fallback: float | None = None,
    *,
    minimum: int = MIN_DEPTH_PIXELS,
    min_cell_pixels: int = MIN_CELL_PIXELS,
) -> np.ndarray | None:
    """Blended per-pixel scale, with cell medians fitted in log space.

    Unsupported cells use the frame median log ratio or the supplied log-scale fallback.
    """
    height, width = model.shape
    cols = np.clip(uv[:, 0].astype(int), 0, width - 1)
    rows = np.clip(uv[:, 1].astype(int), 0, height - 1)
    keep = valid[rows, cols] & (model[rows, cols] > 0)
    if np.count_nonzero(keep) < minimum:
        return None
    log_ratio = np.log(target[keep] / model[rows[keep], cols[keep]])
    nx, ny = cells
    grid = np.full((ny, nx), np.median(log_ratio) if fallback is None else fallback)
    indices = cell_index(uv[keep], (width, height), cells)
    for index in np.unique(indices):
        mine = indices == index
        if np.count_nonzero(mine) >= min_cell_pixels:
            grid.flat[index] = np.median(log_ratio[mine])
    return np.exp(cv2.resize(grid, (width, height), interpolation=cv2.INTER_LINEAR))


def supported_pixels(
    uv: np.ndarray, shape, cells: tuple[int, int] = CELLS, *, min_cell_pixels: int = MIN_CELL_PIXELS
) -> np.ndarray:
    """Pixels in grid cells with enough measured depth samples for their own scale."""
    height, width = shape
    nx, ny = cells
    counts = np.bincount(cell_index(uv, (width, height), cells), minlength=nx * ny).reshape(ny, nx)
    rows = np.minimum(np.arange(height) * ny // height, ny - 1)
    cols = np.minimum(np.arange(width) * nx // width, nx - 1)
    return counts[rows[:, None], cols[None, :]] >= min_cell_pixels
