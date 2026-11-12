"""Compare a LingBot-Map run with ARCore on the same phone session: size, camera path and depth at tracked points.

LingBot-Map's output has no real-world size. One best fit with size (Open3D's point-to-point estimate with
scaling, the Umeyama method) maps its camera centres onto ARCore's, giving the size and the path difference
left over. Depth is then checked against ARCore's tracked points by distance, the check Task117 ran on the
fused learned depth. ARCore is not ground truth: every number here is agreement between two estimates.

Writes compare.json and lingbot_cloud.ply (ARCore world, metres, y up) into the run folder.

    .venv\\Scripts\\python -B -m research.experiments.lingbot_map.compare --run <run folder> --session <v2 session> [--surface <surface.ply>]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import open3d as o3d
from PIL import Image

from research.evaluation.depth_check import BINS, point_targets, summarise
from sitescan.depth.orientation import quarter_turns
from sitescan.session import read_wire_session, wire_v1

SIDE = 518  # LingBot-Map's processed width and crop height (demo.py crop mode)
PATCH = 14
CONF_MIN = 1.5  # demo.py's display threshold for depth confidence
MAX_DEPTH_M = 10.0  # the owner's target scenes: surfaces under about 10 m
VOXEL_M = 0.02  # the room build's fusion voxel
NEAR_M = 0.05  # "within 5 cm", the coverage distance used across the project
CLOUD_STEP = 3  # every third frame, every second pixel, for the cloud
CHUNK = 20  # frames per voxel thinning, to bound memory


def processed_geometry(recorded_size) -> tuple[float, float, int]:
    """(x scale, y scale, rows cropped from the top) for a recorded W x H frame turned clockwise, resized to 518
    wide with the height rounded to whole 14-pixel patches, then centre-cropped to 518 tall."""
    width, height = recorded_size  # after the turn, the recorded width is the height
    new_height = round(width * SIDE / height / PATCH) * PATCH
    return SIDE / height, new_height / width, max(new_height - SIDE, 0) // 2


def processed_pixels(pixels: np.ndarray, recorded_size) -> np.ndarray:
    """Recorded (u, v) to LingBot-Map (x, y). A clockwise turn sends (u, v) to (H - v, u)."""
    sx, sy, top = processed_geometry(recorded_size)
    return np.c_[(recorded_size[1] - pixels[:, 1]) * sx, pixels[:, 0] * sy - top]


def processed_image(path: Path, recorded_size) -> np.ndarray:
    """The colour frame as LingBot-Map saw it, 518 x 518 RGB in 0-1."""
    _, sy, top = processed_geometry(recorded_size)
    turned = Image.open(path).convert("RGB").transpose(Image.Transpose.ROTATE_270)
    resized = turned.resize((SIDE, round(recorded_size[0] * sy)), Image.Resampling.BICUBIC)
    return np.asarray(resized, dtype=np.float32)[top:top + SIDE] / 255


def nearest_rotations(matrices: np.ndarray) -> np.ndarray:
    """The closest true rotation to each 3 x 3 matrix. On the CPU LingBot-Map's camera head runs in bfloat16,
    which leaves its rotations up to 0.4% off orthonormal."""
    u, _, vt = np.linalg.svd(matrices)
    return u @ vt


def similarity(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float]:
    """Least-squares 4 x 4 transform (size x rotation, translation) taking source points onto target, and the size."""
    index = np.arange(len(source))
    estimate = o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=True)
    transform = estimate.compute_transformation(_cloud(source), _cloud(target), o3d.utility.Vector2iVector(np.c_[index, index]))
    return transform, float(np.cbrt(np.linalg.det(transform[:3, :3])))


def _cloud(points: np.ndarray, colours: np.ndarray | None = None) -> o3d.geometry.PointCloud:
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64)))
    if colours is not None:
        cloud.colors = o3d.utility.Vector3dVector(np.asarray(colours, dtype=np.float64))
    return cloud


def _apply(transform: np.ndarray, points: np.ndarray) -> np.ndarray:
    return points @ transform[:3, :3].T + transform[:3, 3]


def _session_frames(session: Path, wanted: set[int]) -> dict:
    """ARCore centre, tracked-point pixels and depths, and turn count per wanted frame; image bytes are dropped."""
    frames = {}
    for frame in read_wire_session(session):
        if frame.seq in wanted and frame.pose is not None:
            pixels, z = point_targets(frame)
            frames[frame.seq] = {"centre": wire_v1.world_from_camera(frame.pose)[:3, 3], "pixels": pixels, "z": z,
                                 "turns": quarter_turns(wire_v1.world_from_camera_cv(frame.pose)), "size": frame.image_size}
    return frames


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--surface", type=Path, help="a room build surface.ply to measure the cloud against")
    args = parser.parse_args(argv)

    run = json.loads((args.run / "run.json").read_text())
    seqs = [int(Path(name).stem) for name in run["names"]]
    depth = np.load(args.run / "depth.npy", mmap_mode="r")
    conf = np.load(args.run / "depth_conf.npy", mmap_mode="r")
    extrinsic = np.load(args.run / "extrinsic.npy")
    intrinsic = np.load(args.run / "intrinsic.npy")
    frames = _session_frames(args.session, set(seqs))
    posed = [i for i, seq in enumerate(seqs) if seq in frames]

    rotations, translations = nearest_rotations(extrinsic[:, :, :3]), extrinsic[:, :, 3]
    lingbot_centres = -np.einsum("nji,nj->ni", rotations, translations)  # camera centre = -R^T t
    arcore_centres = np.array([frames[seqs[i]]["centre"] for i in posed])
    transform, size = similarity(lingbot_centres[posed], arcore_centres)
    path_error = np.linalg.norm(_apply(transform, lingbot_centres[posed]) - arcore_centres, axis=1)
    spread = np.linalg.svd(arcore_centres - arcore_centres.mean(axis=0), compute_uv=False) / np.sqrt(len(posed))

    learned, tracked, upright = [np.zeros(0)], [np.zeros(0)], 0  # ARCore has no tracked points in a walk's first frames
    for i in posed:
        frame = frames[seqs[i]]
        if frame["turns"] != 1 or not len(frame["z"]):
            continue
        upright += 1
        xy = processed_pixels(frame["pixels"], frame["size"])
        inside = (xy[:, 0] >= 0) & (xy[:, 0] < SIDE) & (xy[:, 1] >= 0) & (xy[:, 1] < SIDE)
        values = np.asarray(depth[i], dtype=np.float32)[xy[inside, 1].astype(int), xy[inside, 0].astype(int)]
        keep = values > 0
        learned.append(values[keep] * size)
        tracked.append(frame["z"][inside][keep])
    learned, tracked = np.concatenate(learned), np.concatenate(tracked)
    rows = summarise(learned, tracked, np.ones(len(tracked), bool), bins=BINS + (np.inf,))
    for row in rows:
        row.pop("supported")

    pieces, merged = [], o3d.geometry.PointCloud()
    v, u = np.mgrid[0:SIDE:2, 0:SIDE:2]
    for count, i in enumerate(posed[::CLOUD_STEP], 1):
        d = np.asarray(depth[i, ::2, ::2], dtype=np.float32)
        keep = (d > 0) & (np.asarray(conf[i, ::2, ::2], dtype=np.float32) >= CONF_MIN) & (d * size <= MAX_DEPTH_M)
        fx, fy, cx, cy = intrinsic[i][0, 0], intrinsic[i][1, 1], intrinsic[i][0, 2], intrinsic[i][1, 2]
        camera = np.c_[(u[keep] - cx) / fx * d[keep], (v[keep] - cy) / fy * d[keep], d[keep]]
        world = (camera - translations[i]) @ rotations[i]  # R^T (x - t), row-vector form
        colours = processed_image(args.session / "frames" / run["names"][i], frames[seqs[i]]["size"])[::2, ::2][keep]
        pieces.append(_cloud(_apply(transform, world), colours).voxel_down_sample(VOXEL_M))
        if count % CHUNK == 0:
            for piece in pieces:
                merged += piece
            merged, pieces = merged.voxel_down_sample(VOXEL_M), []
    for piece in pieces:
        merged += piece
    merged = merged.voxel_down_sample(VOXEL_M)
    o3d.io.write_point_cloud(str(args.run / "lingbot_cloud.ply"), merged)

    result = {
        "frames": run["frames"], "posed_frames": len(posed), "upright_frames_with_points": upright,
        "size": round(size, 4),
        "size_from_depth": round(float(np.median(tracked / (learned / size))), 4) if len(tracked) else None,
        "path_rmse_m": round(float(np.sqrt(np.mean(path_error ** 2))), 4), "path_max_m": round(float(path_error.max()), 4),
        "arcore_path_length_m": round(float(np.linalg.norm(np.diff(arcore_centres, axis=0), axis=1).sum()), 3),
        "arcore_path_spread_m": [round(float(s), 3) for s in spread],
        "tracked_point_views": len(tracked), "depth_rows": rows, "cloud_points": len(merged.points),
    }
    if args.surface:
        surface = o3d.io.read_point_cloud(str(args.surface))
        to_surface = np.asarray(merged.compute_point_cloud_distance(surface))
        from_surface = np.asarray(surface.compute_point_cloud_distance(merged))
        result["cloud_to_surface"] = {"median_m": round(float(np.median(to_surface)), 4),
                                      "share_within_5cm": round(float(np.mean(to_surface < NEAR_M)), 3)}
        result["surface_to_cloud_share_within_5cm"] = round(float(np.mean(from_surface < NEAR_M)), 3)
    (args.run / "compare.json").write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
