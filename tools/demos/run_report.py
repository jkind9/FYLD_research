"""Read one finished walkthrough run and prepare the data for its interactive report pages.

Everything comes from the run's saved files (inputs, predictions, scores, timing). The only
extra read is the recording's own sensor depth, used to draw reference and error images on
the depth page; the per-frame numbers are the scorer's, from scores.json.

    python -B -m tools.demos.run_report <run-folder> [--output <folder>]

The pages are written to <run-folder>-report/ by default, so the sealed run is never changed.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from PIL import Image

from experiments.shared.contracts import Calibration
from src.walkthrough import consistency
from src.walkthrough.steps.contracts import read_pose

from .pack import colormap, encode_array, encode_positions, image_data_url

# Frame lags at which the surface page compares surfaces (proposed by Claude 2026-10-08).
GAP_LAGS = (1, 5, 10, 20, 29)
# Display-only caps and colour ranges; each page states them.
MAX_FRAMES = 60
MAX_POINTS = 150_000
DEPTH_RANGE_M = (0.0, 4.0)
ERROR_RANGE_M = (0.0, 0.5)
THUMBNAIL = (320, 240)
# Camera frames are x-right, y-down, z-forward, and the walkthrough world is the first camera.
WORLD_UP = [0.0, -1.0, 0.0]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sample_indices(count: int, limit: int = MAX_FRAMES) -> list[int]:
    """At most `limit` evenly spaced indices, always including the first and last."""
    if count <= limit:
        return list(range(count))
    return sorted({round(float(i)) for i in np.linspace(0, count - 1, limit)})


def load_run(run_path: Path) -> dict[str, Any]:
    """The saved records every page reads; a missing optional file becomes None."""
    def optional(relative: str) -> Any:
        path = run_path / relative
        return read_json(path) if path.is_file() else None

    return {
        "path": run_path,
        "result": read_json(run_path / "output/result.json"),
        "scores": optional("output/scores.json") or {},
        "timing": optional("metadata/timing.json") or {},
        "configuration": optional("metadata/configuration.json") or {},
        "capture": optional("output/predictions/capture.json"),
        "depth": optional("output/predictions/depth.json"),
        "tracking": optional("output/predictions/tracking.json"),
        "surface": optional("output/predictions/surface.json"),
        "mapping": optional("output/predictions/mapping.json"),
        "objects": optional("output/predictions/objects.json"),
    }


def overview_data(run: dict[str, Any]) -> dict[str, Any]:
    """Layer rows, controls, throughput and headline scores."""
    stages = run["timing"].get("stages", {})
    rows = []
    for step in run["result"]["steps"]:
        stage = stages.get(f"prediction_{step['name']}", {})
        rows.append({**step, "fps": stage.get("fps"), "seconds": stage.get("elapsed_seconds")})
    processing_s = sum(
        stages.get(f"prediction_{step['name']}", {}).get("elapsed_seconds") or 0.0
        for step in run["result"]["steps"]
    )
    frames = run["timing"].get("processed_frames")
    scores = run["scores"]
    headline = {}
    if scores.get("tracking", {}).get("status") == "scored":
        headline["tracking_rmse_m"] = scores["tracking"]["result"]["position_rmse_m"]
        headline["tracking_steps"] = (
            scores["tracking"]["result"]["tracked_edges"],
            scores["tracking"]["result"]["possible_transitions"],
        )
    if scores.get("depth", {}).get("status") == "scored":
        headline["depth_abs_rel"] = scores["depth"]["result"]["overall"]["abs_rel"]
    return {
        "rows": rows,
        "controls": run["result"].get("controls") or {},
        "complete": run["result"]["complete"],
        "frames": frames,
        "end_to_end_fps": run["timing"].get("end_to_end_fps"),
        "processing_fps": frames / processing_s if frames and processing_s else None,
        "headline": headline,
        "score_status": {name: entry.get("status") for name, entry in scores.items()},
    }


def depth_data(run: dict[str, Any]) -> dict[str, Any] | None:
    """Per-frame images (colour, prediction, reference, error) and the scorer's series."""
    if run["depth"] is None or run["capture"] is None:
        return None
    scored = run["scores"].get("depth", {})
    per_frame = {row["frame_id"]: row for row in scored.get("result", {}).get("per_frame", [])}
    read_reference = _reference_reader(run)
    capture = {row["frame_id"]: row for row in run["capture"]["frames"]}
    frames = []
    for index in sample_indices(len(run["depth"]["frames"])):
        saved = run["depth"]["frames"][index]
        row = capture[saved["frame_id"]]
        with np.load(run["path"] / saved["arrays"], allow_pickle=False) as arrays:
            predicted = np.where(arrays["valid"], arrays["depth"], np.nan)
        entry = {
            "id": saved["frame_id"],
            "rgb": _thumbnail(run["path"] / row["image"]),
            "predicted": _colour(predicted, DEPTH_RANGE_M),
            "score": per_frame.get(saved["frame_id"]),
        }
        if read_reference is not None:
            stand_in = SimpleNamespace(frame_id=saved["frame_id"], timestamp_s=row["timestamp_s"])
            (reference,) = list(read_reference(iter([stand_in]), run=None))
            truth = np.where(reference.valid, reference.depth, np.nan)
            entry["reference"] = _colour(truth, DEPTH_RANGE_M)
            entry["error"] = _colour(np.abs(predicted - truth), ERROR_RANGE_M, "magma")
        frames.append(entry)
    series = [per_frame[f["frame_id"]] for f in run["depth"]["frames"] if f["frame_id"] in per_frame]
    return {
        "method": run["depth"]["methods"]["depth"],
        "control": run["depth"].get("control"),
        "frames": frames,
        "frameCount": len(run["depth"]["frames"]),
        "absRel": [row["abs_rel"] for row in series],
        "rmse": [row["rmse_m"] for row in series],
        # Median predicted/sensor distance per frame (1.34 = 34% too far), and the error a
        # perfect per-frame scale and shift would leave. Absent in runs scored before Task65.
        "scaleRatio": [row.get("scale_ratio") for row in series],
        "fittedAbsRel": [row.get("fitted_abs_rel") for row in series],
        "coverage": [row["valid_coverage"] for row in series],
        "overall": scored.get("result", {}).get("overall"),
        "bands": scored.get("result", {}).get("distance_bands"),
        "scoreStatus": scored.get("status"),
        "scoreReason": scored.get("reason"),
    }


