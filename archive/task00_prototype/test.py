"""Runnable real-data demo, separate from pytest. Edit variables inside main()."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("OMP_NUM_THREADS", "8")
sys.path.insert(0, str(ROOT / "src"))
from fyld_scene_mapping.experiments import run_experiment, synthetic_demo
from fyld_scene_mapping.reconstruction import ReconstructionSettings

# hyperparams n/a: editable variables stay inside main as requested; run_manifest
# records their effective values and baseline_parameters() records provenance.


def main() -> None:
    """No hidden downloads: missing data explains the exact acquisition command."""
    dataset_path = ROOT / "data" / "tum"
    sequence = "rgbd_dataset_freiburg1_xyz"
    mode = "oracle_pose_rgbd"  # estimated_pose_rgbd or synthetic
    frame_limit = 120
    stride = 1
    timestamp_tolerance_s = 0.02
    min_depth_m, max_depth_m = 0.2, 4.0
    voxel_size_m = 0.015
    grid_resolution_m = 0.02
    pixel_step = 3
    # Explicit reference axes, NOT measured gravity. Change after inspecting a known plane.
    alignment_normal = (0.0, -1.0, 0.0)
    alignment_offset_m = 0.0
    height_slice_m = None  # e.g. (-.7, -.3) in declared map coordinates
    output_path = ROOT / "outputs"
    if mode == "synthetic":
        synthetic_demo(output_path, grid_resolution_m)
        return
    settings = ReconstructionSettings(
        min_depth_m=min_depth_m,
        max_depth_m=max_depth_m,
        pixel_step=pixel_step,
        voxel_size_m=voxel_size_m,
    )
    try:
        run_experiment(
            dataset_path / sequence,
            mode,
            output_path,
            frame_limit,
            stride,
            timestamp_tolerance_s,
            settings,
            grid_resolution_m,
            alignment_normal,
            alignment_offset_m,
            height_slice_m,
        )
    except FileNotFoundError as error:
        print(error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
