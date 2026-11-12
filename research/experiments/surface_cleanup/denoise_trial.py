"""Clean-up and far-sizing trials on one walk, scored against held-out ARCore tracked points.

The depth model runs once per frame that the room pipeline would fuse (fresh ARCore depth, upright input, 8 x 6 grid
size, 4.0 m far limit). Each variant is then fused and scored. Tracked points with even ids may size depth; only
odd ids score it, so no variant is scored on points it was fitted to. Tracked points come from ARCore's tracking,
not its depth maps, so they check depth beyond ARCore depth's reach. Sources: research/surface_denoising.

    python -B -m experiments.surface_cleanup.denoise_trial --session <v2 session> --out <folder>
"""

from __future__ import annotations

import json
import time
from collections import Counter
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree

from apps.cli import parse_room_args, room_parser
from experiments.surface_cleanup.filters import (
    CLUSTER_EPS_M,
    keep_after,
    piece_majority,
)
from experiments.surface_cleanup.masks import (
    edge_mask,
    near_first_passes,
    view_angle_mask,
)
from experiments.surface_cleanup.support import (
    MEASURED_M,
    WIDE_ANGLE_DEG,
    views_measuring,
    wide_support,
)
from sitescan.cleanup import visibility_vote
from sitescan.cleanup.vote import VOTE_FAR_M
from sitescan.depth import load_model
from sitescan.fusion import Fragments
from sitescan.pipelines import DEPTH_MODEL
from sitescan.pipelines.room import fusable_frames, world_points
from sitescan.scale import fit_grid, supported_pixels

FLOOR_Y = -0.76  # ARCore depth fused alone puts the 15 October floor here, with a few cm spread (Task113)
BANDS = (0.0, 1.0, 2.5, 4.0)  # metres; ARCore depth rarely reaches past 2.5 m (Task117)
FAR_FROM_M = 2.5
MIN_FALLBACK_POINTS = 5
SIGHT_RADIUS_M = 0.04  # two voxels
SIGHT_STEP_M = 0.04
SIGHT_START_M = 0.3
SIGHT_END_MARGIN = (0.15, 0.05)  # metres, share of distance: neither tracked points nor surfaces are exact
BEHIND_M = 1.0  # door echo layers lie 0.44-0.5 m apart (Task117), so two layers fit
# Views scored on their own: the hallway door 4.5 m from the first standing spot (Task117) and the staircase.
FOCUS = {"door_frame_65": 65, "stairs_frame_420": 420}
FOCUS_HALF_WIDTH = 30  # recorded frames either side, about 1 s
_PLAIN = {"sizing": "grid", "masks": False, "near_first": False, "vote": None, "wide": None, "pieces": False,
          "measured_m": MEASURED_M, "min_views": 0, "post": None, "eps": CLUSTER_EPS_M}
VARIANTS = {name: _PLAIN | changes for name, changes in {
    "baseline": {},
    "masks": {"masks": True},
    "near_first": {"near_first": True},
    "vote": {"vote": "fused"},  # see-through evidence only from fused depth (under 4 m)
    "vote_far": {"vote": "far"},  # see-through evidence from depth out to VOTE_FAR_M
    "sor": {"post": "sor"},
    "radius": {"post": "radius"},
    "clusters": {"post": "clusters"},
    "clusters_3cm": {"post": "clusters", "eps": 0.03},
    "vote_far_clusters_3cm": {"vote": "far", "post": "clusters", "eps": 0.03},
    "seen_3": {"min_views": 3},  # Open3D's default extraction threshold: a voxel seen by at least 3 frames
    "seen_5": {"min_views": 5},
    "vote_far_seen_3_clusters_3cm": {"vote": "far", "min_views": 3, "post": "clusters", "eps": 0.03},
    "tracked_sizing": {"sizing": "tracked"},
    "far_sizing": {"sizing": "far"},
    "far_sizing_vote_far": {"sizing": "far", "vote": "far"},
    "wide": {"wide": WIDE_ANGLE_DEG},  # far surface needs agreeing views from other spots (COLMAP)
    "wide_6deg": {"wide": 6.0},
    "wide_2m": {"wide": WIDE_ANGLE_DEG, "measured_m": 2.0},  # does one-spot depth at 2.0-2.5 m keep echoes?
    "wide_pieces": {"wide": WIDE_ANGLE_DEG, "pieces": True},  # and mostly-unsupported pieces go whole (PCL)
    "vote_far_wide": {"vote": "far", "wide": WIDE_ANGLE_DEG},
    "vote_far_wide_pieces": {"vote": "far", "wide": WIDE_ANGLE_DEG, "pieces": True},
}.items()}


