"""Task54 owns real depth. Test providers run only in labelled controls."""

from dataclasses import asdict

import numpy as np

from experiments.shared.contracts import Calibration
from experiments.shared.geometry import backproject
from experiments.shared.runs import Run, write_json

from ..config import Configuration
from ..records import StepResult, Unavailable, failed_step
from .artifacts import (
    CaptureOutput,
    DepthArtifact,
    DepthOutput,
    DepthProvider,
    ImageArtifact,
)


def calibration(row: ImageArtifact) -> Calibration:
    if not row["geometry_ready"] or row["rotation_degrees"] != 0:
        raise ValueError("Unsupported phone calibration grid or image rotation")
    if row["lens_distortion"] is None or any(row["lens_distortion"]):
        raise ValueError("Pinhole adapters require explicitly zero lens distortion")
    fx, fy, cx, cy, skew = row["intrinsics"][:5]
    if skew != 0:
        raise ValueError("Pinhole adapters do not support skew")
    expected = (0, 0, row["image_width"], row["image_height"])
    if (
        tuple(row["crop_region"]) != expected
        or tuple(row["pre_correction_active_array_rect"]) != expected
        or tuple(row["sensor_to_image_crop_scale"]) != (1.0, 1.0)
        or row["intrinsics_pixel_grid"] != "pre_correction_active_array"
    ):
        raise ValueError(
            "Cropped or resized phone calibration requires an owning-method grid conversion"
        )
    return Calibration(
        row["image_width"],
        row["image_height"],
        fx,
        fy,
        cx,
        cy,
        "x-right_y-down_z-forward",
    )


def run(
    publication: Run,
    capture: CaptureOutput | None,
    config: Configuration,
    *,
    state: StepResult,
    test_provider: DepthProvider | None = None,
) -> tuple[StepResult, DepthOutput | None]:
    if state.status != "pending":
        return state, None
    artifact = "output/predictions/depth.json"
    try:
        with publication.measure("prediction_depth"):
            if capture is None:
                raise ValueError("Required upstream predictions are missing")
            if test_provider is None:
                raise Unavailable(
                    "Task54 real metric depth implementation is unavailable"
                )
            if not config.software_control:
                raise ValueError("Test depth providers require software_control=True")
            rows: list[DepthArtifact] = []
            for index, row in enumerate(capture["frames"]):
                camera = calibration(row)
                depth, valid = test_provider(row, camera)
                backproject(depth, valid, camera)
                relative = f"output/predictions/depth/{index}.npz"
                path = publication.path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                np.savez(path, depth=depth, valid=valid)
                rows.append(
                    {
                        "frame_id": row["frame_id"],
                        "arrays": relative,
                        "calibration": asdict(camera),
                        "source": "deterministic_test_provider",
                        "depth_definition": "camera_axis_z_metres",
                    }
                )
            output: DepthOutput = {"frames": rows, "software_control": True}
            # Export this layer's predictions before returning downstream data.
            write_json(publication.path / artifact, output)
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        return failed_step(state.name, error), None
    return StepResult(state.name, "complete", "Method outputs saved", artifact), output
