"""Immutable method observations; pixel support survives absent depth or pose."""

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from experiments.shared.contracts import Calibration

from .validation import finite, identifier, pairs, pixel_support, position


@dataclass(frozen=True)
class ObjectObservation:
    source_id: str
    session_id: str
    frame_id: str
    observation_id: str
    timestamp_s: float
    calibration: Calibration
    polygon: tuple[tuple[float, float], ...]
    bbox_xyxy: tuple[float, ...]
    source_hashes: tuple[tuple[str, str], ...]
    depth_available: bool
    method_provenance: tuple[tuple[str, str], ...]
    position_camera_m: tuple[float, ...] | None = None
    position_world_m: tuple[float, ...] | None = None
    world_id: str | None = None
    segment_id: str | None = None
    pose_revision_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("source_id", "session_id", "frame_id", "observation_id"):
            identifier(getattr(self, name), name)
        finite(self.timestamp_s, "timestamp_s")
        polygon, box = pixel_support(self.polygon, self.bbox_xyxy, self.calibration)
        object.__setattr__(self, "polygon", polygon)
        object.__setattr__(self, "bbox_xyxy", box)
        object.__setattr__(
            self,
            "source_hashes",
            pairs(self.source_hashes, "source hashes", hashes=True),
        )
        object.__setattr__(
            self,
            "method_provenance",
            pairs(self.method_provenance, "method provenance"),
        )
        if not isinstance(self.depth_available, bool):
            raise ValueError(  # noqa: TRY004 - schema error
                "depth_available must be boolean"
            )
        camera = position(self.position_camera_m, "position_camera_m", camera=True)
        world = position(self.position_world_m, "position_world_m")
        if not self.depth_available and (camera is not None or world is not None):
            raise ValueError("Missing depth cannot supply metric geometry")
        origin = (self.world_id, self.segment_id, self.pose_revision_id)
        if any(value is not None for value in origin):
            for value in origin:
                identifier(value, "world/segment/pose revision")
        if world is not None and any(value is None for value in origin):
            raise ValueError(
                "World coordinates require explicit world/segment/pose revision"
            )
        object.__setattr__(self, "position_camera_m", camera)
        object.__setattr__(self, "position_world_m", world)

    @property
    def key(self) -> tuple[str, str, str, str]:
        return self.source_id, self.session_id, self.frame_id, self.observation_id

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        for name in ("polygon", "bbox_xyxy", "position_camera_m", "position_world_m"):
            value = values[name]
            values[name] = (
                None
                if value is None
                else [list(v) if isinstance(v, tuple) else v for v in value]
            )
        values["source_hashes"] = dict(self.source_hashes)
        values["method_provenance"] = dict(self.method_provenance)
        return {"schema_version": 1, **values}


def validate_observations(records: Iterable[ObjectObservation]) -> None:
    keys = [record.key for record in records]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate observation key")
