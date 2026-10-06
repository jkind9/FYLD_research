"""Validate recorded Camera2 input and retain lightweight image handles."""

import importlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import cast

from experiments.shared.phone_session import read_phone_session
from experiments.shared.runs import Run, write_json

from ..config import Configuration
from ..records import StepResult, failed_step
from .artifacts import CaptureOutput, ImageArtifact


def run(
    publication: Run, config: Configuration, *, state: StepResult
) -> tuple[StepResult, CaptureOutput | None]:
    if state.status != "pending":
        return state, None
    artifact = "output/predictions/capture.json"
    try:
        with publication.measure("prediction_capture"):
            owner = importlib.import_module(
                "experiments.01_camera_capture_delivery.app.capture_report"
            )
            report = json.loads(config.report.read_text(encoding="utf-8"))
            frames = read_phone_session(
                report, config.bundle, owner.validate_phone_session_export
            )
            if not frames:
                raise ValueError("Capture contains no images")
            rows: list[ImageArtifact] = []
            # The existing reader owns encoded bytes. Decode only one image at a time later.
            for index, frame in enumerate(frames):
                suffix = Path(report["captures"][index]["file"]).suffix
                relative = f"input/images/{index}{suffix}"
                path = publication.path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(frame.image_bytes)
                row = asdict(frame)
                row.pop("image_bytes")
                row.pop("depth_bytes")
                rows.append(cast(ImageArtifact, {**row, "image": relative}))
            write_json(publication.path / "input/capture_report.json", report)
            publication.set_processed_frames(len(rows))
            output: CaptureOutput = {
                "frames": rows,
                "depth": "unavailable",
                "pose": "unavailable",
            }
            # Export this layer's predictions before returning downstream data.
            write_json(publication.path / artifact, output)
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        return failed_step(state.name, error), None
    return StepResult(state.name, "complete", "Method outputs saved", artifact), output
