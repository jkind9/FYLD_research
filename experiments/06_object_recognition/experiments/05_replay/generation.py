"""Create a self-contained immutable Task22 replay generation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, verify_run, write_json

from . import automatic, checked_inputs, payload, report

ROOT = Path(__file__).resolve().parents[4]
RUN_ROOT_RELATIVE = Path("experiments/06_object_recognition/experiments/05_replay/runs")
FEATURE_CACHE_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/05_replay/runs/20261004T150809.296626Z_cdade192a8574e1985f2102cf66b8ef5"
)
FEATURE_CACHE_MANIFEST_SHA256 = (
    "c7469a85043bfb3aa9a6f1eed9cf95190ef0634a44036708ed21c195efe292ed"
)
FEATURE_PRODUCER_SHA256 = (
    "a8b0c763b1d0b086944fe2b44cde0f1f46ea5de7a7fa51b9eeb0263747f1f26f"
)
HYPERPARAMETERS = {
    "sources": {
        "value": {
            "baseline_frames": 60,
            "automatic_frame_indexes": [0, 9, 27, 37, 42, 59],
            "class_proposals": {"cup": 4, "tv": 13},
            "features": 17,
        },
        "source": "inherited Task17/18/28 accepted receipts; bounded by Task22 plan",
    },
    "appearance": {
        "value": {
            "model": "existing YOLO26x",
            "checkpoint_sha256": "9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92",
            "device": "cuda:0",
            "precision": "float32",
            "batch": 1,
            "layer": 22,
            "vector_length": 768,
            "crop": [128, 128],
        },
        "source": "inherited accepted Task20 run receipt; owner authorised existing-checkpoint GPU trial",
    },
    "association": {
        "value": ["combined-last", "combined-viewmedian"],
        "source": "inherited accepted Task21 fixed policy; no tuning",
    },
    "geometry": {
        "value": {
            "calibration": [640, 480, 525, 525, 319.5, 239.5],
            "depth_scale": 5000,
            "valid_depth_m": [0, 4],
            "pose": "supplied tum_freiburg1_desk_mocap/continuous_capture",
            "pose_tolerance_s": 0.02,
        },
        "source": "inherited Task27/Task28 settings and Task17 frozen source",
    },
    "display": {
        "value": {
            "cloud_points": 20000,
            "per_frame_points": 500,
            "jpeg_quality": 90,
            "frustum_length_m": 0.15,
        },
        "source": "inherited Task22 viewer plan and Task28 cache",
    },
}


def _preflight_output(repo: Path) -> None:
    destination = (repo / RUN_ROOT_RELATIVE).resolve()
    protected = [
        repo / checked_inputs.BASELINE_RELATIVE,
        repo / checked_inputs.DETECTION_RELATIVE,
        repo / checked_inputs.APPEARANCE_RELATIVE,
        repo / checked_inputs.IDENTITY_RELATIVE,
        repo / "data",
        repo / "checkpoints",
    ]
    if not destination.is_relative_to(repo.resolve()):
        raise ValueError("Task22 output root must stay inside this repository")
    for source in protected:
        root = source.resolve()
        if destination == root or destination.is_relative_to(root):
            raise ValueError("Task22 output overlaps an accepted input")
        if root.is_relative_to(destination):
            raise ValueError("Task22 output ancestor contains an accepted input")
    for parent in (destination, *destination.parents):
        if (parent / "metadata/status.json").exists():
            raise ValueError("Task22 output is nested inside an existing Run")


def _copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    digest = sha256(source)
    if sha256(destination) != digest:
        raise ValueError("Input artifact changed while copying")
    return digest


def _read_accepted_feature_cache(repo: Path, sources: dict) -> tuple[dict, dict]:
    source = repo / FEATURE_CACHE_RELATIVE
    manifest_path = source / "metadata/manifest.json"
    if sha256(manifest_path) != FEATURE_CACHE_MANIFEST_SHA256:
        raise ValueError("Accepted Task22 feature-extraction manifest differs")
    verify_run(source)
    config = json.loads(
        (source / "metadata/configuration.json").read_text(encoding="utf-8")
    )
    if config.get("source_pins") != sources["pins"]:
        raise ValueError("Cached features belong to different accepted inputs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    producer_relative = "metadata/source/experiments/06_object_recognition/experiments/05_replay/automatic.py"
    if (
        manifest["files"].get(producer_relative, {}).get("sha256")
        != FEATURE_PRODUCER_SHA256
    ):
        raise ValueError("Accepted feature run lacks its pinned producer source")
    automatic_path = source / "output/automatic.json"
    record = manifest["files"].get("output/automatic.json")
    if record is None or sha256(automatic_path) != record["sha256"]:
        raise ValueError("Cached automatic observations fail their manifest hash")
    automatic_data = json.loads(automatic_path.read_text(encoding="utf-8"))
    receipt = automatic_data["feature_receipt"]
    if (
        receipt.get("checkpoint_sha256")
        != "9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92"
        or receipt.get("actual_device") != "cuda:0"
        or receipt.get("actual_fp16") is not False
        or receipt.get("layer_index") != 22
        or receipt.get("vector_length") != 768
        or receipt.get("requested_embedding_count") != 17
        or sum(len(row["observations"]) for row in automatic_data["frames"]) != 17
    ):
        raise ValueError(
            "Accepted cache lacks expected actual-box CUDA feature evidence"
        )
    return automatic_data, {
        "run": FEATURE_CACHE_RELATIVE.as_posix(),
        "manifest_sha256": FEATURE_CACHE_MANIFEST_SHA256,
        "features_sha256": sha256(automatic_path),
    }


def execute(repo: Path = ROOT) -> Path:
    _preflight_output(repo)
    sources = checked_inputs.load(repo)
    baseline = sources["baseline"]
    frames = sources["baseline_rows"]
    cached_auto = (repo / FEATURE_CACHE_RELATIVE).is_dir()
    config = {
        "hyperparameters": HYPERPARAMETERS,
        "source_pins": sources["pins"],
        "feature_cache_manifest_sha256": (
            FEATURE_CACHE_MANIFEST_SHA256 if cached_auto else None
        ),
    }
    copied = {"rgb": [], "depth": []}
    with Run(repo / RUN_ROOT_RELATIVE, repo, config) as run:
        run.set_processed_frames(len(frames))
        for row in frames:
            for kind in ("rgb", "depth"):
                relative = row[kind]
                source = baseline / "input" / relative
                target = run.path / "input" / relative
                copied[kind].append({"path": relative, "sha256": _copy(source, target)})
        copied["cloud_display.npz"] = _copy(
            baseline / "output/cloud_display.npz", run.path / "input/cloud_display.npz"
        )
        copied["baseline_observations.json"] = _copy(
            baseline / "output/observations.json",
            run.path / "input/baseline_observations.json",
        )
        copied["baseline_detections.json"] = _copy(
            baseline / "output/detections.json",
            run.path / "input/baseline_detections.json",
        )
        copied["selection.json"] = _copy(
            baseline / "output/selection.json", run.path / "input/selection.json"
        )
        observations = json.loads(
            (run.path / "input/baseline_observations.json").read_text(encoding="utf-8")
        )
        mutable_frames = []
        for index, row in enumerate(observations["frames"]):
            mutable_frames.append(
                {
                    **row,
                    "frame_index": index,
                    "rgb_source": run.path / "input" / row["rgb"],
                    "depth_source": run.path / "input" / row["depth"],
                }
            )
        if cached_auto:
            auto, feature_source = _read_accepted_feature_cache(repo, sources)
        else:
            with run.measure("actual_box_features_and_location", frames=6):
                auto = automatic.extract(
                    repo, mutable_frames, sources["proposal_frames"]
                )
            feature_source = {"mode": "new bounded extraction"}
        write_json(run.path / "output/automatic.json", auto)
        write_json(run.path / "output/feature_source.json", feature_source)
        write_json(
            run.path / "output/source_pins.json",
            {"pins": sources["pins"], "copied": copied},
        )
        cloud = np.load(run.path / "input/cloud_display.npz")
        proposal_count = payload.write(
            run.path / "review.html",
            run.path,
            mutable_frames,
            observations,
            cloud["world_m"],
            cloud["rgb"],
            auto,
            sources["proposal_frames"],
        )
        with run.measure("report_publication"):
            report.write(
                run.path, sources, auto, proposal_count, copied, feature_source
            )
    return run.path
