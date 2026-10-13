"""Metric and explicitly reference-aligned shape scores for depth maps."""

from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import (
    DepthConvention,
    align_shape_to_metric,
    alignment_fit_pixels,
    apply_native_alignment,
    fit_native_alignment,
)

DISTANCE_BANDS_M = (("0-1m", 0.0, 1.0), ("1-2m", 1.0, 2.0), ("2-4m", 2.0, 4.0))


def score_depth(
    predicted_depth_m: ArrayLike,
    predicted_valid: ArrayLike,
    reference_depth_m: ArrayLike,
    reference_valid: ArrayLike,
) -> dict[str, Any]:
    """Score raw, unaligned metric predictions against valid reference depth."""
    return {
        "view": "metric",
        **_score_arrays(
            predicted_depth_m, predicted_valid, reference_depth_m, reference_valid
        ),
    }


def score_shape_to_metric(
    raw_depth: ArrayLike,
    convention: DepthConvention,
    reference_depth_m: ArrayLike,
    reference_valid: ArrayLike,
) -> dict[str, Any]:
    """Score a per-frame reference-aligned shape diagnostic, never a metric result."""
    aligned_depth_m, aligned_valid, non_positive_aligned_fraction = align_shape_to_metric(
        raw_depth, convention, reference_depth_m, reference_valid
    )
    return {
        "view": "reference_aligned_shape",
        **_score_arrays(
            aligned_depth_m, aligned_valid, reference_depth_m, reference_valid
        ),
        "non_positive_aligned_fraction": non_positive_aligned_fraction,
    }


def score_sparse_fit(
    raw_depth: ArrayLike,
    convention: DepthConvention,
    reference_depth_m: ArrayLike,
    reference_valid: ArrayLike,
    fit_mask: ArrayLike,
    *,
    scale_only: bool = False,
) -> dict[str, Any]:
    """Fit scale from the fit_mask pixels only, then score every valid reference pixel.

    This models a phone that knows the true distance at a few points (for example ARCore
    depth or tracked features). The fit pixels come from the reference, so the score is
    still reference-assisted; it is not an independent metric result.
    """
    eligible = alignment_fit_pixels(raw_depth, convention, reference_depth_m, reference_valid)
    mask = np.asarray(fit_mask)
    if mask.shape != eligible.shape or mask.dtype != np.bool_:
        raise ValueError("Fit mask must be boolean and match the image grid")
    if np.any(mask & ~eligible):
        raise ValueError("Fit pixels must lie on valid reference and prediction pixels")
    scale, shift = fit_native_alignment(
        raw_depth, convention, reference_depth_m, mask, scale_only=scale_only
    )
    aligned_depth_m = apply_native_alignment(raw_depth, convention, scale, shift)
    aligned_valid = eligible & np.isfinite(aligned_depth_m) & (aligned_depth_m > 0)
    return {
        "view": "sparse_point_fit",
        **_score_arrays(
            np.where(aligned_valid, aligned_depth_m, np.nan),
            aligned_valid,
            reference_depth_m,
            reference_valid,
        ),
        "fit_pixels": int(np.count_nonzero(mask)),
        "scale_only": scale_only,
        "native_scale": scale,
        "native_shift": shift,
    }


def _score_arrays(
    predicted_depth_m: ArrayLike,
    predicted_valid: ArrayLike,
    reference_depth_m: ArrayLike,
    reference_valid: ArrayLike,
) -> dict[str, Any]:
    predicted = np.asarray(predicted_depth_m, dtype=np.float64)
    predicted_mask = np.asarray(predicted_valid)
    reference = np.asarray(reference_depth_m, dtype=np.float64)
    reference_mask = np.asarray(reference_valid)
    if predicted.ndim != 2 or predicted.shape != reference.shape:
        raise ValueError("Prediction and reference image grids must match")
    if predicted_mask.shape != predicted.shape or predicted_mask.dtype != np.bool_:
        raise ValueError("Prediction validity mask must be boolean and match the image grid")
    if reference_mask.shape != reference.shape or reference_mask.dtype != np.bool_:
        raise ValueError("Reference validity mask must be boolean and match the image grid")

    valid_reference = reference_mask & np.isfinite(reference) & (reference > 0)
    valid_prediction = predicted_mask & np.isfinite(predicted) & (predicted > 0)
    scored = valid_reference & valid_prediction
    return {
        "overall": _score_region(predicted, reference, valid_reference, scored),
        "distance_bands": {
            name: _score_region(
                predicted,
                reference,
                valid_reference & (reference >= lower) & (reference < upper if upper < 4.0 else reference <= upper),
                scored & (reference >= lower) & (reference < upper if upper < 4.0 else reference <= upper),
            )
            for name, lower, upper in DISTANCE_BANDS_M
        },
    }


def _score_region(
    predicted: NDArray[np.float64],
    reference: NDArray[np.float64],
    region_reference: NDArray[np.bool_],
    region_scored: NDArray[np.bool_],
) -> dict[str, float | int | None]:
    reference_pixels = int(np.count_nonzero(region_reference))
    scored_pixels = int(np.count_nonzero(region_scored))
    coverage = scored_pixels / reference_pixels if reference_pixels else 0.0
    if not scored_pixels:
        return {
            "abs_rel": None,
            "rmse_m": None,
            "delta1": None,
            "valid_coverage": coverage,
            "reference_pixels": reference_pixels,
            "scored_pixels": scored_pixels,
        }

    predicted_values = predicted[region_scored]
    reference_values = reference[region_scored]
    absolute_error = np.abs(predicted_values - reference_values)
    ratio = np.maximum(predicted_values / reference_values, reference_values / predicted_values)
    return {
        "abs_rel": float(np.mean(absolute_error / reference_values)),
        "rmse_m": float(np.sqrt(np.mean(np.square(absolute_error)))),
        "delta1": float(np.mean(ratio < 1.25)),
        "valid_coverage": coverage,
        "reference_pixels": reference_pixels,
        "scored_pixels": scored_pixels,
    }
