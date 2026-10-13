"""TUM RGB/depth selection for offline depth evaluation."""

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

_tum_reader = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.dataset"
)
SAMPLE_STRIDE = 10


@dataclass(frozen=True)
class TumDepthFrame:
    """Selected RGB input and its separate evaluator-only depth reference."""

    frame_id: str
    timestamp_s: float
    colour: NDArray[np.uint8]
    reference_depth_m: NDArray[np.float64]
    reference_valid: NDArray[np.bool_]


@dataclass(frozen=True)
class TumDepthSelection:
    """Every tenth timestamp-associated RGB/depth pair from one TUM sequence."""

    sequence: str
    source_root: Path
    matched_pair_count: int
    stride: int
    frames: tuple[TumDepthFrame, ...]


def select_tum_frames(root: Path, stride: int = SAMPLE_STRIDE) -> TumDepthSelection:
    """Load a deterministic sample using experiment 03's TUM reader."""
    if isinstance(stride, bool) or not isinstance(stride, int) or stride < 1:
        raise ValueError("Sampling stride must be a positive integer")

    _, initial_counts = _tum_reader.associations(root, 1)
    rows, counts = _tum_reader.associations(root, initial_counts["matched_rows"])
    selected = tuple(
        _to_depth_frame(_tum_reader.load_frame(root, row))
        for row in rows[::stride]
    )
    if not selected:
        raise ValueError("TUM sequence has no matched RGB/depth pairs")
    return TumDepthSelection(
        sequence=root.name,
        source_root=root,
        matched_pair_count=counts["matched_rows"],
        stride=stride,
        frames=selected,
    )


def _to_depth_frame(frame: Any) -> TumDepthFrame:
    """Copy only the color input and evaluator reference fields we need."""
    return TumDepthFrame(
        frame_id=frame.frame_id,
        timestamp_s=frame.timestamp_s,
        colour=frame.colour,
        reference_depth_m=frame.depth,
        reference_valid=frame.valid,
    )
