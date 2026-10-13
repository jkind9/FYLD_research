"""Independent scoring after prediction hashes are saved; no reference enters a method."""

import importlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Pose

from .records import StepResult
from .steps.contracts import read_pose

tracking_validation = importlib.import_module("experiments.03_camera_pose_estimation.src.validation")
tracking_records = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")
surface_validation = importlib.import_module("experiments.04_surface_reconstruction.src.validation")
depth_scoring = importlib.import_module("experiments.02_stereo_depth.scoring")
depth_evaluation = importlib.import_module("experiments.02_stereo_depth.evaluate")
depth_geometry = importlib.import_module("experiments.02_stereo_depth.geometry")
SCORED_COMPONENTS = {"depth", "tracking", "surface"}


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


def _depth(run_path: Path, predictions: dict[str, Any], read_reference: Any) -> dict[str, Any]:
    """Score each saved depth frame against reference depth for the same capture time.

    `read_reference` is a depth estimator over frames (for example RecordedSensorDepth's
    loaded reader); it receives only frame IDs and timestamps from capture.json, here in
    the scorer, after predictions were sealed. Metric view only: raw metres, no fitting.
    """
    capture = json.loads((run_path / "output/predictions/capture.json").read_text(encoding="utf-8"))
    timestamps = {row["frame_id"]: row["timestamp_s"] for row in capture["frames"]}
    rows = []
    for frame in predictions["frames"]:
        stand_in = SimpleNamespace(frame_id=frame["frame_id"], timestamp_s=timestamps[frame["frame_id"]])
        (reference,) = list(read_reference(iter([stand_in]), run=None))
        reference_valid = np.asarray(reference.valid, dtype=bool)
        with np.load(run_path / frame["arrays"], allow_pickle=False) as arrays:
            scored = depth_scoring.score_depth(arrays["depth"], arrays["valid"], reference.depth, reference_valid)
            scale = _frame_scale(arrays["depth"], arrays["valid"], reference.depth, reference_valid)
        rows.append({"frame_id": frame["frame_id"], **scored, "scale": scale})
    pooled = depth_evaluation.aggregate_scores(rows)
    per_frame = [
        {"frame_id": row["frame_id"], **row["overall"], **row["scale"], "distance_bands": row["distance_bands"]}
        for row in rows
    ]
    return {**pooled, "per_frame": per_frame, "view": "raw metres against reference depth"}


def _frame_scale(depth: Any, valid: Any, reference_depth: Any, reference_valid: Any) -> dict[str, float | None]:
    """How far off this frame's scale is, and the error left after correcting it.

    `scale_ratio` is the median predicted/reference distance (1.34 = 34% too far).
    `fit_scale` and `fit_shift` map prediction to reference by least squares in metres, and
    `fitted_abs_rel` is the error after that fit: what a perfect per-frame scale would leave.
    Fewer than two shared pixels gives None for all four, never NaN.
    """
    predicted = np.where(valid, depth, np.nan)
    shared = depth_geometry.alignment_fit_pixels(predicted, "metric_depth", reference_depth, reference_valid)
    if np.count_nonzero(shared) < 2:
        return {"scale_ratio": None, "fit_scale": None, "fit_shift": None, "fitted_abs_rel": None}
    ratio = float(np.median(predicted[shared] / reference_depth[shared]))
    fit_scale, fit_shift = depth_geometry.fit_native_alignment(predicted, "metric_depth", reference_depth, shared)
    fitted = depth_scoring.score_shape_to_metric(predicted, "metric_depth", reference_depth, reference_valid)
    return {
        "scale_ratio": ratio,
        "fit_scale": fit_scale,
        "fit_shift": fit_shift,
        "fitted_abs_rel": fitted["overall"]["abs_rel"],
    }


def score(run_path: Path, steps: tuple[StepResult, ...], requests: tuple[ScoreRequest, ...]) -> dict[str, Any]:
    available = {step.name: step for step in steps if step.status == "complete"}
    results: dict[str, Any] = {}
    for request in requests:
        component = request.component
        provenance: dict[str, Any] = {
            "reference_source": (str(request.reference_file) if request.reference_file is not None else None),
            "reference_sha256": None,
        }
        if request.reference_file is not None and component in SCORED_COMPONENTS:
            try:
                provenance["reference_sha256"] = sha256(request.reference_file)
            except OSError as error:
                if component in available:
                    raise
                provenance["reference_unavailable_reason"] = f"{type(error).__name__}: {error}"
        if component not in SCORED_COMPONENTS:
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
        if component == "tracking":
            scored = _tracking(predictions, references, request.options)
        elif component == "depth":
            scored = _depth(run_path, predictions, references)
        else:
            scored = _surface(run_path, predictions, references, request.options)
        results[component] = {**provenance, "status": "scored", "result": scored}
    return results
