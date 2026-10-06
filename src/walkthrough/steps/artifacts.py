"""Static contracts for saved stage manifests, using shared metric records."""

from collections.abc import Callable
from typing import Any, TypedDict

import numpy as np
from numpy.typing import NDArray

from experiments.shared.contracts import Calibration


class ImageArtifact(TypedDict):
    """Phone-reader metadata plus the saved original image handle."""

    frame_id: str
    camera_id: str
    image: str
    image_width: int
    image_height: int
    timestamp_ns: int
    timestamp_source: str
    geometry_ready: bool
    rotation_degrees: int
    lens_distortion: list[float] | tuple[float, ...] | None
    intrinsics: list[float] | tuple[float, ...]
    intrinsics_pixel_grid: str
    crop_region: list[int] | tuple[int, ...]
    pre_correction_active_array_rect: list[int] | tuple[int, ...]
    sensor_to_image_crop_scale: list[float] | tuple[float, ...]


class CaptureOutput(TypedDict):
    frames: list[ImageArtifact]
    depth: str
    pose: str


class DepthArtifact(TypedDict):
    frame_id: str
    arrays: str
    calibration: dict[str, Any]
    source: str
    depth_definition: str


class DepthOutput(TypedDict):
    frames: list[DepthArtifact]
    software_control: bool


class TrackingOutput(TypedDict):
    # Record.to_dict is the owning experiment's existing serialized contract.
    records: list[dict[str, Any]]


class SurfaceShard(TypedDict):
    frame_id: str
    points: str
    point_count: int
    world_id: str
    segment_id: str
    units: str


class SurfaceOutput(TypedDict):
    shards: list[SurfaceShard]
    coverage: str


class MappingOutput(TypedDict):
    software_control: bool
    measurements: dict[str, Any]


class ObjectsOutput(TypedDict):
    frames: list[dict[str, Any]]
    origins: list[dict[str, Any]]
    whole_site_distinct_count: None
    claim: str
    optional_evidence_changes_counting: bool


DepthProvider = Callable[
    [ImageArtifact, Calibration], tuple[NDArray[Any], NDArray[np.bool_]]
]
MappingProvider = Callable[[SurfaceOutput], dict[str, Any]]


class TestProviders(TypedDict, total=False):
    depth: DepthProvider
    mapping: MappingProvider
    # Numbered experiment APIs own their backend/detector protocols. Retain
    # their duck-typed test instances without introducing a second protocol.
    backend: Any
    detector: Any
