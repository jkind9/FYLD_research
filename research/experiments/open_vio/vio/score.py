"""Score a visual-inertial trajectory against a reference with experiment 03's evaluation.

A visual-inertial system reports metric poses, so the rigid error (best rotation and shift, no scale) is the
main score; the scaled error and the 1 s relative error come from the same evaluation.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")
tracking = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")
contracts = importlib.import_module("experiments.shared.contracts")

FIELDS = ("ate_rigid_rmse_m", "ate_scaled_rmse_m", "ate_scaled_size", "rpe_1s_translation_rmse_m", "rpe_1s_rotation_rmse_rad")


def to_camera(poses: list[tuple[float, np.ndarray]], T_cam_imu: np.ndarray) -> list[tuple[float, np.ndarray]]:
    """IMU-to-world poses as camera-to-world poses, for references that follow the camera (ARCore)."""
    imu_from_camera = np.linalg.inv(T_cam_imu)
    return [(t, m @ imu_from_camera) for t, m in poses]


def score(estimate: list[tuple[float, np.ndarray]], reference: list[tuple[float, np.ndarray]], *, tolerance_s: float) -> dict:
    records = [tracking.Record(f"{t:.6f}", t, "tracked", contracts.Pose(m, "vio", "vio", "estimated"), "") for t, m in estimate]
    result = evaluation.evaluate(records, reference, tolerance_s)
    times = np.array([t for t, _ in reference])
    matched = sum(1 for t, _ in estimate if len(times) and np.min(np.abs(times - t)) <= tolerance_s)
    return {k: result[k] for k in FIELDS} | {"estimates": len(estimate), "matched": matched}
