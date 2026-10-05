"""Pure original-pixel box validation and category-specific one-to-one scoring."""

import math
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore[import-untyped]


def box(value: Any, width: int, height: int) -> tuple[float, ...]:
    """Require finite nonempty xyxy within the original image grid."""
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("Box needs four coordinates")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in value
    ):
        raise ValueError("Box coordinates must be finite numbers")
    x1, y1, x2, y2 = map(float, value)
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError("Box exceeds original-pixel bounds or is empty")
    return x1, y1, x2, y2


def validate_predictions(
    rows: Any, width: int, height: int, classes: dict[str, str]
) -> None:
    """Reject invalid scores/classes while retaining every returned proposal."""
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Predictions must be objects in a list")
    for row in rows:
        box(row.get("xyxy"), width, height)
        class_id, confidence = row.get("class_id"), row.get("confidence")
        if (
            isinstance(class_id, bool)
            or not isinstance(class_id, int)
            or str(class_id) not in classes
            or not isinstance(row.get("label"), str)
            or not row["label"]
            or classes.get(str(class_id)) != row.get("label")
        ):
            raise ValueError("Prediction class and category disagree")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
        ):
            raise ValueError("Confidence must be finite in [0,1]")


def iou(first: list[float], second: list[float]) -> float:
    """Continuous rectangle area, no pixel-inclusive +1 convention."""
    intersection = max(0, min(first[2], second[2]) - max(first[0], second[0])) * max(
        0, min(first[3], second[3]) - max(first[1], second[1])
    )
    area = (first[2] - first[0]) * (first[3] - first[1]) + (second[2] - second[0]) * (
        second[3] - second[1]
    )
    return intersection / (area - intersection)


def _validate_scoring_rows(
    predictions: list[dict],
    references: list[dict],
    *,
    width: int = 640,
    height: int = 480,
) -> None:
    """Validate scoring helpers too, independently of production cache checks.

    Task18 frames are 640x480 (the default); other datasets pass their image size.
    """
    classes = {
        str(p.get("class_id")): p["label"]
        for p in predictions
        if isinstance(p, dict) and isinstance(p.get("label"), str)
    }
    validate_predictions(
        predictions, width, height, {**classes, "41": "cup", "62": "tv"}
    )
    if not isinstance(references, list) or any(
        not isinstance(r, dict) for r in references
    ):
        raise ValueError("References must be objects in a list")
    seen = set()
    for reference in references:
        box(reference.get("bbox_xyxy"), width, height)
        identity, category = reference.get("instance_id"), reference.get("category")
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError("Reference instance IDs must be nonempty and unique")
        if not isinstance(category, str) or not category:
            raise ValueError("Reference category must be a nonempty string")
        seen.add(identity)


def score_category(
    predictions: list[dict],
    references: list[dict],
    category: str,
    coverage: str,
    threshold: float,
    *,
    width: int = 640,
    height: int = 480,
) -> dict:
    """Maximise cardinality, then summed IoU; subset outputs have no FP/P/R."""
    if (
        isinstance(threshold, bool)
        or not math.isfinite(threshold)
        or not 0 < threshold <= 1
    ):
        raise ValueError("IoU threshold must be finite in (0,1]")
    if coverage not in {"complete", "subset"}:
        raise ValueError("Scoring requires complete or subset coverage")
    _validate_scoring_rows(predictions, references, width=width, height=height)
    ps = [(i, p) for i, p in enumerate(predictions) if p["label"] == category]
    rs = [(i, r) for i, r in enumerate(references) if r["category"] == category]
    candidates = [
        {"prediction_index": pi, "reference_index": ri, "iou": overlap}
        for pi, p in ps
        for ri, r in rs
        if (overlap := iou(p["xyxy"], r["bbox_xyxy"])) >= threshold
    ]
    matches = []
    if ps and rs:
        # A lost real match costs > the largest possible sum-IoU improvement.
        reward = min(len(ps), len(rs)) + 1
        costs = np.zeros((len(ps), len(rs) + len(ps)), dtype=float)
        costs[:, : len(rs)] = reward
        for row, (_, p) in enumerate(ps):
            for column, (_, r) in enumerate(rs):
                overlap = iou(p["xyxy"], r["bbox_xyxy"])
                if overlap >= threshold:
                    costs[row, column] = -reward - overlap
        rows, columns = linear_sum_assignment(costs)
        matches = [
            {
                "prediction_index": ps[row][0],
                "reference_index": rs[column][0],
                "iou": iou(ps[row][1]["xyxy"], rs[column][1]["bbox_xyxy"]),
            }
            for row, column in zip(rows, columns, strict=True)
            if column < len(rs) and costs[row, column] < 0
        ]
    matched_p = {m["prediction_index"] for m in matches}
    matched_r = {m["reference_index"] for m in matches}
    unmatched_p = [i for i, _ in ps if i not in matched_p]
    count = len(matches)
    return {
        "category": category,
        "coverage": coverage,
        "threshold": threshold,
        "matched": count,
        "missed": len(rs) - count,
        "prediction_count": len(ps),
        "reference_count": len(rs),
        "false_detections": len(ps) - count if coverage == "complete" else None,
        "precision": count / len(ps) if coverage == "complete" and ps else None,
        "recall": count / len(rs) if coverage == "complete" and rs else None,
        "matches": matches,
        "unmatched_predictions": unmatched_p,
        "unmatched_references": [i for i, _ in rs if i not in matched_r],
        "duplicate_candidates": [
            c
            for c in candidates
            if c["prediction_index"] in unmatched_p
            and c["reference_index"] in matched_r
        ],
        "candidates": candidates,
    }


def evaluate(
    frames: list[dict], proposals: list[dict], thresholds: tuple[float, ...]
) -> dict:
    """Account for every frame, including complete-coverage negative views."""
    if len(frames) != len(proposals):
        raise ValueError("Frame/proposal count mismatch")
    results = []
    for threshold in thresholds:
        rows = [
            {
                "frame_id": f["frame_id"],
                "source_selection_index": f["source_selection_index"],
                "categories": {
                    category: score_category(
                        p["proposals"],
                        f["labels"],
                        category,
                        f["label_coverage"][category],
                        threshold,
                    )
                    for category in ("cup", "tv")
                },
            }
            for f, p in zip(frames, proposals, strict=True)
        ]
        summary = {}
        for category in ("cup", "tv"):
            scored = [row["categories"][category] for row in rows]
            matched = sum(r["matched"] for r in scored)
            predictions = sum(r["prediction_count"] for r in scored)
            references = sum(r["reference_count"] for r in scored)
            complete = all(r["coverage"] == "complete" for r in scored)
            summary[category] = {
                "coverage": "complete" if complete else "subset",
                "matched": matched,
                "missed": references - matched,
                "prediction_count": predictions,
                "reference_count": references,
                "false_detections": predictions - matched if complete else None,
                "precision": (
                    matched / predictions if complete and predictions else None
                ),
                "recall": matched / references if complete and references else None,
            }
        results.append({"threshold": threshold, "summary": summary, "frames": rows})
    return {"frame_count": len(frames), "thresholds": results}
