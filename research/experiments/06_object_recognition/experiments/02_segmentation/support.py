"""Measured camera coordinates of selected surfaces, without supplied poses."""

import numpy as np

from experiments.shared.contracts import Calibration
from experiments.shared.geometry import backproject

from .scoring import binary


def summarise(mask: np.ndarray, raw: np.ndarray, calibration: Calibration) -> dict:
    selected = binary(mask)
    if raw.shape != selected.shape or raw.dtype != np.uint16:
        raise ValueError("Expected matching unsigned16 encoded depth")
    depth = raw.astype(np.float64) / 5000
    valid = (depth > 0) & (depth < 4)
    points, _ = backproject(depth, valid & selected, calibration)
    return {
        "area_pixels": int(selected.sum()),
        "raw_valid_pixels": int((selected & (raw != 0)).sum()),
        "processed_valid_pixels": len(points),
        "camera_median_m": np.median(points, axis=0).tolist() if len(points) else None,
        "camera_iqr_m": (
            (
                np.quantile(points, 0.75, axis=0, method="linear")
                - np.quantile(points, 0.25, axis=0, method="linear")
            ).tolist()
            if len(points)
            else None
        ),
        "units": "metres",
        "definition": "coordinate-wise camera surface median; spread is descriptive, not calibrated uncertainty",
    }


def coordinate_difference(summary: dict, baseline: dict) -> list[float] | None:
    a, b = summary["camera_median_m"], baseline["camera_median_m"]
    return (
        (np.asarray(a) - np.asarray(b)).tolist()
        if a is not None and b is not None
        else None
    )
