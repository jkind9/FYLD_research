"""Supplied-depth/supplied-pose control; no tracking inference or surface score."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from experiments.shared.geometry import (
    backproject,
    depth_metres,
    project,
    transform_points,
)

from .icl import Frame


@dataclass(frozen=True)
class Stages:
    depth: NDArray
    mask: NDArray
    pixels: NDArray
    camera: NDArray
    world: NDArray
    model: NDArray
    projection_error: NDArray


class GeometryBackend(Protocol):
    """Array boundary for local/hosted implementations; materialize before export."""

    def __call__(self, frame: Frame) -> Stages: ...


def compute(frame: Frame) -> Stages:
    depth, mask = depth_metres(frame.raw_depth, 5000)
    camera, pixels = backproject(depth, mask, frame.observation.calibration)
    world = transform_points(camera, frame.observation.pose.matrix)
    first_camera = transform_points(world, np.linalg.inv(frame.world_from_first))
    model = transform_points(first_camera, frame.model_from_first, basis=True)
    error = project(camera, frame.observation.calibration) - pixels[:, ::-1]
    for array in (depth, mask, pixels, camera, world, model, error):
        array.setflags(write=False)
    return Stages(depth, mask, pixels, camera, world, model, error)
