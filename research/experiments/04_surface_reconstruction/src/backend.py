"""Dataset-independent accumulation boundary; reference geometry never enters it."""

from research.experiments.geometry_validation.src.control import Stages, compute
from research.experiments.geometry_validation.src.icl import Frame
from research.experiments.shared.contracts import Pose, require_same_origin

from .validation.controls import fault_points

__all__ = ["fault_points", "reconstruct"]


def reconstruct(frame: Frame, origin: Pose) -> Stages:
    """Retain every valid observation as one immutable surface contribution."""
    require_same_origin(origin, frame.observation.pose)
    return compute(frame)