def camera_data(run: dict[str, Any]) -> dict[str, Any] | None:
    """Scored estimated and reference positions per segment, and the error series."""
    if run["tracking"] is None:
        return None
    scored = run["scores"].get("tracking", {})
    if scored.get("status") != "scored":
        positions = [np.asarray(r["pose"]["T_world_camera"])[:3, 3].tolist() for r in run["tracking"]["records"]]
        return {"scored": False, "reason": scored.get("reason"), "segments": [{"estimated": positions, "reference": []}],
                "up": WORLD_UP, "method": run["tracking"]["methods"]["tracking"]}
    result = scored["result"]
    segments: dict[str, dict[str, list]] = {}
    for error in result["errors"]:
        segment = segments.setdefault(error["segment_id"], {"estimated": [], "reference": []})
        segment["estimated"].append(error["estimated_position"])
        segment["reference"].append(error["reference_position"])
    return {
        "scored": True,
        "up": WORLD_UP,
        "segments": list(segments.values()),
        "errorsMm": [1000 * e["position_error_m"] for e in result["errors"]],
        "frameIds": [e["frame_id"] for e in result["errors"]],
        "rmseMm": 1000 * result["position_rmse_m"],
        "stepRmseMm": 1000 * result["relative_translation_rmse_m"],
        "tracked": [result["tracked_edges"], result["possible_transitions"]],
        "alignment": result["alignment"],
        "method": run["tracking"]["methods"]["tracking"],
    }


def surface_data(run: dict[str, Any]) -> dict[str, Any] | None:
    """Sampled world points coloured from their source pixels, plus camera positions."""
    if run["surface"] is None or run["depth"] is None or run["capture"] is None:
        return None
    shards = run["surface"]["shards"]
    total = sum(shard["point_count"] for shard in shards)
    step = max(1, int(np.ceil(total / MAX_POINTS)))
    depth_by_id = {row["frame_id"]: row for row in run["depth"]["frames"]}
    capture = {row["frame_id"]: row for row in run["capture"]["frames"]}
    points, colours, cameras = [], [], []
    for shard in shards:
        xyz = np.load(run["path"] / shard["points"], allow_pickle=False)
        with np.load(run["path"] / depth_by_id[shard["frame_id"]]["arrays"], allow_pickle=False) as arrays:
            valid = arrays["valid"]
        with Image.open(run["path"] / capture[shard["frame_id"]]["image"]) as image:
            rgb = np.asarray(image.convert("RGB"))[valid]
        points.append(xyz[::step])
        colours.append(rgb[::step])
        if "camera_centre_m" in shard:
            cameras.append(shard["camera_centre_m"])
    xyz = np.concatenate(points)
    return {
        "up": WORLD_UP,
        "points": encode_positions(xyz),
        "rgb": encode_array(np.concatenate(colours).astype(np.uint8), "u8"),
        "cameras": cameras,
        "shown": len(xyz),
        "total": int(total),
        "method": run["surface"]["methods"]["surface"],
        **surface_gap_data(run),
    }


