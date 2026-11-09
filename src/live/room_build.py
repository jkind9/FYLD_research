"""Task113: an offline room cloud from the frames that carry ARCore raw depth.

Each frame's image is turned upright for the depth model (Task109), and the predicted depth is fitted to ARCore's
confident raw depth on an 8 x 6 grid of sizes instead of one size per frame. On the 15 October walk, held-out
ARCore pixels scored median AbsRel 0.044 with the grid against 0.065 with one size. Frames are fused with the
live fragments, so ARCore's anchor corrections still apply.

The fused room is then cleaned in two stages (owner, 8 November 2026): the visibility vote drops points that views
see through more than they measure, and only the room's largest pieces of touching grid cells are kept.
surface.ply is the cleaned room; raw_surface.ply is the room before clean-up.

    python -B -m src.live.room_build --session <v2 session> --out <folder> [--far 4.0] [--piece-cell 0.02]
"""

from __future__ import annotations

import argparse
import io
import json
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import open3d as o3d
from PIL import Image

from . import clean, orientation_control, sizing
from .fragments import Fragments
from .processor import LiveProcessor
from .stream import read_session, session_v1

CELLS = (8, 6)  # columns, rows; chosen by held-out AbsRel over 1, 2-parameter, 4 x 3 and 8 x 6 fits
MIN_CELL_PIXELS = 20
TIMELINE_STEP = 12  # pixel stride for the saved per-frame points: about 2,000 per frame
# One ARCore depth period on the Redmi. On the 15 October walk 138 of 147 depth maps were 7-40 ms older than their
# image; frames 669-691 carried 4.4 s old maps that placed a cushion 0.7 m off its fresh-depth position (Task116).
MAX_DEPTH_AGE_S = 0.1


