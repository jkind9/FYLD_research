"""Depth methods consume all colour frames and yield calibrated metric grids."""

import importlib
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Protocol

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
# Experiment 02 owns the ZipDepth adapter and the tested sparse-point scale fit.
zipdepth_owner = importlib.import_module("experiments.02_stereo_depth.zipdepth")
depth_geometry = importlib.import_module("experiments.02_stereo_depth.geometry")
sparse_points = importlib.import_module("experiments.02_stereo_depth.sparse_scale")
ZIPDEPTH_CONVENTION = "relative_inverse_depth"


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


@dataclass(frozen=True)
class DepthAnythingV2Metric:
    """Load an already-acquired indoor Small checkpoint without network access.

    Its output is in metres but biased: on TUM indoor frames it reads 1.34-1.41x too far,
    and the factor varies 0.86-2.09 between frames (experiments/02_stereo_depth/README.md).
    Downstream measurements need a per-frame scale source; this adapter applies none.
    """

    checkpoint: Path
    device: str = "cuda"
    max_depth_m: float = 20.0
    name: str = field(default="depth_anything_v2_metric_indoor_small", init=False)
    control: str | None = field(default=None, init=False)
    output_convention: str = field(default="metric_depth", init=False)

    def __post_init__(self) -> None:
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("Depth Anything V2 device must be cpu or cuda")
        if not np.isfinite(self.max_depth_m) or self.max_depth_m <= 0:
            raise ValueError("Depth Anything V2 maximum depth must be positive and finite")

    def load(self) -> DepthEstimator:
        if not self.checkpoint.is_dir():
            raise FileNotFoundError(
                f"Local model checkpoint directory not found: {self.checkpoint}"
            )

        import torch
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation

        processor = AutoImageProcessor.from_pretrained(
            self.checkpoint, local_files_only=True
        )
        model = AutoModelForDepthEstimation.from_pretrained(
            self.checkpoint, local_files_only=True
        )
        model = model.to(self.device).eval()
        return partial(
            _predict_metric_depth,
            processor=processor,
            model=model,
            torch=torch,
            device=self.device,
            max_depth_m=self.max_depth_m,
        )


def _predict_metric_depth(
    frames: Iterator[ColourFrame],
    *,
    run: Run,
    processor: Any,
    model: Any,
    torch: Any,
    device: str,
    max_depth_m: float = 20.0,
) -> Iterator[DepthPrediction]:
    """Predict metric camera-axis depth using RGB input alone."""
    del run  # Timing is measured by the owning depth layer.
    for frame in frames:
        image = Image.fromarray(frame.colour, mode="RGB")
        inputs = processor(images=image, return_tensors="pt")
        inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
        with torch.inference_mode():
            predicted = model(**inputs).predicted_depth
            prediction = torch.nn.functional.interpolate(
                predicted.unsqueeze(1),
                size=frame.colour.shape[:2],
                mode="bicubic",
                align_corners=False,
            )[0, 0]
        depth, valid = depth_metres(prediction.detach().cpu().numpy(), units_per_metre=1)
        valid &= depth <= max_depth_m
        depth = np.where(valid, depth, np.nan)
        yield DepthPrediction(frame.frame_id, depth, valid)


