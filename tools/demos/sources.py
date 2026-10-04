"""Pinned exported runs used by the demo pages, and loaders for their saved files.

Every page reads only these completed runs. Nothing here reruns an experiment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from tools.demos.geometry import (
    Intrinsics,
    backproject,
    camera_normals,
    depth_edges,
    to_world,
    voxel_fuse,
)

REPLAY_RUN = "experiments/06_object_recognition/experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66"
TRACKING_RUN = "experiments/03_camera_pose_estimation/runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0"
SURFACE_RUN = "experiments/04_surface_reconstruction/runs/20261002T145103.184769Z_000165ef2e044376baf54b675172a64e"
ICL_REFERENCE = "data/icl_nuim/reference_surface/living-room.ply"
SURFACE_FRAMES = ["1", "101", "201", "301", "401", "501", "601", "701", "801"]

# TUM Freiburg1 calibration and depth scale as recorded in the replay run configuration.
TUM = Intrinsics(width=640, height=480, fx=525.0, fy=525.0, cx=319.5, cy=239.5)
TUM_DEPTH_SCALE = 5000.0
TUM_VALID_DEPTH_M = (0.0, 4.0)


@dataclass(frozen=True)
class Frame:
    index: int
    frame_id: str
    timestamp_s: float
    rgb_path: Path
    depth_path: Path
    pose: np.ndarray
    detections: list


def require(path: Path) -> Path:
    """Fail clearly when a pinned run file is missing from this checkout."""
    if not path.exists():
        raise FileNotFoundError(f"missing exported file {path}; pass --source-root pointing at a checkout with local runs")
    return path


def load_replay(root: Path) -> dict:
    """Return the replay observation ledger and its 60 frames with poses and detections."""
    run = root / REPLAY_RUN
    ledger = json.loads(require(run / "input/baseline_observations.json").read_text(encoding="utf-8"))
    frames = [
        Frame(index=f["frame_index"], frame_id=str(f["frame_id"]), timestamp_s=float(f["timestamp_s"]),
              rgb_path=require(run / "input" / f["rgb"]), depth_path=require(run / "input" / f["depth"]),
              pose=np.asarray(f["pose"]["T_world_camera"], dtype=float), detections=f["detections"])
        for f in ledger["frames"]
    ]
    display = np.load(require(run / "input/cloud_display.npz"))
    return {"ledger": ledger, "frames": frames, "display_points": display["world_m"], "display_rgb": display["rgb"]}


def read_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def read_depth_m(path: Path) -> np.ndarray:
    """Decode a TUM 16-bit depth PNG to metres; zero and out-of-range values become NaN."""
    raw = np.asarray(Image.open(path)).astype(float)
    depth = raw / TUM_DEPTH_SCALE
    lo, hi = TUM_VALID_DEPTH_M
    depth[(depth <= lo) | (depth >= hi)] = np.nan
    return depth


def frame_points(frame: Frame, stride: int, edge_jump: float) -> dict[str, np.ndarray]:
    """World points, colours and normals for one frame, with depth-edge pixels removed."""
    depth = read_depth_m(frame.depth_path)
    depth[depth_edges(depth, edge_jump)] = np.nan
    rgb = read_rgb(frame.rgb_path)
    normals_cam = camera_normals(depth, TUM)
    pts_cam, pix = backproject(depth, TUM, stride=stride)
    n_cam = normals_cam[pix[:, 0], pix[:, 1]]
    ok = np.any(n_cam != 0, axis=1)
    rot = frame.pose[:3, :3]
    return {
        "points": to_world(pts_cam[ok], frame.pose),
        "colours": rgb[pix[ok, 0], pix[ok, 1]],
        "normals": n_cam[ok] @ rot.T,
    }


def fused_desk_scene(frames: list[Frame], stride: int, edge_jump: float, voxel_m: float, min_count: int) -> dict:
    """Fuse every replay frame into one voxel-averaged coloured surface with normals."""
    parts = [frame_points(f, stride, edge_jump) for f in frames]
    points = np.concatenate([p["points"] for p in parts])
    colours = np.concatenate([p["colours"] for p in parts])
    normals = np.concatenate([p["normals"] for p in parts])
    fused = voxel_fuse(points, colours, normals, voxel_m, min_count=min_count)
    fused["raw_point_count"] = len(points)
    return fused


def load_tracking(root: Path) -> dict:
    """Estimated poses, per-frame errors against motion capture, and summary metrics."""
    out = root / TRACKING_RUN / "output"
    poses = json.loads(require(out / "poses.json").read_text(encoding="utf-8"))
    metrics = json.loads(require(out / "metrics.json").read_text(encoding="utf-8"))
    return {"poses": poses["records"], "metrics": metrics}


def load_surface(root: Path, per_frame: int, seed: int) -> dict:
    """Sample the 9-view ICL point surface with colours and distance to the reference model."""
    out = root / SURFACE_RUN / "output"
    rng = np.random.default_rng(seed)
    pts, cols, dist, frame_idx, cams = [], [], [], [], []
    for i, fid in enumerate(SURFACE_FRAMES):
        model = np.load(require(out / fid / "model.npy"), mmap_mode="r")
        pick = np.sort(rng.choice(len(model), size=min(per_frame, len(model)), replace=False))
        pts.append(np.asarray(model[pick]))
        cols.append(np.asarray(np.load(out / fid / "rgb.npy", mmap_mode="r")[pick]))
        dist.append(np.asarray(np.load(out / fid / "reference_distance.npy", mmap_mode="r")[pick]))
        frame_idx.append(np.full(len(pick), i, dtype=np.uint8))
        stages = json.loads((out / fid / "stages.json").read_text(encoding="utf-8"))
        cams.append(stages)
    metrics = json.loads(require(out / "metrics.json").read_text(encoding="utf-8"))
    return {"points": np.concatenate(pts), "colours": np.concatenate(cols), "distance_m": np.concatenate(dist),
            "frame": np.concatenate(frame_idx), "stages": cams, "metrics": metrics}


CUP_RECORD = "experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json"


def load_cup_spread(root: Path) -> dict:
    """Spread of the accepted desk cup's 3D positions from the replay's published record."""
    record = json.loads(require(root / CUP_RECORD).read_text(encoding="utf-8"))
    box = record["measurements"]["accepted_desk_cup_observations"]["box_median"]
    return {"rms_mm": float(box["radial_rms_from_median_mm"]), "n": int(box["count"])}


def load_reference_sample(root: Path, count: int, seed: int) -> dict:
    """Random sample of the independent ICL reference surface with its colours."""
    import open3d as o3d

    cloud = o3d.io.read_point_cloud(str(require(root / ICL_REFERENCE)))
    pts = np.asarray(cloud.points)
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(pts), size=min(count, len(pts)), replace=False)
    cols = (np.asarray(cloud.colors)[pick] * 255).astype(np.uint8) if cloud.has_colors() else np.full((len(pick), 3), 160, np.uint8)
    return {"points": pts[pick], "colours": cols, "total": len(pts)}
