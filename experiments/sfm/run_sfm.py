"""Standalone structure from motion on a recorded sequence: camera path, sparse points, scores.

One run = one recording and one feature type; the matches feed both the incremental and the
global mapper. Example (repository root, `.venv-sfm`):

    python -m experiments.sfm.run_sfm --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2 \
        --features sift --run-root experiments/sfm/runs/tum_xyz
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

from experiments.shared.runs import Run, write_json

from .src import export, reconstruct, scoring, sequences

REPO = Path(__file__).resolve().parents[2]
DEFAULT_COLMAP = REPO / "third_party/colmap-4.2.1-windows-nocuda/bin/colmap.exe"

HYPERPARAMETERS = {
    "colmap": {"value": "4.2.1 official Windows build without CUDA (zip SHA-256 c493d88cb4a43f21afba42cb55bf786e5434a0420e73db0ba1454c5d8b3686ae)",
               "source": "proposed by Claude 2026-10-13, not owner-ruled (pycolmap 4.2.1 wheel aborts on ALIKED)"},
    "tum_camera": {"value": ["PINHOLE", list(sequences.TUM_DEFAULT_PINHOLE)],
                   "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:13 (TUM page's recommended default set); "
                             "deviates from the planned fr1 FULL_OPENCV set because that set gave no initial pair on desk (run 2026-10-13), not owner-ruled"},
    "tum_fr1_camera": {"value": ["FULL_OPENCV", list(sequences.TUM_FR1_FULL_OPENCV)],
                       "source": "published TUM fr1 RGB calibration, file formats page checked 2026-10-13 (comparison only: `--calibration fr1`)"},
    "icl_camera": {"value": ["PINHOLE", list(sequences.ICL_PINHOLE)],
                   "source": "inherited data/icl_nuim/conventions.json (fy sign flipped with the y-flip of the reference)"},
    "calibration_refinement": {"value": False, "source": "proposed by Claude 2026-10-13, not owner-ruled"},
    "features": {"value": {"sift": "SIFT, max 8192, SIFT_BRUTEFORCE", "aliked": "ALIKED_N16ROT, max 2048, min score 0.2, ALIKED_LIGHTGLUE min score 0.1"},
                 "source": "COLMAP 4.2.1 defaults"},
    "sequential_pairing": {"value": {"overlap": 10, "quadratic_overlap": True, "loop_detection": False},
                           "source": "COLMAP 4.2.1 defaults"},
    "mappers": {"value": ["incremental", "global"], "source": "COLMAP 4.2.1 defaults except seed 0, multiple models kept"},
    "random_seed": {"value": 0, "source": "proposed by Claude 2026-10-13, not owner-ruled"},
    "frames": {"value": "TUM: every Task65 clip frame; ICL: every 2nd posed frame (1..880)",
               "source": "inherited Task65 clips; ICL spacing proposed by Claude 2026-10-13, not owner-ruled"},
    "depth_model_size": {"value": {"statistic": "median over frames of median(Depth Anything / SfM depth)", "min_points_per_frame": 20},
                         "source": "proposed by Claude 2026-10-13, not owner-ruled"},
    "score_tolerance_s": {"value": 0.02, "source": "inherited experiments/03_camera_pose_estimation/src/evaluation.py:49"},
    "minimum_free_space_gb": {"value": 30, "source": "inherited experiments/02_stereo_depth/scale_drift.py (Task65)"},
    "devices": {"value": "CPU only", "source": "confirmed 2026-10-08 (owner: no GPU without permission)"},
}


def saved_depth(run: Path) -> dict[str, Path]:
    """Frame ID to depth arrays from a finished walkthrough run's depth layer."""
    manifest = json.loads((run / "output/predictions/depth.json").read_text(encoding="utf-8"))
    return {frame["frame_id"]: run / frame["arrays"] for frame in manifest["frames"]}


