"""COLMAP models to saved files: camera path, sparse points and their observations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from .sequences import Sequence


def camera_to_world(cam_from_world_3x4: np.ndarray) -> np.ndarray:
    """Invert COLMAP's world-to-camera [R|t] into a 4x4 camera-to-world pose."""
    rotation, translation = cam_from_world_3x4[:, :3], cam_from_world_3x4[:, 3]
    out = np.eye(4)
    out[:3, :3] = rotation.T
    out[:3, 3] = -rotation.T @ translation
    return out


def frames(sequence: Sequence, models: dict[int, object]) -> list[dict]:
    """One row per sequence frame: its model and camera-to-world pose, or unplaced."""
    index = {name: i for i, name in enumerate(sequence.image_names)}
    rows = [{"frame_id": f, "timestamp_s": t, "image": n, "model_id": None, "T_world_camera": None}
            for f, t, n in zip(sequence.frame_ids, sequence.timestamps_s, sequence.image_names)]
    # Larger models first, so a frame placed twice keeps its pose in the larger model.
    for model_id, model in sorted(models.items(), key=lambda item: -item[1].num_reg_images()):
        for image in model.images.values():
            if not image.has_pose:
                continue
            row = rows[index[image.name]]
            if row["model_id"] is None:
                row["model_id"] = model_id
                row["T_world_camera"] = camera_to_world(image.cam_from_world().matrix()).tolist()
    return rows


def largest_model(models: dict[int, object]) -> int | None:
    return max(models, key=lambda k: models[k].num_reg_images()) if models else None


def points_and_observations(sequence: Sequence, models: dict[int, object], model_id: int) -> tuple[dict, dict]:
    """Sparse points of one model and every (frame, point, pixel) observation."""
    model = models[model_id]
    index = {name: i for i, name in enumerate(sequence.image_names)}
    point_ids = sorted(model.points3D)
    row_of = {pid: i for i, pid in enumerate(point_ids)}
    points = {
        "xyz": np.array([model.points3D[p].xyz for p in point_ids], dtype=np.float64).reshape(-1, 3),
        "rgb": np.array([model.points3D[p].color for p in point_ids], dtype=np.uint8).reshape(-1, 3),
        "error_px": np.array([model.points3D[p].error for p in point_ids], dtype=np.float64),
        "track_length": np.array([model.points3D[p].track.length() for p in point_ids], dtype=np.int32),
    }
    frame_rows, point_rows, uv = [], [], []
    for image in model.images.values():
        if not image.has_pose:
            continue
        for point2d in image.points2D:
            if point2d.has_point3D():
                frame_rows.append(index[image.name])
                point_rows.append(row_of[point2d.point3D_id])
                uv.append(point2d.xy)
    observations = {
        "frame_index": np.array(frame_rows, dtype=np.int32),
        "point_index": np.array(point_rows, dtype=np.int32),
        "uv": np.array(uv, dtype=np.float64).reshape(-1, 2),
    }
    return points, observations


def write(sequence: Sequence, models: dict[int, object], output: Path) -> dict:
    """Save frames.json, the largest model's trajectory.txt, points.npz and observations.npz."""
    output.mkdir(parents=True, exist_ok=True)
    rows = frames(sequence, models)
    (output / "frames.json").write_text(json.dumps({"frames": rows}, allow_nan=False), encoding="utf-8")
    largest = largest_model(models)
    summary = {
        "models": {str(k): m.num_reg_images() for k, m in models.items()},
        "largest_model": largest,
        "frames": len(rows),
        "placed_any_model": sum(r["model_id"] is not None for r in rows),
        "placed_largest_model": sum(r["model_id"] == largest for r in rows) if largest is not None else 0,
    }
    if largest is None:
        return summary
    lines = ["# timestamp tx ty tz qx qy qz qw (camera-to-world, SfM units, largest model)"]
    for row in rows:
        if row["model_id"] == largest:
            pose = np.array(row["T_world_camera"])
            qx, qy, qz, qw = Rotation.from_matrix(pose[:3, :3]).as_quat()
            lines.append(" ".join(f"{v:.9f}" for v in (row["timestamp_s"], *pose[:3, 3], qx, qy, qz, qw)))
    (output / "trajectory.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    points, observations = points_and_observations(sequence, models, largest)
    np.savez(output / "points.npz", **points)
    np.savez(output / "observations.npz", **observations)
    summary["points"] = len(points["xyz"])
    summary["observations"] = len(observations["uv"])
    summary["mean_reprojection_error_px"] = float(points["error_px"].mean()) if len(points["error_px"]) else None
    return summary
