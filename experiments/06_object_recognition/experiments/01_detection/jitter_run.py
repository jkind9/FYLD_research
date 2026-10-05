"""Task45 Part B: box jitter on the TUM freiburg1 desk recording, with a noise floor.

Usage (detector environment, GPU only when no other process is using it):
    .venv-yolo/Scripts/python.exe -B -m \
        experiments.06_object_recognition.experiments.01_detection.jitter_run \
        --data-root <checkout>/data --checkpoint <checkout>/checkpoints/yolo26x.pt

The detector sees only colour images. Depth and motion capture are read after
detection. This measures consistency over time, not placement accuracy.
"""

import argparse
import importlib
import itertools
import math
import time
from pathlib import Path

import cv2
import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, write_json

from .floor import ORB_SETTINGS, features, floor, pair_residuals
from .jitter import (
    backproject_pixel,
    bootstrap_interval,
    centre_depth,
    depth_to_colour_time,
    interpolate_pose,
)
from .jitter_tracks import by_position, link_frames, summarise_track
from .placement import touches_edge
from .placement_run import EXPECTED_CV2, _check_cv2, _detector

SEED = 20261005
DESK = "tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk"
HYPERPARAMETERS = {
    "detector": {
        "value": "YOLO26x, pilot PREDICT_SETTINGS",
        "source": "inherited experiments/06_object_recognition/pilot/detector.py:11-24",
    },
    "data": {
        "value": "TUM freiburg1 desk, all associated colour/depth pairs",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "association_tolerance_s": {
        "value": 0.02,
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:79",
    },
    "calibration": {
        "value": "fx=fy=525, cx=319.5, cy=239.5, no undistortion",
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:13",
    },
    "depth_range": {
        "value": "valid and < 4 m",
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:124",
    },
    "pose_timing": {
        "value": "interpolated linear + slerp; colour-time poses for pixels; depth-time pose only to move depth; refuse gap > 0.02 s",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "depth_reprojection": {
        "value": "round to pixel, nearest depth wins, unfilled invalid",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "depth_window": {
        "value": "central half of box, median",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "depth_flags": {
        "value": "<20 valid or <25% valid; IQR/median > 0.2; edge within 2 px",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "link_gate": {
        "value": "0.5 x previous diagonal, same class, one-to-one; jump up to 2 diagonals",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "min_track": {"value": 5, "source": "confirmed 2026-10-05 under owner delegation"},
    "anchor_window": {
        "value": "+-5 frames",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "ddof": {"value": 1, "source": "confirmed 2026-10-05 under owner delegation"},
    "orb": {
        "value": "nfeatures 500, level 0 only, ratio 0.75 + mutual",
        "source": "inherited experiments/06_object_recognition/experiments/03_appearance/adapter.py:59-71, compare.py:43-55",
    },
    "floor_filters": {
        "value": "7x7 depth window, drop if range > 10% of median; outliers > 5 MAD",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "local_floor_minimum": {
        "value": 30,
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "stratification": {
        "value": "tertiles of camera rotation during the colour-depth time gap",
        "source": "confirmed 2026-10-05 under owner delegation; plan asks for stratification without fixing bands",
    },
    "bootstrap": {
        "value": "1000 track resamples, seed 20261005, 2.5-97.5 percentile",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "opencv": {
        "value": EXPECTED_CV2,
        "source": "confirmed 2026-10-05 under owner delegation",
    },
}


def _owner(name: str):
    return importlib.import_module(f"experiments.03_camera_pose_estimation.src.{name}")


def _poses(root: Path) -> tuple[np.ndarray, list]:
    references = _owner("evaluation").read_references(root / "groundtruth.txt")
    return np.array([r[0] for r in references]), [r[1] for r in references]


def _detections(detector, frame, rgb_path: Path, depth, valid, pose) -> list[dict]:
    found, _ = detector.predict(rgb_path)
    rows = []
    for d in found:
        x1, y1, x2, y2 = d.xyxy
        u, v = (x1 + x2) / 2, (y1 + y2) / 2
        stats = centre_depth(depth, valid, d.xyxy)
        world = (
            None
            if stats["median"] is None
            else backproject_pixel(u, v, stats["median"], frame.calibration, pose)
        )
        rows.append(
            {
                "label": d.label,
                "confidence": d.confidence,
                "xyxy": list(d.xyxy),
                "centre": (u, v),
                "diagonal": math.hypot(x2 - x1, y2 - y1),
                "width": x2 - x1,
                "height": y2 - y1,
                "depth": stats["median"],
                "world": world,
                "flag_sparse": stats["flag_sparse"],
                "flag_spread": stats["flag_spread"],
                "edge": touches_edge(d.xyxy, width=640, height=480),
            }
        )
    return rows


def collect(root: Path, detector) -> tuple[list[dict], list[dict], dict]:
    dataset = _owner("dataset")
    _, counts = dataset.associations(root, 1)
    rows, _ = dataset.associations(root, counts["matched_rows"])
    times, poses = _poses(root)
    frames, refused = [], []
    for sequence, row in enumerate(rows):
        try:
            colour_pose = interpolate_pose(times, poses, row["timestamp_s"])
            depth_pose = interpolate_pose(times, poses, row["depth_timestamp_s"])
        except ValueError as error:
            refused.append({"frame_id": row["frame_id"], "reason": str(error)})
            continue
        frame = dataset.load_frame(root, row)
        depth, valid = depth_to_colour_time(
            frame.depth, frame.valid, frame.calibration, depth_pose, colour_pose
        )
        keypoints, descriptors = features(
            cv2.cvtColor(frame.colour, cv2.COLOR_RGB2GRAY)
        )
        frames.append(
            {
                "sequence": sequence,
                "frame_id": row["frame_id"],
                "pose": colour_pose,
                "time_gap_s": abs(row["timestamp_s"] - row["depth_timestamp_s"]),
                "timestamp_s": row["timestamp_s"],
                "detections": _detections(
                    detector, frame, root / row["rgb"], depth, valid, colour_pose
                ),
                "keypoints": keypoints,
                "descriptors": descriptors,
                "depth": depth,
                "valid": valid,
            }
        )
    return frames, refused, counts


def feature_residuals(frames: list[dict], calibration) -> list[dict]:
    rows = []
    for position, (before, after) in enumerate(itertools.pairwise(frames)):
        if after["sequence"] != before["sequence"] + 1:
            continue
        relative = np.linalg.inv(before["pose"]) @ after["pose"]
        speed = Rotation.from_matrix(relative[:3, :3]).magnitude() / (
            after["timestamp_s"] - before["timestamp_s"]
        )
        gap_rotation = speed * before["time_gap_s"]
        rows += [
            {**r, "frame_position": position, "gap_rotation_rad": gap_rotation}
            for r in pair_residuals(before, after, calibration)
        ]
    return rows


def _tertile_floors(residuals: list[dict]) -> list[dict]:
    """Three bands of camera rotation during the colour-depth gap; each residual once.

    A value equal to an inner edge goes to the upper band.
    """
    if len(residuals) < 3:
        return []
    values = np.array([r["gap_rotation_rad"] for r in residuals])
    edges = np.quantile(values, [0, 1 / 3, 2 / 3, 1])
    bands = np.searchsorted(edges[1:3], values, side="right")
    result = []
    for band in range(3):
        chosen = [
            [r["dx"], r["dy"]]
            for r, b in zip(residuals, bands, strict=True)
            if b == band
        ]
        result.append(
            {
                "gap_rotation_rad": [float(edges[band]), float(edges[band + 1])],
                **floor(np.array(chosen).reshape(-1, 2)),
            }
        )
    return result


def _pooled(tracks: list[dict], key: str) -> dict:
    values = [
        t[key]["radial_rms"]
        for t in tracks
        if t.get(key, {}).get("radial_rms") is not None
    ]
    if len(values) < 2:
        return {
            "n_tracks": len(values),
            "median": None,
            "interval": None,
            "reason": "fewer than 2 scored tracks",
        }
    return {
        "n_tracks": len(values),
        "median": float(np.median(values)),
        "mean": float(np.mean(values)),
        "interval": bootstrap_interval(values, seed=SEED),
        "reason": None,
    }


def _lag1_medians(tracks: list[dict]) -> dict:
    """Median lag-1 autocorrelation per axis; independent jitter gives -0.5."""
    result = {}
    for axis in ("x", "y"):
        values = [
            t["pairwise"][f"lag1_{axis}"]
            for t in tracks
            if t["pairwise"][f"lag1_{axis}"] is not None
        ]
        result[axis] = {
            "n_tracks": len(values),
            "median": float(np.median(values)) if values else None,
            "share_above_minus_0_25": (
                float(np.mean(np.array(values) > -0.25)) if values else None
            ),
        }
    return result


def _box_flags(frames: list[dict]) -> dict:
    """Mutually exclusive depth reasons plus the separate edge flag, as shares of all boxes."""
    boxes = [d for f in frames for d in f["detections"]]
    total = len(boxes) or 1
    no_depth = sum(d["world"] is None for d in boxes)
    sparse = sum(d["world"] is not None and d["flag_sparse"] for d in boxes)
    return {
        "boxes": len(boxes),
        "no_depth": no_depth / total,
        "sparse_depth_with_depth": sparse / total,
        "depth_spread": sum(d["flag_spread"] for d in boxes) / total,
        "touches_edge": sum(d["edge"] for d in boxes) / total,
        "any_flag": sum(
            d["flag_sparse"] or d["flag_spread"] or d["edge"] for d in boxes
        )
        / total,
    }


def summary(frames, refused, tracks, unlinked, residuals) -> dict:
    scored = [t for t in tracks if t["status"] == "scored"]
    clean = [t for t in scored if t["clean"]]
    return {
        "posed_frames": len(frames),
        "refused_frames": refused,
        "detections": sum(len(f["detections"]) for f in frames),
        "detections_without_depth": sum(
            d["world"] is None for f in frames for d in f["detections"]
        ),
        "tracks": {"total": len(tracks), "scored": len(scored), "clean": len(clean)},
        "unlinked": {
            "total": len(unlinked),
            **{
                o: sum(u["outcome"] == o for u in unlinked)
                for o in ("jump", "no_depth", "claimed", "gone")
            },
        },
        "jitter_px_radial": {
            group: {
                method: _pooled(chosen, method)
                for method in ("windowed", "pairwise", "whole_track")
            }
            for group, chosen in (
                ("all", scored),
                ("clean", clean),
                ("flagged", [t for t in scored if not t["clean"]]),
            )
        },
        "lag1_median": {
            group: _lag1_medians(chosen)
            for group, chosen in (
                ("all", scored),
                ("clean", clean),
                ("flagged", [t for t in scored if not t["clean"]]),
            )
        },
        "box_flags": _box_flags(frames),
        "floor_global": floor(
            np.array([[r["dx"], r["dy"]] for r in residuals]).reshape(-1, 2)
        ),
        "floor_by_gap_rotation": _tertile_floors(residuals),
        "claim": "consistency over time on development data; cannot see a steady offset",
    }


def run(
    repo: Path, data_root: Path, checkpoint: Path, output: Path, device: str
) -> Path:
    configuration = {
        "experiment": "task45_part_b_desk_jitter",
        "hyperparameters": HYPERPARAMETERS,
        "opencv": _check_cv2(),
        "checkpoint_sha256": sha256(checkpoint),
        "orb": {k: int(v) for k, v in ORB_SETTINGS.items()},
    }
    root = data_root / DESK
    detector = _detector(checkpoint, device)
    with Run(output, repo, configuration) as published:
        started = time.perf_counter()
        with published.measure("detection_and_features"):
            frames, refused, counts = collect(root, detector)
        published.set_processed_frames(len(frames))
        calibration = _owner("dataset").CALIBRATION
        residuals = feature_residuals(frames, calibration)
        tracks, unlinked = link_frames(frames, calibration)
        indexed = by_position(residuals)
        track_rows = [summarise_track(t, frames, indexed, calibration) for t in tracks]
        report = summary(frames, refused, track_rows, unlinked, residuals)
        report.update(
            associations=counts, elapsed_seconds=time.perf_counter() - started
        )
        write_json(published.path / "output/summary.json", report)
        write_json(published.path / "output/tracks.json", track_rows)
        write_json(published.path / "output/unlinked.json", unlinked)
        write_json(published.path / "output/feature_residuals.json", residuals)
        write_json(
            published.path / "output/detections.json",
            [
                {
                    "frame_id": f["frame_id"],
                    "detections": [
                        {
                            k: (list(v) if isinstance(v, (tuple, np.ndarray)) else v)
                            for k, v in d.items()
                        }
                        for d in f["detections"]
                    ],
                }
                for f in frames
            ],
        )
    return published.path


def main(argv: list[str] | None = None) -> None:
    repo = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description="Task45 Part B desk jitter")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parent / "runs"
    )
    parser.add_argument("--device", default="0")
    arguments = parser.parse_args(argv)
    print(
        run(
            repo,
            arguments.data_root,
            arguments.checkpoint,
            arguments.output,
            arguments.device,
        )
    )


if __name__ == "__main__":
    main()
