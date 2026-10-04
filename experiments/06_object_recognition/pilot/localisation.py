"""Observed surface locations from original image boxes, not inferred object centres."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from experiments.shared.contracts import Pose
from experiments.shared.geometry import backproject, transform_points


@dataclass(frozen=True)
class Detection:
    xyxy: tuple[float, float, float, float]
    label: str
    class_id: int
    confidence: float

    def __post_init__(self) -> None:
        values = np.asarray(self.xyxy, dtype=float)
        if (
            values.shape != (4,)
            or not np.isfinite(values).all()
            or values[2] <= values[0]
            or values[3] <= values[1]
            or not isinstance(self.label, str)
            or not self.label.strip()
            or isinstance(self.class_id, bool)
            or not isinstance(self.class_id, int)
            or self.class_id < 0
            or not np.isfinite(self.confidence)
            or not 0 <= self.confidence <= 1
        ):
            raise ValueError(
                "Detection needs finite xyxy, class and confidence in [0,1]"
            )


def box_support(frame: Any, detection: Detection) -> np.ndarray:
    """Select pixels by their centres; retain only the reader's valid measured depth."""
    x1, y1, x2, y2 = detection.xyxy
    width, height = frame.calibration.width, frame.calibration.height
    if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
        raise ValueError("Box must use original image pixels within calibrated extent")
    v, u = np.indices((height, width))
    return (u + 0.5 >= x1) & (u + 0.5 < x2) & (v + 0.5 >= y1) & (v + 0.5 < y2)


def localise_detection(frame: Any, detection: Detection, pose: Pose | None) -> dict:
    support = box_support(frame, detection)
    points, pixels = backproject(frame.depth, frame.valid & support, frame.calibration)
    result = {
        "status": "no_valid_depth",
        "box_pixel_count": int(support.sum()),
        "valid_pixel_count": len(points),
        "valid_fraction": float(len(points) / support.sum()) if support.any() else None,
        "world_id": pose.world_id if pose else None,
        "segment_id": pose.segment_id if pose else None,
        "pose_source": pose.source if pose else None,
        "units": "metres",
        "box_median": None,
        "centre_sample": None,
        "depth_range_m": None,
        "caveat": "Box support is not a foreground mask; locations are observed surface samples.",
    }
    if not len(points):
        return result
    x1, y1, x2, y2 = detection.xyxy
    centre = np.array([(y1 + y2) / 2, (x1 + x2) / 2])
    distances = np.linalg.norm(pixels + 0.5 - centre, axis=1)
    chosen = int(np.argmin(distances))
    median = np.median(points, axis=0)
    world = (
        transform_points(np.stack([median, points[chosen]]), pose.matrix)
        if pose
        else None
    )
    return {
        **result,
        "status": "located" if pose else "camera_only",
        "box_median": {
            "camera_m": median.tolist(),
            "world_m": world[0].tolist() if world is not None else None,
            "definition": "coordinate-wise camera median, then camera-to-world transform",
        },
        "centre_sample": {
            "camera_m": points[chosen].tolist(),
            "world_m": world[1].tolist() if world is not None else None,
            "pixel_vu": pixels[chosen].tolist(),
            "offset_from_centre_px": float(distances[chosen]),
            "depth_m": float(points[chosen, 2]),
        },
        "depth_range_m": [float(points[:, 2].min()), float(points[:, 2].max())],
    }
