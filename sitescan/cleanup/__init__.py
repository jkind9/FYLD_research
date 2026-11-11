"""Adopted visibility voting and largest surface pieces."""

from typing import NamedTuple

import numpy as np

from .pieces import CELL_M, ROOM_PIECE_MIN_POINTS, ROOM_PIECES, largest_pieces
from .vote import visibility_vote, vote_tallies

__all__ = ["Cleaned", "clean_room", "largest_pieces", "visibility_vote", "vote_tallies"]


class Cleaned(NamedTuple):
    """Input-order masks: points the vote kept, and points kept after the piece filter too."""

    voted: np.ndarray
    kept: np.ndarray


def clean_room(
    points: np.ndarray,
    views,
    *,
    cell: float = CELL_M,
    keep: int = ROOM_PIECES,
    min_points: int = ROOM_PIECE_MIN_POINTS,
) -> Cleaned:
    """Visibility vote, then keep the largest pieces of what the vote left."""
    voted = visibility_vote(points, views)
    kept = voted.copy()
    if np.any(voted):
        kept[voted] = largest_pieces(points[voted], cell, keep, min_points)
    return Cleaned(voted, kept)