def surface_gap_data(run: dict[str, Any]) -> dict[str, Any]:
    """How far each frame's surface sits from an earlier frame's, using the run's own poses.

    A consistent depth source puts the same wall in the same place from every frame; a
    source whose scale changes per frame shows the wall several times along the view.
    """
    if run["tracking"] is None or run["depth"] is None:
        return {"gapByLag": [], "gapLag1": [], "gapLag10": [], "gapSignedLag10": []}
    frames = run["depth"]["frames"]
    poses = [read_pose(record["pose"]) for record in run["tracking"]["records"]]
    cameras = [Calibration(**frame["calibration"]) for frame in frames]

    def load(index: int) -> tuple[np.ndarray, np.ndarray]:
        with np.load(run["path"] / frames[index]["arrays"], allow_pickle=False) as arrays:
            return arrays["depth"], arrays["valid"]

    series = consistency.gap_by_lag(load, poses, cameras, GAP_LAGS)
    table = [
        {
            "lag": lag,
            "medianAbsM": consistency.median_gap(series[lag]),
            "medianSignedM": consistency.median_gap(series[lag], "median_signed_m"),
            "pairs": sum(1 for entry in series[lag] if entry is not None and entry["median_abs_m"] is not None),
        }
        for lag in GAP_LAGS
    ]

    def field(lag: int, name: str) -> list[float | None]:
        return [None if entry is None else entry[name] for entry in series[lag]]

    return {
        "gapByLag": table,
        "gapLag1": field(1, "median_abs_m"),
        "gapLag10": field(10, "median_abs_m"),
        "gapSignedLag10": field(10, "median_signed_m"),
    }


def json_safe(value: Any) -> Any:
    """Page data a browser can parse: NaN and infinity become null, numpy scalars plain numbers."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def map_data(run: dict[str, Any]) -> dict[str, Any] | None:
    if run["mapping"] is None:
        return None
    images = []
    for record in run["mapping"].get("maps", []):
        picture = run["path"] / f"output/visualizations/mapping/origin_{record['origin']:06d}.png"
        images.append({**record, "image": _png(picture) if picture.is_file() else None})
    return {"measurements": run["mapping"]["measurements"], "maps": images,
            "method": run["mapping"]["methods"]["mapping"], "control": run["mapping"].get("control")}


def objects_data(run: dict[str, Any]) -> dict[str, Any] | None:
    if run["objects"] is None:
        return None
    overlays = sorted((run["path"] / "output/visualizations/objects").glob("frame_*.png"))
    frames = [{"id": path.stem, "image": _thumbnail(path, size=None)} for path in
              [overlays[i] for i in sample_indices(len(overlays))]]
    return {"frames": frames, "frameCount": len(overlays), "origins": run["objects"]["origins"],
            "claim": run["objects"].get("claim"), "methods": run["objects"]["methods"]}


def _reference_reader(run: dict[str, Any]) -> Any:
    """The recording's own sensor depth, when the run's source is a TUM folder with depth.txt."""
    source = run["configuration"].get("source") or {}
    saved_root = source.get("root") if isinstance(source, dict) else None
    if not saved_root:
        return None
    root = Path(saved_root)
    if not root.is_absolute():
        root = Path(run["configuration"].get("repo", ".")) / root
    if not (root / "depth.txt").is_file():
        return None
    depth_step = importlib.import_module("src.walkthrough.steps.depth")
    return depth_step.RecordedSensorDepth(root).load()


def _colour(values: np.ndarray, value_range: tuple[float, float], name: str = "turbo") -> str:
    image = Image.fromarray(colormap(values, *value_range, name)).resize(THUMBNAIL, Image.NEAREST)
    return image_data_url(np.asarray(image))


def _thumbnail(path: Path, size: tuple[int, int] | None = THUMBNAIL) -> str:
    with Image.open(path) as image:
        return image_data_url(np.asarray(image.convert("RGB")), size=size)


def _png(path: Path) -> str:
    with Image.open(path) as image:
        return image_data_url(np.asarray(image.convert("RGB")), fmt="PNG")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build interactive pages for one walkthrough run")
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    run_pages = importlib.import_module("tools.demos.run_pages")
    written = run_pages.write_report(args.run, args.output)
    print(json.dumps({"report": str(written[0].parent), "pages": [p.name for p in written]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
