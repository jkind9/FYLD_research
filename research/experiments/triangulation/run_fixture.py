"""Score depth triangulated along a known camera path on the committed TUM desk fixture.

    .venv/Scripts/python.exe -B -m research.experiments.triangulation.run_fixture --label <label>

The fixture's motion-capture poses stand in for an open tracker. They are written as a TUM trajectory
in the recording's own world, where z is up, as Basalt's is; sitescan turns that world upright when
it reads it. The fixture's Kinect depth (7 of 20 frames, 160 x 120) is the reference. No triangulated
fit sees it.

Writes results.json in outputs/tum-desk-20/triangulation-trial/<yyyymmdd-hhmm>_<label>/ and prints the same numbers.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from sitescan import depth, runs, scale, session
from sitescan.pipelines import DEPTH_MODEL, RoomSettings, build_room
from sitescan.pipelines.room import predict_frame
from sitescan.pipelines.targets import sweep_prior
from sitescan.session.wire_v1 import world_from_camera_cv
from sitescan.triangulate import Triangulator
from sitescan.triangulate import project as triangulate_project

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "tum_desk_20"
THREADS = 16
FAR_M = 4.0


def write_trajectory(path: Path) -> Path:
    """The fixture's camera poses as a TUM file, with exact times."""
    rows = []
    for frame in session.frames(FIXTURE):
        quaternion = Rotation.from_matrix(frame.pose[:3, :3]).as_quat()
        values = " ".join(f"{v:.12f}" for v in (*frame.pose[:3, 3], *quaternion))
        rows.append(f"{frame.t_ns // 10**9}.{frame.t_ns % 10**9:09d} {values}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def reference_at(kinect, camera, uv: np.ndarray) -> np.ndarray:
    """Kinect depth at colour pixels (nearest Kinect pixel); 0 where it has none."""
    k = kinect.camera
    cols = np.clip(
        np.rint((uv[:, 0] - camera.cx) / camera.fx * k.fx + k.cx).astype(int), 0, k.width - 1
    )
    rows = np.clip(
        np.rint((uv[:, 1] - camera.cy) / camera.fy * k.fy + k.cy).astype(int), 0, k.height - 1
    )
    return kinect.depth_m[rows, cols]


def errors(measured: np.ndarray, reference: np.ndarray) -> dict:
    """Count, median signed and absolute relative error, and the 90th percentile of the absolute error."""
    good = (reference > 0) & np.isfinite(measured) & (measured > 0)
    relative = measured[good] / reference[good] - 1
    if not len(relative):
        return {"n": 0}
    return {
        "n": len(relative),
        "bias": round(float(np.median(relative)), 4),
        "abs_rel_p50": round(float(np.median(np.abs(relative))), 4),
        "abs_rel_p90": round(float(np.percentile(np.abs(relative), 90)), 4),
    }


def kinect_pixels(kinect, camera) -> tuple[np.ndarray, np.ndarray]:
    """Colour pixels of every valid Kinect pixel, and its depth."""
    uv, metres = scale.depth_targets(kinect, camera, min_confidence=0)
    return uv, metres


def frame_scores(model, trajectory) -> list[dict]:
    """Per Kinect frame: triangulated depth, and learned depth sized six ways, against the Kinect."""
    triangulator = Triangulator()
    rows = []
    for frame in session.read_wire_session(FIXTURE, trajectory):
        pose = world_from_camera_cv(frame.pose)
        camera = session.camera(frame)
        started = time.perf_counter()
        sparse = triangulator.sparse(frame.grey, camera, pose)
        sparse_ms = (time.perf_counter() - started) * 1000
        if frame.depth is None:
            continue
        kinect = session.arcore_depth(frame.depth)
        _, learned, valid = predict_frame(model, frame, pose)
        prior = sweep_prior(learned, valid, sparse)
        started = time.perf_counter()
        dense = triangulator.dense(frame.grey, camera, pose, frame.t_ns, prior)
        dense_ms = (time.perf_counter() - started) * 1000
        global_dense = triangulator.dense(frame.grey, camera, pose, frame.t_ns)
        uv, truth = kinect_pixels(kinect, camera)
        rows_px = np.clip(uv[:, 1].astype(int), 0, camera.height - 1)
        cols_px = np.clip(uv[:, 0].astype(int), 0, camera.width - 1)
        weight = scale.target_weights(sparse.depth_m, sparse.sigma_m)
        dense_uv, dense_m = (
            scale.depth_targets(dense, camera)
            if dense is not None
            else (np.zeros((0, 2)), np.zeros(0))
        )
        fields = {
            "kinect_grid (fitted to the reference itself)": scale.fit_grid(
                learned, valid, uv, truth
            ),
            "sparse_median": scale.fit_one(learned, valid, sparse.uv, sparse.depth_m, 20, weight),
            "sparse_grid": scale.fit_grid(
                learned, valid, sparse.uv, sparse.depth_m, minimum=20, weight=weight
            ),
            "sparse_power": scale.fit_power(learned, valid, sparse.uv, sparse.depth_m, weight),
            "dense_grid": scale.fit_grid(learned, valid, dense_uv, dense_m)
            if len(dense_m)
            else None,
            "dense_power": scale.fit_power(learned, valid, dense_uv, dense_m, minimum=50)
            if len(dense_m)
            else None,
        }
        sized = {}
        for name, field in fields.items():
            if field is None:
                sized[name] = {"n": 0}
                continue
            field = np.broadcast_to(np.asarray(field, float), learned.shape)
            sized[name] = errors((learned * field)[rows_px, cols_px], truth)
        dense_row = (
            {"n": 0} if dense is None else errors(dense_m, reference_at(kinect, camera, dense_uv))
        )
        global_uv, global_m = (
            (np.zeros((0, 2)), np.zeros(0))
            if global_dense is None
            else scale.depth_targets(global_dense, camera)
        )
        rows.append(
            {
                "seq": frame.seq,
                "sparse_points": len(sparse.depth_m),
                "sparse_ms": round(sparse_ms, 1),
                "sparse": errors(sparse.depth_m, reference_at(kinect, camera, sparse.uv)),
                "dense_around_prior": dense_row
                | {
                    "ms": round(dense_ms, 1),
                    "confident_share": None
                    if dense is None
                    else round(float((dense.confidence >= 128).mean()), 3),
                },
                "dense_without_prior": errors(global_m, reference_at(kinect, camera, global_uv)),
                "learned_sized_by": sized,
            }
        )
    return rows


def kinect_frames() -> list:
    """The fixture frames that carry Kinect depth, in the recording's own world."""
    return [frame for frame in session.frames(FIXTURE) if frame.depth is not None]


def kinect_surface(frames) -> np.ndarray:
    """World points of every valid Kinect pixel nearer than the fusion limit, on the recorded poses."""
    parts = []
    for frame in frames:
        uv, metres = kinect_pixels(frame.depth, frame.camera)
        near = metres < FAR_M
        uv, metres = uv[near], metres[near]
        local = np.c_[
            (uv[:, 0] - frame.camera.cx) / frame.camera.fx * metres,
            (uv[:, 1] - frame.camera.cy) / frame.camera.fy * metres,
            metres,
        ]
        parts.append(local @ frame.pose[:3, :3].T + frame.pose[:3, 3])
    return np.concatenate(parts)


def seen_by_kinect(points: np.ndarray, frames) -> np.ndarray:
    """Points that land on a valid Kinect pixel of at least one reference frame, in front or behind it."""
    seen = np.zeros(len(points), bool)
    for frame in frames:
        uv, z = triangulate_project(points, frame.camera, frame.pose)
        inside = (
            (z > 0.1)
            & (uv[:, 0] >= 0)
            & (uv[:, 0] < frame.camera.width)
            & (uv[:, 1] >= 0)
            & (uv[:, 1] < frame.camera.height)
        )
        reference = np.zeros(len(points))
        reference[inside] = reference_at(frame.depth, frame.camera, uv[inside])
        seen |= inside & (reference > 0) & (reference < FAR_M)
    return seen


def room_scores(model, trajectory) -> dict:
    """Room builds from each scale source, scored where the Kinect frames saw.

    Each surface is moved back into the recording's world, and only points that land on a valid
    Kinect pixel are scored: by their distance to the nearest Kinect point.
    """
    frames = kinect_frames()
    tree = cKDTree(kinect_surface(frames))
    back = np.linalg.inv(session.up_to_y((0.0, 0.0, 1.0)))
    runs = {
        "arcore_poses_kinect_depth (today's route)": (RoomSettings(), None),
        "tracker_poses_kinect_depth (only the poses change)": (RoomSettings(), trajectory),
        "tracker_poses_sparse_grid": (RoomSettings(scale_sources=("sparse",)), trajectory),
        "tracker_poses_sparse_power": (
            RoomSettings(scale_sources=("sparse",), scale_fit="power"),
            trajectory,
        ),
        "tracker_poses_dense_then_sparse": (
            RoomSettings(scale_sources=("dense", "sparse")),
            trajectory,
        ),
        "tracker_poses_dense_then_sparse_power": (
            RoomSettings(scale_sources=("dense", "sparse"), scale_fit="power"),
            trajectory,
        ),
    }
    out = {}
    for name, (settings, poses) in runs.items():
        started = time.perf_counter()
        room = build_room(FIXTURE, model, settings, poses)
        surface = room.surface if poses is None else room.surface @ back[:3, :3].T
        seen = seen_by_kinect(surface, frames)
        distance, _ = tree.query(surface[seen])
        summary = room.summary
        out[name] = {
            "seconds": round(time.perf_counter() - started, 1),
            "frames": summary["frames"],
            "scale_frames": summary["scale"]["frames_per_source"],
            "scale_min_median_max": [round(v, 3) for v in summary["scale_min_median_max"]],
            "surface_points": summary["surface_points"],
            "scored_points": int(seen.sum()),
            "to_kinect_m": {
                "p50": round(float(np.median(distance)), 4),
                "p90": round(float(np.percentile(distance, 90)), 4),
            },
            "map": {k: summary["map"].get(k) for k in ("length_m", "width_m", "observed_area_m2")},
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="one to four lowercase words joined by hyphens")
    args = parser.parse_args()
    args.out = runs.new_run("tum-desk-20", "triangulation-trial", args.label, {}, root=runs.OUTPUTS)
    trajectory = session.read_tum(write_trajectory(args.out / "trajectory.txt"), source="mocap")
    model = depth.load_model(DEPTH_MODEL, threads=THREADS)
    results = {"frames": frame_scores(model, trajectory), "rooms": room_scores(model, trajectory)}
    (args.out / "results.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    runs.finish_run(args.out)
    print(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
