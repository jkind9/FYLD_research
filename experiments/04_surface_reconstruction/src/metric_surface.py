"""Observed world points from method depth and estimated camera-to-world poses."""

from numpy.typing import NDArray

from experiments.shared.contracts import Calibration, Pose
from experiments.shared.geometry import backproject, transform_points


def reconstruct_metric(
    depth: NDArray, valid: NDArray, calibration: Calibration, pose: Pose
) -> NDArray:
    """Return every valid pixel as an Nx3 world point, with depth already in metres."""
    if pose.source != "estimated":
        raise ValueError("Metric reconstruction requires an estimated camera pose")
    camera, _ = backproject(depth, valid, calibration)
    return transform_points(camera, pose.matrix)
