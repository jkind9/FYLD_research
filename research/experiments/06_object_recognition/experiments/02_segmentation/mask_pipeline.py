"""Reusable, lineage-aware mask execution for later validation comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np

from .masks import METHODS, segment


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class MaskResult:
    method: str
    status: str
    mask: np.ndarray
    bounds: tuple[int, int, int, int]
    error: str | None
    prompt_mode: str
    frame_id: str
    coordinate_frame: str
    world_id: str
    segment_id: str
    pose_revision_id: str
    elapsed_seconds: float


@dataclass(frozen=True)
class MaskPipelineResult:
    frame_id: str
    results: tuple[MaskResult, ...]
    total_elapsed_seconds: float


def run_methods(
    rgb: np.ndarray,
    box: list[float],
    methods: tuple[str, ...],
    *,
    frame_id: str,
    prompt_mode: str,
    coordinate_frame: str,
    world_id: str,
    segment_id: str,
    pose_revision_id: str,
) -> MaskPipelineResult:
    """Run deterministic mask methods while preserving original-grid lineage."""
    if not isinstance(methods, tuple) or not methods:
        raise ValueError("Methods must be a non-empty tuple")
    if len(set(methods)) != len(methods) or any(method not in METHODS for method in methods):
        raise ValueError("Methods must be unique supported mask names")
    frame_id = _required_text(frame_id, "frame_id")
    prompt_mode = _required_text(prompt_mode, "prompt_mode")
    coordinate_frame = _required_text(coordinate_frame, "coordinate_frame")
    world_id = _required_text(world_id, "world_id")
    segment_id = _required_text(segment_id, "segment_id")
    pose_revision_id = _required_text(pose_revision_id, "pose_revision_id")
    started = perf_counter()
    records: list[MaskResult] = []
    for method in methods:
        method_started = perf_counter()
        result = segment(rgb, box, method)
        mask = np.asarray(result["mask"], dtype=np.uint8).copy()
        mask.setflags(write=False)
        records.append(
            MaskResult(
                method=method,
                status=result["status"],
                mask=mask,
                bounds=result["bounds"],
                error=result["error"],
                prompt_mode=prompt_mode,
                frame_id=frame_id,
                coordinate_frame=coordinate_frame,
                world_id=world_id,
                segment_id=segment_id,
                pose_revision_id=pose_revision_id,
                elapsed_seconds=max(0.0, perf_counter() - method_started),
            )
        )
    return MaskPipelineResult(
        frame_id=frame_id,
        results=tuple(records),
        total_elapsed_seconds=max(0.0, perf_counter() - started),
    )
