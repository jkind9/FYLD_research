"""Adopted visibility voting and largest surface pieces."""

import numpy as np

from .pieces import CELL_M, ROOM_PIECE_MIN_POINTS, ROOM_PIECES, largest_pieces
from .vote import visibility_vote, vote_tallies

__all__ = ["clean_room", "largest_pieces", "visibility_vote", "vote_tallies"]


def clean_room(
    points: np.ndarray,
    views,
    *,
    cell: float = CELL_M,
    keep: int = ROOM_PIECES,
    min_points: int = ROOM_PIECE_MIN_POINTS,
) -> np.ndarray:
    """An input-order mask after visibility voting and keeping the largest pieces."""
    mask = visibility_vote(points, views)
    if np.any(mask):
        mask[mask] = largest_pieces(points[mask], cell, keep, min_points)
    return mask