def window_share(blocked: np.ndarray, samples: np.ndarray, seqs: np.ndarray, focus: int, half_width: int) -> float:
    """Blocked share over sight lines from frames within half_width recorded frames of `focus`."""
    mine = np.abs(seqs - focus) <= half_width
    return float(blocked[mine].sum() / max(samples[mine].sum(), 1))


def far_sizes(learned: np.ndarray, near: np.ndarray, far: np.ndarray) -> np.ndarray:
    """`far` sizes where depth sized by `near` reaches FAR_FROM_M, else `near`: tracked points fix far depth only."""
    return np.where(learned * near >= FAR_FROM_M, far, near)


def tracked_fallback(learned: np.ndarray, valid: np.ndarray, arcore_uv: np.ndarray, pixels: np.ndarray,
                     z: np.ndarray) -> float | None:
    """Log size for cells without ARCore depth: median log(tracked / learned) over tracked points in such cells."""
    h, w = learned.shape
    inside = (pixels[:, 0] >= 0) & (pixels[:, 0] < w) & (pixels[:, 1] >= 0) & (pixels[:, 1] < h)
    cols, rows = pixels[inside, 0].astype(int), pixels[inside, 1].astype(int)
    keep = valid[rows, cols] & (learned[rows, cols] > 0) & ~supported_pixels(arcore_uv, learned.shape)[rows, cols]
    if keep.sum() < MIN_FALLBACK_POINTS:
        return None
    return float(np.median(np.log(z[inside][keep] / learned[rows[keep], cols[keep]])))


