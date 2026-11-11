"""Offline room: every frame with fresh ARCore depth is fused, then the whole room is cleaned once.

Each frame's image is turned upright for the depth model, and the learned depth is scaled to ARCore's
confident raw depth on an 8 x 6 grid. Frames fuse into fragments that follow ARCore's anchor corrections.
The fused room is cleaned by the visibility vote and by keeping its largest pieces.
"""

import io
import time
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from sitescan import cleanup, depth, mapping, scale, session
from sitescan.cleanup.pieces import ROOM_PIECE_MIN_POINTS, ROOM_PIECES
from sitescan.cleanup.vote import VOTE_FAR_M
from sitescan.depth.orientation import quarter_turns
from sitescan.fusion import Fragments
from sitescan.io import write_cloud, write_json, write_timeline
from sitescan.scale.fit import CELLS
from sitescan.session.wire_v1 import world_from_camera, world_from_camera_cv

TIMELINE_STEP = 12  # pixel stride for the saved per-frame points


@dataclass(frozen=True)
class RoomSettings:
    """Far limit and voxel for fusion, the piece-grid cell, and the supported-cells trial switch."""

    far_m: float = 4.0
    voxel_m: float = 0.02
    piece_cell_m: float | None = None
    supported_only: bool = False


@dataclass
class FusableFrame:
    """One frame ready to fuse: its pose, photo, upright-predicted depth and grid scale."""

    frame: object
    keyframe: int
    world_from_camera: np.ndarray
    colour: np.ndarray
    depth: np.ndarray
    valid: np.ndarray
    turns: int
    uv: np.ndarray
    target: np.ndarray
    scale: np.ndarray


@dataclass
class Room:
    """The fused room before and after clean-up, the per-frame timeline and the summary."""

    raw: np.ndarray
    raw_colours: np.ndarray
    cleaned: cleanup.Cleaned
    timeline: list[tuple]
    summary: dict

    @property
    def surface(self) -> np.ndarray:
        """The cleaned surface points."""
        return self.raw[self.cleaned.kept]


def fresh_depth(frame) -> bool:
    """Whether the frame's ARCore depth was measured close enough in time to its image."""
    return scale.fresh_depth(frame.depth.t_ns, frame.camera_t_ns)


def world_points(uv: np.ndarray, z: np.ndarray, intrinsics, world_from_camera: np.ndarray) -> np.ndarray:
    """World positions of pixels at the given camera-plane depths."""
    fx, fy, cx, cy = intrinsics
    camera = np.c_[(uv[:, 0] - cx) / fx * z, (uv[:, 1] - cy) / fy * z, z]
    return camera @ world_from_camera[:3, :3].T + world_from_camera[:3, 3]


def fusable_frames(folder: Path, model: Callable, outcome: Counter) -> Iterator[tuple]:
    """Anchor events and the frames a room build fuses, in recording order.

    Yields ("anchor", anchor id, world_from_anchor) and ("frame", FusableFrame). Skipped frames are
    counted in `outcome`.
    """
    keyframe = None
    for frame in session.read_wire_session(folder):
        if frame.anchor_created is not None:
            keyframe = frame.anchor_created[0]
            yield "anchor", keyframe, world_from_camera(frame.anchor_created[1])
        for anchor_id, pose in frame.anchor_updates.items():
            yield "anchor", anchor_id, world_from_camera(pose)
        if frame.depth is None or frame.pose is None or keyframe is None:
            continue
        if not fresh_depth(frame):
            outcome["stale_depth"] += 1
            continue
        pose = world_from_camera_cv(frame.pose)
        colour = np.asarray(Image.open(io.BytesIO(frame.image_jpeg)).convert("RGB"))
        learned, valid = depth.predict(model, colour, pose)
        uv, target = scale.depth_targets(session.arcore_depth(frame.depth), session.camera(frame))
        fitted = scale.fit_grid(learned, valid, uv, target)
        if fitted is None:
            outcome["too_few_depth_pixels"] += 1
            continue
        yield "frame", FusableFrame(frame, keyframe, pose, colour, learned, valid, quarter_turns(pose), uv, target, fitted)


