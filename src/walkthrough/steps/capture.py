"""Read recorded RGB images and preserve their source metadata."""

import hashlib
import importlib
import io
import json
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from experiments.shared.contracts import Calibration
from experiments.shared.phone_session import read_phone_session
from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .contracts import (
    CaptureOutput,
    ColourFrame,
    ImageArtifact,
    MethodChoice,
    method_label,
)

phone_report = importlib.import_module("experiments.01_camera_capture_delivery.app.capture_report")
pose_dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")


class CaptureSource(MethodChoice, Protocol):
    def read(self, run_context: Run) -> list[ImageArtifact]: ...
    def withheld_inputs(self) -> dict[str, str]: ...


@dataclass(frozen=True)
class PhoneExport:
    """Read experiment 01's phone capture report and image bundle."""

    report: Path
    bundle: Path
    name: str = field(default="phone_export", init=False)
    control: str | None = field(default=None, init=False)

    def read(self, run_context: Run) -> list[ImageArtifact]:
        report = json.loads(self.report.read_text(encoding="utf-8"))
        phone_frames = read_phone_session(report, self.bundle, phone_report.validate_phone_session_export)
        frames: list[ImageArtifact] = []
        for index, frame in enumerate(phone_frames):
            image_path = _save_image(
                run_context,
                Path(report["captures"][index]["file"]),
                frame.image_bytes,
                index,
            )
            phone_grid = {
                name: getattr(frame, name)
                for name in (
                    "geometry_ready",
                    "rotation_degrees",
                    "lens_distortion",
                    "intrinsics",
                    "intrinsics_pixel_grid",
                    "crop_region",
                    "pre_correction_active_array_rect",
                    "sensor_to_image_crop_scale",
                )
            }
            frames.append(
                {
                    "frame_id": frame.frame_id,
                    "source_id": frame.camera_id,
                    "source_frame_id": frame.frame_id,
                    "source_frame_index": frame.frame_number,
                    "image": image_path,
                    "image_width": frame.image_width,
                    "image_height": frame.image_height,
                    "source_sha256": hashlib.sha256(frame.image_bytes).hexdigest(),
                    "timestamp_s": frame.timestamp_ns / 1_000_000_000,
                    "timestamp_source": frame.timestamp_source,
                    "calibration": None,
                    "calibration_source": None,
                    "phone_grid": phone_grid,
                }
            )
        write_json(run_context.path / "input/capture_report.json", report)
        return frames

    def withheld_inputs(self) -> dict[str, str]:
        return {
            "depth": "The phone export reader supplies RGB only; depth methods must estimate it",
            "pose": "The phone export reader supplies no camera poses; tracking must estimate poses",
        }


@dataclass(frozen=True)
class TumSequence:
    """Read RGB inputs with experiment 03's TUM table and calibration."""

    root: Path
    name: str = field(default="tum_sequence", init=False)
    control: str | None = field(default=None, init=False)

    def read(self, run_context: Run) -> list[ImageArtifact]:
        frames: list[ImageArtifact] = []
        for index, (timestamp_s, relative_source) in enumerate(pose_dataset.read_table(self.root / "rgb.txt")):
            source_path = self.root / relative_source
            if source_path.is_symlink() or not source_path.resolve().is_relative_to(self.root.resolve()):
                raise ValueError("TUM RGB path must stay inside the selected dataset")
            image_bytes = source_path.read_bytes()
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.format != "PNG" or image.mode != "RGB":
                    raise ValueError("TUM RGB frames must be RGB PNG images")
                width, height = image.size
            if (width, height) != (
                pose_dataset.CALIBRATION.width,
                pose_dataset.CALIBRATION.height,
            ):
                raise ValueError("TUM RGB image does not match its declared calibration")
            frames.append(
                {
                    "frame_id": Path(relative_source).as_posix(),
                    "source_id": self.root.name,
                    "source_frame_id": Path(relative_source).as_posix(),
                    "source_frame_index": index,
                    "image": _save_image(run_context, source_path, image_bytes, index),
                    "image_width": width,
                    "image_height": height,
                    "source_sha256": hashlib.sha256(image_bytes).hexdigest(),
                    "timestamp_s": timestamp_s,
                    "timestamp_source": "rgb.txt",
                    "calibration": asdict(pose_dataset.CALIBRATION),
                    "calibration_source": "TUM RGB-D tracking reader",
                    "phone_grid": None,
                }
            )
        write_json(
            run_context.path / "input/source.json",
            {
                "kind": "tum_rgb_sequence",
                "source": str(self.root),
                "rgb_table_sha256": hashlib.sha256((self.root / "rgb.txt").read_bytes()).hexdigest(),
                "frames": [
                    {
                        key: row[key]
                        for key in (
                            "source_frame_index",
                            "source_frame_id",
                            "timestamp_s",
                        )
                    }
                    for row in frames
                ],
            },
        )
        return frames

    def withheld_inputs(self) -> dict[str, str]:
        return {
            "depth": "depth/ is a scoring reference; depth methods must estimate it",
            "pose": "groundtruth.txt is a scoring reference; tracking must estimate poses",
        }


