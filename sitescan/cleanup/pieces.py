"""Largest touching surface pieces on the adopted room grid."""

import numpy as np
from scipy import ndimage

ROOM_PIECES = 50
ROOM_PIECE_MIN_POINTS = 5000
CELL_M = 0.02


def largest_pieces(
    points: np.ndarray,
    cell: float,
    keep: int = ROOM_PIECES,
    min_points: int = ROOM_PIECE_MIN_POINTS,
) -> np.ndarray:
    """A mask of points in the largest pieces meeting the minimum point count."""
    cells = np.floor((points - points.min(0)) / cell).astype(np.int64)
    occupied = np.zeros(cells.max(0) + 1, bool)
    occupied[tuple(cells.T)] = True
    labels = ndimage.label(occupied, structure=np.ones((3, 3, 3)))[0][tuple(cells.T)]
    counts = np.bincount(labels)
    largest = np.argsort(counts)[::-1][:keep]
    return np.isin(labels, largest[counts[largest] >= min_points])