def run(args: argparse.Namespace) -> Path:
    free_gb = shutil.disk_usage(args.run_root.parent if args.run_root.parent.exists() else REPO).free / 1e9
    if free_gb < HYPERPARAMETERS["minimum_free_space_gb"]["value"]:
        raise SystemExit(f"Only {free_gb:.0f} GB free; refusing to start")
    sequence = sequences.load(args.recording, every=args.every, calibration=args.calibration)
    settings = reconstruct.Settings(args.features)
    configuration = {
        "experiment": "sfm", "recording": args.recording, "every": args.every, "calibration": args.calibration,
        "settings": settings.to_dict(), "colmap": str(args.colmap), "depth_run": str(args.depth_run) if args.depth_run else None,
        "hyperparameters": HYPERPARAMETERS, "cpu_count": os.cpu_count(),
    }
    depth_index = saved_depth(args.depth_run) if args.depth_run else {}
    with Run(args.run_root, REPO, configuration) as active:
        write_json(active.path / "input/sequence.json", sequence.manifest())
        work = active.path / "debug/colmap"
        with active.measure("features_and_matches", frames=len(sequence.image_names)):
            seconds = reconstruct.features_and_matches(args.colmap, sequence, settings, work)
        summary = {"frames": len(sequence.image_names), "seconds": dict(seconds), "mappers": {}}
        for mapper in reconstruct.MAPPERS:
            out = active.path / "output" / mapper
            try:
                with active.measure(f"map_{mapper}", frames=len(sequence.image_names)):
                    seconds[f"map_{mapper}"] = reconstruct.map_models(args.colmap, sequence, settings, work, mapper)
                models = reconstruct.read_models(work, mapper)
            except RuntimeError as error:
                summary["mappers"][mapper] = {"status": "failed", "reason": str(error)}
                continue
            exported = export.write(sequence, models, out)
            rows = json.loads((out / "frames.json").read_text(encoding="utf-8"))["frames"]
            scores = scoring.score(sequence, rows, tolerance_s=HYPERPARAMETERS["score_tolerance_s"]["value"])
            if depth_index and exported.get("largest_model") is not None:
                points = np.load(out / "points.npz")
                observations = dict(np.load(out / "observations.npz"))

                def depth_for_frame(k: int) -> tuple[np.ndarray, np.ndarray] | None:
                    path = depth_index.get(sequence.frame_ids[k])
                    if path is None:
                        return None
                    arrays = np.load(path)
                    return arrays["depth"], arrays["valid"]

                size = scoring.depth_model_size(rows, points["xyz"], observations, depth_for_frame,
                                                min_points=HYPERPARAMETERS["depth_model_size"]["value"]["min_points_per_frame"])
                scores["depth_model_size"] = size
                if size["size"] is not None:
                    scores["depth_model_sized"] = scoring.sized_score(sequence, rows, size["size"], exported["largest_model"])
            write_json(out / "scores.json", scores)
            summary["mappers"][mapper] = {"status": "complete", "export": exported, "scores": scores,
                                          "seconds": seconds[f"map_{mapper}"]}
        summary["seconds"] = seconds
        summary["frames_per_second"] = {m: len(sequence.image_names) / (seconds["extract"] + seconds["match"] + seconds[f"map_{m}"])
                                        for m in reconstruct.MAPPERS if f"map_{m}" in seconds}
        active.set_processed_frames(len(sequence.image_names))
        write_json(active.path / "output/summary.json", summary)
    return active.path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True, help="tum:<folder> or icl:<folder>")
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--calibration", choices=("default", "fr1"), default="default", help="TUM only")
    parser.add_argument("--features", choices=sorted(reconstruct.FEATURES), required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--depth-run", type=Path, help="finished walkthrough run whose depth maps set the size")
    parser.add_argument("--colmap", type=Path, default=DEFAULT_COLMAP)
    args = parser.parse_args(argv)
    if not args.colmap.is_file():
        parser.error(f"COLMAP not found at {args.colmap}")
    print(run(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
