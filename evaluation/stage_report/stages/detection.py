"""Detection stage: Task18 one-to-one matching, every method and threshold."""

from pathlib import Path

from experiments.evaluation import schema
from experiments.evaluation.stages.common import (
    file_sha256,
    owner,
    read_json,
    require_same,
    scope,
    verified_run,
)

SCORING = "experiments.06_object_recognition.experiments.01_detection.scoring"
EMPTY = "empty_prediction_software_control"
THRESHOLDS = (0.3, 0.5, 0.7)
COUNTS = (
    ("matched", "higher", "reference_count"),
    ("missed", "lower", "reference_count"),
    ("false_detections", "lower", "prediction_count"),
)
RATES = (
    ("precision", "higher", "prediction_count"),
    ("recall", "higher", "reference_count"),
)


def _reason(summary: dict, key: str) -> str | None:
    if summary[key] is not None:
        return None
    if summary["coverage"] == "subset":
        return "labels cover only selected positives; not scorable"
    return f"empty denominator ({key})"


def _measures(method: str, result: dict) -> list[dict]:
    measures = []
    for block in result["thresholds"]:
        threshold = block["threshold"]
        for category, summary in sorted(block["summary"].items()):
            for key, better, samples in COUNTS + RATES:
                measures.append(
                    schema.measure(
                        method,
                        f"{category}.{key}@iou{threshold}",
                        summary[key],
                        "count" if (key, better, samples) in COUNTS else "fraction",
                        samples=summary[samples],
                        coverage=summary["coverage"],
                        better=better,
                        reason=_reason(summary, key),
                    )
                )
    return measures


def _rows(method: str, result: dict) -> list[dict]:
    return [
        {
            "method": method,
            "threshold": block["threshold"],
            "frame_id": frame["frame_id"],
            "category": category,
            **{k: scored[k] for k in ("matched", "missed", "false_detections")},
        }
        for block in result["thresholds"]
        for frame in block["frames"]
        for category, scored in sorted(frame["categories"].items())
    ]


def detection_section(
    run_path: Path,
    *,
    dataset: str,
    pinned_sha256: str | None = None,
    input_mode: str = "isolated",
    reference_kind: str = "provisional",
) -> dict:
    run_path = Path(run_path)
    run = verified_run(run_path, pinned_sha256)
    scoring = owner(SCORING)
    annotations = read_json(run_path / "input/annotations.json")
    frames = annotations["frames"]
    cached = read_json(run_path / "output/cached_proposals.json")["frames"]
    stored = read_json(run_path / "output/scores.json")
    measures, rows = [], []
    for method in sorted(stored):
        proposals = [{"proposals": []} for _ in frames] if method == EMPTY else cached
        result = scoring.evaluate(frames, proposals, THRESHOLDS)
        require_same(stored[method], result, f"detection {method}")
        measures += _measures(method, result)
        rows += _rows(method, result)
    return schema.section(
        "detection",
        run=run,
        dataset=dataset,
        reference={
            "id": "annotations.json",
            "version": str(annotations.get("name", "unnamed")),
            "sha256": file_sha256(run_path / "input/annotations.json"),
            "kind": reference_kind,
        },
        input_mode=input_mode,
        scope=scope([frame["frame_id"] for frame in frames]),
        measures=measures,
        rows=rows,
    )