def cell_index(uv: np.ndarray, image_size, cells: tuple[int, int] = CELLS) -> np.ndarray:
    """Grid cell of each pixel (u, v), numbered row by row."""
    (w, h), (nx, ny) = image_size, cells
    cols, rows = np.clip(uv[:, 0].astype(int), 0, w - 1), np.clip(uv[:, 1].astype(int), 0, h - 1)
    return np.minimum(rows * ny // h, ny - 1) * nx + np.minimum(cols * nx // w, nx - 1)


def supported_pixels(uv: np.ndarray, shape, cells: tuple[int, int] = CELLS) -> np.ndarray:
    """Pixels whose grid cell holds at least MIN_CELL_PIXELS ARCore depth pixels, so their size is not the fallback."""
    (h, w), (nx, ny) = shape, cells
    counts = np.bincount(cell_index(uv, (w, h), cells), minlength=nx * ny).reshape(ny, nx)
    rows, cols = np.minimum(np.arange(h) * ny // h, ny - 1), np.minimum(np.arange(w) * nx // w, nx - 1)
    return counts[rows[:, None], cols[None, :]] >= MIN_CELL_PIXELS


def upright_depth(model, colour: np.ndarray, world_from_camera: np.ndarray):
    """Learned depth and validity on the recorded grid, predicted from the image turned upright (Task109)."""
    turns = orientation_control.quarter_turns(world_from_camera)
    depth, valid = model(np.ascontiguousarray(orientation_control.upright(colour, turns)))
    return orientation_control.recorded(depth, turns), orientation_control.recorded(valid, turns), turns


def grid_size(model: np.ndarray, valid: np.ndarray, uv: np.ndarray, target: np.ndarray,
              cells: tuple[int, int] = CELLS, fallback: float | None = None) -> np.ndarray | None:
    """Per-pixel size: median target / model in each cell, blended.

    A cell with too few targets takes `fallback` (a log size), or the frame median when none is given.
    """
    h, w = model.shape
    cols, rows = np.clip(uv[:, 0].astype(int), 0, w - 1), np.clip(uv[:, 1].astype(int), 0, h - 1)
    keep = valid[rows, cols] & (model[rows, cols] > 0)
    if keep.sum() < sizing.MIN_DEPTH_PIXELS:
        return None
    cols, rows = cols[keep], rows[keep]
    log_ratio = np.log(target[keep] / model[rows, cols])
    nx, ny = cells
    grid = np.full((ny, nx), np.median(log_ratio) if fallback is None else fallback)
    cell = cell_index(uv[keep], (w, h), cells)
    for index in np.unique(cell):
        mine = cell == index
        if mine.sum() >= MIN_CELL_PIXELS:
            grid.flat[index] = np.median(log_ratio[mine])
    return np.exp(cv2.resize(grid, (w, h), interpolation=cv2.INTER_LINEAR))


def fresh_depth(frame) -> bool:
    return frame.camera_t_ns - frame.depth.t_ns <= MAX_DEPTH_AGE_S * 1e9


def _world(uv: np.ndarray, z: np.ndarray, intrinsics, world_from_camera: np.ndarray) -> np.ndarray:
    fx, fy, cx, cy = intrinsics
    camera = np.c_[(uv[:, 0] - cx) / fx * z, (uv[:, 1] - cy) / fy * z, z]
    return camera @ world_from_camera[:3, :3].T + world_from_camera[:3, 3]


def _save_timeline(path: Path, frames: list) -> None:
    """Each fused frame's camera, sampled learned-depth points (with photo colours) and ARCore depth points.

    Points use the frame's pose when fused, before later anchor corrections, so they show where that frame put them.
    """
    seq, poses, intrinsics, sizes, points, colours, arcore = zip(*frames)
    np.savez_compressed(path, seq=np.array(seq), poses=np.array(poses), intrinsics=np.array(intrinsics),
                        sizes=np.array(sizes), points=np.concatenate(points), colours=np.concatenate(colours),
                        point_offsets=np.cumsum([0, *map(len, points)]), arcore=np.concatenate(arcore),
                        arcore_offsets=np.cumsum([0, *map(len, arcore)]))


def vote_views(fragments, placed: list) -> list:
    """(camera_from_world, intrinsics, see-through evidence) per fused frame.

    placed holds (world_from_camera, intrinsics, keyframe, placing anchor when fused, evidence) per frame. Each camera
    moves by its anchor's correction since that frame was fused, as the surface it fused did.
    """
    return [(np.linalg.inv(fragments.placing_anchor(keyframe) @ np.linalg.inv(then) @ world_from_camera), k, evidence)
            for world_from_camera, k, keyframe, then, evidence in placed]


def _write_cloud(path: Path, points: np.ndarray, colours: np.ndarray) -> None:
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    cloud.colors = o3d.utility.Vector3dVector(colours)
    o3d.io.write_point_cloud(str(path), cloud)


def room_parser(description: str) -> argparse.ArgumentParser:
    """The options every room build shares; callers add their own."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--far", type=float, default=4.0, help="furthest fused depth in metres (inherited 4.0)")
    parser.add_argument("--voxel", type=float, default=0.02)
    parser.add_argument("--threads", type=int, default=16)
    return parser


def parse_room_args(parser: argparse.ArgumentParser, argv: list[str] | None) -> argparse.Namespace:
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"{args.out} already exists; runs are never overwritten")
    return args


def depth_model(threads: int):
    """Depth Anything V2 Metric Small on the CPU (run.depth_anything pins the device)."""
    import torch

    from .run import DEPTH_CHECKPOINT, depth_anything
    torch.set_num_threads(threads)
    return depth_anything(DEPTH_CHECKPOINT)


def fusable_frames(session: Path, model, outcome: Counter):
    """Anchor events and the frames a room build fuses, in session order.

    Yields ("anchor", anchor id, world_from_anchor) and ("frame", record), where the record holds the frame, its
    keyframe, OpenCV pose, photo, upright-predicted depth and validity, quarter turns, ARCore targets and grid size.
    Skipped frames are counted in `outcome`.
    """
    keyframe = None
    for frame in read_session(session):
        if frame.anchor_created is not None:
            keyframe = frame.anchor_created[0]
            yield "anchor", keyframe, session_v1.world_from_camera(frame.anchor_created[1])
        for anchor_id, pose in frame.anchor_updates.items():
            yield "anchor", anchor_id, session_v1.world_from_camera(pose)
        if frame.depth is None or frame.pose is None or keyframe is None:
            continue
        if not fresh_depth(frame):
            outcome["stale_depth"] += 1
            continue
        world_from_camera = session_v1.world_from_camera_cv(frame.pose)
        colour = np.asarray(Image.open(io.BytesIO(frame.image_jpeg)).convert("RGB"))
        depth, valid, turns = upright_depth(model, colour, world_from_camera)
        uv, target = sizing.depth_targets(frame.depth, frame.intrinsics, frame.image_size)
        size = grid_size(depth, valid, uv, target)
        if size is None:
            outcome["too_few_depth_pixels"] += 1
            continue
        yield "frame", SimpleNamespace(frame=frame, keyframe=keyframe, world_from_camera=world_from_camera,
                                       colour=colour, depth=depth, valid=valid, turns=turns, uv=uv, target=target,
                                       size=size)


def main(argv: list[str] | None = None) -> int:
    parser = room_parser(__doc__.splitlines()[0])
    parser.add_argument("--supported-only", action="store_true",
                        help="fuse only pixels whose grid cell has its own ARCore size (Task117 experiment)")
    parser.add_argument("--piece-cell", type=float,
                        help="grid cell in metres for joining surface into pieces, like splat width (default --voxel)")
    args = parse_room_args(parser, argv)
    fragments, cameras, outcome, sizes, timeline, placed = Fragments(voxel_m=args.voxel), [], Counter(), [], [], []
    for kind, *item in fusable_frames(args.session, depth_model(args.threads), outcome):
        if kind == "anchor":
            fragments.set_anchor(*item)
            continue
        record = item[0]
        frame, world_from_camera, colour, size, uv = (record.frame, record.world_from_camera, record.colour,
                                                       record.size, record.uv)
        valid = record.valid & supported_pixels(uv, size.shape) if args.supported_only else record.valid
        sized = record.depth * size
        depth = np.where(valid & (sized < args.far), sized, 0.0)
        fragments.integrate(depth, colour, frame.intrinsics, world_from_camera, record.keyframe)
        placed.append((world_from_camera, frame.intrinsics, record.keyframe,
                       fragments.placing_anchor(record.keyframe).copy(),
                       np.where(record.valid & (sized < clean.VOTE_FAR_M), sized, 0.0).astype(np.float32)))
        cameras.append(world_from_camera[:3, 3])
        sizes.append(float(np.median(size)))
        outcome["fused"] += 1
        outcome[f"turns_{record.turns}"] += 1
        rows, cols = np.nonzero(depth[::TIMELINE_STEP, ::TIMELINE_STEP] > 0)
        rows, cols = rows * TIMELINE_STEP, cols * TIMELINE_STEP
        timeline.append((frame.seq, world_from_camera, frame.intrinsics, frame.image_size,
                         _world(np.c_[cols, rows], depth[rows, cols], frame.intrinsics, world_from_camera),
                         colour[rows, cols], _world(uv[::2], record.target[::2], frame.intrinsics, world_from_camera)))

    raw, raw_colours = fragments.surface(), fragments.colours()
    started = time.perf_counter()
    voted = clean.visibility_vote(raw, vote_views(fragments, placed))
    vote_s, started = time.perf_counter() - started, time.perf_counter()
    cell = args.piece_cell or args.voxel
    keep = np.flatnonzero(voted)[clean.largest_pieces(raw[voted], cell)]
    clean_up = {"raw_points": len(raw), "vote_removed": int((~voted).sum()),
                "pieces_removed": int(voted.sum()) - len(keep), "piece_cell_m": cell,
                "pieces_kept_at_most": clean.ROOM_PIECES, "piece_min_points": clean.ROOM_PIECE_MIN_POINTS,
                "vote_s": round(vote_s, 2), "pieces_s": round(time.perf_counter() - started, 2)}
    surface = raw[keep]
    args.out.mkdir(parents=True)
    _save_timeline(args.out / "frames.npz", timeline)
    _write_cloud(args.out / "raw_surface.ply", raw, raw_colours)
    _write_cloud(args.out / "surface.ply", surface, raw_colours[keep])
    summary = {"session": str(args.session), "far_m": args.far, "voxel_m": args.voxel, "cells": CELLS,
               "supported_only": args.supported_only, "clean_up": clean_up,
               "frames": dict(outcome), "size_median_min_median_max": [min(sizes), float(np.median(sizes)), max(sizes)],
               "surface_points": len(surface),
               "map": LiveProcessor._map(SimpleNamespace(_cameras=cameras), surface)}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
