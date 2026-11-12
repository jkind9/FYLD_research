"""Largest touching surface pieces on the adopted room grid."""

import numpy as np
from scipy import ndimage

ROOM_PIECES = 50
ROOM_PIECE_MIN_POINTS = 5000
CELL_M = 0.02


def piece_ranks(points: np.ndarray, cell: float, neighbours: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Each point's piece rank (0 is the largest touching piece) and every piece's point count, largest first.

    Filled cells join when they touch. With `neighbours`, only cells with at least that many filled
    neighbours (of 26) extend a chain, so a thin streak touching a wall can split off. Other filled
    cells join a chain cell they touch, or else form pieces of their own.
    """
    cells = np.floor((points - points.min(0)) / cell).astype(np.int64)
    occupied = np.zeros(cells.max(0) + 1, bool)
    occupied[tuple(cells.T)] = True
    cube = np.ones((3, 3, 3))
    if neighbours:
        around = ndimage.convolve(occupied.astype(np.uint8), cube.astype(np.uint8), mode="constant") - occupied
        chain = occupied & (around >= neighbours)
        grid, count = ndimage.label(chain, structure=cube)
        grid = np.where(chain, grid, ndimage.maximum_filter(grid, size=3) * occupied)
        rest = occupied & (grid == 0)
        grid = np.where(rest, ndimage.label(rest, structure=cube)[0] + count, grid)
    else:
        grid = ndimage.label(occupied, structure=cube)[0]
    labels = grid[tuple(cells.T)]
    counts = np.bincount(labels)  # label 0 is empty space: no point has it, and it sorts last
    order = np.argsort(counts)[::-1]
    rank = np.empty_like(order)
    rank[order] = np.arange(len(order))
    return rank[labels], counts[order[:-1]]


def largest_pieces(
    points: np.ndarray,
    cell: float,
    keep: int = ROOM_PIECES,
    min_points: int = ROOM_PIECE_MIN_POINTS,
) -> np.ndarray:
    """A mask of points in the largest pieces meeting the minimum point count."""
    rank, sizes = piece_ranks(points, cell)
    return (rank < keep) & (sizes[rank] >= min_points)
