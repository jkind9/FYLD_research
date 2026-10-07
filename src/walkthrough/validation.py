"""Independent scoring after prediction hashes are saved; no reference enters a method."""

import importlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Pose

from .records import StepResult
from .steps.contracts import read_pose

tracking_validation = importlib.import_module("experiments.03_camera_pose_estimation.src.validation")
tracking_records = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")
surface_validation = importlib.import_module("experiments.04_surface_reconstruction.src.validation")


@dataclass(frozen=True)
class ScoreRequest:
    component: str
    load_references: Callable[[], Any]
    options: Mapping[str, Any] = field(default_factory=dict)
    reference_file: Path | None = None

    def __post_init__(self) -> None:
        if self.component not in {
            "depth",
            "tracking",
            "surface",
            "mapping",
            "detection",
            "segmentation",
            "appearance",
            "identity",
        }:
            raise ValueError("Unknown experiment validation component")


def _tracking(predictions: dict[str, Any], references: Any, options: Mapping[str, Any]) -> dict[str, Any]:
    records = []
    for row in predictions["records"]:
        pose = read_pose(row["pose"])
        # The frozen scorer groups by segment only; include its world in that key.
        scoring_pose = Pose(pose.matrix, pose.world_id, json.dumps([pose.world_id, pose.segment_id]), pose.source)
        records.append(
            tracking_records.Record(row["frame_id"], row["timestamp_s"], row["status"], scoring_pose, row["reason"])
        )
    return tracking_validation.evaluate(records, references, **options)


def _surface(
    run_path: Path,
    predictions: dict[str, Any],
    references: Mapping[str, Any],
    options: Mapping[str, Any],
) -> dict[str, Any]:
    origin = references["world_id"], references["segment_id"]
    if any((s["world_id"], s["segment_id"]) != origin for s in predictions["shards"]):
        raise ValueError("Surface references must match every scored origin; no silent alignment")
    scorer = surface_validation.SurfaceScorer(references["points"], **options)
    for shard in predictions["shards"]:
        points = np.load(run_path / shard["points"], allow_pickle=False, mmap_mode="r")
        scorer.observe(points)
    return scorer.summary()


def score(run_path: Path, steps: tuple[StepResult, ...], requests: tuple[ScoreRequest, ...]) -> dict[str, Any]:
    available = {step.name: step for step in steps if step.status == "complete"}
    results: dict[str, Any] = {}
    for request in requests:
        component = request.component
        provenance: dict[str, Any] = {
            "reference_source": (str(request.reference_file) if request.reference_file is not None else None),
            "reference_sha256": None,
        }
        if request.reference_file is not None and component in {"tracking", "surface"}:
            try:
                provenance["reference_sha256"] = sha256(request.reference_file)
            except OSError as error:
                if component in available:
                    raise
                provenance["reference_unavailable_reason"] = f"{type(error).__name__}: {error}"
        if component not in {"tracking", "surface"}:
            results[component] = {
                **provenance,
                "status": "unavailable",
                "reason": "Task56 must adapt complete observations to this scorer's independent reference schema",
            }
            continue
        if component not in available:
            blocked = next((step for step in steps if step.name == component), None)
            reason = f"{component} is {blocked.status}: {blocked.reason}" if blocked else f"{component} was not run"
            results[component] = {**provenance, "status": "unavailable", "reason": reason}
            continue
        artifact = available[component].artifact
        if artifact is None:
            raise ValueError("Completed step is missing its saved prediction artifact")
        predictions = json.loads((run_path / artifact).read_text(encoding="utf-8"))
        references = request.load_references()
        results[component] = {
            **provenance,
            "status": "scored",
            "result": (
                _tracking(predictions, references, request.options)
                if component == "tracking"
                else _surface(run_path, predictions, references, request.options)
            ),
        }
    return results