def sight_line_hits(surface: cKDTree, cameras: np.ndarray, points: np.ndarray,
                    behind: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """(samples with surface within SIGHT_RADIUS_M, samples) along each camera-to-point line, which should be empty.

    With `behind`, the samples run from just past the point to BEHIND_M past it instead: the wall a tracked point lies
    on should have no copy there, though a room beyond an open door can.
    """
    blocked, samples = np.zeros(len(points), int), np.zeros(len(points), int)
    for i, (camera, point) in enumerate(zip(cameras, points)):
        distance = np.linalg.norm(point - camera)
        margin = max(SIGHT_END_MARGIN[0], SIGHT_END_MARGIN[1] * distance)
        steps = (distance + np.arange(margin, BEHIND_M, SIGHT_STEP_M) if behind
                 else np.arange(SIGHT_START_M, distance - margin, SIGHT_STEP_M))
        if len(steps):
            line = camera + np.outer(steps, (point - camera) / distance)
            blocked[i] = np.count_nonzero(surface.query_ball_point(line, SIGHT_RADIUS_M, return_length=True))
            samples[i] = len(steps)
    return blocked, samples


def collect(session: Path, model) -> tuple[list, Counter]:
    """('anchor', id, pose) and ('frame', record) events in session order, for the frames the room pipeline fuses."""
    events, outcome = [], Counter()
    for kind, *item in fusable_frames(session, model, outcome):
        if kind == "anchor":
            events.append((kind, *item))
            continue
        record = item[0]
        frame, world_from_camera, depth, valid, uv, target, grid = (
            record.frame, record.world_from_camera, record.depth, record.valid, record.uv, record.target, record.scale)
        camera = (frame.points_world - world_from_camera[:3, 3]) @ world_from_camera[:3, :3]
        ahead = camera[:, 2] > 0
        ids, pixels, z = frame.point_ids[ahead], frame.points_pixel[ahead], camera[ahead, 2]
        fit = ids % 2 == 0
        fallback = tracked_fallback(depth, valid, uv, pixels[fit], z[fit])
        outcome["tracked_fallback" if fallback is not None else "no_tracked_fallback"] += 1
        tracked = grid if fallback is None else fit_grid(depth, valid, uv, target, fallback=fallback)
        far_fit = fit & (z >= FAR_FROM_M)
        far_fallback = tracked_fallback(depth, valid, uv, pixels[far_fit], z[far_fit])
        far = grid if far_fallback is None else far_sizes(depth, grid, fit_grid(depth, valid, uv, target,
                                                                                  fallback=far_fallback))
        h, w = depth.shape
        inside = ~fit & (pixels[:, 0] >= 0) & (pixels[:, 0] < w) & (pixels[:, 1] >= 0) & (pixels[:, 1] < h)
        cols, rows = pixels[inside, 0].astype(int), pixels[inside, 1].astype(int)
        events.append(("frame", SimpleNamespace(
            seq=frame.seq, keyframe=record.keyframe, world_from_camera=world_from_camera, intrinsics=frame.intrinsics,
            colour=record.colour,
            depth=depth.astype(np.float32), valid=valid,
            sizes={"grid": grid.astype(np.float32), "tracked": tracked.astype(np.float32),
                   "far": far.astype(np.float32)},
            arcore=world_points(uv[::4], target[::4], frame.intrinsics, world_from_camera),
            held_out=SimpleNamespace(ids=ids[~fit], world=frame.points_world[ahead][~fit], z=z[~fit],
                                     rows=rows, cols=cols, inside=inside[~fit],
                                     supported=supported_pixels(uv, depth.shape)[rows, cols]))))
        outcome["frames"] += 1
    return events, outcome


def fuse(events: list, variant: dict, voxel: float, far: float) -> tuple[np.ndarray, np.ndarray, list, dict, list]:
    """Surface, colours, per frame the correction now @ inverse(then) of the anchor placing it, removal counts, and
    per frame (camera_from_world, intrinsics, fused depth, see-through evidence out to VOTE_FAR_M)."""
    fragments, placed, removed = Fragments(voxel_m=voxel), [], Counter()
    for kind, *rest in events:
        if kind == "anchor":
            fragments.set_anchor(*rest)
            continue
        frame = rest[0]
        sized = frame.depth * frame.sizes[variant["sizing"]]
        seen = frame.valid & (sized > 0)
        keep = seen & (sized < far)
        if variant["masks"]:
            edge, angle = edge_mask(sized), view_angle_mask(sized, frame.intrinsics)
            removed["edge_pixels"] += int((keep & edge).sum())
            removed["angle_pixels"] += int((keep & angle & ~edge).sum())
            seen &= ~edge & ~angle
            keep &= ~edge & ~angle
        removed["fused_pixels"] += int(keep.sum())
        depth = np.where(keep, sized, 0.0)
        for part, repeats in near_first_passes(depth) if variant["near_first"] else [(depth, 1)]:
            for _ in range(repeats):
                fragments.integrate(part, frame.colour, frame.intrinsics, frame.world_from_camera, frame.keyframe)
        far_evidence = np.where(seen & (sized < VOTE_FAR_M), sized, 0.0)
        placed.append((frame, fragments.placing_anchor(frame.keyframe).copy(), far_evidence, depth))
    surface, colours = fragments.surface(), fragments.colours()
    corrections = [fragments.placing_anchor(f.keyframe) @ np.linalg.inv(then) for f, then, *_ in placed]
    views = [(np.linalg.inv(c @ f.world_from_camera), f.intrinsics, d, e)
             for c, (f, _, e, d) in zip(corrections, placed)]
    fused = [(cam, k, d) for cam, k, d, _ in views]
    if variant["vote"]:
        evidence = [(cam, k, e if variant["vote"] == "far" else d) for cam, k, d, e in views]
        keep = visibility_vote(surface, evidence)
        removed["vote_points"] = int((~keep).sum())
        surface, colours = surface[keep], colours[keep]
    if variant["wide"]:
        keep = wide_support(surface, fused, variant["measured_m"], variant["wide"])
        if variant["pieces"]:
            cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(surface))
            cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=3 * voxel, max_nn=30))
            keep = piece_majority(surface, np.asarray(cloud.normals), ~keep)
        removed["wide_points"] = int((~keep).sum())
        surface, colours = surface[keep], colours[keep]
    if variant["min_views"]:
        seen = views_measuring(surface, fused)
        keep = seen >= variant["min_views"]
        removed["seen_too_few_times_points"] = int((~keep).sum())
        surface, colours = surface[keep], colours[keep]
    if variant["post"]:
        keep = keep_after(surface, variant["post"], variant["eps"])
        removed["post_points"] = int((~keep).sum())
        surface, colours = surface[keep], colours[keep]
    return surface, colours, corrections, dict(removed), views


def diagnose(frames: list, far: float) -> dict:
    """Where baseline pixels lie: share by distance band, on depth edges, seen side-on, and beyond the far limit."""
    counts = Counter()
    for frame in frames:
        depth = frame.depth * frame.sizes["grid"]
        valid = frame.valid & (depth > 0)
        fused = valid & (depth < far)
        edge, angle = edge_mask(depth), view_angle_mask(depth, frame.intrinsics)
        counts["beyond_far"] += int((valid & ~fused).sum())
        for low, high in pairwise(BANDS):
            band = fused & (depth >= low) & (depth < high)
            counts[f"{low}-{high}"] += int(band.sum())
            counts[f"{low}-{high}_edge"] += int((band & edge).sum())
            counts[f"{low}-{high}_angle"] += int((band & angle).sum())
    total = sum(counts[f"{low}-{high}"] for low, high in pairwise(BANDS))
    out = {"beyond_far_share_of_valid": counts["beyond_far"] / (total + counts["beyond_far"])}
    for low, high in pairwise(BANDS):
        band = max(counts[f"{low}-{high}"], 1)
        out[f"{low}-{high} m"] = {"share_of_fused": band / total, "edge_share": counts[f"{low}-{high}_edge"] / band,
                                  "side_on_share": counts[f"{low}-{high}_angle"] / band}
    return out


