"""Summarise live SLAM runs: median (and range) over repeats per system and recording.

    python -m experiments.live_slam.report experiments/live_slam/runs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

FIELDS = ("live_mm", "final_mm", "placed", "models", "median_ms", "p95_ms")


def run_row(run: Path) -> dict | None:
    """One finished run's numbers; None if it did not complete."""
    status = json.loads((run / "metadata/status.json").read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        return None
    scores = json.loads((run / "output/scores.json").read_text(encoding="utf-8"))
    live, final = scores["live"], scores["final"]

    def mm(block):
        value = block.get("largest_model", {}).get("ate_scaled_rmse_m")
        return np.nan if value is None else 1000 * value

    return {"live_mm": mm(live), "final_mm": mm(final), "placed": live["placed_fraction_largest_model"],
            "models": live["models"], "median_ms": scores["timing"]["median_ms"], "p95_ms": scores["timing"]["p95_ms"]}


def combine(rows: list[dict]) -> dict:
    """(median, minimum, maximum) of each field over the repeats."""
    out = {"repeats": len(rows)}
    for field in FIELDS:
        values = np.array([r[field] for r in rows], dtype=float)
        out[field] = (float(np.nanmedian(values)), float(np.nanmin(values)), float(np.nanmax(values)))
    return out


def table(root: Path) -> str:
    lines = ["| Setting | Repeats | Frames tracked (largest map) | Maps | Live path error | Final path error | ms per frame, median | ms per frame, 95th pct |",
             "|---|---:|---:|---:|---|---|---:|---:|"]
    for group in sorted(p for p in root.iterdir() if p.is_dir()):
        rows = [r for r in (run_row(run) for run in sorted(group.iterdir()) if (run / "metadata/status.json").is_file()) if r]
        if not rows:
            continue
        c = combine(rows)
        lines.append(f"| {group.name} | {c['repeats']} | {100 * c['placed'][0]:.1f}% | {c['models'][0]:.0f} "
                     f"| {c['live_mm'][0]:.1f} mm ({c['live_mm'][1]:.1f}-{c['live_mm'][2]:.1f}) "
                     f"| {c['final_mm'][0]:.1f} mm ({c['final_mm'][1]:.1f}-{c['final_mm'][2]:.1f}) "
                     f"| {c['median_ms'][0]:.1f} | {c['p95_ms'][0]:.1f} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(table(Path(sys.argv[1])))
