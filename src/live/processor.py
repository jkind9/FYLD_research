"""Live processing of a phone session v1 stream: surface, top-down map and object counts, updated in a loop.

add() is called for every received frame and only records it; update() does the work on the newest posed
frame (preferring one with new ARCore depth) and returns one record. The caller runs update() as often as it
can; each call must finish in under a second to meet the 1 update per second floor.
"""

from __future__ import annotations

import importlib
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import open3d as o3d
from PIL import Image

from experiments.shared.contracts import Calibration, Pose

from . import sizing
from .fragments import DEPTH_RANGE_M, Fragments
from .stream import session_v1

footprint_owner = importlib.import_module("experiments.05_birds_eye_mapping.measure")
localisation = importlib.import_module("experiments.06_object_recognition.pilot.localisation")
association = importlib.import_module("experiments.06_object_recognition.pilot.association")

# Task55's frozen grid-footprint settings (src/walkthrough/steps/mapping.py GridFootprint).
MAP_SETTINGS = {"cell_size_m": 0.05, "inlier_distance_m": 0.02, "iterations": 500, "sample_size": 50_000, "seed": 0}
MIN_MAP_POINTS = 1000


class LiveProcessor:
    def __init__(self, depth_model, detector, *, voxel_m: float, keyframes_per_fragment: int = 10,
                 max_distance_m: float = 0.35, ambiguity_margin_m: float = 0.05):
        """depth_model(rgb) -> (depth_m, valid); detector(image_path) -> (detections, metadata), or None."""
        self.depth_model, self.detector = depth_model, detector
        self.fragments = Fragments(voxel_m=voxel_m, keyframes_per_fragment=keyframes_per_fragment)
        self.max_distance_m, self.ambiguity_margin_m = max_distance_m, ambiguity_margin_m
        self._lock = threading.Lock()
        self._anchors: dict[int, np.ndarray] = {}
        self._keyframe: int | None = None
        self._pending = None
        self._corrections = 0
        self.frames_received = 0
        self.size: float | None = None
        self.updates = 0
        self._cameras: list[np.ndarray] = []
        self._tracks: dict[str, dict] = {}
        self._track_anchor: dict[str, tuple[int, np.ndarray]] = {}  # object -> (keyframe, position in its anchor frame)
        self._next_object = 1
        self._worker = ThreadPoolExecutor(max_workers=1)

    def add(self, frame: session_v1.Frame, image_path: Path) -> None:
        with self._lock:
            self.frames_received += 1
            if frame.anchor_created is not None:
                anchor_id, pose = frame.anchor_created
                self._anchors[anchor_id] = session_v1.world_from_camera(pose)
                self._keyframe = anchor_id
            for anchor_id, pose in frame.anchor_updates.items():
                if anchor_id in self._anchors:
                    self._anchors[anchor_id] = session_v1.world_from_camera(pose)
                    self._corrections += 1
            if frame.pose is None or self._keyframe is None:
                return
            if frame.depth is not None or self._pending is None or self._pending[0].depth is None:
                self._pending = (frame, Path(image_path), self._keyframe, time.perf_counter())

    def update(self) -> dict | None:
        with self._lock:
            if self._pending is None:
                return None
            (frame, image_path, keyframe, arrived), self._pending = self._pending, None
            anchors, corrections, self._corrections = dict(self._anchors), self._corrections, 0
            received = self.frames_received
        ms: dict[str, float] = {}
        clock = time.perf_counter()

        def lap(name: str) -> None:
            nonlocal clock
            now = time.perf_counter()
            ms[name] = round((now - clock) * 1000, 1)
            clock = now

        colour = np.asarray(Image.open(image_path).convert("RGB"))
        lap("decode")
        model, valid = self.depth_model(colour)
        lap("depth_model")
        size, source = sizing.frame_size(model, valid, frame, self.size)
        lap("sizing")
        self.updates += 1
        record = {"update": self.updates, "frame_seq": frame.seq, "frame_t_ns": frame.t_ns, "frames_received": received,
                  "size": size, "size_source": source, "corrections": corrections}
        if size is None:
            return record | {"skipped": "no size source yet", "stage_ms": ms}
        self.size = size
        depth = model * size
        valid = valid & np.isfinite(depth) & (depth >= DEPTH_RANGE_M[0]) & (depth < DEPTH_RANGE_M[1])
        world_from_camera = session_v1.world_from_camera_cv(frame.pose)
        for anchor_id, matrix in anchors.items():
            self.fragments.set_anchor(anchor_id, matrix)
        # Detection runs beside fusion and mapping (both release the interpreter lock in native code).
        objects = None if self.detector is None else self._worker.submit(
            self._objects, image_path, depth, valid, frame, world_from_camera, keyframe, anchors)
        self.fragments.integrate(np.where(valid, depth, 0.0), colour, frame.intrinsics, world_from_camera, keyframe)
        self._cameras.append(world_from_camera[:3, 3])
        lap("fusion")
        surface = self.fragments.surface()
        lap("surface")
        record["map"] = self._map(surface)
        lap("map")
        if objects is not None:
            ms["objects_alongside"], record["detections"] = objects.result()
            lap("objects_wait")
        return record | {"surface_points": len(surface), "fragments": len(self.fragments.frames_per_fragment()),
                         "counts": dict(Counter(t["label"] for t in self._tracks.values())), "stage_ms": ms,
                         "latency_ms": round((time.perf_counter() - arrived) * 1000, 1)}

    def surface(self) -> np.ndarray:
        return self.fragments.surface()

    def _map(self, surface: np.ndarray) -> dict:
        """Task55's footprint on the surface thinned to half a map cell, so its cost stays flat as the surface grows."""
        if len(surface) < MIN_MAP_POINTS:
            return {"skipped": f"fewer than {MIN_MAP_POINTS} surface points"}
        settings = MAP_SETTINGS
        cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(surface))
        surface = np.asarray(cloud.voxel_down_sample(settings["cell_size_m"] / 2).points)
        try:
            plane = footprint_owner.fit_dominant_plane(
                surface, inlier_distance_m=settings["inlier_distance_m"], iterations=settings["iterations"],
                sample_size=settings["sample_size"], seed=settings["seed"])
            measured = footprint_owner.footprint(surface, plane, np.mean(self._cameras, 0) - plane.point,
                                                 cell_size_m=settings["cell_size_m"], band_m=settings["inlier_distance_m"])
        except ValueError as error:
            return {"skipped": str(error)}
        return {"observed_area_m2": measured.observed_area_m2, "plane_area_m2": measured.plane_area_m2,
                "length_m": measured.length_m, "width_m": measured.width_m, "highest_m": measured.highest_m,
                "plane_normal": measured.plane.normal.tolist()}

    def _objects(self, image_path, depth, valid, frame, world_from_camera, keyframe, anchors) -> tuple[float, list[dict]]:
        """Detect, place and count on the worker thread; returns its milliseconds and one log row per detection."""
        started = time.perf_counter()
        detections, _ = self.detector(image_path)
        fx, fy, cx, cy = frame.intrinsics
        h, w = depth.shape
        view = SimpleNamespace(depth=np.where(valid, depth, 0.0), valid=valid,
                               calibration=Calibration(w, h, fx, fy, cx, cy, "x-right_y-down_z-forward"))
        pose = Pose(world_from_camera, "arcore", "session", "estimated")
        proposals = []
        for detection in detections:
            median = localisation.localise_detection(view, detection, pose)["box_median"]
            proposals.append({**asdict(detection), "frame_index": self.updates,
                              "world_position_m": median["world_m"] if median else None})
        # Objects follow ARCore's corrections through the anchor of the keyframe they were last seen from.
        for object_id, (anchor_id, relative) in self._track_anchor.items():
            self._tracks[object_id]["last_position_m"] = (anchors[anchor_id][:3, :3] @ relative + anchors[anchor_id][:3, 3]).tolist()
        nearest = [_nearest_same_class(p, self._tracks) for p in proposals]
        decided, self._tracks, self._next_object = association.associate_frame(
            proposals, self._tracks, self._next_object, self.max_distance_m, self.ambiguity_margin_m)
        inverse = np.linalg.inv(anchors[keyframe])
        for row in decided:
            if row["object_id"] is not None:
                position = np.asarray(row["world_position_m"])
                self._track_anchor[row["object_id"]] = (keyframe, inverse[:3, :3] @ position + inverse[:3, 3])
        log = [{"label": row["label"], "confidence": round(row["confidence"], 3), "outcome": row["association"],
                "object_id": row["object_id"], "nearest_same_class_m": distance} for row, distance in zip(decided, nearest)]
        return round((time.perf_counter() - started) * 1000, 1), log


def _nearest_same_class(proposal: dict, tracks: dict[str, dict]) -> float | None:
    """Distance from a placed detection to the closest object of its class before matching; None if either is missing."""
    if proposal["world_position_m"] is None:
        return None
    distances = [np.linalg.norm(np.subtract(proposal["world_position_m"], t["last_position_m"]))
                 for t in tracks.values() if t["class_id"] == proposal["class_id"]]
    return round(float(min(distances)), 3) if distances else None
