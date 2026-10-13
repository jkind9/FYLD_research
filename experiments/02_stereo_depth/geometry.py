"""Output-convention conversion and reference alignment for depth scoring."""

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

DepthConvention = Literal[
    "metric_depth",
    "relative_depth",
    "relative_inverse_depth",
    "affine_invariant_log_depth",
]


def metric_depth(raw_depth_m: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Keep positive finite metric depth and mark every other pixel invalid."""
    depth_m = np.asarray(raw_depth_m, dtype=np.float64)
    if depth_m.ndim != 2:
        raise ValueError("Depth must be a two-dimensional image")
    valid = np.isfinite(depth_m) & (depth_m > 0)
    return np.where(valid, depth_m, np.nan), valid


_CONVENTIONS = (
    "metric_depth",
    "relative_depth",
    "relative_inverse_depth",
    "affine_invariant_log_depth",
)


def alignment_fit_pixels(
    raw_depth: ArrayLike,
    convention: DepthConvention,
    reference_depth_m: ArrayLike,
    reference_valid: ArrayLike,
) -> NDArray[np.bool_]:
    """Pixels where both the reference and the native prediction can enter a fit."""
    prediction = np.asarray(raw_depth, dtype=np.float64)
    reference = np.asarray(reference_depth_m, dtype=np.float64)
    reference_mask = np.asarray(reference_valid)
    if prediction.ndim != 2 or prediction.shape != reference.shape:
        raise ValueError("Prediction and reference image grids must match")
    if reference_mask.shape != reference.shape or reference_mask.dtype != np.bool_:
        raise ValueError("Reference validity mask must be boolean and match the image grid")
    if convention not in _CONVENTIONS:
        raise ValueError("Shape alignment requires a relative depth convention")

    valid_prediction = np.isfinite(prediction)
    if convention == "metric_depth":
        valid_prediction &= prediction > 0
    return reference_mask & np.isfinite(reference) & (reference > 0) & valid_prediction


def fit_native_alignment(
    raw_depth: ArrayLike,
    convention: DepthConvention,
    reference_depth_m: ArrayLike,
    fit_mask: ArrayLike,
    *,
    scale_only: bool = False,
) -> tuple[float, float]:
    """Least-squares scale and shift from fit_mask pixels, in the prediction's native space.

    Native space means metres for metric/relative depth, inverse metres for inverse depth
    and log metres for log depth. scale_only fits one factor through zero and is allowed
    only for metric depth, where it models correcting a biased metric model.
    """
    prediction = np.asarray(raw_depth, dtype=np.float64)
    reference = np.asarray(reference_depth_m, dtype=np.float64)
    mask = np.asarray(fit_mask)
    if mask.shape != prediction.shape or mask.dtype != np.bool_:
        raise ValueError("Fit mask must be boolean and match the image grid")
    if scale_only and convention != "metric_depth":
        raise ValueError("A scale-only fit is defined only for metric depth")
    if np.count_nonzero(mask) < 2:
        raise ValueError("At least two valid reference and prediction pixels are required")

    target = reference[mask]
    if convention == "affine_invariant_log_depth":
        target = np.log(target)
    elif convention == "relative_inverse_depth":
        target = 1.0 / target
    source = prediction[mask]
    if scale_only:
        return float(np.dot(source, target) / np.dot(source, source)), 0.0
    design = np.column_stack((source, np.ones(source.size)))
    scale, shift = np.linalg.lstsq(design, target, rcond=None)[0]
    return float(scale), float(shift)


def apply_native_alignment(
    raw_depth: ArrayLike, convention: DepthConvention, scale: float, shift: float
) -> NDArray[np.float64]:
    """Apply a native-space fit and convert to metres; non-finite results stay non-finite."""
    aligned_native = scale * np.asarray(raw_depth, dtype=np.float64) + shift
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        if convention == "affine_invariant_log_depth":
            return np.exp(aligned_native)
        if convention == "relative_inverse_depth":
            return 1.0 / aligned_native
    return aligned_native


def align_shape_to_metric(
    raw_depth: ArrayLike,
    convention: DepthConvention,
    reference_depth_m: ArrayLike,
    reference_valid: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.bool_], float]:
    """Fit a per-frame affine alignment, then return valid aligned depth in metres."""
    fit_valid = alignment_fit_pixels(raw_depth, convention, reference_depth_m, reference_valid)
    scale, shift = fit_native_alignment(raw_depth, convention, reference_depth_m, fit_valid)
    aligned_depth_m = apply_native_alignment(raw_depth, convention, scale, shift)

    aligned_valid = fit_valid & np.isfinite(aligned_depth_m) & (aligned_depth_m > 0)
    candidates = aligned_depth_m[fit_valid]
    non_positive_fraction = (
        float(np.count_nonzero(np.isfinite(candidates) & (candidates <= 0)) / candidates.size)
        if candidates.size
        else 0.0
    )
    return np.where(aligned_valid, aligned_depth_m, np.nan), aligned_valid, non_positive_fraction
