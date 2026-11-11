"""Software-only arrays and pair transforms; no physical accuracy evidence."""

import importlib
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.walkthrough.config import PipelineSpec
from src.walkthrough.steps.contracts import ColourFrame, DepthPrediction

pose_backends = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.backend"
)
pose_tracking = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.tracking"
)
localisation = importlib.import_module(
    "experiments.06_object_recognition.pilot.localisation"
)


@dataclass(frozen=True)
class Fixture:
    name: str
    runnable: Any
    control: str = field(default="software", init=False)

    def load(self) -> Any:
        return self.runnable


def flat_depth(frames: Iterator[ColourFrame], *, run: Any) -> Iterator[DepthPrediction]:
    for frame in frames:
        shape = frame.calibration.height, frame.calibration.width
        yield DepthPrediction(
            frame.frame_id, np.full(shape, 2.0), np.ones(shape, dtype=bool)
        )


def no_site_measurements(surface: Any, run_path: Path) -> dict[str, Any]:
    return {
        "status": "fixture_only",
        "physical_dimensions": None,
        "physical_area": None,
    }


class IdentityBackend:
    def estimate(self, source: Any, target: Any) -> Any:
        return pose_backends.PairResult(
            True, np.eye(4), "software_control_identity_transform"
        )


class WholeImageDetector:
    def predict(self, image: Path) -> tuple[list[Any], dict[str, Any]]:
        with Image.open(image) as pixels:
            width, height = pixels.size
        return [localisation.Detection((0, 0, width, height), "fixture", 0, 1.0)], {
            "image_shape_hw": [height, width],
            "source": "software_control",
        }


def with_controls(spec: PipelineSpec, **swaps: Any) -> PipelineSpec:
    choices = {
        "depth": Fixture("flat_depth", flat_depth),
        "tracking": Fixture(
            "identity_backend", partial(pose_tracking.track, backend=IdentityBackend())
        ),
        "mapping": Fixture("no_site_measurements", no_site_measurements),
        "objects": replace(
            spec.objects, detector=Fixture("whole_image", WholeImageDetector())
        ),
    }
    return replace(spec, **{**choices, **swaps})
