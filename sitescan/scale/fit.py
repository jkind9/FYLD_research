"""Median scale fits shared by the live and room pipelines."""

import cv2
import numpy as np

CELLS = (8, 6)
MIN_DEPTH_PIXELS = 50
MIN_CELL_PIXELS = 20
MIN_POINTS = 20


def pixel_rows_cols(uv: np.ndarray, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    """Integer rows and columns of pixel positions, clipped to the image."""
    return np.clip(uv[:, 1].astype(int), 0, height - 1), np.clip(uv[:, 0].astype(int), 0, width - 1)


def weighted_median(values: np.ndarray, weight: np.ndarray | None = None) -> float:
    """The median; with weights, the first value where the sorted weights reach half their sum."""
    if weight is None:
        return float(np.median(values))
    order = np.argsort(values)
    cumulative = np.cumsum(weight[order])
    return float(values[order][np.searchsorted(cumulative, 0.5 * cumulative[-1])])


def fit_ratio(
    model_depth: np.ndarray, target_depth: np.ndarray, weight: np.ndarray | None = None
) -> float | None:
    """Median target-to-learned ratio from at least two positive, finite depth pairs."""
    good = (
        np.isfinite(model_depth)
        & np.isfinite(target_depth)
        & (model_depth > 0)
        & (target_depth > 0)
    )
    if np.count_nonzero(good) < 2:
        return None
    ratio = target_depth[good] / model_depth[good]
    return weighted_median(ratio, None if weight is None else weight[good])


def fit_one(
    model: np.ndarray,
    valid: np.ndarray,
    uv: np.ndarray,
    target: np.ndarray,
    minimum: int = MIN_DEPTH_PIXELS,
    weight: np.ndarray | None = None,
) -> float | None:
    """One median scale for a frame, weighted if weights are given; None without enough targets."""
    height, width = model.shape
    rows, cols = pixel_rows_cols(uv, width, height)
    keep = valid[rows, cols]
    if np.count_nonzero(keep) < minimum:
        return None
    kept_weight = None if weight is None else weight[keep]
    return fit_ratio(model[rows, cols][keep], target[keep], kept_weight)


def cell_index(uv: np.ndarray, image_size, cells: tuple[int, int] = CELLS) -> np.ndarray:
    """Row-major grid cell IDs for colour pixels, clipped to the image bounds."""
    width, height = image_size
    nx, ny = cells
    rows, cols = pixel_rows_cols(uv, width, height)
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
    weight: np.ndarray | None = None,
) -> np.ndarray | None:
    """Blended per-pixel scale, with cell medians fitted in log space.

    Unsupported cells use the frame median log ratio or the supplied log-scale fallback.
    With weights, every median is a weighted median.
    """
    height, width = model.shape
    rows, cols = pixel_rows_cols(uv, width, height)
    keep = valid[rows, cols] & (model[rows, cols] > 0)
    if np.count_nonzero(keep) < minimum:
        return None
    log_ratio = np.log(target[keep] / model[rows[keep], cols[keep]])
    kept_weight = None if weight is None else weight[keep]
    nx, ny = cells
    frame_log_scale = weighted_median(log_ratio, kept_weight) if fallback is None else fallback
    grid = np.full((ny, nx), frame_log_scale)
    indices = cell_index(uv[keep], (width, height), cells)
    for index in np.unique(indices):
        mine = indices == index
        if np.count_nonzero(mine) >= min_cell_pixels:
            cell_weight = None if weight is None else kept_weight[mine]
            grid.flat[index] = weighted_median(log_ratio[mine], cell_weight)
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
