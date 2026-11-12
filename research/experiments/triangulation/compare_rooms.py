"""Compare a room built from triangulated depth with one built from ARCore depth, on the same walk.

    .venv/Scripts/python.exe -B -m research.experiments.triangulation.compare_rooms <room A> <room B> --label <label>

Each room folder is a run of `apps.cli room` (surface.ply, frames.npz, summary.json, run.json). The report
is printed and saved as comparison.json in outputs/<room A's recording>/compare/<yyyymmdd-hhmm>_<label>/. Neither
room is ground truth. The script reports how far each surface lies from the other, split by how
far a point is from the nearest camera, since ARCore depth reaches about 2.5 m.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree

from sitescan import runs

NEAR_M = 2.5


def load(folder: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Cleaned surface points, camera centres and the summary of one room run."""
    points = np.asarray(o3d.io.read_point_cloud(str(folder / "surface.ply")).points)
    cameras = np.load(folder / "frames.npz")["poses"][:, :3, 3]
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    return points, cameras, summary


def distances(points: np.ndarray, cameras: np.ndarray, other: np.ndarray) -> dict:
    """Median and 90th-percentile distance to the other surface, overall and by camera range."""
    gap, _ = cKDTree(other).query(points)
    reach, _ = cKDTree(cameras).query(points)
    out = {}
    for name, keep in (("all", np.ones(len(points), bool)), (f"under_{NEAR_M}_m", reach < NEAR_M),
                       (f"from_{NEAR_M}_m", reach >= NEAR_M)):
        if keep.any():
            out[name] = {"points": int(keep.sum()), "p50_m": round(float(np.median(gap[keep])), 4),
                         "p90_m": round(float(np.percentile(gap[keep], 90)), 4)}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--label", required=True, help="one to four lowercase words joined by hyphens")
    parser.add_argument("--root", type=Path, default=runs.OUTPUTS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    first, first_cameras, first_summary = load(args.first)
    second, second_cameras, second_summary = load(args.second)
    report = {}
    for name, summary in ((args.first.name, first_summary), (args.second.name, second_summary)):
        report[name] = {"frames": summary["frames"], "pose_source": summary["pose_source"],
                        "scale": summary["scale"], "scale_min_median_max": summary["scale_min_median_max"],
                        "surface_points": summary["surface_points"],
                        "map_m": [summary["map"]["length_m"], summary["map"]["width_m"]],
                        "plane_normal": summary["map"]["plane_normal"]}
    report[f"{args.first.name} to {args.second.name}"] = distances(first, first_cameras, second)
    report[f"{args.second.name} to {args.first.name}"] = distances(second, second_cameras, first)
    recording = json.loads((args.first / "run.json").read_text(encoding="utf-8"))["recording"]
    out = runs.new_run(recording, "compare", args.label, {}, root=args.root, inputs=(args.first, args.second))
    (out / "comparison.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    runs.finish_run(out)
    print(json.dumps(report, indent=1))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
