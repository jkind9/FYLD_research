"""Every layer's contract: what its method receives and returns, and what the layer saves.

Methods see only the method contract. Later layers see only the saved outputs.
src/walkthrough/README.md, "Layer contracts", lists both with units and checks.
"""

import importlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypedDict

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from experiments.shared.contracts import Calibration, Pose
from experiments.shared.runs import Run

from ..records import Unavailable

# Experiment folders start with digits, so `import` syntax cannot name them.
pose_dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
pose_tracking = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")
# Numeric experiment names need dynamic imports; runtime records retain their owning classes.
if TYPE_CHECKING:
    RGBDFrame = Any
    PoseRecord = Any
else:
    RGBDFrame = pose_dataset.RGBDFrame
    PoseRecord = pose_tracking.Record


# ---- Method contracts ----


class MethodChoice(Protocol):
    """Read-only identity and control label shared by frozen method choices."""

    @property
    def name(self) -> str: ...

    @property
    def control(self) -> str | None: ...


@dataclass(frozen=True)
class ColourFrame:
    """What a depth method receives per frame."""

    frame_id: str
    timestamp_s: float | None
    calibration: Calibration
    colour: NDArray[np.uint8]


@dataclass(frozen=True)
class DepthPrediction:
    """What a depth method returns per frame: camera-axis metres and a trusted-pixel mask."""

    frame_id: str
    depth: NDArray[np.floating]
    valid: NDArray[np.bool_]


class DepthEstimator(Protocol):
    def __call__(self, frames: Iterator[ColourFrame], *, run: Run) -> Iterator[DepthPrediction]:
        """All frames in, one prediction per frame out, same order. run is for optional inner timing."""


class TrackingEstimator(Protocol):
    def __call__(self, frames: Iterator[RGBDFrame], *, run: Run) -> list[PoseRecord]:
        """All RGB-D frames in, one pose record per frame out, same order. Unplaced frames get pose None and a reason."""


# ---- Saved outputs ----


class ImageArtifact(TypedDict):
    """One saved image and the source facts available for it. Absent facts are None."""

    frame_id: str
    source_id: str
    source_frame_id: str
    source_frame_index: int
    image: str
    image_width: int
    image_height: int
    source_sha256: str
    timestamp_s: float | None
    timestamp_source: str | None
    calibration: dict[str, Any] | None
    calibration_source: str | None
    phone_grid: dict[str, Any] | None


class CaptureOutput(TypedDict):
    methods: dict[str, str]
    frames: list[ImageArtifact]
    withheld_from_methods: dict[str, str]  # each held-back input, with the reason


class DepthArtifact(TypedDict):
    frame_id: str
    arrays: str
    calibration: dict[str, Any]
    source: str
    depth_definition: str


class DepthOutput(TypedDict):
    methods: dict[str, str]
    frames: list[DepthArtifact]
    control: str | None


class TrackingOutput(TypedDict):
    methods: dict[str, str]
    records: list[dict[str, Any]]  # experiment 03's Record.to_dict()
    control: str | None


class SurfaceShard(TypedDict):
    frame_id: str
    points: str
    point_count: int
    world_id: str
    segment_id: str
    units: str


class SurfaceOutput(TypedDict):
    methods: dict[str, str]
    shards: list[SurfaceShard]
    coverage: str


class MappingOutput(TypedDict):
    methods: dict[str, str]
    control: str | None
    measurements: dict[str, Any]


class ObjectsOutput(TypedDict):
    synthetic_detector: bool
    methods: dict[str, str]
    frames: list[dict[str, Any]]
    origins: list[dict[str, Any]]
    whole_site_distinct_count: None
    claim: str
    optional_evidence_changes_counting: bool


# ---- Shared readers ----


def method_label(choice: Any) -> str:
    """The chosen method's short name and class, saved with predictions and shown on visuals."""
    return f"{choice.name} ({type(choice).__module__}.{type(choice).__qualname__})"


def read_pose(row: dict[str, Any]) -> Pose:
    """Rebuild a saved pose, refusing anything but a valid metric camera-to-world transform."""
    if row["units"] != "metres" or row["direction"] != "camera_to_world":
        raise ValueError("Expected metric camera-to-world pose")
    return Pose(row["T_world_camera"], row["world_id"], row["segment_id"], row["source"])


def check_capture_clock(capture: CaptureOutput) -> None:
    """Refuse missing or mixed capture clocks before a tracking method loads."""
    rows = capture["frames"]
    if any(row["timestamp_s"] is None or row["timestamp_source"] is None for row in rows):
        raise Unavailable("Tracking needs a source timestamp and its clock label")
    if len({(row["source_id"], row["timestamp_source"]) for row in rows}) != 1:
        raise ValueError("Tracking requires one camera and one declared capture clock")


def load_rgbd_frames(run_path: Path, capture: CaptureOutput, depth: DepthOutput) -> Iterator[RGBDFrame]:
    """Yield RGB-D frames one at a time, for one camera and one declared clock."""
    check_capture_clock(capture)
    rows = capture["frames"]
    for row, measured in zip(rows, depth["frames"], strict=True):
        with Image.open(run_path / row["image"]) as image:
            colour = np.asarray(image.convert("RGB"))
        with np.load(run_path / measured["arrays"], allow_pickle=False) as arrays:
            yield RGBDFrame(
                row["frame_id"],
                row["timestamp_s"],
                row["timestamp_s"],
                Calibration(**measured["calibration"]),
                colour,
                arrays["depth"],
                arrays["valid"],
            )