@dataclass(frozen=True)
class ScaledZipDepth:
    """ZipDepth's phone build, scaled each frame from a few recorded depth pixels.

    ZipDepth gives inverse depth up to an unknown scale and shift. Each frame, this fits
    them from `points_per_frame` random pixels of the recorded TUM depth, which stands in
    for the few known distances a phone will supply (ARCore depth or tracked points). The
    recorded depth is a reference answer, so the run is a labelled reference control.
    """

    checkpoint: Path
    reference_root: Path
    points_per_frame: int = 50
    seed: int = 0
    device: str = "cpu"
    max_depth_m: float = 20.0
    name: str = field(default="zipdepth_scaled_by_recorded_points", init=False)
    control: str = field(default="reference", init=False)

    def __post_init__(self) -> None:
        if type(self.points_per_frame) is not int or self.points_per_frame < 2:
            raise ValueError("points_per_frame must be an integer of at least 2")
        if not np.isfinite(self.max_depth_m) or self.max_depth_m <= 0:
            raise ValueError("Scaled ZipDepth maximum depth must be positive and finite")

    def load(self) -> DepthEstimator:
        try:
            predict_inverse_depth = zipdepth_owner.ZipDepth(
                self.checkpoint, build="npu", device=self.device
            ).load()
        except ModuleNotFoundError as error:
            if (error.name or "").split(".")[0] == "zipdepth":
                raise Unavailable(
                    "ZipDepth code is not importable; add data/models/ZipDepth to PYTHONPATH"
                ) from error
            raise Unavailable(
                f"ZipDepth needs the Python package {error.name!r}; "
                "install experiments/02_stereo_depth/requirements-task54-host.txt"
            ) from error
        read_recorded = RecordedSensorDepth(self.reference_root).load()
        return partial(
            _predict_scaled_zipdepth,
            predict_inverse_depth=predict_inverse_depth,
            read_recorded=read_recorded,
            settings=self,
        )


def _predict_scaled_zipdepth(
    frames: Iterator[ColourFrame],
    *,
    run: Run,
    predict_inverse_depth: Any,
    read_recorded: DepthEstimator,
    settings: ScaledZipDepth,
) -> Iterator[DepthPrediction]:
    """One frame at a time: ZipDepth, the recorded depth, a sparse fit, then metres."""
    for index, frame in enumerate(frames):
        (relative,) = list(predict_inverse_depth(iter([frame]), run=run))
        (recorded,) = list(read_recorded(iter([frame]), run=run))
        eligible = depth_geometry.alignment_fit_pixels(
            relative.depth, ZIPDEPTH_CONVENTION, recorded.depth, recorded.valid
        )
        available = int(np.count_nonzero(eligible))
        if available < settings.points_per_frame:
            raise ValueError(
                f"{frame.frame_id}: only {available} pixels have both recorded and ZipDepth "
                f"depth; {settings.points_per_frame} needed"
            )
        fit_pixels = sparse_points.choose_fit_pixels(
            eligible, settings.points_per_frame, np.random.default_rng([settings.seed, index])
        )
        scale, shift = depth_geometry.fit_native_alignment(
            relative.depth, ZIPDEPTH_CONVENTION, recorded.depth, fit_pixels
        )
        if not scale > 0:
            raise ValueError(
                f"{frame.frame_id}: fitted inverse-depth scale {scale:g} is not positive"
            )
        metres = depth_geometry.apply_native_alignment(
            relative.depth, ZIPDEPTH_CONVENTION, scale, shift
        )
        valid = (
            relative.valid
            & np.isfinite(metres)
            & (metres > 0)
            & (metres <= settings.max_depth_m)
        )
        yield DepthPrediction(frame.frame_id, np.where(valid, metres, np.nan), valid)


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
                row: DepthArtifact = {
                    "frame_id": frame["frame_id"],
                    "arrays": relative,
                    "calibration": asdict(camera),
                    "source": method_label(method),
                    "depth_definition": "camera_axis_z_metres",
                }
                if prediction.diagnostics is not None:
                    row["method_diagnostics"] = plain_diagnostics(frame["frame_id"], prediction.diagnostics)
                rows.append(row)
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


def plain_diagnostics(frame_id: str, diagnostics: dict[str, Any]) -> dict[str, float | int | bool | None]:
    """Method diagnostics as plain JSON values; NaN, infinity or other types fail the frame."""
    plain: dict[str, float | int | bool | None] = {}
    for key, value in diagnostics.items():
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, float) and not np.isfinite(value):
            raise ValueError(f"{frame_id}: depth diagnostic {key!r} is not finite ({value})")
        if value is not None and not isinstance(value, (bool, int, float)):
            raise ValueError(f"{frame_id}: depth diagnostic {key!r} must be a number, boolean or None")
        plain[str(key)] = value
    return plain


def validate(capture: CaptureOutput, output: DepthOutput) -> None:
    if [row["frame_id"] for row in capture["frames"]] != [row["frame_id"] for row in output["frames"]]:
        raise ValueError("Depth output frame identities must match capture")
