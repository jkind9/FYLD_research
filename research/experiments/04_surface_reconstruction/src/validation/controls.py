"""Deliberate ICL depth/pose faults for independent scoring sensitivity checks."""

import numpy as np
from numpy.typing import NDArray

from experiments.geometry_validation.src.control import compute
from experiments.geometry_validation.src.icl import Frame
from experiments.shared.geometry import transform_points


def fault_points(frame: Frame, fault: str) -> NDArray:
    """Deliberate fault fixtures; neither changes the supplied input record."""
    stages = compute(frame)
    if fault == "double_depth":
        world = transform_points(stages.camera * 2, frame.observation.pose.matrix)
    elif fault == "inverse_pose":
        world = transform_points(
            stages.camera, np.linalg.inv(frame.observation.pose.matrix)
        )
    else:
        raise ValueError("Unknown geometry fault")
    return transform_points(
        world,
        frame.model_from_first @ np.linalg.inv(frame.world_from_first),
        basis=True,
    )
