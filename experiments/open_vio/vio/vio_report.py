"""One table of every run under a folder (each run's scores.json), for the README.

    python experiments/open_vio/vio/vio_report.py experiments/open_vio/runs/vio_tumvi_room1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def row(run: Path) -> str:
    s = json.loads((run / "scores.json").read_text(encoding="utf-8"))
    if "error" in s or s.get("ate_rigid_rmse_m") is None:
        return f"| {run.name} | failed: {s.get('error', 'no score')} (exit {s['exit_code']}) | | | | |"
    return (f"| {run.name} | {s['ate_rigid_rmse_m']:.3f} | {s['ate_scaled_rmse_m']:.3f} | {s['rpe_1s_translation_rmse_m']:.3f} | "
            f"{100 * s['tracked_fraction']:.0f}% | {s['ms_per_frame_whole_run']:.0f} |")


def table(root: Path) -> str:
    lines = ["| Run | Rigid ATE (m) | Scaled ATE (m) | RPE 1 s (m) | Frames placed | ms per frame |", "|---|---|---|---|---|---|"]
    lines += [row(run) for run in sorted(Path(root).iterdir()) if (run / "scores.json").exists()]
    return "\n".join(lines)


if __name__ == "__main__":
    print(table(Path(sys.argv[1])))
