"""Hash-checked Task17 supports, supplied poses and the accepted Task20 cache."""

from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Calibration, Pose
from experiments.shared.geometry import associate_times, backproject, transform_points

ROOT = Path(__file__).resolve().parents[4]
ORIGINAL_SHA256 = "a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920"
PUBLICATION_SHA256 = "eb30954d32b56778d55ac4a1858dd933ddec7550d2aa4da5bfb9e9ae1b5d57e3"
PUBLISHED_SHA256 = "27fe047dac254161ea823d6c55aeb28e16bd88cd993f1e4bf8fbdee40d4741d3"
TASK20_MANIFEST_SHA256 = (
    "f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4"
)
TASK20_RUN_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/03_appearance/runs/20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d"
)
WORLD_ID = "tum_freiburg1_desk_mocap"
SEGMENT_ID = "continuous_capture"
TIME_TOLERANCE_S = 0.02

source_api = importlib.import_module(
    "experiments.06_object_recognition.experiments.02_segmentation.run"
)
appearance_run = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.run"
)
appearance_cache = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.cache"
)
dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
evaluation = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.evaluation"
)
localisation = importlib.import_module(
    "experiments.06_object_recognition.pilot.localisation"
)


def support_coordinate_difference(
    polygon_camera_m: list[float] | None,
    polygon_world_m: list[float] | None,
    box_localisation: dict,
) -> dict:
    """Compare two visible-depth supports; this is not an accuracy estimate."""
    box_median = box_localisation.get("box_median") or {}
    box_camera = box_median.get("camera_m")
    box_world = box_median.get("world_m")
    camera_delta = (
        [float(box - polygon) for box, polygon in zip(box_camera, polygon_camera_m)]
        if box_camera is not None and polygon_camera_m is not None
        else None
    )
    world_delta = (
        [float(box - polygon) for box, polygon in zip(box_world, polygon_world_m)]
        if box_world is not None and polygon_world_m is not None
        else None
    )
    return {
        "box_minus_polygon_camera_m": camera_delta,
        "box_minus_polygon_camera_delta_norm_m": (
            float(np.linalg.norm(camera_delta)) if camera_delta is not None else None
        ),
        "box_minus_polygon_world_m": world_delta,
        "box_minus_polygon_world_delta_norm_m": (
            float(np.linalg.norm(world_delta)) if world_delta is not None else None
        ),
        "interpretation": "Descriptive difference between support-conditioned visible surfaces; not centre error or coordinate accuracy.",
    }


def output_root(repo: Path, destination: Path) -> Path:
    root = repo.resolve()
    resolved = destination.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Output must remain inside the repository")
    protected = [repo / "data", repo / "checkpoints", repo / TASK20_RUN_RELATIVE]
    protected.extend(
        (
            repo / "data/object_revisits/desk_smoke_v1",
            repo / "experiments/06_object_recognition/datasets",
        )
    )
    for path in protected:
        source = path.resolve()
        if (
            resolved == source
            or resolved.is_relative_to(source)
            or source.is_relative_to(resolved)
        ):
            raise ValueError("Output overlaps a protected source tree")
    for ancestor in (resolved, *resolved.parents):
        if (ancestor / "metadata/status.json").exists() or (
            ancestor / "metadata/status.json"
        ).is_symlink():
            raise ValueError("Output must not be inside or contain an existing Run")
    return resolved


def preflight(repo: Path) -> tuple[dict, Path, dict]:
    manifest = source_api.preflight(repo)
    publication = repo / "data/object_revisits/desk_smoke_v1"
    if (
        sha256(repo / "experiments/06_object_recognition/datasets/desk_smoke_v1.json")
        != ORIGINAL_SHA256
    ):
        raise ValueError("Task17 original annotation pin differs")
    if sha256(publication / "publication.json") != PUBLICATION_SHA256:
        raise ValueError("Task17 publication receipt pin differs")
    if sha256(publication / "annotations.json") != PUBLISHED_SHA256:
        raise ValueError("Task17 published annotation pin differs")
    cache = repo / TASK20_RUN_RELATIVE
    if sha256(cache / "metadata/manifest.json") != TASK20_MANIFEST_SHA256:
        raise ValueError("Accepted Task20 completion manifest differs")
    return (
        manifest,
        cache,
        json.loads((publication / "publication.json").read_text(encoding="utf-8")),
    )


