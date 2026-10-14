"""How many metric depth readings does the SfM world need to get its real-world size?

Draws N depth-camera readings at SfM points, sizes the world from them, and scores the camera
path against the true path. Example (`.venv-sfm`):

    python -m experiments.sfm.run_metric_points --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2 \
        --every 1 --sfm-run experiments/sfm/runs/tum_xyz/<run>/output/incremental --run-root experiments/sfm/runs/metric_tum_xyz
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from experiments.shared.runs import Run, write_json

from . import run_dense
from .src import metric_points, scoring, sequences

REPO = Path(__file__).resolve().parents[2]
READING_COUNTS = (5, 20, 100, None)  # None is every reading

HYPERPARAMETERS = {
    "readings_n": {"value": [5, 20, 100, "all"], "source": "owner handover 2026-10-14"},
    "draws_per_setting": {"value": 100, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "seed": {"value": "draw i uses seed i", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "point_filter": {"value": "track length >= 3, reprojection error <= 2 px", "source": "inherited run_dense.py sfm_frame_sizes"},
    "reading_range_m": {"value": [0.1, 4.0], "source": "inherited run_dense.py depth_range_m"},
    "size_statistic": {"value": "median of ratios", "source": "inherited scoring.py depth_model_size"},
    "fusion_draw": {"value": "per-run draw with the median absolute size error", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "reading_noise": {"value": "none; depth camera read as recorded", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "devices": {"value": "CPU only", "source": "owner 2026-10-14 handover"},
}
DRAWS = HYPERPARAMETERS["draws_per_setting"]["value"]
SIZE_RULES = {"run": metric_points.run_size, "frame": metric_points.frame_size}


def percentiles(values: list[float]) -> dict:
    return {"median": float(np.median(values)), "p10": float(np.percentile(values, 10)), "p90": float(np.percentile(values, 90))}


def settings(sequence, rows, data, model_id: int, best_size: float) -> tuple[list[dict], dict]:
    """One result per rule and N over the draws, and the per-run draw to fuse for each N."""
    out, chosen = [], {}
    frames_with_readings = len(np.unique(data["frame"]))
    for rule, size_of in SIZE_RULES.items():
        for n in READING_COUNTS:
            seeds = range(DRAWS if n is not None else 1)
            sizes = [size_of(data, n, seed) for seed in seeds]
            errors_pct = [100 * (s / best_size - 1) for s in sizes]
            path_mm = [1000 * scoring.sized_score(sequence, rows, s, model_id)["ate_rigid_rmse_m"] for s in sizes]
            total = None if n is None else (n if rule == "run" else n * frames_with_readings)
            out.append({"rule": rule, "n": "all" if n is None else n, "readings_in_total_at_most": total, "draws": len(sizes),
                        "size": percentiles(sizes), "size_error_pct": percentiles(errors_pct), "path_rigid_mm": percentiles(path_mm)})
            if rule == "run":
                pick = int(np.argsort(np.abs(errors_pct))[len(errors_pct) // 2])
                chosen["all" if n is None else str(n)] = {"seed": pick, "size": sizes[pick], "size_error_pct": errors_pct[pick]}
    return out, chosen


def run(args: argparse.Namespace) -> Path:
    sequence = sequences.load(args.recording, every=args.every)
    folder = args.sfm_run
    rows = json.loads((folder / "frames.json").read_text(encoding="utf-8"))["frames"]
    _, info = run_dense.sfm_poses(sequence, folder, "best-fit")
    model_id, best_size = info["largest_model"], info["size"]
    largest_only = [r if r["model_id"] == model_id else {**r, "T_world_camera": None} for r in rows]
    points = np.load(folder / "points.npz")
    observations = dict(np.load(folder / "observations.npz"))
    keep = (points["track_length"] >= 3) & (points["error_px"] <= 2.0)
    low, high = HYPERPARAMETERS["reading_range_m"]["value"]
    configuration = {"experiment": "sfm metric points", "recording": args.recording, "every": args.every,
                     "sfm_run": str(folder), "hyperparameters": HYPERPARAMETERS}
    with Run(args.run_root, REPO, configuration) as active:
        write_json(active.path / "input/sequence.json", sequence.manifest())
        with active.measure("readings"):
            data = metric_points.readings(largest_only, points["xyz"], observations, keep,
                                          lambda k: run_dense.sensor_depth(sequence, k), min_depth_m=low, max_depth_m=high)
        with active.measure("draws"):
            results, chosen = settings(sequence, rows, data, model_id, best_size)
        active.set_processed_frames(len(rows))
        reference = scoring.sized_score(sequence, rows, best_size, model_id)
        write_json(active.path / "output/metric_points.json", {
            "best_fit_size": best_size, "best_fit_path_rigid_mm": 1000 * reference["ate_rigid_rmse_m"],
            "readings_available": len(data["ratio"]), "frames_with_readings": len(np.unique(data["frame"])),
            "settings": results})
        write_json(active.path / "output/sizes.json", {"per_run": chosen, "best_fit_size": best_size})
    return active.path


def table(summary: dict) -> str:
    header = (f"Best fit size {summary['best_fit_size']:.4f}, path error {summary['best_fit_path_rigid_mm']:.1f} mm; "
              f"{summary['readings_available']} readings in {summary['frames_with_readings']} frames")
    lines = [header, "| Rule | N | Readings in total | Size error, median (10th-90th) | Path error, median (10th-90th) |",
             "|---|---|---:|---|---|"]
    for r in summary["settings"]:
        e, p = r["size_error_pct"], r["path_rigid_mm"]
        lines.append(f"| {r['rule']} | {r['n']} | {r['readings_in_total_at_most'] or 'all'} | {e['median']:+.1f}% ({e['p10']:+.1f} to {e['p90']:+.1f}) "
                     f"| {p['median']:.1f} mm ({p['p10']:.1f}-{p['p90']:.1f}) |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--sfm-run", type=Path, required=True, help="<sfm run>/output/<mapper>")
    parser.add_argument("--run-root", type=Path, required=True)
    path = run(parser.parse_args(argv))
    print(path)
    print(table(json.loads((path / "output/metric_points.json").read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
