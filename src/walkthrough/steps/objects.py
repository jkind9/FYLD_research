"""Task46 box-depth counting, isolated by estimated world and segment."""

import importlib
from dataclasses import asdict
from typing import Any

import numpy as np

from experiments.shared.runs import Run, write_json

from ..config import Configuration
from ..records import StepResult, Unavailable, failed_step
from . import surface, tracking
from .artifacts import (
    CaptureOutput,
    DepthOutput,
    ObjectsOutput,
    TrackingOutput,
)


def optional_evidence(
    run: Run, frame: Any, detection: Any, config: Configuration, key: str
) -> dict[str, Any]:
    evidence = {}
    mask = None
    if config.segmentation is not None:
        owner = importlib.import_module(
            "experiments.06_object_recognition.experiments.02_segmentation.masks"
        )
        with run.measure("diagnostic_segmentation", frames=1):
            result = owner.segment(
                frame.colour, list(detection.xyxy), config.segmentation
            )
        mask = result["mask"]
        relative = f"output/predictions/objects/masks/{key}.npy"
        path = run.path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, mask, allow_pickle=False)
        evidence["segmentation"] = {**result, "mask": relative}
    if config.appearance:
        owner = importlib.import_module(
            "experiments.06_object_recognition.experiments.03_appearance.adapter"
        )
        if mask is None:
            localisation = importlib.import_module(
                "experiments.06_object_recognition.pilot.localisation"
            )
            mask = np.where(localisation.box_support(frame, detection), 255, 0).astype(
                np.uint8
            )
        with run.measure("diagnostic_appearance", frames=1):
            crop = owner.prepare_crop(frame.colour, mask, detection.xyxy)
            evidence["appearance"] = owner.describe_classical(crop)
    return evidence


def run(
    publication: Run,
    capture: CaptureOutput | None,
    depth: DepthOutput | None,
    tracked: TrackingOutput | None,
    config: Configuration,
    *,
    state: StepResult,
    test_detector: Any = None,
) -> tuple[StepResult, ObjectsOutput | None]:
    if state.status != "pending":
        return state, None
    artifact = "output/predictions/objects.json"
    try:
        with publication.measure("prediction_objects"):
            if capture is None or depth is None or tracked is None:
                raise ValueError("Required upstream predictions are missing")
            # Validate counting settings and select the existing detector.
            if config.max_distance_m is None or config.ambiguity_margin_m is None:
                raise Unavailable(
                    "Counting requires explicit inherited distance and ambiguity settings"
                )
            if test_detector is not None and not config.software_control:
                raise ValueError("Test detector requires software_control=True")
            if test_detector is None and config.checkpoint is None:
                raise Unavailable(
                    "Object detector requires an already acquired checkpoint"
                )
            detector_owner = importlib.import_module(
                "experiments.06_object_recognition.pilot.detector"
            )
            localisation = importlib.import_module(
                "experiments.06_object_recognition.pilot.localisation"
            )
            association = importlib.import_module(
                "experiments.06_object_recognition.pilot.association"
            )
            detector = (
                test_detector
                if test_detector is not None
                else detector_owner.YoloDetector(config.checkpoint, "cpu")
            )
            origins: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
            observations: list[dict[str, Any]] = []
            next_number = 1
            rows = capture["frames"]
            records = tracked["records"]
            if len(rows) != len(records):
                raise ValueError("Capture/tracking frame counts differ")
            for index, (frame, row, record) in enumerate(
                zip(
                    tracking.frames(publication, capture, depth),
                    rows,
                    records,
                    strict=True,
                )
            ):
                # Validate the observation and retain its estimated origin.
                if frame.frame_id != record["frame_id"]:
                    raise ValueError("Object/tracking observation identities differ")
                estimated = surface.pose(record["pose"])
                if estimated.source != "estimated":
                    raise ValueError("Object methods require estimated poses")
                origin = estimated.world_id, estimated.segment_id

                # Detect and localise proposals on the original calibrated grid.
                detections, metadata = detector.predict(publication.path / row["image"])
                if metadata["image_shape_hw"] != [
                    frame.calibration.height,
                    frame.calibration.width,
                ]:
                    raise ValueError(
                        "Detector proposals do not use the original calibrated grid"
                    )
                proposals = []
                for number, detection in enumerate(detections):
                    location = localisation.localise_detection(
                        frame, detection, estimated
                    )
                    median = location["box_median"]
                    proposals.append(
                        {
                            **asdict(detection),
                            "frame_id": frame.frame_id,
                            "observation_id": f"{frame.frame_id}:detection:{number}",
                            "timestamp_s": frame.timestamp_s,
                            "frame_index": index,
                            "world_position_m": median["world_m"] if median else None,
                            "localisation": location,
                            **optional_evidence(
                                publication,
                                frame,
                                detection,
                                config,
                                f"{index}-{number}",
                            ),
                        }
                    )

                # Apply Task46 counting within this world and segment only.
                decisions, updated, next_number = association.associate_frame(
                    proposals,
                    origins.get(origin, {}),
                    next_number,
                    config.max_distance_m,
                    config.ambiguity_margin_m,
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
            output: ObjectsOutput = {
                "frames": observations,
                "origins": [
                    {
                        "world_id": world,
                        "segment_id": segment,
                        "distinct_provisional_count": len(state),
                        "tracks": list(state.values()),
                    }
                    for (world, segment), state in origins.items()
                ],
                "whole_site_distinct_count": None,
                "claim": "Per-origin provisional IDs only; no identity joins across origins",
                "optional_evidence_changes_counting": False,
            }
            # Export this layer's predictions before returning downstream data.
            write_json(publication.path / artifact, output)
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        return failed_step(state.name, error), None
    return StepResult(state.name, "complete", "Method outputs saved", artifact), output