def collect(
    run: Any, repo: Path, manifest: dict, cache: Path, publication_receipt: dict
) -> tuple[list[dict], list[dict], dict]:
    """Copy verified method inputs, form anonymous geometry rows and verify descriptors."""
    method, _evaluator_rows = appearance_run._inputs(
        run, repo, manifest, synthetic=False
    )
    signature = appearance_run._signature(method)
    descriptor_payload = appearance_cache.read_verified(cache, signature)
    descriptors = {row["key"]: row["yolo"] for row in descriptor_payload["rows"]}
    if set(descriptors) != {row["key"] for row in method} or len(descriptors) != len(
        method
    ):
        raise ValueError(
            "Task20 descriptor membership does not match the frozen observations"
        )
    frame_lookup = {frame["frame_id"]: frame for frame in manifest["frames"]}
    source_root = (
        repo / "data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk"
    )
    _, counts = dataset.associations(source_root, 1, TIME_TOLERANCE_S)
    frame_rows, _ = dataset.associations(
        source_root, counts["matched_rows"], TIME_TOLERANCE_S
    )
    frames_by_timestamp = {float(row["timestamp_s"]): row for row in frame_rows}
    references = evaluation.read_references(source_root / "groundtruth.txt")
    pose_matches = associate_times(
        [frame["timestamp_s"] for frame in manifest["frames"]],
        [r[0] for r in references],
        TIME_TOLERANCE_S,
    )
    pose_by_frame = {
        manifest["frames"][i]["frame_id"]: references[j] for i, j in pose_matches
    }
    pub_members = {row["path"]: row["sha256"] for row in publication_receipt["files"]}
    labels_by_frame = {
        frame["frame_id"]: frame["labels"] for frame in manifest["frames"]
    }
    method_rows: list[dict] = []
    evaluator_truth = []
    frame_sources = []
    frame_files = {}
    pose_source_sha = sha256(source_root / "groundtruth.txt")
    for frame in manifest["frames"]:
        source_frame = frames_by_timestamp.get(float(frame["timestamp_s"]))
        if (
            source_frame is None
            or abs(
                float(source_frame["depth_timestamp_s"]) - float(frame["timestamp_s"])
            )
            > TIME_TOLERANCE_S
        ):
            raise ValueError(
                "Task17 frame has no checked RGB-D pair inside the timestamp tolerance"
            )
        pose_row = pose_by_frame.get(frame["frame_id"])
        pose = Pose(pose_row[1], WORLD_ID, SEGMENT_ID, "supplied") if pose_row else None
        rgb_target = run.path / "input/rgb" / f"{frame['frame_id']}.png"
        rgb_hash = sha256(rgb_target)
        if rgb_hash != frame["rgb"]["sha256"]:
            raise ValueError("Copied RGB differs from Task17 annotation")
        depth_target = run.path / "input/depth" / f"frame-{frame['frame_id']}.png"
        depth_target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source_root / source_frame["depth"], depth_target)
        depth_hash = sha256(depth_target)
        if depth_hash != frame["depth"]["sha256"]:
            raise ValueError("Copied depth differs from Task17 annotation")
        frame_files[frame["frame_id"]] = (
            source_frame,
            pose,
            depth_target,
            depth_hash,
            rgb_hash,
        )
        frame_sources.append(
            {
                "frame_id": frame["frame_id"],
                "timestamp_s": frame["timestamp_s"],
                "rgb_sha256": rgb_hash,
                "depth_sha256": depth_hash,
                "pose_timestamp_s": pose_row[0] if pose_row else None,
                "pose_matrix": pose.matrix.tolist() if pose else None,
                "pose_present": pose is not None,
                "pose_source_sha256": pose_source_sha,
            }
        )
    for item in method:
        frame = frame_lookup[item["frame_id"]]
        source_frame, pose, depth_target, depth_hash, rgb_sha = frame_files[
            frame["frame_id"]
        ]
        pose_row = pose_by_frame.get(frame["frame_id"])
        label = next(
            label
            for label in labels_by_frame[frame["frame_id"]]
            if tuple(label["bbox_xyxy"]) == tuple(item["bbox"])
        )
        support_name = f"masks/{frame['frame_id']}/{label['instance_id']}.png"
        if support_name not in pub_members:
            raise ValueError(
                "Task17 publication lacks a hash-pinned provisional support"
            )
        support_source = publication_root(repo) / support_name
        support_target = run.path / "input/masks" / f"{item['key']}.png"
        shutil.copyfile(support_source, support_target)
        support_hash = sha256(support_target)
        if support_hash != pub_members[support_name]:
            raise ValueError(
                "Copied provisional support differs from Task17 publication"
            )
        with Image.open(support_target) as image:
            mask = np.asarray(image.convert("L")) > 0
        with Image.open(depth_target) as image:
            encoded = np.asarray(image)
        depth_m = encoded.astype(np.float64) / 5000.0
        valid = (
            mask
            & (encoded != 0)
            & np.isfinite(depth_m)
            & (depth_m > 0)
            & (depth_m < 4.0)
        )
        camera_calibration = Calibration(**manifest["calibration"])
        camera_points, _ = backproject(depth_m, valid, camera_calibration)
        camera_median = np.median(camera_points, axis=0) if len(camera_points) else None
        world_points = (
            transform_points(camera_median[None, :], pose.matrix)[0]
            if camera_median is not None and pose
            else None
        )
        box = tuple(float(x) for x in item["bbox"])
        category = label["category"]
        valid_depth = (
            np.isfinite(depth_m) & (encoded != 0) & (depth_m > 0) & (depth_m < 4.0)
        )
        detection = localisation.Detection(
            box, category, 41 if category == "cup" else 62, 1.0
        )
        box_comparison = localisation.localise_detection(
            SimpleNamespace(
                depth=depth_m, valid=valid_depth, calibration=camera_calibration
            ),
            detection,
            pose,
        )
        support_difference = support_coordinate_difference(
            camera_median.tolist() if camera_median is not None else None,
            world_points.tolist() if world_points is not None else None,
            box_comparison,
        )
        obs = {
            "observation_id": item["key"],
            "frame_id": frame["frame_id"],
            "session_id": frame["session_id"],
            "timestamp_s": float(frame["timestamp_s"]),
            "category": category,
            "bbox_xyxy": list(box),
            "position_camera_m": (
                camera_median.tolist() if camera_median is not None else None
            ),
            "position_world_m": (
                world_points.tolist() if world_points is not None else None
            ),
            "world_id": pose.world_id if pose else None,
            "segment_id": pose.segment_id if pose else None,
            "pose_revision_id": "supplied-base-v1" if pose else None,
            "pose_camera_to_world": pose.matrix.tolist() if pose else None,
            "pose_source_timestamp_s": pose_row[0] if pose_row else None,
            "appearance": descriptors[item["key"]] or None,
            "box_support_comparison": box_comparison,
            "polygon_vs_box_coordinate_difference": support_difference,
            "geometry": {
                "camera_surface_median": (
                    camera_median.tolist() if camera_median is not None else None
                ),
                "world_surface_median": (
                    world_points.tolist() if world_points is not None else None
                ),
                "valid_pixels": len(camera_points),
                "support_pixels": int(mask.sum()),
                "invalid_pixels": int(mask.sum() - valid.sum()),
                "valid_fraction": (
                    float(valid.sum() / mask.sum()) if mask.any() else None
                ),
                "camera_coordinate_iqr_m": (
                    (
                        np.quantile(camera_points, 0.75, axis=0)
                        - np.quantile(camera_points, 0.25, axis=0)
                    ).tolist()
                    if len(camera_points)
                    else None
                ),
                "depth_sha256": depth_hash,
                "support_sha256": support_hash,
                "rgb_sha256": rgb_sha,
                "pose_matrix": pose.matrix.tolist() if pose else None,
            },
        }
        method_rows.append(obs)
        # Evaluator identity and split stay in a separate file and never enter association.
        evaluator_truth.append(
            {
                "observation_id": item["key"],
                "instance_id": label["instance_id"],
                "partition": frame["partition"],
            }
        )
    return (
        method_rows,
        evaluator_truth,
        {
            "signature": signature,
            "cache_manifest_sha256": TASK20_MANIFEST_SHA256,
            "frame_sources": frame_sources,
        },
    )


def publication_root(repo: Path) -> Path:
    return repo / "data/object_revisits/desk_smoke_v1"
