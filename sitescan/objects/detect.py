"""Object boxes on RGB arrays from the YOLO26x COCO detector."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import numpy as np

# The official YOLO26x checkpoint the counting results were measured with.
CHECKPOINT_SHA256 = "9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92"

SETTINGS = {
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


@dataclass(frozen=True)
class Detection:
    """One box in original image pixels, with its COCO class and score."""

    xyxy: tuple[float, float, float, float]
    label: str
    class_id: int
    confidence: float


def detect(image: np.ndarray, *, model, device: str) -> list[Detection]:
    """Boxes found in one RGB image."""
    # Ultralytics reads arrays as BGR, the order OpenCV decodes files in.
    [result] = model.predict(np.ascontiguousarray(image[..., ::-1]), device=device, **SETTINGS)
    boxes = result.boxes
    return [
        Detection(tuple(map(float, xyxy)), result.names[int(class_id)], int(class_id), float(score))
        for xyxy, class_id, score in zip(
            boxes.xyxy.cpu().tolist(), boxes.cls.cpu().tolist(), boxes.conf.cpu().tolist(), strict=True
        )
    ]


def load_detector(checkpoint: Path | str, *, device: str = "cpu") -> Callable[[np.ndarray], list[Detection]]:
    """An RGB-to-boxes callable, loading the verified local checkpoint once."""
    checkpoint = Path(checkpoint)
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Detector checkpoint not found: {checkpoint}")
    with checkpoint.open("rb") as weights:
        if hashlib.file_digest(weights, "sha256").hexdigest() != CHECKPOINT_SHA256:
            raise ValueError(f"{checkpoint} is not the YOLO26x checkpoint the counts were measured with")
    from ultralytics import YOLO

    return partial(detect, model=YOLO(str(checkpoint.resolve()), task="detect"), device=device)
