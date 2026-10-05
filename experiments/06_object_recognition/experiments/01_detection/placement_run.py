"""Task45 Part A: detect on COCO val2017 and score box placement against outlines.

Usage (detector environment, GPU only when no other process is using it):
    .venv-yolo/Scripts/python.exe -B -m \
        experiments.06_object_recognition.experiments.01_detection.placement_run \
        --data-root <checkout>/data --checkpoint <checkout>/checkpoints/yolo26x.pt

`--limit N` scores only the first N images (by image id) for a smoke check.
The detector sees only image pixels; outlines are read after detection.
"""

import argparse
import importlib
import json
import time
from pathlib import Path

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, write_json

from . import coco
from .coco_scoring import PLACEMENT_AT, THRESHOLDS, score_image, summarise

EXPECTED_CV2 = "5.0.0"
HYPERPARAMETERS = {
    "detector": {
        "value": "YOLO26x",
        "source": "inherited experiments/06_object_recognition/pilot/detector.py:11",
    },
    "predict_settings": {
        "value": "imgsz 640, conf 0.25, iou 0.7, max_det 300",
        "source": "inherited experiments/06_object_recognition/pilot/detector.py:13-24",
    },
    "matching_thresholds": {
        "value": list(THRESHOLDS),
        "source": "inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:89",
    },
    "placement_thresholds": {
        "value": list(PLACEMENT_AT),
        "source": "0.5 inherited Task18 primary; 0.3 confirmed 2026-10-05 under owner delegation",
    },
    "assignment": {
        "value": "max cardinality then max summed IoU, same class, one-to-one",
        "source": "inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:90",
    },
    "data": {
        "value": "COCO val2017, all 5000 images",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "crowd_rule": {
        "value": "ignore unmatched detection if intersection / own area >= threshold vs same-class crowd box",
        "source": "confirmed 2026-10-05 under owner delegation; COCO evaluator rule",
    },
    "crowd_as_clutter": {
        "value": True,
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "rasterising": {
        "value": "pixel-centre even-odd on unrounded vertices; same rule for boxes",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "size_bands_px2": {
        "value": [1024, 9216],
        "source": "inherited COCO evaluation definition, on annotation area",
    },
    "edge_margin_px": {
        "value": 2.0,
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "clutter_bands": {
        "value": None,
        "source": "n/a no band edges chosen; Spearman only",
    },
    "device": {
        "value": "cuda 0",
        "source": "confirmed 2026-10-05 by owner, when no other process uses it",
    },
    "opencv": {
        "value": EXPECTED_CV2,
        "source": "confirmed 2026-10-05 under owner delegation",
    },
}


def _detector(checkpoint: Path, device: str):
    module = importlib.import_module("experiments.06_object_recognition.pilot.detector")
    return module.YoloDetector(checkpoint, device)


def _check_cv2() -> str:
    import cv2

    if cv2.__version__ != EXPECTED_CV2:
        raise RuntimeError(f"Expected OpenCV {EXPECTED_CV2}, loaded {cv2.__version__}")
    return cv2.__version__


def _proposals(detections) -> list[dict]:
    return [
        {
            "xyxy": list(d.xyxy),
            "label": d.label,
            "class_id": d.class_id,
            "confidence": d.confidence,
        }
        for d in detections
    ]


def run(
    repo: Path,
    data_root: Path,
    checkpoint: Path,
    output: Path,
    device: str,
    limit: int | None,
) -> Path:
    cv2_version = _check_cv2()
    destination = data_root / "coco2017"
    receipt = coco.check_extraction(destination)
    detector = _detector(checkpoint, device)
    data = json.loads((destination / coco.ANNOTATIONS).read_text(encoding="utf-8"))
    names = {int(k): v for k, v in detector.model.names.items()}
    records = coco.image_records(data, coco.class_map(data["categories"], names))
    records = records[:limit] if limit else records
    configuration = {
        "experiment": "task45_part_a_coco_placement",
        "hyperparameters": HYPERPARAMETERS,
        "extraction_receipt": receipt,
        "checkpoint_sha256": sha256(checkpoint),
        "opencv": cv2_version,
        "images": len(records),
        "limit": limit,
    }
    with Run(output, repo, configuration) as published:
        proposals, counts, rows, rejected = [], [], [], 0
        started = time.perf_counter()
        with published.measure("detection", frames=len(records)):
            for record in records:
                path = destination / record["file"]
                detections, metadata = detector.predict(path)
                proposals.append(
                    {
                        "image_id": record["image_id"],
                        "file": record["file"],
                        "sha256": sha256(path),
                        "image_shape_hw": metadata["image_shape_hw"],
                        "proposals": _proposals(detections),
                    }
                )
        with published.measure("scoring", frames=len(records)):
            for record, entry in zip(records, proposals, strict=True):
                if entry["image_shape_hw"] != [record["height"], record["width"]]:
                    raise ValueError(
                        f"Image {record['image_id']} size differs from its annotation"
                    )
                scored = score_image(record, entry["proposals"])
                counts += scored["counts"]
                rows += scored["placement"]
                rejected += scored["rejected_proposals"]
        published.set_processed_frames(len(records))
        write_json(published.path / "output/proposals.json", proposals)
        write_json(published.path / "output/counts.json", counts)
        write_json(published.path / "output/placement_rows.json", rows)
        summary = summarise(counts, rows)
        summary.update(
            images=len(records),
            rejected_proposals=rejected,
            elapsed_seconds=time.perf_counter() - started,
            claim="in-distribution: Ultralytics validates checkpoints on val2017, so these may be optimistic",
        )
        write_json(published.path / "output/summary.json", summary)
    return published.path


def main(argv: list[str] | None = None) -> None:
    repo = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description="Task45 Part A COCO placement")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parent / "runs"
    )
    parser.add_argument("--device", default="0")
    parser.add_argument("--limit", type=int, default=None)
    arguments = parser.parse_args(argv)
    print(
        run(
            repo,
            arguments.data_root,
            arguments.checkpoint,
            arguments.output,
            arguments.device,
            arguments.limit,
        )
    )


if __name__ == "__main__":
    main()
