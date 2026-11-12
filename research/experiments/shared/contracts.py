"""Portable schema v1; metres, pixel calibration and explicit coordinate origins."""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Calibration:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    axes: str

    def __post_init__(self) -> None:
        if (
            self.width < 1
            or self.height < 1
            or not isinstance(self.width, int)
            or not isinstance(self.height, int)
            or not np.isfinite([self.fx, self.fy, self.cx, self.cy]).all()
            or self.fx <= 0
            or self.fy == 0
        ):
            raise ValueError("Invalid resolution or focal lengths")
        expected = (
            "x-right_y-up_z-forward" if self.fy < 0 else "x-right_y-down_z-forward"
        )
        if self.axes != expected:
            raise ValueError("Camera axes must agree with signed fy")


@dataclass(frozen=True)
class Pose:
    matrix: NDArray
    world_id: str
    segment_id: str
    source: str

    def __post_init__(self) -> None:
        from .geometry import validate_transform

        matrix = np.array(self.matrix, dtype=np.float64, copy=True)
        validate_transform(matrix)
        if (
            not self.world_id
            or not self.segment_id
            or self.source not in {"supplied", "estimated"}
        ):
            raise ValueError(
                "Pose needs origin identifiers and supplied/estimated source"
            )
        matrix.setflags(write=False)
        object.__setattr__(self, "matrix", matrix)

    def to_dict(self) -> dict[str, Any]:
        return {
            "T_world_camera": self.matrix.tolist(),
            "world_id": self.world_id,
            "segment_id": self.segment_id,
            "source": self.source,
            "units": "metres",
            "direction": "camera_to_world",
        }


@dataclass(frozen=True)
class Observation:
    frame_id: str
    camera_id: str
    timestamp_s: float | None
    clock: str
    calibration: Calibration
    pose: Pose

    def __post_init__(self) -> None:
        if not self.frame_id or not self.camera_id or not self.clock:
            raise ValueError("Observation identifiers and clock are required")
        if self.timestamp_s is not None and not np.isfinite(self.timestamp_s):
            raise ValueError("Capture timestamp must be finite seconds")
        if (self.clock == "frame_index_only") != (self.timestamp_s is None):
            raise ValueError("Frame indices cannot masquerade as capture timestamps")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "frame_id": self.frame_id,
            "camera_id": self.camera_id,
            "timestamp_s": self.timestamp_s,
            "clock": self.clock,
            "calibration": asdict(self.calibration),
            "pose": self.pose.to_dict(),
            "depth_definition": "camera_axis_z_metres",
            "colour_registration": "same_pixel_grid",
        }


def require_same_origin(first: Pose, second: Pose) -> None:
    if (first.world_id, first.segment_id) != (second.world_id, second.segment_id):
        raise ValueError("Unresolved world/segment origins cannot be combined")
