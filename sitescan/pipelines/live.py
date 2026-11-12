"""Live processing: surface, top-down map and object counts, updated in a loop as frames arrive.

`add()` is called for every received frame and only records it. `update()` does the work on the newest
posed frame, preferring one with new ARCore depth, and returns one record. The caller runs `update()` as
often as it can; each call must finish in under a second to meet the floor of one update per second.
"""

import json
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from sitescan import mapping, scale, session
from sitescan.fusion import Fragments
from sitescan.fusion.fragments import DEPTH_RANGE_M
from sitescan.io import write_cloud, write_json
from sitescan.objects import Objects
from sitescan.objects.match import AMBIGUITY_MARGIN_M, MAX_DISTANCE_M
from sitescan.session.wire_v1 import world_from_camera, world_from_camera_cv
from sitescan.triangulate import SparseDepth, Triangulator
from sitescan.types import MeasuredDepth

from . import targets

MAP_SETTINGS = {"cell_size_m": 0.05, "inlier_distance_m": 0.02, "iterations": 500, "sample_size": 50_000, "seed": 0}
MIN_MAP_POINTS = 1000
LIVE_SOURCES = ("arcore_depth", "tracked_points")


@dataclass(frozen=True)
class LiveSettings:
    """Fusion voxel and fragment size, object matching distances, and scale sources in order."""

    voxel_m: float = 0.02
    keyframes_per_fragment: int = 10
    max_distance_m: float = MAX_DISTANCE_M
    ambiguity_margin_m: float = AMBIGUITY_MARGIN_M
    scale_sources: tuple[str, ...] = LIVE_SOURCES


def frame_scale(
    learned: np.ndarray,
    valid: np.ndarray,
    frame,
    previous: float | None,
    sources: tuple[str, ...] = LIVE_SOURCES,
    sparse: SparseDepth | None = None,
    dense: MeasuredDepth | None = None,
) -> tuple[float | None, str]:
    """(scale, source) for one frame: the first named source that fits, else the previous scale."""
    pose = None if frame.pose is None else world_from_camera_cv(frame.pose)
    for source in sources:
        found = targets.scale_targets(source, frame, pose, sparse, dense)
        if found is None:
            continue
        uv, metres, weight = found
        fitted = scale.fit_one(learned, valid, uv, metres, targets.MINIMUM[source], weight)
        if fitted is not None:
            return fitted, source
    return (previous, "previous") if previous is not None else (None, "none")


class LiveProcessor:
    """Surface, map and counts updated from the newest frame, once per update."""

    def __init__(self, depth_model: Callable, detector: Callable | None = None, settings: LiveSettings = LiveSettings()):
        """depth_model(rgb) -> (depth_m, valid); detector(rgb) -> list of Detection, or None for no objects."""
        self.depth_model, self.detector = depth_model, detector
        self.scale_sources = settings.scale_sources
        triangulated = set(settings.scale_sources) & set(targets.TRIANGULATED)
        self.triangulator = Triangulator() if triangulated else None
        self.fragments = Fragments(voxel_m=settings.voxel_m, keyframes_per_fragment=settings.keyframes_per_fragment)
        self.objects = Objects(max_distance_m=settings.max_distance_m, ambiguity_margin_m=settings.ambiguity_margin_m)
        self._lock = threading.Lock()
        self._anchors: dict[int, np.ndarray] = {}
        self._keyframe: int | None = None
        self._pending = None
        self._corrections = 0
        self._cameras: list[np.ndarray] = []
        self._worker = ThreadPoolExecutor(max_workers=1)
        self.frames_received = 0
        self.scale: float | None = None
        self.updates = 0

    def add(self, frame, image_path: Path) -> None:
        """Record a received wire frame and the path of its saved colour image."""
        with self._lock:
            self.frames_received += 1
            if frame.anchor_created is not None:
                anchor_id, pose = frame.anchor_created
                self._anchors[anchor_id] = world_from_camera(pose)
                self._keyframe = anchor_id
            for anchor_id, pose in frame.anchor_updates.items():
                if anchor_id in self._anchors:
                    self._anchors[anchor_id] = world_from_camera(pose)
                    self._corrections += 1
            if frame.pose is None or self._keyframe is None:
                return
            if frame.depth is not None or self._pending is None or self._pending[0].depth is None:
                self._pending = (frame, Path(image_path), self._keyframe, time.perf_counter())

    def update(self) -> dict | None:
        """Process the newest pending frame; None when nothing new has arrived."""
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
        learned, valid = self.depth_model(colour)
        lap("depth_model")
        sparse, dense = None, None
        if self.triangulator is not None:
            sparse, dense = self._triangulate(frame, learned, valid)
            lap("triangulate")
        fitted, source = frame_scale(
            learned, valid, frame, self.scale, self.scale_sources, sparse, dense
        )
        lap("scale")
        self.updates += 1
        record = {"update": self.updates, "frame_seq": frame.seq, "frame_t_ns": frame.t_ns, "frames_received": received,
                  "scale": fitted, "scale_source": source, "corrections": corrections}
        if fitted is None:
            return record | {"skipped": "no scale source yet", "stage_ms": ms}
        self.scale = fitted
        metric = learned * fitted
        valid = valid & np.isfinite(metric) & (metric >= DEPTH_RANGE_M[0]) & (metric < DEPTH_RANGE_M[1])
        pose = world_from_camera_cv(frame.pose)
        for anchor_id, matrix in anchors.items():
            self.fragments.set_anchor(anchor_id, matrix)
        # Detection runs beside fusion and mapping (both release the interpreter lock in native code).
        objects = None if self.detector is None else self._worker.submit(
            self._objects, colour, metric, valid, frame, pose, keyframe, anchors)
        self.fragments.integrate(np.where(valid, metric, 0.0), colour, frame.intrinsics, pose, keyframe)
        self._cameras.append(pose[:3, 3])
        lap("fusion")
        surface = self.fragments.surface()
        lap("surface")
        record["map"] = mapping.measure_site(surface, self._cameras, min_points=MIN_MAP_POINTS, **MAP_SETTINGS)
        lap("map")
        if objects is not None:
            ms["objects_alongside"], record["detections"] = objects.result()
            lap("objects_wait")
        return record | {"surface_points": len(surface), "fragments": len(self.fragments.frames_per_fragment()),
                         "counts": self.objects.counts(), "stage_ms": ms,
                         "latency_ms": round((time.perf_counter() - arrived) * 1000, 1)}

    def surface(self) -> np.ndarray:
        """The fused surface so far, in world metres."""
        return self.fragments.surface()

    def _triangulate(self, frame, learned, valid) -> tuple[SparseDepth, MeasuredDepth | None]:
        """Sparse depth against the keyframe window, and plane-sweep depth when a source asks."""
        camera = session.camera(frame)
        pose = world_from_camera_cv(frame.pose)
        sparse = self.triangulator.sparse(frame.grey, camera, pose)
        if "dense" not in self.scale_sources:
            return sparse, None
        prior = targets.sweep_prior(learned, valid, sparse)
        return sparse, self.triangulator.dense(frame.grey, camera, pose, frame.t_ns, prior)

    def _objects(self, colour, metric, valid, frame, pose, keyframe, anchors) -> tuple[float, list[dict]]:
        """Detect, place and count on the worker thread; returns its milliseconds and one row per detection."""
        started = time.perf_counter()
        detections = self.detector(colour)
        log = self.objects.update(detections, np.where(valid, metric, 0.0), valid, session.camera(frame), pose,
                                  keyframe, anchors, self.updates)
        return round((time.perf_counter() - started) * 1000, 1), log