def vote_views(fragments: Fragments, placed: list) -> list:
    """(camera_from_world, intrinsics, see-through evidence) per fused frame.

    `placed` holds (world_from_camera, intrinsics, keyframe, placing anchor when fused, evidence) per frame.
    Each camera moves by its anchor's correction since that frame was fused, as the surface it fused did.
    """
    return [(np.linalg.inv(fragments.placing_anchor(keyframe) @ np.linalg.inv(then) @ pose), k, evidence)
            for pose, k, keyframe, then, evidence in placed]


def timeline_entry(item: FusableFrame, fused: np.ndarray) -> tuple:
    """A frame's camera, a sample of its fused points with colours, and a sample of its ARCore points."""
    frame, pose = item.frame, item.world_from_camera
    rows, cols = np.nonzero(fused[::TIMELINE_STEP, ::TIMELINE_STEP] > 0)
    rows, cols = rows * TIMELINE_STEP, cols * TIMELINE_STEP
    return (frame.seq, pose, frame.intrinsics, frame.image_size,
            world_points(np.c_[cols, rows], fused[rows, cols], frame.intrinsics, pose),
            item.colour[rows, cols], world_points(item.uv[::2], item.target[::2], frame.intrinsics, pose))


def build_room(folder: Path, model: Callable, settings: RoomSettings = RoomSettings()) -> Room:
    """Fuse every frame with fresh ARCore depth, then clean the room and measure it."""
    fragments = Fragments(voxel_m=settings.voxel_m)
    cameras, scales, timeline, placed, outcome = [], [], [], [], Counter()
    for kind, *event in fusable_frames(folder, model, outcome):
        if kind == "anchor":
            fragments.set_anchor(*event)
            continue
        item = event[0]
        frame = item.frame
        valid = item.valid & scale.supported_pixels(item.uv, item.scale.shape) if settings.supported_only else item.valid
        metric = item.depth * item.scale
        fused = np.where(valid & (metric < settings.far_m), metric, 0.0)
        fragments.integrate(fused, item.colour, frame.intrinsics, item.world_from_camera, item.keyframe)
        evidence = np.where(item.valid & (metric < VOTE_FAR_M), metric, 0.0).astype(np.float32)
        placed.append((item.world_from_camera, frame.intrinsics, item.keyframe,
                       fragments.placing_anchor(item.keyframe).copy(), evidence))
        cameras.append(item.world_from_camera[:3, 3])
        scales.append(float(np.median(item.scale)))
        outcome["fused"] += 1
        outcome[f"turns_{item.turns}"] += 1
        timeline.append(timeline_entry(item, fused))

    raw, raw_colours = fragments.surface(), fragments.colours()
    cell = settings.piece_cell_m or settings.voxel_m
    started = time.perf_counter()
    cleaned = cleanup.clean_room(raw, vote_views(fragments, placed), cell=cell)
    surface = raw[cleaned.kept]
    summary = {
        "session": str(folder), "far_m": settings.far_m, "voxel_m": settings.voxel_m, "cells": CELLS,
        "supported_only": settings.supported_only,
        "clean_up": {"raw_points": len(raw), "vote_removed": int((~cleaned.voted).sum()),
                     "pieces_removed": int(cleaned.voted.sum() - cleaned.kept.sum()), "piece_cell_m": cell,
                     "pieces_kept_at_most": ROOM_PIECES, "piece_min_points": ROOM_PIECE_MIN_POINTS,
                     "clean_s": round(time.perf_counter() - started, 2)},
        "frames": dict(outcome), "scale_min_median_max": [min(scales), float(np.median(scales)), max(scales)],
        "surface_points": len(surface), "map": mapping.measure_site(surface, cameras),
    }
    return Room(raw, raw_colours, cleaned, timeline, summary)


def save_room(room: Room, out: Path) -> None:
    """surface.ply (cleaned), raw_surface.ply, frames.npz (per-frame timeline) and summary.json."""
    out.mkdir(parents=True)
    write_timeline(out / "frames.npz", room.timeline)
    write_cloud(out / "raw_surface.ply", room.raw, room.raw_colours)
    write_cloud(out / "surface.ply", room.surface, room.raw_colours[room.cleaned.kept])
    write_json(out / "summary.json", room.summary)
