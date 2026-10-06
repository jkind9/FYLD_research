"""Export full metric observed geometry shards with their estimated origins."""

import importlib
from typing import Any

import numpy as np

from experiments.shared.contracts import Calibration, Pose
from experiments.shared.runs import Run, write_json

from ..config import Configuration
from ..records import StepResult, failed_step
from .artifacts import DepthOutput, SurfaceOutput, SurfaceShard, TrackingOutput


def pose(row: dict[str, Any] | None) -> Pose:
    if row is None or row["units"] != "metres" or row["direction"] != "camera_to_world":
        raise ValueError("Expected metric camera-to-world pose")
    return Pose(
        row["T_world_camera"], row["world_id"], row["segment_id"], row["source"]
    )


def run(
    publication: Run,
    depth: DepthOutput | None,
    tracking: TrackingOutput | None,
    config: Configuration,
    *,
    state: StepResult,
) -> tuple[StepResult, SurfaceOutput | None]:
    if state.status != "pending":
        return state, None
    artifact = "output/predictions/surface.json"
    try:
        with publication.measure("prediction_surface"):
            if depth is None or tracking is None:
                raise ValueError("Required upstream predictions are missing")
            owner = importlib.import_module(
                "experiments.04_surface_reconstruction.src.metric_surface"
            )
            if len(depth["frames"]) != len(tracking["records"]):
                raise ValueError("Depth/tracking observation counts differ")
            shards: list[SurfaceShard] = []
            for index, (frame, record) in enumerate(
                zip(depth["frames"], tracking["records"], strict=True)
            ):
                if frame["frame_id"] != record["frame_id"]:
                    raise ValueError("Depth/tracking observation identities differ")
                estimated = pose(record["pose"])
                with np.load(
                    publication.path / frame["arrays"], allow_pickle=False
                ) as arrays:
                    points = owner.reconstruct_metric(
                        arrays["depth"],
                        arrays["valid"],
                        Calibration(**frame["calibration"]),
                        estimated,
                    )
                relative = f"output/predictions/surface/{index}.npy"
                path = publication.path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                np.save(path, points, allow_pickle=False)
                shards.append(
                    {
                        "frame_id": frame["frame_id"],
                        "points": relative,
                        "point_count": len(points),
                        "world_id": estimated.world_id,
                        "segment_id": estimated.segment_id,
                        "units": "metres",
                    }
                )
            output: SurfaceOutput = {
                "shards": shards,
                "coverage": "observed_points_only; unseen space unknown",
            }
            # Export this layer's predictions before returning downstream data.
            write_json(publication.path / artifact, output)
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        return failed_step(state.name, error), None
    return StepResult(state.name, "complete", "Method outputs saved", artifact), output
