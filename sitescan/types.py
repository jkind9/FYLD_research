"""Arrays and records shared by the processing stages."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Camera:
    """Pinhole intrinsics and image dimensions, in pixels."""

    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int


@dataclass(frozen=True)
class ArcoreDepth:
    """Camera-plane depth in metres and confidence from 0 to 255."""

    t_ns: int
    depth_m: np.ndarray
    confidence: np.ndarray
    camera: Camera


@dataclass(frozen=True)
class Frame:
    """RGB image and OpenCV camera poses in the recording's world, in metres."""

    seq: int
    t_ns: int
    image: np.ndarray
    camera: Camera | None
    pose: np.ndarray | None
    depth: ArcoreDepth | None
    point_ids: np.ndarray
    points_world: np.ndarray
    points_pixel: np.ndarray
    points_confidence: np.ndarray
    anchor_created: tuple[int, np.ndarray] | None
    anchor_updates: dict[int, np.ndarray]
    tracking: str
    failure: str
    arcore_t_ns: int | None
