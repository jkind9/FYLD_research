"""Score saved depth predictions against selected TUM sensor references."""

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from .dataset import TumDepthSelection
from .geometry import DepthConvention, metric_depth
from .scoring import score_depth, score_shape_to_metric

_CONVENTIONS = {
    "metric_depth",
    "relative_depth",
    "relative_inverse_depth",
    "affine_invariant_log_depth",
}


def evaluate_predictions(
    selection: TumDepthSelection,
    predictions: Mapping[str, ArrayLike],
    convention: DepthConvention,
) -> dict[str, Any]:
    """Score prediction maps keyed by frame ID; this function never calls a model."""
    if convention not in _CONVENTIONS:
        raise ValueError(f"Unsupported depth convention: {convention}")
    selected_ids = {frame.frame_id for frame in selection.frames}
    prediction_ids = set(predictions)
    missing = selected_ids - prediction_ids
    extra = prediction_ids - selected_ids
    if missing or extra:
        raise ValueError(
            "Prediction frame IDs differ: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )

    metric_rows: list[dict[str, Any]] = []
    shape_rows: list[dict[str, Any]] = []
    for frame in selection.frames:
        raw_prediction = np.asarray(predictions[frame.frame_id])
        shape_score = score_shape_to_metric(
            raw_prediction,
            convention,
            frame.reference_depth_m,
            frame.reference_valid,
        )
        shape_rows.append({"frame_id": frame.frame_id, **shape_score})
        if convention == "metric_depth":
            predicted_m, predicted_valid = metric_depth(raw_prediction)
            metric_rows.append(
                {
                    "frame_id": frame.frame_id,
                    **score_depth(
                        predicted_m,
                        predicted_valid,
                        frame.reference_depth_m,
                        frame.reference_valid,
                    ),
                }
            )

    metric_view: dict[str, Any]
    if convention == "metric_depth":
        metric_view = {
            "available": True,
            "aggregate": aggregate_scores(metric_rows),
            "per_frame": metric_rows,
        }
    else:
        metric_view = {
            "available": False,
            "reason": (
                "Relative predictions have no metric scale before reference fitting."
            ),
            "aggregate": None,
            "per_frame": [],
        }
    return {
        "sequence": selection.sequence,
        "convention": convention,
        "sample_stride": selection.stride,
        "matched_pair_count": selection.matched_pair_count,
        "evaluated_frame_count": len(selection.frames),
        "frame_ids": [frame.frame_id for frame in selection.frames],
        "metric": metric_view,
        "reference_aligned_shape": {
            "aggregate": aggregate_scores(shape_rows),
            "per_frame": shape_rows,
        },
    }


def aggregate_scores(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Pool per-frame errors by scored pixels and coverage by reference pixels."""
    if not rows:
        return {"overall": _aggregate_region([]), "distance_bands": {}}
    region_names = tuple(rows[0]["distance_bands"])
    return {
        "view": rows[0]["view"],
        "overall": _aggregate_region([row["overall"] for row in rows]),
        "distance_bands": {
            name: _aggregate_region([row["distance_bands"][name] for row in rows])
            for name in region_names
        },
    }


def _aggregate_region(regions: Sequence[dict[str, Any]]) -> dict[str, Any]:
    reference_pixels = sum(region["reference_pixels"] for region in regions)
    scored_pixels = sum(region["scored_pixels"] for region in regions)
    result: dict[str, Any] = {
        "valid_coverage": scored_pixels / reference_pixels if reference_pixels else 0.0,
        "reference_pixels": reference_pixels,
        "scored_pixels": scored_pixels,
    }
    for metric in ("abs_rel", "rmse_m", "delta1"):
        valid = [region for region in regions if region[metric] is not None]
        weight_total = sum(region["scored_pixels"] for region in valid)
        if not weight_total:
            result[metric] = None
        elif metric == "rmse_m":
            result[metric] = float(
                np.sqrt(
                    sum(
                        region[metric] ** 2 * region["scored_pixels"]
                        for region in valid
                    )
                    / weight_total
                )
            )
        else:
            result[metric] = float(
                sum(region[metric] * region["scored_pixels"] for region in valid)
                / weight_total
            )
    return result
