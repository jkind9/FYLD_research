"""Call the unchanged tracking kernel on one calibrated RGB-D frame at a time."""

import importlib
from collections.abc import Iterator
from typing import Any

import numpy as np
from PIL import Image

from experiments.shared.contracts import Calibration
from experiments.shared.runs import Run, write_json

from ..config import Configuration
from ..records import StepResult, failed_step
from .artifacts import CaptureOutput, DepthOutput, TrackingOutput


def frames(run: Run, capture: CaptureOutput, depth: DepthOutput) -> Iterator[Any]:
    owner = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
    if len(capture["frames"]) != len(depth["frames"]):
        raise ValueError("Capture/depth frame counts differ")
    camera_id, clock = None, None
    for row, measured in zip(capture["frames"], depth["frames"], strict=True):
        if row["frame_id"] != measured["frame_id"]:
            raise ValueError("Capture/depth frame identities differ")
        current = (row["camera_id"], row["timestamp_source"])
        if camera_id is not None and current != (camera_id, clock):
            raise ValueError(
                "Tracking requires one camera and one declared capture clock"
            )
        camera_id, clock = current
        with Image.open(run.path / row["image"]) as image:
            colour = np.asarray(image.convert("RGB"))
        with np.load(run.path / measured["arrays"], allow_pickle=False) as arrays:
            timestamp = row["timestamp_ns"] / 1_000_000_000
            yield owner.RGBDFrame(
                row["frame_id"],
                timestamp,
                timestamp,
                Calibration(**measured["calibration"]),
                colour,
                arrays["depth"],
                arrays["valid"],
            )


def run(
    publication: Run,
    capture: CaptureOutput | None,
    depth: DepthOutput | None,
    config: Configuration,
    *,
    state: StepResult,
    test_backend: Any = None,
) -> tuple[StepResult, TrackingOutput | None]:
    if state.status != "pending":
        return state, None
    artifact = "output/predictions/tracking.json"
    try:
        with publication.measure("prediction_tracking"):
            if capture is None or depth is None:
                raise ValueError("Required upstream predictions are missing")
            owner = importlib.import_module(
                "experiments.03_camera_pose_estimation.src.tracking"
            )
            backend = importlib.import_module(
                "experiments.03_camera_pose_estimation.src.backend"
            )
            if test_backend is not None and not config.software_control:
                raise ValueError("Test backend requires software_control=True")
            selected = backend.CPUOdometry() if test_backend is None else test_backend
            records = owner.track(
                frames(publication, capture, depth),
                selected,
                publication,
                publication.path.name,
            )
            if not records or any(record.pose is None for record in records):
                raise ValueError(
                    "Tracking failed for one or more observations; no complete geometry"
                )
            output: TrackingOutput = {
                "records": [record.to_dict() for record in records]
            }
            # Export this layer's predictions before returning downstream data.
            write_json(publication.path / artifact, output)
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        return failed_step(state.name, error), None
    return StepResult(state.name, "complete", "Method outputs saved", artifact), output
