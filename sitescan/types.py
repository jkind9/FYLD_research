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
class MeasuredDepth:
    """Camera-plane depth in metres, confidence from 0 to 255, and where the depth came from.

    `source` is "arcore" for the phone's raw depth or "sweep" for depth triangulated between
    keyframes. Either has its own camera, which may be smaller than the colour image.
    """

    t_ns: int
    depth_m: np.ndarray
    confidence: np.ndarray
    camera: Camera
    source: str


@dataclass(frozen=True)
class Trajectory:
    """Camera poses from a tracker: OpenCV world_from_camera in metres, in a world with +y up."""

    source: str
    t_ns: np.ndarray
    world_from_camera: np.ndarray


@dataclass(frozen=True)
class Calibration:
    """One phone's colour camera, lens distortion and camera pose in the motion sensors' frame."""

    camera: Camera
    distortion: tuple[float, ...]
    imu_from_camera: np.ndarray


@dataclass(frozen=True)
class Frame:
    """RGB image and OpenCV camera poses in the recording's world, in metres."""

    seq: int
    t_ns: int
    image: np.ndarray
    camera: Camera | None
    pose: np.ndarray | None
    depth: MeasuredDepth | None
    point_ids: np.ndarray
    points_world: np.ndarray
    points_pixel: np.ndarray
    points_confidence: np.ndarray
    anchor_created: tuple[int, np.ndarray] | None
    anchor_updates: dict[int, np.ndarray]
    tracking: str
    failure: str
    arcore_t_ns: int | None
    pose_source: str
