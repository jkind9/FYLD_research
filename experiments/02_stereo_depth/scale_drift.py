"""Does each frame's depth scale drift, and does that drift break the walkthrough?

Two jobs, both reading only files:

    python -m experiments.02_stereo_depth.scale_drift clip --source data/tum --sequence rgbd_dataset_freiburg1_desk \
        --output outputs/task65_clips/rgbd_dataset_freiburg1_desk_every2
    python -m experiments.02_stereo_depth.scale_drift summarise --run "Depth Anything=<run folder>" ... \
        --output experiments/02_stereo_depth/runs/task65/scale_drift.json
    python -m experiments.02_stereo_depth.scale_drift check-space --path outputs --minimum-gb 30

`clip` makes a full-length clip that the walkthrough tracker can follow (every 2nd frame
that has sensor depth). `summarise` reads finished walkthrough runs and reports, per run,
how far each frame's scale is off, whether scale jumps line up with camera-error jumps, and
how far apart overlapping surfaces from different frames sit (with the run's own camera path
and with the recording's motion-capture path). It reads walkthrough runs, so it imports the
walkthrough's surface-gap measure; the recording's references are used only for scoring.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr  # type: ignore[import-untyped]

from experiments.shared.contracts import Calibration, Pose

from .run import _resolve_sequence_root

pose_dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
pose_evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")
consistency = importlib.import_module("src.walkthrough.consistency")
contracts = importlib.import_module("src.walkthrough.steps.contracts")

HYPERPARAMETERS = {
    "clip_every": {"value": 2, "source": "inherited outputs/task51_real_clips/*/CLIP_SOURCE.txt"},
    "clip_depth_tolerance_s": {"value": 0.02, "source": "inherited experiment 03 dataset.py:79"},
    "clip_max_gap_s": {"value": 0.1, "source": "inherited experiments/03_camera_pose_estimation/src/tracking.py:70"},
    "gap_lags_frames": {"value": [1, 5, 10, 20, 29], "source": "proposed by Claude 2026-10-08, not owner-ruled"},
    "reference_pose_tolerance_s": {"value": 0.02, "source": "inherited experiment 03 dataset.py:79"},
    "minimum_free_space_gb": {"value": 30, "source": "proposed by Claude 2026-10-08, not owner-ruled"},
}
GAP_LAGS = tuple(HYPERPARAMETERS["gap_lags_frames"]["value"])


# ---- Clips ----


def make_clip(
    source: Path,
    output: Path,
    *,
    sequence: str | None = None,
    every: int = HYPERPARAMETERS["clip_every"]["value"],
    tolerance_s: float = HYPERPARAMETERS["clip_depth_tolerance_s"]["value"],
    max_gap_s: float = HYPERPARAMETERS["clip_max_gap_s"]["value"],
) -> dict[str, Any]:
    """Copy every `every`-th RGB frame that has sensor depth within `tolerance_s`, with that depth.

    Refuses (writing nothing) when the kept frames have a gap the tracker would treat as a
    break (more than `max_gap_s`).
    """
    root = _resolve_sequence_root(source, sequence) if sequence else source
    rgb = pose_dataset.read_table(root / "rgb.txt")
    depth = pose_dataset.read_table(root / "depth.txt")
    depth_times = np.array([t for t, _ in depth])
    paired = []
    for timestamp, name in rgb:
        nearest = int(np.argmin(np.abs(depth_times - timestamp)))
        if abs(depth_times[nearest] - timestamp) <= tolerance_s:
            paired.append((timestamp, name, depth[nearest]))
    kept = paired[::every]
    gaps = np.diff([t for t, _, _ in kept])
    largest = float(gaps.max()) if gaps.size else 0.0
    if largest > max_gap_s:
        raise ValueError(f"Kept frames have a {largest:.3f} s gap; the tracker splits at {max_gap_s} s")
    for timestamp, name, (_, depth_name) in kept:
        for relative in (name, depth_name):
            (output / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, output / relative)
    _write_table(output / "rgb.txt", "rgb", [(t, n) for t, n, _ in kept])
    _write_table(output / "depth.txt", "depth", [d for _, _, d in kept])
    shutil.copyfile(root / "groundtruth.txt", output / "groundtruth.txt")
    summary = {
        "source": str(root),
        "frames": len(kept),
        "dropped_without_depth": len(rgb) - len(paired),
        "largest_gap_s": largest,
        "settings": {"every": every, "tolerance_s": tolerance_s, "max_gap_s": max_gap_s},
    }
    (output / "CLIP_SOURCE.txt").write_text(
        f"Copied from {root}: every {every}nd RGB row among the {len(paired)} rows with depth within "
        f"{tolerance_s} s ({len(rgb) - len(paired)} dropped), {len(kept)} frames, largest gap {largest:.3f} s, "
        "nearest depth image each, full groundtruth.txt. Made by experiments/02_stereo_depth/scale_drift.py.\n",
        encoding="utf-8",
    )
    return summary


def _write_table(path: Path, kind: str, rows: list[tuple[float, str]]) -> None:
    lines = [f"# {kind} frames", "# timestamp filename", *(f"{t:.6f} {name}" for t, name in rows)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---- Summaries ----


def summarise_run(run_path: Path, *, lags: tuple[int, ...] = GAP_LAGS) -> dict[str, Any]:
    """Scale, surface-gap, camera, area and speed numbers for one finished walkthrough run."""
    run = {name: _read(run_path / relative) for name, relative in RUN_FILES.items()}
    per_frame = run["scores"].get("depth", {}).get("result", {}).get("per_frame", [])
    tracking = run["scores"].get("tracking", {}).get("result", {})
    ratios = [row.get("scale_ratio") for row in per_frame]
    known = [r for r in ratios if r is not None]
    poses = [contracts.read_pose(r["pose"]) for r in run["tracking"]["records"]] if run["tracking"] else []
    reference = _reference_poses(run, run_path)
    return {
        "run": str(run_path),
        "complete": run["result"].get("complete"),
        "controls": run["result"].get("controls") or {},
        "depth_method": run["depth"]["methods"]["depth"] if run["depth"] else None,
        "depth_abs_rel": run["scores"].get("depth", {}).get("result", {}).get("overall", {}).get("abs_rel"),
        "fitted_abs_rel_median": _median([row.get("fitted_abs_rel") for row in per_frame]),
        "scale_ratio": {
            "min": min(known) if known else None,
            "median": _median(known),
            "max": max(known) if known else None,
            "median_frame_change": _median(np.abs(np.diff(np.log(known))).tolist()) if len(known) > 1 else None,
        },
        "scale_change_vs_camera_error_change": _jump_correlation(per_frame, tracking.get("errors", [])),
        "surface_gap_m": _gaps(run, run_path, poses, lags) if poses else {},
        "reference_pose_gap_m": _gaps(run, run_path, reference[0], lags) if reference else None,
        "reference_pose_missing_frames": reference[1] if reference else None,
        "camera_rmse_m": tracking.get("position_rmse_m"),
        "tracked_steps": [tracking.get("tracked_edges"), tracking.get("possible_transitions")],
        "plane_area_m2": _plane_area(run["mapping"]),
        **_speeds(run["timing"]),
    }


RUN_FILES = {
    "result": "output/result.json",
    "scores": "output/scores.json",
    "capture": "output/predictions/capture.json",
    "depth": "output/predictions/depth.json",
    "tracking": "output/predictions/tracking.json",
    "mapping": "output/predictions/mapping.json",
    "timing": "metadata/timing.json",
    "configuration": "metadata/configuration.json",
}


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _median(values: list[float | None]) -> float | None:
    known = [v for v in values if v is not None]
    return float(np.median(known)) if known else None


def _jump_correlation(per_frame: list[dict[str, Any]], errors: list[dict[str, Any]]) -> float | None:
    """Spearman rank correlation of |frame-to-frame scale change| with |camera-error change|."""
    error_by_frame = {e["frame_id"]: e["position_error_m"] for e in errors}
    pairs = [(row["scale_ratio"], error_by_frame[row["frame_id"]]) for row in per_frame
             if row.get("scale_ratio") is not None and row["frame_id"] in error_by_frame]
    if len(pairs) < 4:
        return None
    scale, error = np.array(pairs).T
    scale_change, error_change = np.abs(np.diff(np.log(scale))), np.abs(np.diff(error))
    if np.ptp(scale_change) == 0 or np.ptp(error_change) == 0:
        return None  # a constant series has no ranking to correlate
    return float(spearmanr(scale_change, error_change).statistic)


def _gaps(run: dict[str, Any], run_path: Path, poses: list[Pose], lags: tuple[int, ...]) -> dict[str, Any]:
    frames = run["depth"]["frames"]
    cameras = [Calibration(**frame["calibration"]) for frame in frames]

    def load(index: int) -> tuple[np.ndarray, np.ndarray]:
        with np.load(run_path / frames[index]["arrays"], allow_pickle=False) as arrays:
            return arrays["depth"], arrays["valid"]

    series = consistency.gap_by_lag(load, poses, cameras, tuple(lag for lag in lags if lag < len(frames)))
    return {
        str(lag): {
            "median_abs_m": consistency.median_gap(entries),
            "median_signed_m": consistency.median_gap(entries, "median_signed_m"),
            "pairs": sum(1 for e in entries if e is not None and e["median_abs_m"] is not None),
        }
        for lag, entries in series.items()
    }


def _reference_poses(run: dict[str, Any], run_path: Path) -> tuple[list[Pose], int] | None:
    """The recording's motion-capture pose for each frame; a frame without one gets its own
    world label, so `gap_by_lag` never pairs it. Returns the poses and the missing count."""
    source = (run["configuration"].get("source") or {}) if run["configuration"] else {}
    root = source.get("root") if isinstance(source, dict) else None
    if not root or not run["capture"]:
        return None
    root = Path(root) if Path(root).is_absolute() else Path(run["configuration"].get("repo", ".")) / root
    if not (root / "groundtruth.txt").is_file():
        return None
    references = pose_evaluation.read_references(root / "groundtruth.txt")
    tolerance = HYPERPARAMETERS["reference_pose_tolerance_s"]["value"]
    rows = [argparse.Namespace(frame_id=f["frame_id"], timestamp_s=f["timestamp_s"]) for f in run["capture"]["frames"]]
    poses, missing = [], 0
    for row, matched in contracts.nearest_references(iter(rows), [t for t, _ in references], tolerance):
        if matched is None:
            missing += 1
            poses.append(Pose(np.eye(4), f"no-reference-{row.frame_id}", "0", "supplied"))
        else:
            poses.append(Pose(references[matched][1], "motion-capture", "0", "supplied"))
    return poses, missing


def _plane_area(mapping: dict[str, Any]) -> float | None:
    areas = [m["value"] for name, m in (mapping.get("measurements") or {}).items()
             if name.endswith("plane area") and isinstance(m, dict) and isinstance(m.get("value"), (int, float))]
    return float(sum(areas)) if areas else None


def _speeds(timing: dict[str, Any]) -> dict[str, float | None]:
    stages = timing.get("stages", {})
    depth = stages.get("prediction_depth", {})
    processing = sum(stage.get("elapsed_seconds") or 0.0 for name, stage in stages.items() if name.startswith("prediction_"))
    frames = timing.get("processed_frames")
    return {
        "depth_layer_fps": depth["frames"] / depth["elapsed_seconds"] if depth.get("elapsed_seconds") else None,
        "processing_fps": frames / processing if frames and processing else None,
        "end_to_end_fps": timing.get("end_to_end_fps"),
    }


def json_safe(value: Any) -> Any:
    """NaN and infinity become null and numpy scalars plain numbers, so JSON stays strict."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def markdown_table(rows: list[dict[str, Any]], headline_lag: str = "20") -> str:
    """One row per run: the numbers the README tables quote."""
    def number(value: Any, pattern: str) -> str:
        return "—" if value is None else pattern.format(value)

    header = (
        "| Run | Control | Depth AbsRel | After per-frame fit | Scale ratio min-max | Camera RMSE (mm) "
        f"| Surface gap, {headline_lag} frames apart (mm) | Same, motion-capture poses (mm) | Plane area (m²) "
        "| Depth layer fps | Processing fps |"
    )
    lines = [header, "|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        own = row["surface_gap_m"].get(headline_lag, {}).get("median_abs_m")
        mocap = (row["reference_pose_gap_m"] or {}).get(headline_lag, {}).get("median_abs_m")
        scale = row["scale_ratio"]
        lines.append(
            f"| {row.get('label', row['run'])} | {', '.join(f'{k}: {v}' for k, v in row['controls'].items()) or 'none'} "
            f"| {number(row['depth_abs_rel'], '{:.3f}')} | {number(row['fitted_abs_rel_median'], '{:.3f}')} "
            f"| {number(scale['min'], '{:.2f}')}-{number(scale['max'], '{:.2f}')} "
            f"| {number(row['camera_rmse_m'] and row['camera_rmse_m'] * 1000, '{:.0f}')} "
            f"| {number(own and own * 1000, '{:.0f}')} | {number(mocap and mocap * 1000, '{:.0f}')} "
            f"| {number(row['plane_area_m2'], '{:.2f}')} | {number(row['depth_layer_fps'], '{:.2f}')} "
            f"| {number(row['processing_fps'], '{:.2f}')} |"
        )
    return "\n".join(lines) + "\n"


def check_free_space(path: Path, minimum_gb: float = HYPERPARAMETERS["minimum_free_space_gb"]["value"]) -> float:
    """Stop (exit) when the disk holding `path` has less than `minimum_gb` free."""
    free_gb = shutil.disk_usage(path).free / 1e9
    if free_gb < minimum_gb:
        raise SystemExit(f"Only {free_gb:.1f} GB free at {path}; at least {minimum_gb} GB needed before a full-length run")
    return free_gb


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    clip = commands.add_parser("clip")
    clip.add_argument("--source", type=Path, required=True)
    clip.add_argument("--sequence")
    clip.add_argument("--output", type=Path, required=True)
    summary = commands.add_parser("summarise")
    summary.add_argument("--run", action="append", required=True, help="LABEL=RUN_FOLDER")
    summary.add_argument("--output", type=Path, required=True)
    space = commands.add_parser("check-space")
    space.add_argument("--path", type=Path, default=Path("."))
    space.add_argument("--minimum-gb", type=float, default=HYPERPARAMETERS["minimum_free_space_gb"]["value"])
    args = parser.parse_args(argv)
    if args.command == "clip":
        if args.output.exists():
            parser.error(f"{args.output} already exists; clips are never overwritten")
        print(json.dumps(make_clip(args.source, args.output, sequence=args.sequence), indent=2))
    elif args.command == "check-space":
        print(f"{check_free_space(args.path, args.minimum_gb):.1f} GB free")
    else:
        rows = []
        for entry in args.run:
            label, _, folder = entry.partition("=")
            rows.append({"label": label, **summarise_run(Path(folder))})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = json_safe({"hyperparameters": HYPERPARAMETERS, "runs": rows})
        args.output.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
        args.output.with_suffix(".md").write_text(markdown_table(rows), encoding="utf-8")
        print(markdown_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
