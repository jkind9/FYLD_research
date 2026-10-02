"""Dataset-dependent contract check; absent data is a visible skip, not a benchmark."""

from pathlib import Path

import numpy as np
import pytest

from fyld_scene_mapping.datasets import ground_truth_at, select_frames
from fyld_scene_mapping.geometry import Intrinsics
from fyld_scene_mapping.reconstruction import ReconstructionSettings, read_observation


def test_tum_sample_calibration_depth_and_association() -> None:
    sequence = (
        Path(__file__).resolve().parents[1] / "data/tum/rgbd_dataset_freiburg1_xyz"
    )
    if not (sequence / "rgb.txt").exists():
        pytest.skip(
            "TUM absent: python scripts/download_sample_data.py; no dataset benchmark executed"
        )
    frames, info = select_frames(sequence, 120, 1, 0.02)
    assert len(frames) == 120 and info["max_rgb_depth_offset_s"] <= 0.02
    rgb, depth = read_observation(frames[0], Intrinsics(), ReconstructionSettings())
    assert rgb.shape == (480, 640, 3) and np.isfinite(depth).sum() > 10000
    gt, _ = ground_truth_at(
        sequence / "groundtruth.txt", np.array([f.timestamp for f in frames]), 0.02
    )
    assert all(p is not None for p in gt)
