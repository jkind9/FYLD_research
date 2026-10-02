"""Optional Experiment C. Use .venv-colmap/Scripts/python.exe; no hidden download."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OMP_NUM_THREADS", "8")
sys.path.insert(0, str(ROOT / "src"))
from fyld_scene_mapping.image_only import HYPERPARAMETERS, run_image_only


def main() -> None:
    dataset_path = ROOT / "data" / "tum" / "rgbd_dataset_freiburg1_xyz"
    frame_limit = 120
    stride = 1
    timestamp_tolerance_s = 0.02
    output_path = ROOT / "outputs" / "colmap_image_only"
    run_image_only(dataset_path, output_path, frame_limit, stride, timestamp_tolerance_s)


if __name__ == "__main__":
    main()