def sizing_ratios(frames: list, key: str) -> dict:
    """Fused / tracked depth at held-out tracked points in cells without ARCore depth, near and far."""
    out = {}
    for low, high in pairwise((0.0, FAR_FROM_M, np.inf)):
        ratio = []
        for frame in frames:
            held = frame.held_out
            mine = ~held.supported & (held.z[held.inside] >= low) & (held.z[held.inside] < high)
            fused = (frame.depth * frame.sizes[key])[held.rows, held.cols]
            ratio.append((fused / held.z[held.inside])[mine & frame.valid[held.rows, held.cols]])
        ratio = np.concatenate(ratio)
        out[f"from {low} m"] = {"count": len(ratio), "median": float(np.median(ratio)),
                                "p25": float(np.percentile(ratio, 25)), "p75": float(np.percentile(ratio, 75))}
    return out


def score(surface: np.ndarray, frames: list, corrections: list) -> dict:
    """Empty sight lines, distance to tracked points, ARCore depth coverage and floor figures for one surface."""
    tree = cKDTree(surface)
    move = [lambda p, c=c: p @ c[:3, :3].T + c[:3, 3] for c in corrections]
    cameras = np.concatenate([np.repeat(m(f.world_from_camera[:3, 3][None]), len(f.held_out.z), 0)
                              for f, m in zip(frames, move)])
    points = np.concatenate([m(f.held_out.world) for f, m in zip(frames, move)])
    z = np.concatenate([f.held_out.z for f in frames])
    blocked, samples = sight_line_hits(tree, cameras, points)
    out = {"surface_points": len(surface)}
    for low, high in pairwise((0.0, FAR_FROM_M, np.inf)):
        mine = (z >= low) & (z < high)
        out[f"blocked_sight_line_share_from_{low}_m"] = float(blocked[mine].sum() / max(samples[mine].sum(), 1))
        distance, _ = tree.query(points[mine])
        out[f"tracked_point_to_surface_from_{low}_m"] = {"median_m": float(np.median(distance)),
                                                         "within_10cm": float(np.mean(distance <= 0.10))}
    arcore = np.concatenate([m(f.arcore) for f, m in zip(frames, move)])
    out["arcore_depth_within_5cm"] = float(np.isfinite(tree.query(arcore, distance_upper_bound=0.05)[0]).mean())
    out["below_floor_10cm_points"] = int(np.sum(surface[:, 1] < FLOOR_Y - 0.10))
    out["within_5cm_of_floor_points"] = int(np.sum(np.abs(surface[:, 1] - FLOOR_Y) <= 0.05))
    seqs = np.concatenate([np.full(len(f.held_out.z), f.seq) for f in frames])
    near_surface = tree.query(points)[0] <= 0.10
    behind, behind_samples = sight_line_hits(tree, cameras, points, behind=True)
    out["behind_share_from_2.5_m"] = float(behind[z >= FAR_FROM_M].sum() / max(behind_samples[z >= FAR_FROM_M].sum(), 1))
    for name, focus in FOCUS.items():
        out[f"blocked_share_{name}"] = window_share(blocked, samples, seqs, focus, FOCUS_HALF_WIDTH)
        out[f"behind_share_{name}"] = window_share(behind, behind_samples, seqs, focus, FOCUS_HALF_WIDTH)
        out[f"within_10cm_{name}"] = window_share(near_surface, np.ones(len(points)), seqs, focus, FOCUS_HALF_WIDTH)
    out["floating_points"] = int((~keep_after(surface, "clusters")).sum())
    return out


def main(argv: list[str] | None = None) -> int:
    args = parse_room_args(room_parser(__doc__.splitlines()[0]), argv)
    events, outcome = collect(args.session, load_model(DEPTH_MODEL, threads=args.threads))
    frames = [record for kind, record, *_ in events if kind == "frame"]
    args.out.mkdir(parents=True)
    results = {"session": str(args.session), "far_m": args.far, "voxel_m": args.voxel, "frames": dict(outcome),
               "where_pixels_lie": diagnose(frames, args.far),
               "sizing_at_held_out_points": {key: sizing_ratios(frames, key) for key in ("grid", "tracked", "far")},
               "variants": {}}
    for name, variant in VARIANTS.items():
        start = time.perf_counter()
        surface, colours, corrections, removed, _ = fuse(events, variant, args.voxel, args.far)
        seconds = time.perf_counter() - start
        results["variants"][name] = {"fuse_seconds": round(seconds, 1), "removed": removed,
                                     **score(surface, frames, corrections)}
        print(name, json.dumps(results["variants"][name]))
        cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(surface))
        cloud.colors = o3d.utility.Vector3dVector(colours)
        o3d.io.write_point_cloud(str(args.out / f"{name}.ply"), cloud)
    (args.out / "results.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
