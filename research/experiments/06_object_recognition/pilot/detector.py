"""Explicitly acquired local weights; original-pixel outputs and explicit device."""

import json
from pathlib import Path

from experiments.datasets.acquisition import sha256

from .localisation import Detection

# Measured official checkpoint receipt; other models need their own protocol.
CHECKPOINT_SHA256 = "9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92"

PREDICT_SETTINGS = {
    "imgsz": 640,
    "conf": 0.25,
    "iou": 0.7,
    "max_det": 300,
    "batch": 1,
    "augment": False,
    "rect": True,
    "half": False,
    "save": False,
    "verbose": False,
}


class YoloDetector:
    def __init__(self, checkpoint: Path, device: str) -> None:
        if (
            not checkpoint.is_file()
            or checkpoint.is_symlink()
            or checkpoint.suffix != ".pt"
        ):
            raise ValueError(
                "Supply an already acquired regular .pt checkpoint; no automatic download"
            )
        if device not in {"cpu", "0"}:
            raise ValueError("Explicit device must be cpu or authorised GPU 0")
        # Ultralytics strips apostrophes and renames legacy basenames on loading.
        resolved = str(checkpoint.resolve())
        if (
            checkpoint.name != "yolo26x.pt"
            or "'" in resolved
            or "yolov3" in resolved
            or "yolov5" in resolved
            or sha256(checkpoint) != CHECKPOINT_SHA256
        ):
            raise ValueError("This pilot requires the verified YOLO26x checkpoint")
        from ultralytics import YOLO

        self.model = YOLO(resolved, task="detect")
        self.device = device

    def predict(self, image: Path) -> tuple[list[Detection], dict]:
        results = self.model.predict(str(image), device=self.device, **PREDICT_SETTINGS)
        if len(results) != 1:
            raise ValueError("Single-frame pilot requires exactly one result")
        result = results[0]
        boxes = result.boxes
        if boxes is None:
            raise ValueError("Detector did not return a boxes container")
        if result.names.get(41) != "cup":
            raise ValueError("Detector class 41 must mean cup in this pilot")
        detections = [
            Detection(
                tuple(map(float, xyxy)),
                result.names[int(class_id)],
                int(class_id),
                float(score),
            )
            for xyxy, class_id, score in zip(
                boxes.xyxy.cpu().tolist(),
                boxes.cls.cpu().tolist(),
                boxes.conf.cpu().tolist(),
                strict=True,
            )
        ]
        metadata = {
            "image_shape_hw": list(result.orig_shape),
            "speed_ms": result.speed,
            "effective_arguments": json.loads(
                json.dumps(vars(self.model.predictor.args), default=str)
            ),
            "actual_device": str(self.model.predictor.model.device),
            "actual_fp16": bool(self.model.predictor.model.fp16),
            "class_names": result.names,
        }
        return detections, metadata
