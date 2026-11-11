"""Tiny sealed run folders for wrapper tests; every value is hand-computable."""

import importlib
import json
from pathlib import Path

import numpy as np

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import _inventory, write_json

scoring = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.scoring"
)
identity_run_module = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.run"
)


def seal(path: Path) -> str:
    """Write the manifest and completion receipt exactly as `Run.finish` does."""
    (path / "metadata").mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "files": _inventory(path)}
    write_json(path / "metadata/manifest.json", manifest)
    digest = sha256(path / "metadata/manifest.json")
    write_json(
        path / "metadata/status.json",
        {"status": "complete", "manifest_sha256": digest},
    )
    return digest


def camera_run(path: Path, offset_m: float = 0.05, frames: int = 3) -> str:
    """Reference moves 0.1 m per frame along x; estimates after frame 0 add offset_m in y."""
    records, rows = [], ["# timestamp tx ty tz qx qy qz qw"]
    for i in range(frames):
        timestamp = 100.0 + i * 0.1
        rows.append(f"{timestamp:.4f} {0.1 * i} 0 0 0 0 0 1")
        matrix = np.eye(4)
        matrix[0, 3] = 0.1 * i
        matrix[1, 3] = offset_m if i else 0.0
        records.append(
            {
                "frame_id": str(i),
                "timestamp_s": timestamp,
                "status": "tracked" if i else "initialized",
                "reason": "fixture",
                "pose": {
                    "T_world_camera": matrix.tolist(),
                    "world_id": "fixture-world",
                    "segment_id": "0",
                    "source": "estimated",
                    "units": "metres",
                    "direction": "camera_to_world",
                },
            }
        )
    write_json(path / "output/poses.json", {"schema_version": 1, "records": records})
    reference = path / "input/evaluation/groundtruth.txt"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_text("\n".join(rows) + "\n", encoding="utf-8")
    from experiments.evaluation.stages import camera

    write_json(path / "output/metrics.json", camera.score(path))
    return seal(path)


CUPS = [
    {"bbox_xyxy": [10, 10, 50, 50], "category": "cup", "instance_id": "cup-a"},
    {"bbox_xyxy": [100, 100, 140, 140], "category": "cup", "instance_id": "cup-b"},
]


def _frame() -> dict:
    return {
        "frame_id": "f0",
        "source_selection_index": 0,
        "label_coverage": {"cup": "complete", "tv": "subset"},
        "labels": CUPS,
    }


def _prediction(xyxy: list[float]) -> dict:
    return {"xyxy": xyxy, "label": "cup", "class_id": 41, "confidence": 0.9}


def detection_run(path: Path, drop_second: bool = False) -> str:
    """Two complete-coverage cups; dropping one prediction halves recall."""
    predictions = [_prediction([10, 10, 50, 50])]
    if not drop_second:
        predictions.append(_prediction([100, 100, 140, 140]))
    frames = [_frame()]
    write_json(path / "input/annotations.json", {"frames": frames})
    write_json(
        path / "output/cached_proposals.json",
        {"manifest_sha256": "fixture", "frames": [{"proposals": predictions}]},
    )
    write_json(
        path / "output/scores.json",
        {
            "synthetic_control_fixture": scoring.evaluate(
                frames, [{"proposals": predictions}], (0.3, 0.5, 0.7)
            ),
            "empty_prediction_software_control": scoring.evaluate(
                frames, [{"proposals": []}], (0.3, 0.5, 0.7)
            ),
        },
    )
    return seal(path)


def surface_run(path: Path, recovery: bool = True) -> str:
    """Two frames of distances; four reference vertices, two within 0.05 m."""
    per_frame = {"1": np.array([0.01, 0.03]), "2": np.array([0.07])}
    for frame, values in per_frame.items():
        (path / "output" / frame).mkdir(parents=True, exist_ok=True)
        np.save(path / "output" / frame / "reference_distance.npy", values)
    np.save(path / "output/reference_distance.npy", np.array([0.0, 0.04, 0.2, 0.5]))
    write_json(path / "metadata/configuration.json", {"frame_ids": [1, 2]})
    from experiments.evaluation.stages import surface

    metrics = surface.score(path, 0.05)
    metrics["threshold_m"] = 0.05
    reference = path / "input/evaluation/living-room.ply"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_bytes(b"ply fixture")
    if recovery:
        metrics["recovery"] = {"reference_sha256": sha256(reference)}
    write_json(path / "output/metrics.json", metrics)
    return seal(path)


TRUTH = [
    {"observation_id": "o1", "instance_id": "ref-a"},
    {"observation_id": "o2", "instance_id": "ref-a"},
    {"observation_id": "o3", "instance_id": "ref-b"},
]
CONDITIONS = {
    # A returning object keeps one ID; the other object gets its own.
    "good": [("o1", "x", "new"), ("o2", "x", "matched"), ("o3", "y", "new")],
    # Wrong merge: both reference objects share one ID.
    "merged": [("o1", "x", "new"), ("o2", "x", "matched"), ("o3", "x", "matched")],
}


def identity_run(path: Path) -> str:
    observations = [
        {"observation_id": row["observation_id"], "timestamp_s": float(i)}
        for i, row in enumerate(TRUTH)
    ]
    write_json(path / "input/evaluator_truth.json", TRUTH)
    write_json(path / "input/method_observations.json", observations)
    conditions = {}
    for name, decisions in CONDITIONS.items():
        rows = [
            {"observation_id": o, "object_id": obj, "decision": d}
            for o, obj, d in decisions
        ]
        write_json(
            path / f"output/conditions/{name}/decisions.json", {"observations": rows}
        )
        score = identity_run_module._score(rows, TRUTH, observations)
        conditions[name] = {"score": score}
    write_json(path / "output/summary.json", {"conditions": conditions})
    return seal(path)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
