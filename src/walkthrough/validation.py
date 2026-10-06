"""Scorer-only references, imported through each experiment's validation area."""

import importlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np

from experiments.shared.contracts import Pose
from experiments.shared.runs import Run

from .config import Configuration
from .records import StepResult


@dataclass(frozen=True)
class ScoreRequest:
    component: str
    load_references: Callable[[], Any]
    options: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.component not in {
            "tracking",
            "surface",
            "detection",
            "segmentation",
            "appearance",
            "identity",
        }:
            raise ValueError("Unknown experiment validation component")
        object.__setattr__(self, "options", MappingProxyType(dict(self.options)))


def _readonly(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _readonly(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_readonly(item) for item in value)
    return value


def score_compatible(
    component: str,
    function: str,
    prediction_args: tuple[Any, ...],
    reference_args: tuple[Any, ...],
    **kwargs: Any
) -> Any:
    """Call existing schemas only; Task56 owns complete physical survey adapters."""
    owners = {
        "tracking": (
            "experiments.03_camera_pose_estimation.src.validation",
            {"evaluate"},
        ),
        "surface": (
            "experiments.04_surface_reconstruction.src.validation",
            {"SurfaceScorer"},
        ),
        "detection": (
            "experiments.06_object_recognition.experiments.01_detection.validation",
            {"evaluate"},
        ),
        "segmentation": (
            "experiments.06_object_recognition.experiments.02_segmentation.validation",
            {"mask_scores", "instance_events"},
        ),
        "appearance": (
            "experiments.06_object_recognition.experiments.03_appearance.validation",
            {"label_pairs", "rank_queries"},
        ),
        "identity": (
            "experiments.06_object_recognition.experiments.04_geometry_identity.validation",
            {"score_identity"},
        ),
    }
    if component not in owners or function not in owners[component][1]:
        raise ValueError("Unknown public experiment scorer")
    return getattr(importlib.import_module(owners[component][0]), function)(
        *prediction_args, *reference_args, **kwargs
    )


def _tracking(
    predictions: Mapping[str, Any], references: Any, options: Mapping[str, Any]
) -> dict[str, Any]:
    owner = importlib.import_module(
        "experiments.03_camera_pose_estimation.src.validation"
    )
    records_api = importlib.import_module(
        "experiments.03_camera_pose_estimation.src.tracking"
    )
    records = []
    for row in predictions["records"]:
        p = row["pose"]
        estimated = (
            None
            if p is None
            else Pose(p["T_world_camera"], p["world_id"], p["segment_id"], p["source"])
        )
        records.append(
            records_api.Record(
                row["frame_id"],
                row["timestamp_s"],
                row["status"],
                estimated,
                row["reason"],
            )
        )
    truth = (
        owner.read_references(references)
        if isinstance(references, Path)
        else references
    )
    return owner.evaluate(records, truth, **options)


def _surface(
    run: Run,
    predictions: Mapping[str, Any],
    references: Mapping[str, Any],
    options: Mapping[str, Any],
) -> dict[str, Any]:
    owner = importlib.import_module(
        "experiments.04_surface_reconstruction.src.validation"
    )
    origin = references["world_id"], references["segment_id"]
    shards = predictions["shards"]
    if any((s["world_id"], s["segment_id"]) != origin for s in shards):
        raise ValueError(
            "Surface references must match every scored origin; no silent alignment"
        )
    scorer = owner.SurfaceScorer(references["points"], **options)
    for shard in shards:
        points = np.load(run.path / shard["points"], allow_pickle=False, mmap_mode="r")
        scorer.observe(points)
    return scorer.summary()


def score(
    run: Run,
    config: Configuration,
    states: tuple[StepResult, ...],
    requests: tuple[ScoreRequest, ...],
) -> dict[str, Any]:
    available = {state.name: state for state in states if state.status == "complete"}
    results = {}
    for request in requests:
        component = request.component
        stage = component if component in {"tracking", "surface"} else "objects"
        disabled = (component == "segmentation" and config.segmentation is None) or (
            component == "appearance" and not config.appearance
        )
        if disabled or stage not in available:
            results[component] = {
                "status": "unavailable",
                "reason": "Component disabled or predictions incomplete",
            }
            continue
        if component not in {"tracking", "surface"}:
            results[component] = {
                "status": "unavailable",
                "reason": "Task56 must adapt complete observations to this scorer's independent reference schema",
            }
            continue
        artifact = available[stage].artifact
        if artifact is None:
            raise ValueError("Completed step is missing its saved prediction artifact")
        predictions = _readonly(
            json.loads((run.path / artifact).read_text(encoding="utf-8"))
        )
        # No method or disabled component receives this loader or its answers.
        references = request.load_references()
        results[component] = (
            _tracking(predictions, references, request.options)
            if component == "tracking"
            else _surface(run, predictions, references, request.options)
        )
    return results