def _save_image(run_context: Run, source_path: Path, image_bytes: bytes, index: int) -> str:
    relative = f"input/images/{index:06d}{source_path.suffix.lower() or '.png'}"
    destination = run_context.path / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(image_bytes)
    return relative


def run(run_context: Run, source: CaptureSource) -> tuple[StepResult, CaptureOutput | None]:
    artifact = "output/predictions/capture.json"
    try:
        with run_context.measure("load_capture"):
            (run_context.path / "input/images").mkdir(parents=True, exist_ok=True)
        with run_context.measure("prediction_capture"):
            output: CaptureOutput = {
                "methods": {"input": method_label(source)},
                "frames": source.read(run_context),
                "withheld_from_methods": source.withheld_inputs(),
            }
            validate(output)
            write_json(run_context.path / artifact, output)
            run_context.set_processed_frames(len(output["frames"]))
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("capture", error, source.name), None
    step = StepResult("capture", "complete", "Input images saved", source.name, len(output["frames"]), artifact)
    return step, output


def validate(output: CaptureOutput) -> None:
    if not output["frames"]:
        raise ValueError("Capture must return at least one saved frame")
    identities = [frame["frame_id"] for frame in output["frames"]]
    if len(set(identities)) != len(identities):
        raise ValueError("Capture frame identities must be unique")
    if not output["withheld_from_methods"] or not all(output["withheld_from_methods"].values()):
        raise ValueError("Capture must explain inputs withheld from methods")
    for frame in output["frames"]:
        if not frame["source_sha256"] or not frame["source_frame_id"]:
            raise ValueError("Each saved image needs its source identity and hash")


def calibration_for(row: ImageArtifact) -> Calibration:
    if row["calibration"] is not None:
        return Calibration(**row["calibration"])
    grid = row["phone_grid"]
    if grid is None or not grid["geometry_ready"]:
        raise Unavailable("Input source does not provide usable camera calibration")
    if grid["rotation_degrees"] != 0:
        raise ValueError("Unsupported phone calibration grid or image rotation")
    if grid["lens_distortion"] is None or any(grid["lens_distortion"]):
        raise ValueError("Pinhole adapters require explicitly zero lens distortion")
    fx, fy, cx, cy, skew = grid["intrinsics"][:5]
    if skew != 0:
        raise ValueError("Pinhole adapters do not support skew")
    expected = (0, 0, row["image_width"], row["image_height"])
    if (
        tuple(grid["crop_region"]) != expected
        or tuple(grid["pre_correction_active_array_rect"]) != expected
        or tuple(grid["sensor_to_image_crop_scale"]) != (1.0, 1.0)
        or grid["intrinsics_pixel_grid"] != "pre_correction_active_array"
    ):
        raise ValueError("Cropped phone calibration needs an owning-method grid conversion")
    return Calibration(
        row["image_width"],
        row["image_height"],
        fx,
        fy,
        cx,
        cy,
        "x-right_y-down_z-forward",
    )


def saved_colour_frames(run_path: Path, capture: CaptureOutput) -> Iterator[ColourFrame]:
    for row in capture["frames"]:
        with Image.open(run_path / row["image"]) as image:
            colour = np.asarray(image.convert("RGB"))
        yield ColourFrame(row["frame_id"], row["timestamp_s"], calibration_for(row), colour)
