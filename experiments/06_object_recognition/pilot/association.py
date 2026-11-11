"""Same-class counting for the pilot replays: the product method with the pilot's settings check."""

from __future__ import annotations

import numpy as np

from sitescan.objects.match import associate_frame as _associate_frame


def associate_frame(
    detections: list[dict],
    tracks: dict[str, dict],
    next_number: int,
    max_distance_m: float,
    ambiguity_margin_m: float,
) -> tuple[list[dict], dict[str, dict], int]:
    """Assign same-class detections one-to-one, preserving ambiguous results."""
    if (
        not np.isfinite([max_distance_m, ambiguity_margin_m]).all()
        or max_distance_m <= 0
        or ambiguity_margin_m < 0
        or isinstance(next_number, bool)
        or not isinstance(next_number, int)
        or next_number < 1
    ):
        raise ValueError("Association settings must be finite and positive")
    return _associate_frame(detections, tracks, next_number, max_distance_m, ambiguity_margin_m)