def wall_ms(record: dict) -> float:
    """An update's own time: the detection that runs alongside is already inside objects_wait."""
    return sum(ms for stage, ms in record["stage_ms"].items() if stage != "objects_alongside")


def summarise(records: list[dict], finished: list[float], processor: LiveProcessor) -> dict:
    """Update rate, gaps, stage times and scale sources over a run."""
    gaps = np.diff(finished)
    stages = sorted({name for r in records for name in r["stage_ms"]})
    return {
        "frames_received": processor.frames_received, "updates": len(records),
        "seconds": float(finished[-1] - finished[0]) if len(finished) > 1 else 0.0,
        "updates_per_second": float(len(gaps) / gaps.sum()) if len(gaps) else 0.0,
        "longest_gap_s": float(gaps.max()) if len(gaps) else None,
        "gaps_over_1s": int((gaps > 1.0).sum()),
        "update_ms_median": float(np.median([wall_ms(r) for r in records])) if records else None,
        "stage_ms_median": {s: float(np.median([r["stage_ms"][s] for r in records if s in r["stage_ms"]])) for s in stages},
        "latency_ms_median": float(np.median([r["latency_ms"] for r in records if "latency_ms" in r])) if records else None,
        "scale_sources": {s: sum(r["scale_source"] == s for r in records) for s in {r["scale_source"] for r in records}},
        "corrections": sum(r["corrections"] for r in records),
        "surface_points": len(processor.surface()), "final": records[-1] if records else None,
    }


def run_live(processor: LiveProcessor, feed: Callable[[], None], out: Path, about: dict) -> dict:
    """Feed frames on a thread and update as often as possible until the feed ends.

    `feed()` passes every frame to `processor.add` and returns when the stream ends. Writes
    updates.jsonl (one line per update), surface.ply and summary.json, which starts with `about`.
    """
    done = threading.Event()

    def stream():
        try:
            feed()
        finally:
            done.set()

    threading.Thread(target=stream, daemon=True).start()
    finished, records = [], []
    with open(out / "updates.jsonl", "w", encoding="utf-8") as log:
        while True:
            stream_ended = done.is_set()  # read before update(), so a last frame is never left behind
            record = processor.update()
            if record is None:
                if stream_ended:
                    break
                time.sleep(0.005)
                continue
            finished.append(time.perf_counter())
            records.append(record)
            log.write(json.dumps(record) + "\n")
            log.flush()
            print(f"update {record['update']}: frame {record['frame_seq']}, {record.get('surface_points', 0)} points, "
                  f"counts {record.get('counts', {})}, {wall_ms(record):.0f} ms", flush=True)
    surface = processor.surface()
    if len(surface):
        write_cloud(out / "surface.ply", surface)
    summary = about | summarise(records, finished, processor)
    write_json(out / "summary.json", summary, indent=2)
    return summary
