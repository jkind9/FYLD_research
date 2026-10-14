"""Run a live SLAM system in WSL on a recording, one frame at a time, and score the poses it reported.

    python -m experiments.live_slam.run_live --system stella --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2 \
        --run-root experiments/live_slam/runs/stella_tum_xyz

Needs the systems built by native/setup_wsl.sh and the runners built as in README.md. Uses `.venv-sfm`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from experiments.sfm.src import scoring, sequences
from experiments.shared.runs import Run, write_json

from .src import trajectory

REPO = Path(__file__).resolve().parents[2]
HOME = "/home/jkind/live_slam"
SYSTEMS = {
    "stella": {"runner": f"{HOME}/runners/stella/build/run_stella", "vocabulary": f"{HOME}/vocab/orb_vocab.fbow",
               "template": f"{HOME}/src/stella_vslam/example/tum_rgbd/TUM_RGBD_mono_1.yaml",
               "key": r"^(\s*)({name}):.*$", "libraries": f"{HOME}/install/lib", "final": ("final_tum.txt", 1.0)},
    "orbslam3": {"runner": f"{HOME}/runners/orbslam3/build/run_orbslam3", "vocabulary": f"{HOME}/src/ORB_SLAM3/Vocabulary/ORBvoc.txt",
                 "template": f"{HOME}/src/ORB_SLAM3/Examples/Monocular/TUM1.yaml",
                 "key": r"^()(Camera1\.{name}):.*$", "libraries": f"{HOME}/src/ORB_SLAM3/lib:{HOME}/install/lib",
                 "final": ("final_euroc.txt", 1e-9)},
}
HYPERPARAMETERS = {
    "mode": {"value": "monocular, images only", "source": "owner live ruling 2026-10-14"},
    "camera": {"value": "recording's pinhole from experiments/sfm/src/sequences.py, distortion zero", "source": "inherited Task67"},
    "features_and_vocabulary": {"value": "each system's TUM monocular example settings and published ORB vocabulary", "source": "system defaults"},
    "pose_reported": {"value": "live: pose returned for that frame; final: system's saved trajectory after the run", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "frame_pacing": {"value": "as fast as processed, no real-time waits", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "time_match_tolerance_s": {"value": 0.001, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "devices": {"value": "CPU only, WSL2", "source": "owner 2026-10-14 (no GPU)"},
}


def config_text(template: str, key: str, params: tuple[float, ...]) -> str:
    """The system's own example settings with this recording's pinhole camera and no distortion."""
    values = dict(zip(("fx", "fy", "cx", "cy"), params[:4])) | {k: 0.0 for k in ("k1", "k2", "p1", "p2", "k3")}
    for name, value in values.items():
        template = re.sub(key.format(name=name), lambda m, v=value: f"{m.group(1)}{m.group(2)}: {v}", template, flags=re.MULTILINE)
    return template


def wsl(command: str) -> subprocess.CompletedProcess:
    return subprocess.run(["wsl", "-d", "Ubuntu", "--", "bash", "-c", command], capture_output=True, text=True, check=False)  # the caller reads the return code


def timing(path: Path) -> dict:
    ms = np.loadtxt(path, ndmin=1)
    return {"median_ms": float(np.median(ms)), "p95_ms": float(np.percentile(ms, 95)), "max_ms": float(ms.max()),
            "frames_per_second": float(1000 / ms.mean())}


def run(args: argparse.Namespace) -> Path:
    system = SYSTEMS[args.system]
    sequence = sequences.load(args.recording, every=args.every)
    configuration = {"experiment": "live slam", "system": args.system, "recording": args.recording, "every": args.every,
                     "hyperparameters": HYPERPARAMETERS}
    with Run(args.run_root, REPO, configuration) as active:
        inputs, outputs = active.path / "input", active.path / "output"
        write_json(inputs / "sequence.json", sequence.manifest())
        (inputs / "frames.txt").write_text(trajectory.frame_list(list(sequence.timestamps_s),
                                                                 [sequence.image_root / n for n in sequence.image_names]))
        template = wsl(f"cat {system['template']}").stdout
        (inputs / "camera.yaml").write_text(config_text(template, system["key"], sequence.camera_params), encoding="utf-8")
        with active.measure("slam", frames=len(sequence.image_names)):
            result = wsl(f"export LD_LIBRARY_PATH={system['libraries']}:$LD_LIBRARY_PATH; {system['runner']} {system['vocabulary']} "
                         f"{trajectory.to_wsl(inputs / 'camera.yaml')} {trajectory.to_wsl(inputs / 'frames.txt')} {trajectory.to_wsl(outputs)}")
        (active.path / "debug").mkdir(exist_ok=True)
        (active.path / "debug/runner.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"{args.system} runner failed ({result.returncode}); see debug/runner.log")
        ids, times = list(sequence.frame_ids), list(sequence.timestamps_s)
        live = trajectory.rows(ids, times, trajectory.read_poses(outputs / "live.txt"))
        name, time_scale = system["final"]
        final = trajectory.rows(ids, times, trajectory.read_trajectory(outputs / name, time_scale=time_scale))
        active.set_processed_frames(len(ids))
        write_json(outputs / "scores.json", {"live": scoring.score(sequence, live), "final": scoring.score(sequence, final),
                                             "timing": timing(outputs / "frame_ms.txt")})
    return active.path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--system", choices=sorted(SYSTEMS), required=True)
    parser.add_argument("--recording", required=True)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--run-root", type=Path, required=True)
    path = run(parser.parse_args(argv))
    scores = json.loads((path / "output/scores.json").read_text(encoding="utf-8"))
    for kind in ("live", "final"):
        best = scores[kind].get("largest_model", {})
        print(kind, f"placed {scores[kind].get('placed_fraction_largest_model', 0):.2%}",
              f"best fit with size {1000 * best.get('ate_scaled_rmse_m', float('nan')):.1f} mm")
    print("timing", scores["timing"], "\n", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
