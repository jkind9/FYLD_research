"""Bounded multi-frame YOLO, RGB-D and supplied-pose identity replay."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore[import-untyped]

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Pose
from experiments.shared.geometry import associate_times, backproject, transform_points
from experiments.shared.runs import Run, verify_run, write_json
from experiments.shared.visualization import sample_points

from .detector import PREDICT_SETTINGS, YoloDetector  # type: ignore[import-not-found]
from .localisation import (  # type: ignore[import-not-found]
    Detection,
    localise_detection,
)
from .replay_viewer import write_replay_review  # type: ignore[import-not-found]

dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
evaluation = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.evaluation"
)
ROOT = Path(__file__).resolve().parents[3]
MAX_FRAMES = 60
DISPLAY_FRAME_CAP = 500
DISPLAY_CLOUD_CAP = 20000
ASSOCIATION_DISTANCE_M = 0.35
AMBIGUITY_MARGIN_M = 0.05
TIME_TOLERANCE_S = 0.02
CLIP_START_S = 1305031454.127701
CLIP_END_S = 1305031472.795640
WORLD_ID = "tum_freiburg1_desk_mocap"
SEGMENT_ID = "continuous_capture"

HYPERPARAMETERS = {
    "model": {
        "value": "YOLO26x COCO",
        "source": "inherited task_list/closed/27_localise_yolo_cup_detections_in_recorded_rgbd.md",
    },
    "checkpoint_sha256": {
        "value": "9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92",
        "source": "inherited Task27 verified checkpoint receipt",
    },
    "package": {
        "value": "ultralytics==8.4.172",
        "source": "inherited Task27 pilot environment",
    },
    "device_precision_batch": {
        "value": ["cuda:0", "FP32", 1],
        "source": "inherited Task27 GPU trial; GPU replay authorised by owner 2026-10-03",
    },
    "prediction_settings": {
        "value": PREDICT_SETTINGS,
        "source": "inherited experiments/06_object_recognition/pilot/detector.py:18",
    },
    "class_handling": {
        "value": "retain all detector classes and proposals",
        "source": "confirmed 2026-10-03: owner requested all instances and distinct same-class objects",
    },
    "sequence_span": {
        "value": [1305031454.127701, 1305031472.795640],
        "source": "confirmed 2026-10-03: Task17 visual inventory of stationary desk cup before camera look-away and later return view",
    },
    "frame_count_cap": {
        "value": MAX_FRAMES,
        "source": "confirmed 2026-10-03: bounded exploratory replay",
    },
    "frame_sampling": {
        "value": "integer linspace over paired RGB-D rows; include both endpoints",
        "source": "confirmed 2026-10-03: bounded 18.67-second desk revisit clip",
    },
    "rgb_depth_pose_tolerance_s": {
        "value": TIME_TOLERANCE_S,
        "source": "inherited Task27 receipt and experiments/03_camera_pose_estimation/src/dataset.py:78",
    },
    "intrinsics": {
        "value": [640, 480, 525, 525, 319.5, 239.5],
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:14",
    },
    "depth_units_validity": {
        "value": [5000, "0 < depth_m < 4"],
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:126",
    },
    "pose_quaternion": {
        "value": "finite nonzero quaternion normalized",
        "source": "inherited Task27 reference-pose integration control",
    },
    "localisation_support": {
        "value": ["all valid box pixels", "nearest valid pixel to box centre"],
        "source": "inherited Task27 experiments/06_object_recognition/pilot/localisation.py:49",
    },
    "association": {
        "value": {
            "same_class_only": True,
            "assignment": "global maximum-cardinality then minimum total distance",
            "position_source": "world-coordinate box median",
            "max_distance_m": ASSOCIATION_DISTANCE_M,
            "ambiguity_margin_m": AMBIGUITY_MARGIN_M,
            "ambiguity_rule": "unresolved when an alternative full-cardinality assignment is within the margin",
            "outside_gate": "unresolved after the class has an existing track; do not mint a new ID",
            "retention": "all selected frames; no expiry inside clip",
        },
        "source": "confirmed 2026-10-03: owner asked us to choose and record initial settings",
    },
    "display_sampling": {
        "value": [DISPLAY_FRAME_CAP, DISPLAY_CLOUD_CAP, "integer linspace"],
        "source": "confirmed 2026-10-03: bounded offline viewer display",
    },
    "repeats": {
        "value": 1,
        "source": "confirmed 2026-10-03: one exploratory replay",
    },
}


def associate_frame(
    detections: list[dict],
    tracks: dict[str, dict],
    next_number: int,
    max_distance_m: float,
    ambiguity_margin_m: float,
) -> tuple[list[dict], dict[str, dict], int]:
    """Assign same-class detections one-to-one, preserving ambiguous results."""
    if (
        not np.isfinite([max_distance_m, ambiguity_margin_m]).all()
        or max_distance_m <= 0
        or ambiguity_margin_m < 0
        or isinstance(next_number, bool)
        or not isinstance(next_number, int)
        or next_number < 1
    ):
        raise ValueError("Association settings must be finite and positive")

    updated_tracks = {
        object_id: {
            **track,
            "last_position_m": list(track["last_position_m"]),
        }
        for object_id, track in tracks.items()
    }
    records = [dict(detection) for detection in detections]
    candidates_by_detection: dict[int, list[tuple[float, str]]] = {}
    unresolved: dict[int, str] = {}

    for index, detection in enumerate(records):
        position = detection.get("world_position_m")
        if position is None:
            unresolved[index] = "unresolved_no_position"
            continue
        point = np.asarray(position, dtype=float)
        if point.shape != (3,) or not np.isfinite(point).all():
            unresolved[index] = "unresolved_no_position"
            continue
        candidates = []
        for object_id, track in updated_tracks.items():
            if track["class_id"] != detection["class_id"]:
                continue
            previous = np.asarray(track["last_position_m"], dtype=float)
            distance = float(np.linalg.norm(point - previous))
            if distance <= max_distance_m:
                candidates.append((distance, object_id))
        candidates.sort(key=lambda item: (item[0], item[1]))
        candidates_by_detection[index] = candidates

    matched_detections: dict[int, tuple[str, float]] = {}
    classes = {record["class_id"] for record in records}
    for class_id in classes:
        detection_indexes = [
            index
            for index, candidates in candidates_by_detection.items()
            if index not in unresolved
            and records[index]["class_id"] == class_id
            and candidates
        ]
        track_ids = sorted(
            object_id
            for object_id, track in updated_tracks.items()
            if track["class_id"] == class_id
        )
        if not detection_indexes or not track_ids:
            continue
        dummy_cost = (
            max_distance_m * (min(len(detection_indexes), len(track_ids)) + 1) + 1
        )
        invalid_cost = dummy_cost * (len(detection_indexes) + len(track_ids) + 1)
        costs = np.full(
            (len(detection_indexes), len(track_ids) + len(detection_indexes)),
            dummy_cost,
            dtype=float,
        )
        costs[:, : len(track_ids)] = invalid_cost
        distance_lookup: dict[tuple[int, str], float] = {}
        track_columns = {
            object_id: column for column, object_id in enumerate(track_ids)
        }
        for row, index in enumerate(detection_indexes):
            for distance, object_id in candidates_by_detection[index]:
                costs[row, track_columns[object_id]] = distance
                distance_lookup[(index, object_id)] = distance

        def solve(
            matrix: np.ndarray,
            track_count: int = len(track_ids),
            unmatched_cost: float = dummy_cost,
        ) -> tuple[dict[int, int], float]:
            assignment_rows, assignment_columns = linear_sum_assignment(matrix)
            assignment = {
                int(row): int(column)
                for row, column in zip(assignment_rows, assignment_columns, strict=True)
                if column < track_count and matrix[row, column] < unmatched_cost
            }
            total_distance = sum(
                float(matrix[row, column]) for row, column in assignment.items()
            )
            return assignment, total_distance

        base_assignment, base_distance = solve(costs)
        ambiguous_rows = set()
        for row, column in base_assignment.items():
            alternative_costs = costs.copy()
            alternative_costs[row, column] = invalid_cost
            alternative, alternative_distance = solve(alternative_costs)
            if (
                len(alternative) == len(base_assignment)
                and alternative_distance - base_distance < ambiguity_margin_m
            ):
                ambiguous_rows.add(row)

        for row, column in base_assignment.items():
            index = detection_indexes[row]
            if row in ambiguous_rows:
                unresolved[index] = "unresolved_ambiguous"
                continue
            object_id = track_ids[column]
            matched_detections[index] = (
                object_id,
                distance_lookup[(index, object_id)],
            )

    for index, record in enumerate(records):
        position = record.get("world_position_m")
        frame_index = int(record.get("frame_index", 0))
        record["coordinate_delta_m"] = None
        record["association_distance_m"] = None
        if index in unresolved:
            record["association"] = unresolved[index]
            record["object_id"] = None
            continue
        if index in matched_detections:
            assert position is not None
            object_id, distance = matched_detections[index]
            old_position = updated_tracks[object_id]["last_position_m"]
            new_position = [float(value) for value in position]
            record["association"] = "matched"
            record["object_id"] = object_id
            record["association_distance_m"] = distance
            record["coordinate_delta_m"] = [
                float(new_position[axis] - old_position[axis]) for axis in range(3)
            ]
            updated_tracks[object_id] = {
                **updated_tracks[object_id],
                "last_position_m": new_position,
                "last_frame_index": frame_index,
                "observation_count": updated_tracks[object_id]["observation_count"] + 1,
            }
            continue

        if candidates_by_detection.get(index):
            record["association"] = "unresolved_track_already_assigned"
            record["object_id"] = None
            continue
        if any(track["class_id"] == record["class_id"] for track in tracks.values()):
            record["association"] = "unresolved_outside_gate"
            record["object_id"] = None
            continue
        assert position is not None
        object_id = f"object-{next_number:04d}"
        next_number += 1
        record["association"] = "new"
        record["object_id"] = object_id
        updated_tracks[object_id] = {
            "object_id": object_id,
            "class_id": int(record["class_id"]),
            "label": str(record["label"]),
            "last_position_m": [float(value) for value in position],
            "last_frame_index": frame_index,
            "observation_count": 1,
        }
    return records, updated_tracks, next_number


def select_rows(
    root: Path,
    start_timestamp_s: float,
    end_timestamp_s: float,
    max_frames: int = MAX_FRAMES,
) -> list[dict]:
    if (
        not np.isfinite([start_timestamp_s, end_timestamp_s]).all()
        or end_timestamp_s < start_timestamp_s
        or isinstance(max_frames, bool)
        or not isinstance(max_frames, int)
        or max_frames < 1
    ):
        raise ValueError("Select a valid ordered time span and positive frame cap")
    _, counts = dataset.associations(root, 1, TIME_TOLERANCE_S)
    rows, _ = dataset.associations(root, counts["matched_rows"], TIME_TOLERANCE_S)
    selected = [
        row
        for row in rows
        if start_timestamp_s <= row["timestamp_s"] <= end_timestamp_s
    ]
    if not selected:
        raise ValueError("No paired RGB-D observations fall inside the selected span")
    if len(selected) > max_frames:
        selected_indexes = np.linspace(
            0, len(selected) - 1, max_frames, dtype=int
        ).tolist()
        selected = [selected[index] for index in selected_indexes]
    return selected


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _members(repo: Path, source: Path) -> dict:
    return _read(repo / "experiments/datasets/tum_freiburg1_member_hashes.json")[
        "sequences"
    ][source.name]["members"]


def _capture(
    run: Run, source: Path, relative: str, members: dict, destination: str
) -> str:
    path = source / relative
    if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
        raise ValueError("Source path escapes the acquired sequence")
    digest = sha256(path)
    if relative not in members or digest != members[relative]["sha256"]:
        raise ValueError(f"Acquired source hash differs: {relative}")
    target = run.path / "input" / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    if sha256(target) != digest:
        raise ValueError(f"Source changed while capturing: {relative}")
    return digest


def _pose_at(
    timestamp_s: float, references: list[tuple[float, np.ndarray]]
) -> tuple[float, Pose] | None:
    matches = associate_times(
        [timestamp_s], [reference[0] for reference in references], TIME_TOLERANCE_S
    )
    if not matches:
        return None
    reference_timestamp, matrix = references[matches[0][1]]
    pose = Pose(matrix, WORLD_ID, SEGMENT_ID, "supplied")
    return reference_timestamp, pose


def _box(item: dict[str, Any]) -> tuple[float, float, float, float]:
    values = item["xyxy"]
    return float(values[0]), float(values[1]), float(values[2]), float(values[3])


def _cloud_sample(frame, pose: Pose) -> tuple[np.ndarray, np.ndarray, int]:
    camera, pixels = backproject(frame.depth, frame.valid, frame.calibration)
    world = transform_points(camera, pose.matrix)
    colours = frame.colour[pixels[:, 0], pixels[:, 1]]
    sampled = sample_points(world, colours, DISPLAY_FRAME_CAP)
    return (
        np.asarray(sampled["points"], dtype=np.float32).reshape(-1, 3),
        np.asarray(sampled["colours"], dtype=np.uint8).reshape(-1, 3),
        len(world),
    )


def _validate_inference_metadata(metadata: dict[str, Any]) -> None:
    if metadata.get("image_shape_hw") != [480, 640]:
        raise ValueError("Detector grid must match the original 640x480 RGB")
    if (
        not str(metadata.get("actual_device", "")).startswith("cuda:0")
        or metadata.get("actual_fp16") is not False
    ):
        raise ValueError("Replay inference must run on cuda:0 in FP32")


def replay(
    repo: Path,
    source: Path,
    checkpoint: Path,
    start_timestamp_s: float,
    end_timestamp_s: float,
    device: str = "0",
) -> Path:
    if device != "0":
        raise ValueError("This authorised replay uses the existing GPU device 0")
    if not checkpoint.is_file() or checkpoint.is_symlink():
        raise ValueError("Provide the existing regular local YOLO26x checkpoint")
    checkpoint_hash = sha256(checkpoint)
    expected_hash = "9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92"
    if checkpoint_hash != expected_hash:
        raise ValueError("Existing checkpoint hash differs from Task27's receipt")
    rows = select_rows(source, start_timestamp_s, end_timestamp_s)
    configuration = {
        "phase": "bounded_persistent_identity_replay",
        "source": str(source.resolve()),
        "checkpoint_sha256": checkpoint_hash,
        "hyperparameters": HYPERPARAMETERS,
        "selected_frame_count": len(rows),
        "pose_input": "supplied TUM motion-capture poses",
        "detection_depth_input": "RGB detector outputs saved before depth/pose processing",
    }
    run = Run(
        repo / "experiments/06_object_recognition/pilot/runs", repo, configuration
    )
    members = _members(repo, source)
    with run:
        with run.measure("input_capture", frames=len(rows)):
            for relative in ("rgb.txt", "depth.txt", "groundtruth.txt"):
                _capture(run, source, relative, members, relative)
            captured_rows = select_rows(
                run.path / "input", start_timestamp_s, end_timestamp_s
            )
            if [row["rgb"] for row in captured_rows] != [row["rgb"] for row in rows]:
                raise ValueError(
                    "Captured timestamp pairing differs from original source"
                )
            input_hashes = {}
            for row in captured_rows:
                for key in ("rgb", "depth"):
                    relative = row[key]
                    input_hashes[relative] = _capture(
                        run, source, relative, members, relative
                    )
            write_json(
                run.path / "output/selection.json",
                {
                    "start_timestamp_s": start_timestamp_s,
                    "end_timestamp_s": end_timestamp_s,
                    "selected_frames": captured_rows,
                    "source_sha256": input_hashes,
                },
            )

        with run.measure("model_load"):
            adapter = YoloDetector(checkpoint, device)
        proposals_by_frame = []
        detector_metadata = []
        with run.measure("detection", frames=len(captured_rows)):
            for row in captured_rows:
                rgb_path = run.path / "input" / row["rgb"]
                detections, metadata = adapter.predict(rgb_path)
                _validate_inference_metadata(metadata)
                proposals_by_frame.append([asdict(item) for item in detections])
                detector_metadata.append(metadata)
            if sha256(checkpoint) != checkpoint_hash:
                raise ValueError("Checkpoint changed during the replay")
            write_json(
                run.path / "output/detections.json",
                {
                    "frames": [
                        {
                            "frame_index": index,
                            "timestamp_s": row["timestamp_s"],
                            "proposals": proposals,
                        }
                        for index, (row, proposals) in enumerate(
                            zip(captured_rows, proposals_by_frame, strict=True)
                        )
                    ],
                    "metadata": detector_metadata,
                    "filtering": "none; every returned class and box is retained",
                },
            )

        references = evaluation.read_references(run.path / "input/groundtruth.txt")
        tracks: dict[str, dict] = {}
        next_number = 1
        observations = []
        cloud_points: list[np.ndarray] = []
        cloud_colours: list[np.ndarray] = []
        displayed_points = 0
        with run.measure("depth_pose_localisation_association", frames=len(rows)):
            for frame_index, (row, proposals) in enumerate(
                zip(captured_rows, proposals_by_frame, strict=True)
            ):
                frame = dataset.load_frame(run.path / "input", row)
                matched_pose = _pose_at(frame.timestamp_s, references)
                pose_info = None
                camera_origin = None
                cloud_start = displayed_points
                valid_point_count = 0
                if matched_pose is not None:
                    pose_timestamp, pose = matched_pose
                    pose_info = {
                        **pose.to_dict(),
                        "reference_timestamp_s": pose_timestamp,
                        "rgb_timestamp_s": frame.timestamp_s,
                        "pose_time_difference_s": abs(
                            pose_timestamp - frame.timestamp_s
                        ),
                    }
                    camera_origin = pose.matrix[:3, 3].tolist()
                    points, colours, valid_point_count = _cloud_sample(frame, pose)
                    remaining = DISPLAY_CLOUD_CAP - displayed_points
                    points, colours = points[:remaining], colours[:remaining]
                    cloud_points.append(points)
                    cloud_colours.append(colours)
                    displayed_points += len(points)

                localised = []
                for detection_index, proposal in enumerate(proposals):
                    detection = Detection(
                        _box(proposal),
                        proposal["label"],
                        int(proposal["class_id"]),
                        float(proposal["confidence"]),
                    )
                    geometry = localise_detection(
                        frame, detection, matched_pose[1] if matched_pose else None
                    )
                    world_position = (
                        geometry["box_median"]["world_m"]
                        if geometry["box_median"] is not None
                        else None
                    )
                    localised.append(
                        {
                            "frame_index": frame_index,
                            "detection_index": detection_index,
                            "class_id": detection.class_id,
                            "label": detection.label,
                            "confidence": detection.confidence,
                            "xyxy": list(detection.xyxy),
                            "camera_position_m": (
                                geometry["box_median"]["camera_m"]
                                if geometry["box_median"]
                                else None
                            ),
                            "world_position_m": world_position,
                            "localisation": geometry,
                        }
                    )

                assigned, tracks, next_number = associate_frame(
                    localised,
                    tracks,
                    next_number,
                    ASSOCIATION_DISTANCE_M,
                    AMBIGUITY_MARGIN_M,
                )
                observations.append(
                    {
                        "frame_index": frame_index,
                        "frame_id": row["frame_id"],
                        "timestamp_s": frame.timestamp_s,
                        "rgb": row["rgb"],
                        "depth": row["depth"],
                        "camera_origin_world_m": camera_origin,
                        "pose": pose_info,
                        "point_count": valid_point_count,
                        "cloud_start": cloud_start,
                        "cloud_stop": displayed_points,
                        "detections": assigned,
                        "tracks": {
                            object_id: dict(track)
                            for object_id, track in tracks.items()
                        },
                        "failures": [
                            {
                                "detection_index": item["detection_index"],
                                "label": item["label"],
                                "association": item["association"],
                            }
                            for item in assigned
                            if item["association"].startswith("unresolved")
                        ],
                    }
                )

        all_points = (
            np.concatenate(cloud_points)
            if cloud_points
            else np.empty((0, 3), dtype=np.float32)
        )
        all_colours = (
            np.concatenate(cloud_colours)
            if cloud_colours
            else np.empty((0, 3), dtype=np.uint8)
        )
        np.savez_compressed(
            run.path / "output/cloud_display.npz",
            world_m=all_points,
            rgb=all_colours,
        )
        write_json(
            run.path / "output/observations.json",
            {
                "world_id": WORLD_ID,
                "segment_id": SEGMENT_ID,
                "position_method": "coordinate-wise median of valid detector-box depth pixels",
                "association_max_distance_m": ASSOCIATION_DISTANCE_M,
                "ambiguity_margin_m": AMBIGUITY_MARGIN_M,
                "frames": observations,
                "tracks": tracks,
                "counts": {
                    "frames": len(observations),
                    "detections": sum(
                        len(frame["detections"]) for frame in observations
                    ),
                    "object_ids": len(tracks),
                    "unresolved": sum(len(frame["failures"]) for frame in observations),
                },
            },
        )
        with run.measure("interactive_report"):
            write_replay_review(
                run.path / "review.html",
                run.path / "input",
                observations,
                all_points,
                all_colours,
                DISPLAY_CLOUD_CAP,
            )
        run.set_processed_frames(len(rows))
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT
        / "data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk",
    )
    parser.add_argument(
        "--checkpoint", type=Path, default=ROOT / "checkpoints/yolo26x.pt"
    )
    parser.add_argument("--device", choices=("0",), default="0")
    parser.add_argument("--start", type=float, default=CLIP_START_S)
    parser.add_argument("--end", type=float, default=CLIP_END_S)
    args = parser.parse_args()
    config_dir = ROOT / "outputs/task28_yolo_config"
    (config_dir / "Ultralytics").mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(config_dir)
    path = replay(ROOT, args.source, args.checkpoint, args.start, args.end, args.device)
    print(path)


if __name__ == "__main__":
    main()
