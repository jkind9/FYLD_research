"""Depth methods consume all colour frames and yield calibrated metric grids."""

import importlib
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from experiments.shared.geometry import check_depth_grid, depth_metres
from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .capture import calibration_for, saved_colour_frames
from .contracts import (
    CaptureOutput,
    ColourFrame,
    DepthArtifact,
    DepthEstimator,
    DepthOutput,
    DepthPrediction,
    MethodChoice,
    check_reference_tolerance,
    method_label,
    nearest_references,
)

pose_dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")


class DepthMethod(MethodChoice, Protocol):
    def load(self) -> DepthEstimator: ...


@dataclass(frozen=True)
class RecordedSensorDepth:
    """Supply experiment 03's recorded TUM depth as a reference control."""

    root: Path
    tolerance_s: float = 0.02  # inherited from experiment 03 dataset.py:79
    units_per_metre: float = 5000.0  # inherited from experiment 03 dataset.py:123
    max_depth_m: float = 4.0  # inherited from experiment 03 dataset.py:124
    name: str = field(default="recorded_sensor_depth", init=False)
    control: str = field(default="reference", init=False)

    def __post_init__(self) -> None:
        check_reference_tolerance(self.tolerance_s)
        for name in ("units_per_metre", "max_depth_m"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")

    def load(self) -> DepthEstimator:
        rows = pose_dataset.read_table(self.root / "depth.txt")
        return partial(self._predict, rows=rows)

    def _predict(
        self, frames: Iterator[ColourFrame], *, run: Run, rows: list[tuple[float, str]]
    ) -> Iterator[DepthPrediction]:
        for frame, matched in nearest_references(frames, [row[0] for row in rows], self.tolerance_s):
            if matched is None:
                raise ValueError(f"{frame.frame_id}: No sensor depth within {self.tolerance_s:g} s")
            path = self.root / rows[matched][1]
            if path.is_symlink() or not path.resolve().is_relative_to(self.root.resolve()):
                raise ValueError("TUM depth path must stay inside the selected dataset")
            with Image.open(path) as image:
                encoded = np.asarray(image)
                if image.format != "PNG" or encoded.dtype != np.uint16:
                    raise ValueError(f"{frame.frame_id}: Expected uint16 depth PNG")
            depth, valid = depth_metres(encoded, self.units_per_metre)
            yield DepthPrediction(frame.frame_id, depth, valid & (depth < self.max_depth_m))


def run(run_context: Run, capture: CaptureOutput, method: DepthMethod | None) -> tuple[StepResult, DepthOutput | None]:
    artifact = "output/predictions/depth.json"
    name = None if method is None else method.name
    try:
        if method is None:
            raise Unavailable("Task54 real metric depth implementation is unavailable")
        for frame in capture["frames"]:
            calibration_for(frame)
        with run_context.measure("load_depth"):
            estimate = method.load()
        with run_context.measure("prediction_depth", frames=len(capture["frames"])):
            predictions = iter(estimate(saved_colour_frames(run_context.path, capture), run=run_context))
            rows: list[DepthArtifact] = []
            for index, frame in enumerate(capture["frames"]):
                with run_context.measure("depth_frame", frames=1):
                    prediction = next(predictions, None)
                if prediction is None:
                    raise ValueError(
                        f"Depth returned too few predictions: expected {len(capture['frames'])}, got {index}"
                    )
                if prediction.frame_id != frame["frame_id"]:
                    raise ValueError(
                        f"Depth prediction order differs: expected {frame['frame_id']}, got {prediction.frame_id}"
                    )
                camera = calibration_for(frame)
                check_depth_grid(prediction.depth, prediction.valid, camera)
                relative = f"output/predictions/depth/{index:06d}.npz"
                path = run_context.path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                np.savez(path, depth=prediction.depth, valid=prediction.valid)
                rows.append(
                    {
                        "frame_id": frame["frame_id"],
                        "arrays": relative,
                        "calibration": asdict(camera),
                        "source": method_label(method),
                        "depth_definition": "camera_axis_z_metres",
                    }
                )
            if next(predictions, None) is not None:
                raise ValueError(f"Depth returned too many predictions: expected {len(rows)}")
            output: DepthOutput = {
                "methods": {"depth": method_label(method)},
                "frames": rows,
                "control": method.control,
            }
            write_json(run_context.path / artifact, output)
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("depth", error, name), None
    return (
        StepResult("depth", "complete", "Method outputs saved", name, len(rows), artifact),
        output,
    )


def validate(capture: CaptureOutput, output: DepthOutput) -> None:
    if [row["frame_id"] for row in capture["frames"]] != [row["frame_id"] for row in output["frames"]]:
        raise ValueError("Depth output frame identities must match capture")
