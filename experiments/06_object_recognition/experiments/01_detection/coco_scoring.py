"""Task45 Part A scoring of one COCO image, and the summary across images.

Matching is Task18's `score_category` with the image's own size. Every matched
pair at the placement thresholds gets a placement row; every image, category
and threshold gets a hit/miss row, with crowd-absorbed detections counted
separately from false detections.
"""

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import spearmanr  # type: ignore[import-untyped]

from .coco import outline
from .placement import (
    background_and_coverage,
    clutter,
    crowd_ignored,
    placement,
    size_band,
    touches_edge,
)
from .scoring import box, score_category

THRESHOLDS = (0.3, 0.5, 0.7)
PLACEMENT_AT = (0.5, 0.3)


def valid_proposals(
    rows: list[dict], width: int, height: int
) -> tuple[list[dict], int]:
    """Keep proposals the scorer accepts; count, never hide, the rest."""
    kept, rejected = [], 0
    for row in rows:
        try:
            box(row["xyxy"], width, height)
        except ValueError:
            rejected += 1
            continue
        kept.append(row)
    return kept, rejected


def _outlines(record: dict) -> tuple[list, list]:
    width, height = record["width"], record["height"]
    references = [outline(r, width=width, height=height) for r in record["references"]]
    crowds = [outline(c, width=width, height=height) for c in record["crowds"]]
    return references, crowds


def _placement_row(
    record, prediction, reference, own, others, others_mask, threshold
) -> dict:
    width, height = record["width"], record["height"]
    return {
        "image_id": record["image_id"],
        "instance_id": reference["instance_id"],
        "category": reference["category"],
        "threshold": threshold,
        "confidence": prediction["confidence"],
        **placement(prediction["xyxy"], reference["bbox_xyxy"]),
        **background_and_coverage(prediction["xyxy"], reference["bbox_xyxy"], own),
        **clutter(
            reference["bbox_xyxy"], others, others_mask, width=width, height=height
        ),
        "size_band": size_band(reference["area"]),
        "truncated": touches_edge(reference["bbox_xyxy"], width=width, height=height),
    }


def score_image(
    record: dict,
    proposals: list[dict],
    *,
    thresholds: Sequence[float] = THRESHOLDS,
    placement_at: Sequence[float] = PLACEMENT_AT,
) -> dict:
    width, height = record["width"], record["height"]
    predictions, rejected = valid_proposals(proposals, width, height)
    references, crowds = record["references"], record["crowds"]
    reference_masks, crowd_masks = _outlines(record)
    covering = sum(
        (m.astype(np.uint16) for m in reference_masks + crowd_masks),
        np.zeros((height, width), dtype=np.uint16),
    )
    categories = sorted(
        {r["category"] for r in references} | {p["label"] for p in predictions}
    )
    counts, rows = [], []
    for threshold in thresholds:
        for category in categories:
            result = score_category(
                predictions,
                references,
                category,
                "complete",
                threshold,
                width=width,
                height=height,
            )
            unmatched = [predictions[i] for i in result["unmatched_predictions"]]
            same_class_crowds = [c for c in crowds if c["category"] == category]
            ignored = len(
                crowd_ignored(unmatched, same_class_crowds, threshold=threshold)
            )
            counts.append(
                {
                    "image_id": record["image_id"],
                    "category": category,
                    "threshold": threshold,
                    "matched": result["matched"],
                    "missed": result["missed"],
                    "false_detections": result["false_detections"] - ignored,
                    "ignored_crowd": ignored,
                    "references": result["reference_count"],
                    "predictions": result["prediction_count"],
                }
            )
            if threshold not in placement_at:
                continue
            for match in result["matches"]:
                index = match["reference_index"]
                own = reference_masks[index]
                others = [r for i, r in enumerate(references) if i != index] + crowds
                rows.append(
                    _placement_row(
                        record,
                        predictions[match["prediction_index"]],
                        references[index],
                        own,
                        others,
                        (covering - own.astype(np.uint16)) > 0,
                        threshold,
                    )
                )
    return {"counts": counts, "placement": rows, "rejected_proposals": rejected}


def _quantiles(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "median": None, "p10": None, "p90": None, "reason": "no values"}
    array = np.asarray(values, dtype=float)
    return {
        "n": len(values),
        "median": float(np.median(array)),
        "p10": float(np.percentile(array, 10)),
        "p90": float(np.percentile(array, 90)),
        "reason": None,
    }


def _rank_correlation(rows: list[dict], first: str, second: str) -> dict:
    pairs = [
        (r[first], r[second])
        for r in rows
        if r[first] is not None and r[second] is not None
    ]
    if len(pairs) < 3:
        return {"n": len(pairs), "spearman": None, "reason": "fewer than 3 pairs"}
    result = spearmanr([p[0] for p in pairs], [p[1] for p in pairs])
    rho = float(result.statistic)
    return {
        "n": len(pairs),
        "spearman": None if math.isnan(rho) else rho,
        "reason": None,
    }


MEASURES = (
    "iou",
    "centre_offset",
    "centre_offset_fraction",
    "excess_background",
    "outline_coverage",
    "width_ratio",
    "height_ratio",
)


def _group(rows: list[dict]) -> dict:
    return {m: _quantiles([r[m] for r in rows if r[m] is not None]) for m in MEASURES}


def summarise(counts: list[dict], rows: list[dict]) -> dict:
    summary: dict = {"hits": {}, "placement": {}}
    for threshold in sorted({c["threshold"] for c in counts}):
        chosen = [c for c in counts if c["threshold"] == threshold]
        totals = {
            k: sum(c[k] for c in chosen)
            for k in (
                "matched",
                "missed",
                "false_detections",
                "ignored_crowd",
                "references",
            )
        }
        detections = totals["matched"] + totals["false_detections"]
        totals["recall"] = (
            totals["matched"] / totals["references"] if totals["references"] else None
        )
        totals["precision"] = totals["matched"] / detections if detections else None
        summary["hits"][str(threshold)] = totals
    for threshold in sorted({r["threshold"] for r in rows}):
        chosen = [r for r in rows if r["threshold"] == threshold]
        clean = [r for r in chosen if not r["truncated"]]
        summary["placement"][str(threshold)] = {
            "all": _group(chosen),
            "not_truncated": _group(clean),
            "truncated": _group([r for r in chosen if r["truncated"]]),
            "by_size": {
                band: _group([r for r in clean if r["size_band"] == band])
                for band in ("small", "medium", "large")
            },
            "clutter": {
                f"{measure}~{driver}": _rank_correlation(clean, measure, driver)
                for measure in ("centre_offset_fraction", "excess_background", "iou")
                for driver in ("covered_by_others", "overlapping_objects")
            },
        }
    return summary
