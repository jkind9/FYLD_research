"""Observed metric grids on a fitted reference plane."""

import numpy as np

from .plane import INLIER_DISTANCE_M, scatter_axes
from .types import Footprint, Plane

CELL_SIZE_M = 0.05
MAX_GRID_CELLS = 16_000_000


def onto_plane(chunk: np.ndarray, point: np.ndarray, normal: np.ndarray):
    """Signed height and projected world points on the reference plane."""
    heights = (chunk - point) @ normal
    return heights, chunk - np.outer(heights, normal)


def signed_axes(axes: np.ndarray) -> np.ndarray:
    """Axes oriented so each largest-magnitude component is positive."""
    return np.vstack([axis * np.sign(axis[np.argmax(np.abs(axis))]) for axis in axes])


def grid_shape(coordinates: np.ndarray, cell_size_m: float):
    """Grid origin coordinates and shape, retaining the existing allocation limit."""
    minimum = coordinates.min(axis=0)
    maximum = coordinates.max(axis=0)
    shape = tuple(int(size) for size in np.floor((maximum - minimum) / cell_size_m) + 1)
    if shape[0] * shape[1] > MAX_GRID_CELLS:
        raise ValueError(
            f"Grid would need {shape[0] * shape[1]:,} cells (limit {MAX_GRID_CELLS:,}); "
            f"the points span {maximum[0] - minimum[0]:.1f} m by {maximum[1] - minimum[1]:.1f} m"
        )
    return minimum, shape


def fill_grid(cells: np.ndarray, heights: np.ndarray, shape, band_m: float):
    """Observed cells, plane-band cells and the highest signed height per cell."""
    observed = np.zeros(shape, dtype=np.bool_)
    plane_cells = np.zeros(shape, dtype=np.bool_)
    max_height = np.full(shape, -np.inf)
    observed[cells[:, 0], cells[:, 1]] = True
    on_plane = np.abs(heights) <= band_m
    plane_cells[cells[on_plane, 0], cells[on_plane, 1]] = True
    np.maximum.at(max_height, (cells[:, 0], cells[:, 1]), heights)
    max_height[~observed] = np.nan
    return observed, plane_cells, max_height


def footprint(
    points: np.ndarray,
    plane: Plane,
    up: np.ndarray,
    *,
    cell_size_m: float = CELL_SIZE_M,
    band_m: float = INLIER_DISTANCE_M,
) -> Footprint:
    """A plane-aligned grid of observed area, dimensions and signed surface heights."""
    points = np.asarray(points, dtype=np.float64)
    normal = plane.normal / np.linalg.norm(plane.normal)
    if normal @ up < 0:
        normal = -normal
    oriented = Plane(plane.point, normal, plane.inlier_fraction, plane.source)
    heights, projected = onto_plane(points, plane.point, normal)
    local = projected[np.abs(heights) <= band_m] - plane.point
    total = np.zeros(3)
    outer = np.zeros((3, 3))
    total += local.sum(axis=0)
    outer += local.T @ local
    _, axes = scatter_axes(plane.point, total, outer, len(local))
    basis = signed_axes(axes[:2])
    coordinates = projected @ basis.T
    minimum, shape = grid_shape(coordinates, cell_size_m)
    cells = np.floor((coordinates - minimum) / cell_size_m).astype(np.int64)
    observed, plane_cells, max_height = fill_grid(cells, heights, shape, band_m)
    origin = minimum @ basis + (plane.point @ normal) * normal
    return Footprint(
        oriented, basis, origin, float(cell_size_m), observed, plane_cells, max_height, len(points)
    )
