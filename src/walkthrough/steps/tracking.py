"""Tracking methods consume a calibrated RGB-D sequence and preserve pose origins."""

import importlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Protocol

from numpy.typing import NDArray

from experiments.shared.contracts import Pose
from experiments.shared.geometry import associate_times
from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .contracts import (
    CaptureOutput,
    DepthOutput,
    MethodChoice,
    PoseRecord,
    RGBDFrame,
    TrackingEstimator,
    TrackingOutput,
    check_capture_clock,
    load_rgbd_frames,
    method_label,
    read_pose,
)

pose_tracking = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")
pose_backends = importlib.import_module("experiments.03_camera_pose_estimation.src.backend")
pose_evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")


class TrackingMethod(MethodChoice, Protocol):
    def load(self) -> TrackingEstimator: ...


@dataclass(frozen=True)
class CpuOdometry:
    name: str = field(default="cpu_odometry", init=False)
    control: str | None = field(default=None, init=False)

    def load(self) -> TrackingEstimator:
        return partial(pose_tracking.track, backend=pose_backends.CPUOdometry())


@dataclass(frozen=True)
class ReferencePoses:
    groundtruth: Path
    tolerance_s: float = 0.02
    name: str = field(default="reference_poses", init=False)
    control: str = field(default="reference", init=False)

    def load(self) -> TrackingEstimator:
        references = pose_evaluation.read_references(self.groundtruth)
        return partial(self._estimate, references=references)

    def _estimate(
        self,
        frames: Iterator[RGBDFrame],
        *,
        run: Run,
        references: list[tuple[float, NDArray]],
    ) -> list[PoseRecord]:
        observations = list(frames)
        matches = dict(
            associate_times(
                [frame.timestamp_s for frame in observations],
                [row[0] for row in references],
                self.tolerance_s,
            )
        )
        records = []
        for index, frame in enumerate(observations):
            if index in matches:
                pose = Pose(references[matches[index]][1], "tum_groundtruth", "0", "supplied")
                reason = "reference control"
            else:
                pose = None
                reason = f"No ground-truth pose within {self.tolerance_s:g} s"
            records.append(PoseRecord(frame.frame_id, frame.timestamp_s, "supplied", pose, reason))
        return records


def run(
    run_context: Run, capture: CaptureOutput, depth: DepthOutput, method: TrackingMethod
) -> tuple[StepResult, TrackingOutput | None]:
    artifact = "output/predictions/tracking.json"
    try:
        check_capture_clock(capture)
        with run_context.measure("load_tracking"):
            estimate = method.load()
        with run_context.measure("prediction_tracking", frames=len(capture["frames"])):
            records = estimate(load_rgbd_frames(run_context.path, capture, depth), run=run_context)
            source_ids = [frame["frame_id"] for frame in capture["frames"]]
            if len(records) != len(source_ids):
                raise ValueError(f"Tracking returned {len(records)} records for {len(source_ids)} frames")
            if [record.frame_id for record in records] != source_ids:
                raise ValueError("Tracking record order must match capture")
            lost = [record for record in records if record.pose is None]
            if lost:
                raise ValueError(
                    f"Tracking could not place {len(lost)} of {len(records)} frames; first {lost[0].frame_id}: {lost[0].reason}"
                )
            output: TrackingOutput = {
                "methods": {"tracking": method_label(method)},
                "records": [record.to_dict() for record in records],
                "control": method.control,
            }
            validate(capture, output)
            write_json(run_context.path / artifact, output)
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("tracking", error, method.name), None
    step = StepResult("tracking", "complete", "Method outputs saved", method.name, len(records), artifact)
    return step, output


def validate(capture: CaptureOutput, output: TrackingOutput) -> None:
    if [row["frame_id"] for row in capture["frames"]] != [row["frame_id"] for row in output["records"]]:
        raise ValueError("Tracking frame identities must match capture")
    for source, record in zip(capture["frames"], output["records"], strict=True):
        if record["timestamp_s"] != source["timestamp_s"]:
            raise ValueError(f"Frame {source['frame_id']}: tracking timestamp must match capture")
        read_pose(record["pose"])
