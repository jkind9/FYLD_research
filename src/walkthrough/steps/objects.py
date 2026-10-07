"""Swappable detection with Task46 counting, isolated by world and segment."""

import importlib
import math
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from experiments.shared.contracts import Pose
from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .contracts import (
    CaptureOutput,
    DepthOutput,
    MethodChoice,
    ObjectsOutput,
    TrackingOutput,
    load_rgbd_frames,
    method_label,
    read_pose,
)

detector_owner = importlib.import_module("experiments.06_object_recognition.pilot.detector")
localisation = importlib.import_module("experiments.06_object_recognition.pilot.localisation")
association = importlib.import_module("experiments.06_object_recognition.pilot.association")
segmentation_owner = importlib.import_module("experiments.06_object_recognition.experiments.02_segmentation.masks")
appearance_owner = importlib.import_module("experiments.06_object_recognition.experiments.03_appearance.adapter")
PROPOSAL_FIELDS = {"xyxy", "label", "object_id", "association"}


class Detector(Protocol):
    """Return detections and image_shape_hw metadata on the original image grid."""

    def predict(self, image: Path) -> tuple[list[Any], dict[str, Any]]: ...


class DetectorMethod(MethodChoice, Protocol):
    def load(self) -> Detector: ...


@dataclass(frozen=True)
class Yolo26x:
    """Load experiment 06's CPU detector from an acquired checkpoint."""

    checkpoint: Path
    name: str = field(default="yolo26x", init=False)
    control: str | None = field(default=None, init=False)

    def load(self) -> Detector:
        return detector_owner.YoloDetector(Path(self.checkpoint), "cpu")


@dataclass(frozen=True)
class ClassicalSegmentation:
    """Select a mask method from experiment 06's segmentation comparison."""

    method: str
    name: str = field(default="classical_segmentation", init=False)
    control: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.method not in segmentation_owner.METHODS:
            raise ValueError("Choose an existing segmentation method explicitly")

    def load(self) -> Callable:
        return partial(segmentation_owner.segment, method=self.method)


@dataclass(frozen=True)
class ClassicalAppearance:
    """Use experiment 06's classical appearance comparison."""

    name: str = field(default="classical_appearance", init=False)
    control: str | None = field(default=None, init=False)

    def load(self) -> Callable:
        return describe_appearance


def describe_appearance(colour: np.ndarray, mask: np.ndarray, xyxy: tuple) -> dict[str, Any]:
    return appearance_owner.describe_classical(appearance_owner.prepare_crop(colour, mask, xyxy))


@dataclass(frozen=True)
class ObjectSettings:
    detector: DetectorMethod | None = None
    max_distance_m: float | None = None
    ambiguity_margin_m: float | None = None
    segmentation: ClassicalSegmentation | None = None
    appearance: ClassicalAppearance | None = None

    def __post_init__(self) -> None:
        for name in ("max_distance_m", "ambiguity_margin_m"):
            value = getattr(self, name)
            if value is not None and (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value < 0
                or (name == "max_distance_m" and value == 0)
            ):
                raise ValueError("Explicit counting settings must be finite valid metres")


def run(
    run_context: Run,
    capture: CaptureOutput,
    depth: DepthOutput,
    tracked: TrackingOutput,
    settings: ObjectSettings,
) -> tuple[StepResult, ObjectsOutput | None]:
    artifact = "output/predictions/objects.json"
    name = settings.detector.name if settings.detector is not None else None
    try:
        if settings.max_distance_m is None or settings.ambiguity_margin_m is None:
            raise Unavailable("Counting needs inherited distance and ambiguity settings")
        if settings.detector is None:
            raise Unavailable("Object detector requires an already acquired checkpoint")
        with run_context.measure("load_objects"):
            detector = settings.detector.load()
            segment = settings.segmentation.load() if settings.segmentation is not None else None
            appearance = settings.appearance.load() if settings.appearance is not None else None
        with run_context.measure("prediction_objects", frames=len(capture["frames"])):
            observations, origins = _count(
                run_context,
                capture,
                depth,
                tracked,
                settings,
                detector,
                segment,
                appearance,
            )
            output = _output(settings.detector, observations, origins)
            validate(capture, output)
            write_json(run_context.path / artifact, output)
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("objects", error, name), None
    return (
        StepResult(
            "objects",
            "complete",
            "Method outputs saved",
            name,
            len(observations),
            artifact,
        ),
        output,
    )


