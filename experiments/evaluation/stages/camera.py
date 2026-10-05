"""Camera path stage: layer 3 position error against motion-capture poses."""

from pathlib import Path

import numpy as np

from experiments.evaluation import schema
from experiments.evaluation.stages.common import (
    file_sha256,
    owner,
    read_json,
    require_keys,
    require_same,
    scope,
    verified_run,
)
from experiments.shared.contracts import Pose

EVALUATION = "experiments.03_camera_pose_estimation.src.evaluation"
TRACKING = "experiments.03_camera_pose_estimation.src.tracking"
METHOD = "layer3_tracker"
TOO_FEW = "scorer returned no value (too few tracked frames matched to the reference)"
REPORTED = (
    "position_rmse_m",
    "relative_translation_rmse_m",
    "relative_rotation_rmse_rad",
    "tracked_fraction",
)


def records(run_path: Path) -> list:
    tracking = owner(TRACKING)
    rows = read_json(run_path / "output/poses.json")["records"]
    return [
        tracking.Record(
            row["frame_id"],
            row["timestamp_s"],
            row["status"],
            (
                None
                if row["pose"] is None
                else Pose(
                    np.array(row["pose"]["T_world_camera"], dtype=np.float64),
                    row["pose"]["world_id"],
                    row["pose"]["segment_id"],
                    row["pose"]["source"],
                )
            ),
            row["reason"],
        )
        for row in rows
    ]


def score(run_path: Path) -> dict:
    evaluation = owner(EVALUATION)
    reference = evaluation.read_references(
        run_path / "input/evaluation/groundtruth.txt"
    )
    return evaluation.evaluate(records(run_path), reference)


def _measure(
    metrics: dict, key: str, name: str, unit: str, better: str, samples: str
) -> dict:
    value = metrics[key]
    return schema.measure(
        METHOD,
        name,
        value,
        unit,
        samples=metrics[samples],
        coverage="complete",
        better=better,
        reason=None if value is not None else TOO_FEW,
    )


def camera_section(
    run_path: Path,
    *,
    dataset: str,
    pinned_sha256: str | None = None,
    input_mode: str = "isolated",
    reference_kind: str = "independent",
) -> dict:
    run_path = Path(run_path)
    run = verified_run(run_path, pinned_sha256)
    metrics = score(run_path)
    stored = read_json(run_path / "output/metrics.json")
    require_keys(stored, REPORTED, "camera")
    for key in stored.keys() & metrics.keys():
        require_same(stored[key], metrics[key], f"camera {key}")
    poses = read_json(run_path / "output/poses.json")["records"]
    reference_path = run_path / "input/evaluation/groundtruth.txt"
    return schema.section(
        "camera_path",
        run=run,
        dataset=dataset,
        reference={
            "id": "motion-capture groundtruth.txt",
            "version": "copied into run input",
            "sha256": file_sha256(reference_path),
            "kind": reference_kind,
        },
        input_mode=input_mode,
        scope=scope([f"{r['frame_id']}@{r['timestamp_s']!r}" for r in poses]),
        measures=[
            _measure(
                metrics,
                "position_rmse_m",
                "position_rmse",
                "m",
                "lower",
                "position_samples",
            ),
            _measure(
                metrics,
                "relative_translation_rmse_m",
                "relative_translation_rmse",
                "m",
                "lower",
                "relative_pairs",
            ),
            _measure(
                metrics,
                "relative_rotation_rmse_rad",
                "relative_rotation_rmse",
                "rad",
                "lower",
                "relative_pairs",
            ),
            _measure(
                metrics,
                "tracked_fraction",
                "tracked_fraction",
                "fraction",
                "higher",
                "possible_transitions",
            ),
        ],
        rows=metrics["errors"],
    )
