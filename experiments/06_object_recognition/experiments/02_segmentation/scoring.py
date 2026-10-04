"""Synthetic-only overlap, boundary and instance-event software controls."""

import numpy as np
from scipy.ndimage import (  # type: ignore[import-untyped]
    binary_erosion,
    distance_transform_edt,
)


def binary(mask: np.ndarray) -> np.ndarray:
    if mask.ndim != 2 or mask.dtype != np.uint8 or not np.isin(mask, [0, 255]).all():
        raise ValueError("Expected uint8 binary mask 0/255")
    return mask != 0


def mask_scores(
    prediction: np.ndarray, reference: np.ndarray, *, synthetic: bool
) -> dict:
    a, b = binary(prediction), binary(reference)
    if a.shape != b.shape:
        raise ValueError("Mask dimensions differ")
    if not synthetic:
        return {
            "status": "unavailable_provisional_reference",
            "iou": None,
            "boundary_f1": None,
        }
    union = (a | b).sum()
    aa, bb = a & ~binary_erosion(a), b & ~binary_erosion(b)
    if not aa.any() or not bb.any():
        boundary = float(not aa.any() and not bb.any())
    else:
        precision = float((distance_transform_edt(~bb)[aa] <= 1).mean())
        recall = float((distance_transform_edt(~aa)[bb] <= 1).mean())
        boundary = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
    return {
        "status": "synthetic_control",
        "iou": float((a & b).sum() / union) if union else 1.0,
        "boundary_f1": boundary,
    }


def instance_events(
    predictions: list[np.ndarray], references: list[np.ndarray], *, synthetic: bool
) -> dict:
    if not synthetic:
        raise ValueError("Instance events require synthetic references")
    ps, rs = [binary(p) for p in predictions], [binary(r) for r in references]
    shapes = {p.shape for p in ps + rs}
    if len(shapes) > 1:
        raise ValueError("Mask dimensions differ")
    overlap = np.array([[np.any(p & r) for r in rs] for p in ps], bool).reshape(
        len(ps), len(rs)
    )
    return {
        "merges": int((overlap.sum(axis=1) > 1).sum()),
        "splits": int((overlap.sum(axis=0) > 1).sum()),
    }
