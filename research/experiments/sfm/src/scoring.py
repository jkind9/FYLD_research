"""Camera-path scores for saved SfM frames, and a run-wide size from a depth model."""

from __future__ import annotations

import importlib
from collections.abc import Callable

import numpy as np

from experiments.shared.contracts import Pose

from .sequences import Sequence

evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")
tracking = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")

SCORE_FIELDS = ("ate_scaled_rmse_m", "ate_scaled_size", "ate_rigid_rmse_m", "rpe_1s_translation_rmse_m",
                "rpe_1s_rotation_rmse_rad", "position_rmse_m", "position_samples", "segments")


def records(rows: list[dict], *, size: float = 1.0, only_model: int | None = None) -> list:
    """Experiment 03 records; each SfM model is its own segment, unplaced frames are lost."""
    out = []
    for row in rows:
        placed = row["model_id"] is not None and (only_model is None or row["model_id"] == only_model)
        if not placed:
            out.append(tracking.Record(row["frame_id"], row["timestamp_s"], "lost", None, "not placed by SfM"))
            continue
        matrix = np.array(row["T_world_camera"], dtype=np.float64)
        matrix[:3, 3] *= size
        pose = Pose(matrix, "sfm", f"model-{row['model_id']}", "estimated")
        out.append(tracking.Record(row["frame_id"], row["timestamp_s"], "tracked", pose, ""))
    return out


def score(sequence: Sequence, rows: list[dict], *, tolerance_s: float = 0.02) -> dict:
    """Task70 scores over all models (each aligned separately) and over the largest model only."""
    references = sequence.references()
    counts: dict[int, int] = {}
    for row in rows:
        if row["model_id"] is not None:
            counts[row["model_id"]] = counts.get(row["model_id"], 0) + 1
    largest = max(counts, key=counts.get) if counts else None
    out = {
        "frames": len(rows),
        "placed_fraction_any_model": sum(counts.values()) / len(rows),
        "placed_fraction_largest_model": (counts[largest] / len(rows)) if largest is not None else 0.0,
        "models": len(counts),
    }
    if largest is None:
        return out
    every = evaluation.evaluate(records(rows), references, tolerance_s)
    one = evaluation.evaluate(records(rows, only_model=largest), references, tolerance_s)
    out["all_models"] = {k: every[k] for k in SCORE_FIELDS}
    out["largest_model"] = {k: one[k] for k in SCORE_FIELDS}
    return out


def depth_model_size(
    rows: list[dict],
    xyz: np.ndarray,
    observations: dict[str, np.ndarray],
    depth_for_frame: Callable[[int], tuple[np.ndarray, np.ndarray] | None],
    *,
    min_points: int = 20,
) -> dict:
    """Run-wide metric size: median over frames of median(model depth / SfM depth) at observed points."""
    per_frame = {}
    for k in np.unique(observations["frame_index"]):
        row = rows[int(k)]
        loaded = depth_for_frame(int(k))
        if row["T_world_camera"] is None or loaded is None:
            continue
        depth, valid = loaded
        mask = observations["frame_index"] == k
        world_from_camera = np.array(row["T_world_camera"])
        points = xyz[observations["point_index"][mask]]
        camera = (points - world_from_camera[:3, 3]) @ world_from_camera[:3, :3]
        u = np.rint(observations["uv"][mask, 0]).astype(int)
        v = np.rint(observations["uv"][mask, 1]).astype(int)
        inside = (u >= 0) & (v >= 0) & (u < depth.shape[1]) & (v < depth.shape[0]) & (camera[:, 2] > 0)
        u, v, z = u[inside], v[inside], camera[inside, 2]
        good = valid[v, u] & np.isfinite(depth[v, u]) & (depth[v, u] > 0)
        if good.sum() >= min_points:
            per_frame[int(k)] = (float(np.median(depth[v, u][good] / z[good])), int(good.sum()))
    if not per_frame:
        return {"size": None, "frames_used": 0}
    sizes = np.array([s for s, _ in per_frame.values()])
    return {
        "size": float(np.median(sizes)),
        "frames_used": len(per_frame),
        "points_per_frame_median": float(np.median([n for _, n in per_frame.values()])),
        "frame_size_spread": [float(np.percentile(sizes, 10)), float(np.percentile(sizes, 90))],
    }


def sized_score(sequence: Sequence, rows: list[dict], size: float, model_id: int, *, tolerance_s: float = 0.02) -> dict:
    """Best-fit rigid error of the largest model after multiplying it by a given size."""
    result = evaluation.evaluate(records(rows, size=size, only_model=model_id), sequence.references(), tolerance_s)
    return {"size": size, "ate_rigid_rmse_m": result["ate_rigid_rmse_m"],
            "rpe_1s_translation_rmse_m": result["rpe_1s_translation_rmse_m"]}
