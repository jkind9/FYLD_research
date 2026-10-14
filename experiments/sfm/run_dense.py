"""Fuse per-frame depth along a camera path into one surface and score it against a reference.

Poses come from the recording's ground truth (`--poses true`, Task71 controls) or from a saved
SfM run (`--poses sfm:<run>/output/<mapper>`, Task72). Example (`.venv-sfm`):

    python -m experiments.sfm.run_dense --recording icl:data/icl_nuim/trajectory2 --every 2 \
        --depth sensor --poses true --run-root experiments/sfm/runs/dense_icl
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from experiments.shared.runs import Run, write_json

from .src import dense, references, scoring, sequences

evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")
surface_evaluation = importlib.import_module("experiments.04_surface_reconstruction.src.evaluation")

REPO = Path(__file__).resolve().parents[2]
DEPTH_CHOICES = ("sensor", "model", "model-frame-reference", "model-run-reference", "model-sfm-size",
                 "model-sfm-size-shift", "sparse")

HYPERPARAMETERS = {
    "tsdf_voxel_m": {"value": {"icl": 0.01, "tum": 0.02}, "source": "proposed by Claude 2026-10-13, not owner-ruled"},
    "tsdf_truncation_voxels": {"value": 4, "source": "Open3D tutorial convention; proposed by Claude 2026-10-13, not owner-ruled"},
    "depth_range_m": {"value": [0.1, 4.0], "source": "inherited src/walkthrough/steps/contracts.py RGBD_MAX_DEPTH_M"},
    "score_threshold_m": {"value": 0.05, "source": "inherited experiment 04 reporting threshold"},
    "fusion_camera": {"value": {"tum": [525.0, 525.0, 319.5, 239.5], "icl": [481.2, 480.0, 319.5, 239.5]},
                      "source": "TUM page default for registered depth (inherited experiment 03 dataset.py:13); ICL conventions.json"},
    "sensor_depth_units_per_metre": {"value": 5000, "source": "inherited TUM and ICL conventions"},
    "reference_sizes": {"value": {"frame": "least squares through zero over pixels valid in both",
                                  "run": "median over frames of per-frame median(sensor / model)"},
                        "source": "inherited Task65 ReferenceFrameScale and ReferenceGlobalScale"},
    "sfm_frame_size": {"value": {"statistic": "median(SfM depth / model depth)", "min_points": 20,
                                 "point_filter": "track length >= 3, reprojection error <= 2 px",
                                 "shift_variant": "least squares, refit without largest 10% residuals"},
                       "source": "proposed by Claude 2026-10-13, not owner-ruled"},
    "sfm_metric_size": {"value": ["best-fit size from camera path (reference upper bound)", "depth-model size from Task67 scores (deployable)"],
                        "source": "proposed by Claude 2026-10-13, not owner-ruled"},
    "devices": {"value": "CPU only", "source": "confirmed 2026-10-08"},
}


def depth_maps(folder: Path | None) -> dict[str, Path]:
    """Frame ID to model depth arrays, from a walkthrough run or a dump_depth folder."""
    if folder is None:
        return {}
    if (folder / "index.json").is_file():
        index = json.loads((folder / "index.json").read_text(encoding="utf-8"))
        return {frame_id: folder / name for frame_id, name in index["frames"].items()}
    manifest = json.loads((folder / "output/predictions/depth.json").read_text(encoding="utf-8"))
    return {frame["frame_id"]: folder / frame["arrays"] for frame in manifest["frames"]}


def sensor_depth(sequence: sequences.Sequence, k: int) -> tuple[np.ndarray, np.ndarray] | None:
    name = sequence.depth_names[k] if sequence.depth_names else None
    if name is None:
        return None
    raw = np.asarray(Image.open(sequence.image_root / name), dtype=np.float64)
    depth = raw / HYPERPARAMETERS["sensor_depth_units_per_metre"]["value"]
    return depth, raw > 0


def model_depth(maps: dict[str, Path], sequence: sequences.Sequence, k: int) -> tuple[np.ndarray, np.ndarray] | None:
    path = maps.get(sequence.frame_ids[k])
    if path is None:
        return None
    arrays = np.load(path)
    return arrays["depth"].astype(np.float64), arrays["valid"]


def kind_of(recording: str) -> str:
    return recording.partition(":")[0]


def camera_for(recording: str) -> dense.Pinhole:
    fx, fy, cx, cy = HYPERPARAMETERS["fusion_camera"]["value"][kind_of(recording)]
    return dense.Pinhole(640, 480, fx, fy, cx, cy)


def true_poses(sequence: sequences.Sequence) -> list[np.ndarray | None]:
    refs = sequence.references()
    times = np.array([t for t, _ in refs])
    out = []
    for stamp in sequence.timestamps_s:
        i = int(np.argmin(np.abs(times - stamp)))
        out.append(refs[i][1] if abs(times[i] - stamp) <= 0.02 else None)
    return out


def depth_model_size(sequence: sequences.Sequence, folder: Path, maps: dict[str, Path]) -> float | None:
    """Run-wide size from model depth at the SfM points: the saved Task67 value, else computed from `maps`."""
    scores = json.loads((folder / "scores.json").read_text(encoding="utf-8"))
    if scores.get("depth_model_size", {}).get("size") is not None:
        return scores["depth_model_size"]["size"]
    rows = json.loads((folder / "frames.json").read_text(encoding="utf-8"))["frames"]
    points = np.load(folder / "points.npz")
    return scoring.depth_model_size(rows, points["xyz"], dict(np.load(folder / "observations.npz")),
                                    lambda k: model_depth(maps, sequence, k))["size"]


def sfm_poses(sequence: sequences.Sequence, folder: Path, size_source: str,
              maps: dict[str, Path] | None = None) -> tuple[list[np.ndarray | None], dict]:
    """SfM camera-to-world poses of the largest model, sized to metres and placed in the reference world."""
    rows = json.loads((folder / "frames.json").read_text(encoding="utf-8"))["frames"]
    counts: dict[int, int] = {}
    for row in rows:
        if row["model_id"] is not None:
            counts[row["model_id"]] = counts.get(row["model_id"], 0) + 1
    largest = max(counts, key=counts.get)
    truth = true_poses(sequence)
    placed = [i for i, r in enumerate(rows) if r["model_id"] == largest and truth[i] is not None]
    estimated = np.array([np.array(rows[i]["T_world_camera"])[:3, 3] for i in placed])
    reference = np.array([truth[i][:3, 3] for i in placed])
    if size_source == "best-fit":
        size = None
    elif isinstance(size_source, float):
        size = size_source
    elif size_source == "depth-model":
        size = depth_model_size(sequence, folder, maps or {})
        if size is None:
            raise ValueError("No depth-model size: the SfM run saved none and no model depth matched its points")
    else:
        raise ValueError("SfM size must be best-fit, depth-model or a number")
    rotation, translation, fitted = _align(estimated, reference, size)
    poses = []
    for row in rows:
        if row["model_id"] != largest:
            poses.append(None)
            continue
        pose = np.array(row["T_world_camera"])
        moved = np.eye(4)
        moved[:3, :3] = rotation @ pose[:3, :3]
        moved[:3, 3] = fitted * rotation @ pose[:3, 3] + translation
        poses.append(moved)
    return poses, {"largest_model": largest, "size": fitted, "size_source": size_source,
                   "alignment": "rotation and shift fitted to the true camera centres (scoring only)",
                   "rotation": rotation.tolist(), "translation": translation.tolist()}


def _align(estimated: np.ndarray, reference: np.ndarray, size: float | None) -> tuple[np.ndarray, np.ndarray, float]:
    """Umeyama fit; with a given size only rotation and shift are fitted."""
    mean_e, mean_r = estimated.mean(0), reference.mean(0)
    e, r = estimated - mean_e, reference - mean_r
    u, d, vt = np.linalg.svd(r.T @ e / len(e))
    sign = np.diag([1.0, 1.0, np.sign(np.linalg.det(u) * np.linalg.det(vt))])
    rotation = u @ sign @ vt
    fitted = float(np.trace(np.diag(d) @ sign) / np.mean(np.sum(e**2, 1))) if size is None else float(size)
    return rotation, mean_r - fitted * rotation @ mean_e, fitted


def size_option(text: str) -> str | float:
    """`--sfm-size` value: a named source, or metres per SfM unit."""
    if text in ("best-fit", "depth-model"):
        return text
    try:
        return float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("use best-fit, depth-model or a number of metres per SfM unit") from None


def reference_surface(args: argparse.Namespace, sequence: sequences.Sequence, camera: dense.Pinhole, voxel: float) -> tuple[np.ndarray, str]:
    if kind_of(args.recording) == "icl":
        return references.icl_reference(Path(args.recording.partition(":")[2]).parent), "ICL publisher surface model"
    poses = true_poses(sequence)
    frames = (dense.DepthFrame(*sensor_depth(sequence, k), poses[k]) for k in range(len(poses))
              if poses[k] is not None and sensor_depth(sequence, k) is not None)
    points, _ = dense.fuse_tsdf(frames, camera, voxel_m=voxel, truncation_voxels=HYPERPARAMETERS["tsdf_truncation_voxels"]["value"],
                                min_depth_m=0.1, max_depth_m=4.0)
    return points, "sensor reference: Kinect depth fused along the motion-capture path (carries sensor and timing error)"


def reference_size_per_frame(model: np.ndarray, model_valid: np.ndarray, sensor: np.ndarray, sensor_valid: np.ndarray) -> float | None:
    """Least squares through zero of sensor on model depth over pixels valid in both (Task65 rule)."""
    both = model_valid & sensor_valid & np.isfinite(model) & (model > 0)
    if both.sum() < 2:
        return None
    return float(np.dot(model[both], sensor[both]) / np.dot(model[both], model[both]))


def depth_frames(args: argparse.Namespace, sequence: sequences.Sequence, poses: list[np.ndarray | None],
                 maps: dict[str, Path], sfm_sizes: list[dict] | None) -> tuple[list[dense.DepthFrame], dict]:
    """Per-frame depth for the chosen source, sized as that source requires, with its pose."""
    loaded, notes = [], {"frames_without_pose": 0, "frames_without_depth": 0}
    run_ratios = []
    for k in range(len(sequence.image_names)):
        if poses[k] is None:
            notes["frames_without_pose"] += 1
            continue
        if args.depth == "sensor":
            pair = sensor_depth(sequence, k)
        else:
            pair = model_depth(maps, sequence, k)
        if pair is None:
            notes["frames_without_depth"] += 1
            continue
        depth, valid = pair
        if args.depth == "model-frame-reference":
            sensor = sensor_depth(sequence, k)
            size = reference_size_per_frame(depth, valid, *sensor) if sensor else None
            if size is None:
                notes["frames_without_depth"] += 1
                continue
            depth = depth * size
        elif args.depth == "model-run-reference":
            sensor = sensor_depth(sequence, k)
            both = valid & sensor[1] & np.isfinite(depth) & (depth > 0) if sensor else None
            if both is not None and both.any():
                run_ratios.append(float(np.median(sensor[0][both] / depth[both])))
        elif args.depth in ("model-sfm-size", "model-sfm-size-shift"):
            row = sfm_sizes[k]
            if row["size"] is None:
                notes["frames_without_depth"] += 1
                continue
            depth = depth * row["size"] + row["shift"]
        loaded.append(dense.DepthFrame(depth, valid, poses[k]))
    if args.depth == "model-run-reference":
        size = float(np.median(run_ratios))
        loaded = [dense.DepthFrame(f.depth_m * size, f.valid, f.world_from_camera) for f in loaded]
        notes["run_reference_size"] = size
    return loaded, notes


def sfm_frame_sizes(sequence: sequences.Sequence, folder: Path, maps: dict[str, Path], metric_size: float,
                    *, with_shift: bool) -> list[dict]:
    """Per-frame size taking model depth into metres, from the SfM points each frame observed."""
    settings = HYPERPARAMETERS["sfm_frame_size"]["value"]
    rows = json.loads((folder / "frames.json").read_text(encoding="utf-8"))["frames"]
    points = np.load(folder / "points.npz")
    observations = dict(np.load(folder / "observations.npz"))
    good_point = (points["track_length"] >= 3) & (points["error_px"] <= 2.0)
    keep = good_point[observations["point_index"]]
    observations = {name: values[keep] for name, values in observations.items()}
    camera_depth = np.full(len(observations["uv"]), np.nan)
    for k in np.unique(observations["frame_index"]):
        mask = observations["frame_index"] == k
        pose = np.array(rows[int(k)]["T_world_camera"])
        world = points["xyz"][observations["point_index"][mask]]
        camera_depth[mask] = ((world - pose[:3, 3]) @ pose[:3, :3])[:, 2]

    def model_depth_at(k: int, uv: np.ndarray) -> np.ndarray | None:
        pair = model_depth(maps, sequence, k)
        if pair is None:
            return None
        depth, valid = pair
        u = np.clip(np.rint(uv[:, 0]).astype(int), 0, depth.shape[1] - 1)
        v = np.clip(np.rint(uv[:, 1]).astype(int), 0, depth.shape[0] - 1)
        return np.where(valid[v, u], depth[v, u], np.nan)

    sizes = dense.frame_sizes(len(rows), observations, camera_depth, model_depth_at,
                              min_points=settings["min_points"], with_shift=with_shift)
    for row in sizes:
        if row["size"] is not None:
            row["size"] *= metric_size
            row["shift"] *= metric_size
    return sizes


def run(args: argparse.Namespace) -> Path:
    sequence = sequences.load(args.recording, every=args.every)
    kind = kind_of(args.recording)
    camera = camera_for(args.recording)
    voxel = HYPERPARAMETERS["tsdf_voxel_m"]["value"][kind]
    maps = depth_maps(args.depth_maps)
    folder = None
    if args.poses == "true":
        poses, pose_info = true_poses(sequence), {"source": "ground truth (reference control)"}
    else:
        folder = Path(args.poses.partition(":")[2])
        poses, pose_info = sfm_poses(sequence, folder, args.sfm_size, maps)
    sfm_sizes = None
    if args.depth in ("model-sfm-size", "model-sfm-size-shift"):
        if folder is None:
            raise SystemExit("SfM-sized depth needs --poses sfm:<folder>")
        sfm_sizes = sfm_frame_sizes(sequence, folder, maps, pose_info["size"], with_shift=args.depth.endswith("shift"))
    configuration = {"experiment": "sfm dense", "recording": args.recording, "every": args.every, "depth": args.depth,
                     "depth_maps": str(args.depth_maps) if args.depth_maps else None, "poses": args.poses,
                     "sfm_size": args.sfm_size, "size_note": args.size_note, "hyperparameters": HYPERPARAMETERS}
    with Run(args.run_root, REPO, configuration) as active:
        write_json(active.path / "input/sequence.json", sequence.manifest())
        with active.measure("reference"):
            reference, reference_label = reference_surface(args, sequence, camera, voxel)
        notes: dict = {}
        if args.depth == "sparse":
            points_file = np.load(folder / "points.npz")
            rotation, translation = np.array(pose_info["rotation"]), np.array(pose_info["translation"])
            points = pose_info["size"] * points_file["xyz"] @ rotation.T + translation
        else:
            frames, notes = depth_frames(args, sequence, poses, maps, sfm_sizes)
            with active.measure("fusion", frames=len(frames)):
                points, fusion = dense.fuse_tsdf(frames, camera, voxel_m=voxel,
                                                 truncation_voxels=HYPERPARAMETERS["tsdf_truncation_voxels"]["value"],
                                                 min_depth_m=HYPERPARAMETERS["depth_range_m"]["value"][0],
                                                 max_depth_m=HYPERPARAMETERS["depth_range_m"]["value"][1])
            notes.update(fusion)
            active.set_processed_frames(len(frames))
        with active.measure("scoring"):
            scorer = surface_evaluation.SurfaceScorer(reference, HYPERPARAMETERS["score_threshold_m"]["value"])
            scorer.observe(points)
            scores = scorer.summary()
        np.save(active.path / "output/surface_points.npy", points.astype(np.float32))
        if sfm_sizes is not None:
            write_json(active.path / "output/frame_sizes.json", {"frames": sfm_sizes})
        write_json(active.path / "output/scores.json", {
            "surface": scores, "reference": reference_label, "poses": {k: v for k, v in pose_info.items() if k not in ("rotation", "translation")},
            "notes": notes, "points": len(points)})
    return active.path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--depth", choices=DEPTH_CHOICES, required=True)
    parser.add_argument("--depth-maps", type=Path, help="walkthrough run or dump_depth folder with model depth")
    parser.add_argument("--poses", default="true", help="true, or sfm:<sfm run>/output/<mapper>")
    parser.add_argument("--sfm-size", type=size_option, default="best-fit",
                        help="best-fit, depth-model, or metres per SfM unit (e.g. from run_metric_points)")
    parser.add_argument("--size-note", help="label for the report's Poses column, e.g. '20 metric readings'")
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.depth.startswith("model") and args.depth_maps is None:
        parser.error("model depth choices need --depth-maps")
    print(run(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
