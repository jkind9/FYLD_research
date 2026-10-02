"""Explicit A/B matrix; identical subset, no automatic acquisition or method updates."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("OMP_NUM_THREADS", "8")
sys.path.insert(0, str(ROOT / "src"))
from fyld_scene_mapping.experiments import run_experiment
from fyld_scene_mapping.reconstruction import ReconstructionSettings

# hyperparams n/a: this entry uses the declared baseline defaults; every effective
# value and its provenance is saved under run_manifest.hyperparameters.


def main() -> None:
    """Run the two required controls sequentially, preserving partial failure evidence."""
    sequence = ROOT / "data" / "tum" / "rgbd_dataset_freiburg1_xyz"
    frame_limit = 120
    stride = 1
    timestamp_tolerance_s = 0.02
    output_path = ROOT / "outputs"
    settings = ReconstructionSettings()
    methods = ["oracle_pose_rgbd", "estimated_pose_rgbd"]
    for method in methods:
        run_experiment(
            sequence,
            method,
            output_path,
            frame_limit,
            stride,
            timestamp_tolerance_s,
            settings,
        )


if __name__ == "__main__":
    main()
