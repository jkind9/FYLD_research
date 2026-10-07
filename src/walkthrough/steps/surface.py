"""One observed world point per valid source pixel, with explicit origins."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from experiments.shared.contracts import Calibration, Pose
from experiments.shared.geometry import backproject, transform_points
from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .contracts import (
    DepthOutput,
    MethodChoice,
    SurfaceOutput,
    SurfaceShard,
    TrackingOutput,
    method_label,
    read_pose,
)

SurfaceEstimator = Callable[[NDArray, NDArray, Calibration, Pose], NDArray]


class SurfaceMethod(MethodChoice, Protocol):
    """Load a method returning world Nx3 points in np.nonzero(valid) order."""

    def load(self) -> SurfaceEstimator: ...


@dataclass(frozen=True)
class MetricPoints:
    """Build experiment 04's point representation using shared geometry and supplied origins."""

    name: str = field(default="metric_points", init=False)
    control: str | None = field(default=None, init=False)

    def load(self) -> SurfaceEstimator:
        return metric_points


def metric_points(depth: NDArray, valid: NDArray, calibration: Calibration, pose: Pose) -> NDArray:
    points, _ = backproject(depth, valid, calibration)
    return transform_points(points, pose.matrix)


def run(
    run_context: Run,
    depth: DepthOutput,
    tracking: TrackingOutput,
    method: SurfaceMethod,
) -> tuple[StepResult, SurfaceOutput | None]:
    artifact = "output/predictions/surface.json"
    frame_id = None
    try:
        with run_context.measure("load_surface"):
            reconstruct = method.load()
        shards: list[SurfaceShard] = []
        with run_context.measure("prediction_surface", frames=len(depth["frames"])):
            for index, (frame, record) in enumerate(zip(depth["frames"], tracking["records"], strict=True)):
                frame_id = frame["frame_id"]
                with run_context.measure("surface_frame", frames=1):
                    pose = read_pose(record["pose"])
                    if pose.source != "estimated" and tracking["control"] != "reference":
                        raise ValueError("Supplied poses are outside a labelled reference control")
                    with np.load(run_context.path / frame["arrays"], allow_pickle=False) as arrays:
                        points = np.asarray(
                            reconstruct(
                                arrays["depth"],
                                arrays["valid"],
                                Calibration(**frame["calibration"]),
                                pose,
                            )
                        )
                        if points.shape != (int(arrays["valid"].sum()), 3) or not np.isfinite(points).all():
                            raise ValueError("Surface must return finite Nx3 points, one per valid source pixel")
                    relative = f"output/predictions/surface/{index:06d}.npy"
                    path = run_context.path / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    np.save(path, points, allow_pickle=False)
                    shards.append(
                        {
                            "frame_id": frame_id,
                            "points": relative,
                            "point_count": len(points),
                            "world_id": pose.world_id,
                            "segment_id": pose.segment_id,
                            "units": "metres",
                        }
                    )
            output: SurfaceOutput = {
                "methods": {"surface": method_label(method)},
                "shards": shards,
                "coverage": "observed_points_only; unseen space unknown",
            }
            write_json(run_context.path / artifact, output)
    except (Unavailable, ValueError, OSError) as error:
        if frame_id is not None:
            error = type(error)(f"Frame {frame_id}: {error}")
        return failed_step("surface", error, method.name), None
    return (
        StepResult(
            "surface",
            "complete",
            "Method outputs saved",
            method.name,
            len(shards),
            artifact,
        ),
        output,
    )


def validate(depth: DepthOutput, output: SurfaceOutput) -> None:
    """Keep the source frame identities and metric units in every saved shard."""
    if [row["frame_id"] for row in depth["frames"]] != [row["frame_id"] for row in output["shards"]] or any(
        row["units"] != "metres" for row in output["shards"]
    ):
        raise ValueError("Surface output must match depth identities and declare metres")