def _count(
    run_context: Run,
    capture: CaptureOutput,
    depth: DepthOutput,
    tracked: TrackingOutput,
    settings: ObjectSettings,
    detector: Detector,
    segment: Callable | None,
    appearance: Callable | None,
) -> tuple[list[dict[str, Any]], dict]:
    origins: dict[tuple[str, str], dict] = {}
    observations = []
    next_number = 1
    for index, (frame, row, record) in enumerate(
        zip(
            load_rgbd_frames(run_context.path, capture, depth),
            capture["frames"],
            tracked["records"],
            strict=True,
        )
    ):
        try:
            with run_context.measure("objects_frame", frames=1):
                pose = read_pose(record["pose"])
                if pose.source != "estimated" and tracked["control"] != "reference":
                    raise ValueError("Supplied poses are outside a labelled reference control")
                origin = pose.world_id, pose.segment_id
                detections, metadata = detector.predict(run_context.path / row["image"])
                if metadata["image_shape_hw"] != [
                    frame.calibration.height,
                    frame.calibration.width,
                ]:
                    raise ValueError("Detector proposals do not use the original calibrated grid")
                proposals = [
                    _place(
                        run_context,
                        frame,
                        detection,
                        pose,
                        index,
                        number,
                        segment,
                        appearance,
                    )
                    for number, detection in enumerate(detections)
                ]
                decisions, updated, next_number = association.associate_frame(
                    proposals,
                    origins.get(origin, {}),
                    next_number,
                    settings.max_distance_m,
                    settings.ambiguity_margin_m,
                )
                origins = {**origins, origin: updated}
                observations.append(
                    {
                        "frame_id": frame.frame_id,
                        "world_id": origin[0],
                        "segment_id": origin[1],
                        "proposals": decisions,
                        "detector": metadata,
                    }
                )
        except (ValueError, OSError) as error:
            raise ValueError(f"Frame {frame.frame_id}: {error}") from error
    return observations, origins


def _place(
    run_context: Run,
    frame: Any,
    detection: Any,
    pose: Pose,
    index: int,
    number: int,
    segment: Callable | None,
    appearance: Callable | None,
) -> dict[str, Any]:
    location = localisation.localise_detection(frame, detection, pose)
    median = location["box_median"]
    return {
        **asdict(detection),
        "frame_id": frame.frame_id,
        "observation_id": f"{frame.frame_id}:detection:{number}",
        "timestamp_s": frame.timestamp_s,
        "frame_index": index,
        "world_position_m": median["world_m"] if median else None,
        "localisation": location,
        **_optional_evidence(run_context, frame, detection, segment, appearance, f"{index}-{number}"),
    }


def _optional_evidence(
    run_context: Run,
    frame: Any,
    detection: Any,
    segment: Callable | None,
    appearance: Callable | None,
    key: str,
) -> dict[str, Any]:
    evidence = {}
    mask = None
    if segment is not None:
        with run_context.measure("diagnostic_segmentation", frames=1):
            result = segment(frame.colour, list(detection.xyxy))
        mask = result["mask"]
        relative = f"output/predictions/objects/masks/{key}.npy"
        path = run_context.path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, mask, allow_pickle=False)
        evidence["segmentation"] = {**result, "mask": relative}
    if appearance is not None:
        if mask is None:
            mask = np.where(localisation.box_support(frame, detection), 255, 0).astype(np.uint8)
        with run_context.measure("diagnostic_appearance", frames=1):
            evidence["appearance"] = appearance(frame.colour, mask, detection.xyxy)
    return evidence


def _output(method: DetectorMethod, observations: list[dict[str, Any]], origins: dict) -> ObjectsOutput:
    return {
        "synthetic_detector": method.control == "software",
        "methods": {
            "detection": method_label(method),
            "localisation": "experiments.06_object_recognition.pilot.localisation.localise_detection",
            "counting": "experiments.06_object_recognition.pilot.association.associate_frame",
        },
        "frames": observations,
        "origins": [
            {
                "world_id": world,
                "segment_id": segment,
                "distinct_provisional_count": len(tracks),
                "tracks": list(tracks.values()),
            }
            for (world, segment), tracks in origins.items()
        ],
        "whole_site_distinct_count": None,
        "claim": "Per-origin provisional IDs only; no identity joins across origins",
        "optional_evidence_changes_counting": False,
    }


def validate(capture: CaptureOutput, output: ObjectsOutput) -> None:
    if [row["frame_id"] for row in capture["frames"]] != [row["frame_id"] for row in output["frames"]] or output[
        "whole_site_distinct_count"
    ] is not None:
        raise ValueError("Object output must match capture identities and leave whole-site counts unset")
    for frame in output["frames"]:
        for proposal in frame["proposals"]:
            if not PROPOSAL_FIELDS <= proposal.keys():
                raise ValueError(f"Frame {frame['frame_id']}: object proposal needs {sorted(PROPOSAL_FIELDS)}")
