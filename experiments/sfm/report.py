"""Markdown tables of finished runs: SfM runs (one row per mapper) or surface runs (`--dense`).

    python -m experiments.sfm.report experiments/sfm/runs/tum_desk/* experiments/sfm/runs/tum_xyz/*
    python -m experiments.sfm.report --dense experiments/sfm/runs/dense_icl/*
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def rows(run: Path) -> list[dict]:
    """One row per mapper of a complete run; failed mappers keep their reason."""
    status = json.loads((run / "metadata/status.json").read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        return []
    configuration = json.loads((run / "metadata/configuration.json").read_text(encoding="utf-8"))
    summary = json.loads((run / "output/summary.json").read_text(encoding="utf-8"))
    out = []
    for mapper, result in summary["mappers"].items():
        row = {"recording": Path(configuration["recording"].partition(":")[2]).name, "calibration": configuration.get("calibration") if configuration["recording"].startswith("tum:") else "icl",
               "features": configuration["settings"]["features"], "mapper": mapper, "status": result["status"],
               "frames": summary["frames"], "run": run.name}
        if result["status"] == "complete":
            scores = result["scores"]
            largest = scores.get("largest_model", {})
            row.update({
                "placed": round(scores["placed_fraction_largest_model"] * summary["frames"]),
                "models": scores["models"],
                "scaled_mm": None if largest.get("ate_scaled_rmse_m") is None else 1000 * largest["ate_scaled_rmse_m"],
                "size": largest.get("ate_scaled_size"),
                "depth_size": (scores.get("depth_model_sized") or {}).get("size"),
                "depth_sized_mm": None if not scores.get("depth_model_sized") else 1000 * scores["depth_model_sized"]["ate_rigid_rmse_m"],
                "fps": summary["frames_per_second"].get(mapper),
                "seconds": summary["seconds"]["extract"] + summary["seconds"]["match"] + summary["seconds"][f"map_{mapper}"],
            })
        out.append(row)
    return out


def table(all_rows: list[dict]) -> str:
    def number(value, pattern):
        return "—" if value is None else pattern.format(value)

    lines = [("| Recording | Camera | Features | Mapper | Placed (largest model) | Models | Best fit with size | Fitted size "
             "| Depth-model size, error | Seconds | Frames per second |"),
             "|---|---|---|---|---:|---:|---:|---:|---|---:|---:|"]
    for row in all_rows:
        if row["status"] != "complete":
            lines.append(f"| {row['recording']} | {row['calibration']} | {row['features']} | {row['mapper']} | failed | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {row['recording']} | {row['calibration']} | {row['features']} | {row['mapper']} | {row['placed']} / {row['frames']} | {row['models']} "
            f"| {number(row['scaled_mm'], '{:.1f} mm')} | {number(row['size'], '{:.3f}')} "
            f"| {number(row['depth_size'], '{:.3f}')}, {number(row['depth_sized_mm'], '{:.0f} mm')} "
            f"| {number(row['seconds'], '{:.0f}')} | {number(row['fps'], '{:.2f}')} |")
    return "\n".join(lines) + "\n"


def dense_row(run: Path) -> dict | None:
    """One surface run: recording, depth source, poses and the surface scores; None if unfinished."""
    status = json.loads((run / "metadata/status.json").read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        return None
    configuration = json.loads((run / "metadata/configuration.json").read_text(encoding="utf-8"))
    scores = json.loads((run / "output/scores.json").read_text(encoding="utf-8"))
    surface = scores["surface"]
    given = configuration["sfm_size"]
    size_label = {"best-fit": "best-fit size", "depth-model": "depth-model size"}.get(given, f"size {given}")
    poses = configuration["poses"] if configuration["poses"] == "true" else f"SfM ({configuration.get('size_note') or size_label})"
    return {"recording": Path(configuration["recording"].partition(":")[2]).name, "depth": configuration["depth"],
            "poses": poses, "mean_mm": 1000 * surface["accuracy"]["mean_m"], "rmse_mm": 1000 * surface["accuracy"]["rmse_m"],
            "within": surface["reconstruction_within_threshold_fraction"], "coverage": surface["reference_coverage_fraction"],
            "points": scores["points"], "size": scores["poses"].get("size")}


def dense_table(all_rows: list[dict]) -> str:
    lines = ["| Recording | Depth | Poses | Mean distance to reference | RMSE | Points within 5 cm | Reference covered within 5 cm | Points |",
             "|---|---|---|---:|---:|---:|---:|---:|"]
    for row in all_rows:
        lines.append(f"| {row['recording']} | {row['depth']} | {row['poses']} | {row['mean_mm']:.1f} mm | {row['rmse_mm']:.1f} mm "
                     f"| {100 * row['within']:.1f}% | {100 * row['coverage']:.1f}% | {row['points']} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    dense_mode = "--dense" in arguments
    runs = sorted(Path(a) for a in arguments if a != "--dense" and Path(a).is_dir())
    if dense_mode:
        print(dense_table([row for row in (dense_row(run) for run in runs) if row is not None]))
    else:
        print(table([row for run in runs for row in rows(run)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
