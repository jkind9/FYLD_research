"""One-frame detection, followed by a separately verified RGB-D mapping control."""

import argparse
import hashlib
import importlib
import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Pose
from experiments.shared.geometry import associate_times, backproject, transform_points
from experiments.shared.runs import Run, verify_run, write_json

from .detector import PREDICT_SETTINGS, YoloDetector
from .localisation import Detection, localise_detection
from .report import annotate, write_cloud_review

dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
evaluation = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.evaluation"
)
ROOT = Path(__file__).resolve().parents[3]
HYPERPARAMETERS = {
    "model": {
        "value": "YOLO26x COCO",
        "source": "confirmed 2026-10-03: delegated strong YOLO GPU model",
    },
    "frame": {
        "value": "1305031128.547399.png",
        "source": "confirmed 2026-10-03: delegated one suitable xyz frame",
    },
    "device": {"value": "0", "source": "confirmed 2026-10-03: GPU authorised"},
    "prediction_settings": {
        "value": PREDICT_SETTINGS,
        "source": "confirmed 2026-10-03: delegated trial, published defaults",
    },
    "target_class": {"value": 41, "source": "confirmed 2026-10-03: cup/mug target"},
    "association_tolerance_s": {
        "value": 0.02,
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:78",
    },
    "intrinsics": {
        "value": [640, 480, 525, 525, 319.5, 239.5],
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:14",
    },
    "depth_units_per_metre": {
        "value": 5000,
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:126",
    },
    "depth_max_m": {
        "value": 4,
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:127",
    },
    "reference_quaternion": {
        "value": "finite nonzero quaternion normalised",
        "source": "inherited experiments/03_camera_pose_estimation/src/evaluation.py:29",
    },
    "support": {
        "value": ["all valid box pixels", "nearest valid pixel to box centre"],
        "source": "n/a explicit analytic baselines, not foreground segmentation",
    },
    "display_cap": {"value": 20000, "source": "n/a display only; full cloud saved"},
    "display_sampling": {
        "value": "integer linspace, original row-major point order",
        "source": "inherited experiments/shared/visualization.py:55",
    },
    "repeats": {
        "value": 1,
        "source": "confirmed 2026-10-03: single-frame exploratory trial",
    },
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_parent(root: Path, relative: str, files: dict) -> dict:
    payload = (root / relative).read_bytes()
    if hashlib.sha256(payload).hexdigest() != files[relative]["sha256"]:
        raise ValueError(f"Parent artifact changed before reading: {relative}")
    return json.loads(payload)


def select_row(root: Path, rgb_name: str) -> dict:
    """Resolve by original name AFTER pairing, not the first paired observation."""
    _, counts = dataset.associations(root, 1)
    rows, _ = dataset.associations(root, counts["matched_rows"])
    selected = [row for row in rows if row["rgb"] == "rgb/" + rgb_name]
    if len(selected) != 1:
        raise ValueError("Requested RGB name must have exactly one matched depth row")
    return selected[0]


def _capture(
    run: Run, root: Path, relative: str, destination: str, members: dict
) -> str:
    source = root / relative
    if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
        raise ValueError("Source path escapes original dataset")
    digest = sha256(source)
    if relative not in members or digest != members[relative]["sha256"]:
        raise ValueError(f"Source does not match acquired archive member: {relative}")
    target = run.path / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if sha256(target) != digest:
        raise ValueError("Source changed during copy")
    return digest


def _members(repo: Path, root: Path) -> dict:
    return _read(repo / "experiments/datasets/tum_freiburg1_member_hashes.json")[
        "sequences"
    ][root.name]["members"]


def detect(
    repo: Path,
    source: Path,
    checkpoint: Path,
    rgb_name: str,
    device: str,
    detector: Any = None,
) -> Path:
    if not checkpoint.is_file() or checkpoint.is_symlink():
        raise ValueError("Checkpoint must already exist as a regular local file")
    model_hash = sha256(checkpoint)
    parameters = {
        **HYPERPARAMETERS,
        "frame": {"value": rgb_name, "source": "explicit authorised selection"},
        "device": {"value": device, "source": "explicit authorised device"},
    }
    config = {
        "phase": "detection",
        "hyperparameters": parameters,
        "checkpoint_sha256": model_hash,
        "checkpoint": str(checkpoint.resolve()),
        "source": str(source.resolve()),
        "pose_input": "none",
        "depth_input": "none",
        "package": "ultralytics==8.4.172",
    }
    with Run(
        repo / "experiments/06_object_recognition/pilot/runs", repo, config
    ) as run:
        with run.measure("input_capture"):
            members = _members(repo, source)
            for relative in ("rgb.txt", "depth.txt"):
                _capture(run, source, relative, "input/" + relative, members)
            # Resolve against captured tables so pairing is immutable during the run.
            row = select_row(run.path / "input", rgb_name)
            image_hash = _capture(run, source, row["rgb"], "input/rgb.png", members)
            write_json(
                run.path / "output/frame.json", {"row": row, "rgb_sha256": image_hash}
            )
        with run.measure("model_load"):
            adapter = (
                detector if detector is not None else YoloDetector(checkpoint, device)
            )
        with run.measure("detection", frames=1):
            detections, metadata = adapter.predict(run.path / "input/rgb.png")
            with Image.open(run.path / "input/rgb.png") as image:
                width, height = image.size
            if metadata["image_shape_hw"] != [height, width]:
                raise ValueError("Detector output grid differs from original RGB")
            for item in detections:
                x1, y1, x2, y2 = item.xyxy
                if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
                    raise ValueError("Detector box is outside original RGB grid")
            if sha256(checkpoint) != model_hash:
                raise ValueError("Checkpoint changed during inference")
            proposals = [asdict(item) for item in detections]
            write_json(
                run.path / "output/detections.json",
                {
                    "proposals": proposals,
                    "metadata": metadata,
                    "filtering": "all boxes returned after recorded model confidence/NMS settings",
                },
            )
        with run.measure("report"):
            annotate(
                run.path / "input/rgb.png", proposals, run.path / "debug/detections.png"
            )
        run.set_processed_frames(1)
    verify_run(run.path)
    return run.path


def map_detection(repo: Path, detection_run: Path, reviewed: bool) -> Path:
    if not reviewed:
        raise ValueError("Visually inspect published detection image before mapping")
    verify_run(detection_run)
    parent_manifest_hash = sha256(detection_run / "metadata/manifest.json")
    parent_manifest = _read(detection_run / "metadata/manifest.json")["files"]
    parent_config = _read_parent(
        detection_run, "metadata/configuration.json", parent_manifest
    )
    if parent_config["phase"] != "detection":
        raise ValueError("Mapping requires a verified detection-stage run")
    config = {
        "phase": "reference_pose_mapping",
        "hyperparameters": {**HYPERPARAMETERS, **parent_config["hyperparameters"]},
        "detection_run": str(detection_run.resolve()),
        "detection_manifest_sha256": parent_manifest_hash,
        "detection_visually_reviewed": True,
        "pose_input": "supplied TUM motion capture integration control",
    }
    with Run(
        repo / "experiments/06_object_recognition/pilot/runs", repo, config
    ) as run:
        with run.measure("input_capture"):
            source = Path(parent_config["source"])
            members = _members(repo, source)
            row = _read_parent(detection_run, "output/frame.json", parent_manifest)[
                "row"
            ]
            rgb_hash = _capture(run, source, row["rgb"], "input/" + row["rgb"], members)
            if rgb_hash != sha256(detection_run / "input/rgb.png"):
                raise ValueError("Mapping RGB differs from detected RGB")
            _capture(run, source, row["depth"], "input/" + row["depth"], members)
            _capture(
                run, source, "groundtruth.txt", "input/reference_poses.txt", members
            )
            for relative in (
                "output/frame.json",
                "output/detections.json",
                "debug/detections.png",
            ):
                target = run.path / "input/detection" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(detection_run / relative, target)
                if sha256(target) != parent_manifest[relative]["sha256"]:
                    raise ValueError(f"Copied parent artifact hash differs: {relative}")
            # Reverify after copies to catch parent changes during capture.
            verify_run(detection_run)
            if sha256(detection_run / "metadata/manifest.json") != parent_manifest_hash:
                raise ValueError(
                    "Parent detection manifest changed during mapping capture"
                )
        with run.measure("depth_and_supplied_pose", frames=1):
            frame = dataset.load_frame(run.path / "input", row)
            references = evaluation.read_references(
                run.path / "input/reference_poses.txt"
            )
            matches = associate_times(
                [frame.timestamp_s], [r[0] for r in references], 0.02
            )
            if not matches:
                raise ValueError(
                    "No supplied pose within inherited 0.02 s tolerance; no world marker"
                )
            ref_time, matrix = references[matches[0][1]]
            pose = Pose(
                matrix, "tum_freiburg1_xyz_mocap", "continuous_capture", "supplied"
            )
            provenance = {
                **pose.to_dict(),
                "reference_timestamp_s": ref_time,
                "rgb_timestamp_s": frame.timestamp_s,
                "depth_timestamp_s": frame.depth_timestamp_s,
                "pose_time_difference_s": abs(ref_time - frame.timestamp_s),
                "quaternion_conversion": HYPERPARAMETERS["reference_quaternion"][
                    "value"
                ],
            }
            proposals = _read(run.path / "input/detection/output/detections.json")[
                "proposals"
            ]
        with run.measure("backprojection_and_localisation"):
            camera, pixels = backproject(frame.depth, frame.valid, frame.calibration)
            world = transform_points(camera, pose.matrix)
            colours = frame.colour[pixels[:, 0], pixels[:, 1]]
            locations = [
                {
                    "detection_index": i,
                    "label": item["label"],
                    "confidence": item["confidence"],
                    "xyxy": item["xyxy"],
                    **localise_detection(frame, Detection(**item), pose),
                }
                for i, item in enumerate(proposals)
                if item["class_id"] == 41
            ]
            np.savez_compressed(
                run.path / "output/cloud.npz",
                camera_m=camera,
                world_m=world,
                rgb=colours,
                pixel_vu=pixels,
            )
            write_json(
                run.path / "output/localisations.json",
                {
                    "locations": locations,
                    "pose": provenance,
                    "frame": row,
                    "hyperparameters": config["hyperparameters"],
                    "claim": "observed surface positions; no independent object-centre accuracy or stable identities",
                },
            )
        with run.measure("report"):
            write_cloud_review(
                run.path / "review.html",
                run.path / "input/detection/debug/detections.png",
                camera,
                world,
                colours,
                locations,
                provenance,
            )
        run.set_processed_frames(1)
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("detect", "map"))
    parser.add_argument(
        "--checkpoint", type=Path, default=ROOT / "checkpoints/yolo26x.pt"
    )
    parser.add_argument("--device", choices=("cpu", "0"), default="0")
    parser.add_argument("--rgb", default=HYPERPARAMETERS["frame"]["value"])
    parser.add_argument("--detection-run", type=Path)
    parser.add_argument("--reviewed", action="store_true")
    args = parser.parse_args()
    config_dir = ROOT / "outputs/task27_yolo_config"
    (config_dir / "Ultralytics").mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(config_dir)
    if args.phase == "detect":
        path = detect(
            ROOT,
            ROOT / "data/tum/rgbd_dataset_freiburg1_xyz",
            args.checkpoint,
            args.rgb,
            args.device,
        )
    else:
        if args.detection_run is None:
            parser.error("map requires --detection-run")
        path = map_detection(ROOT, args.detection_run, args.reviewed)
    print(path)


if __name__ == "__main__":
    main()
