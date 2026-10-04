"""Pinned accepted-run extraction; no detector imports, poses or identity outputs."""

import importlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

from .scoring import validate_predictions

detector = importlib.import_module("experiments.06_object_recognition.pilot.detector")
ACCEPTED_MANIFEST_SHA256 = (
    "e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3"
)
ACCEPTED_ANNOTATIONS_SHA256 = (
    "a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920"
)
ACCEPTED_RELATIVE = "experiments/06_object_recognition/pilot/runs/20261003T200418.845966Z_f20e5b1de3744f47a850ffa3b3ba396b"
SELECTION_INDEXES = (0, 9, 27, 37, 42, 59)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _metadata(metadata: dict) -> None:
    if (
        metadata.get("actual_device") != "cuda:0"
        or metadata.get("actual_fp16") is not False
    ):
        raise ValueError("Accepted predecessor requires CUDA0 FP32")
    if metadata.get("image_shape_hw") != [480, 640]:
        raise ValueError("Predecessor must use original 640x480 grid")
    arguments = metadata.get("effective_arguments", {})
    # The accepted Ultralytics receipt stores half=None after predictor setup;
    # actual_fp16=False above independently confirms the inherited FP32 setting.
    if any(
        (bool(arguments.get(key)) if key == "half" else arguments.get(key)) != value
        for key, value in detector.PREDICT_SETTINGS.items()
    ):
        raise ValueError("Predecessor prediction settings differ")
    if (
        metadata.get("class_names", {}).get("41") != "cup"
        or metadata.get("class_names", {}).get("62") != "tv"
    ):
        raise ValueError("Predecessor class vocabulary differs")


def check_cache(
    cache: Path, capture_frames: list[dict], expected_manifest_sha256: str
) -> dict:
    """Pure cache integrity helper; a synthetic expected hash proves no GPU claim.

    Publication only calls load_accepted_cache, which fixes the accepted hash.
    capture_frames is an RGB-only projection; references never enter extraction.
    """
    if not cache.is_dir():
        raise ValueError(
            "Accepted cache unavailable; transfer the completed Task28 run offline"
        )
    if sha256(cache / "metadata/manifest.json") != expected_manifest_sha256:
        raise ValueError("Predecessor is not the pinned completion manifest")
    verify_run(cache)
    configuration = read_json(cache / "metadata/configuration.json")
    if configuration.get("checkpoint_sha256") != detector.CHECKPOINT_SHA256:
        raise ValueError("Predecessor checkpoint hash differs")
    packages = read_json(cache / "metadata/environment.json")["packages"]
    if {p["name"].lower(): p["version"] for p in packages}.get(
        "ultralytics"
    ) != "8.4.172":
        raise ValueError("Predecessor package differs")
    selection = read_json(cache / "output/selection.json")["selected_frames"]
    detections = read_json(cache / "output/detections.json")
    records, metadata = detections["frames"], detections["metadata"]
    if len(records) != len(selection) or len(metadata) != len(selection):
        raise ValueError("Predecessor frame accounting mismatch")
    indexes = [r["frame_index"] for r in records]
    if indexes != list(range(len(selection))) or len(
        {(s["frame_id"], s["rgb"]) for s in selection}
    ) != len(selection):
        raise ValueError("Duplicate or unordered predecessor frames")
    used_indexes, used_rgb, used_frames = set(), set(), set()
    extracted = []
    for capture in capture_frames:
        index = capture["source_selection_index"]
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or not 0 <= index < len(records)
        ):
            raise ValueError("Invalid predecessor selection index")
        rgb, frame_id = capture["rgb"], capture["frame_id"]
        if (
            index in used_indexes
            or rgb["sha256"] in used_rgb
            or frame_id in used_frames
        ):
            raise ValueError("Duplicate requested source/frame")
        used_indexes.add(index)
        used_rgb.add(rgb["sha256"])
        used_frames.add(frame_id)
        selected, record, meta = selection[index], records[index], metadata[index]
        relative = PurePosixPath(selected["rgb"])
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in selected["rgb"]
            or ":" in selected["rgb"]
        ):
            raise ValueError("Unsafe predecessor RGB path")
        cached_image = cache / "input" / relative
        if (
            selected["frame_id"] != frame_id
            or selected["timestamp_s"] != capture["timestamp_s"]
            or record["timestamp_s"] != capture["timestamp_s"]
            or not rgb["path"].endswith("/" + relative.as_posix())
            or sha256(cached_image) != rgb["sha256"]
        ):
            raise ValueError("Original frame/RGB/hash join differs")
        _metadata(meta)
        validate_predictions(record["proposals"], 640, 480, meta["class_names"])
        extracted.append(
            {
                "frame_id": frame_id,
                "source_selection_index": index,
                "rgb": rgb,
                "timestamp_s": capture["timestamp_s"],
                "proposals": record["proposals"],
                "predecessor_metadata": meta,
            }
        )
    return {
        "frames": extracted,
        "manifest_sha256": expected_manifest_sha256,
        "checkpoint_sha256": detector.CHECKPOINT_SHA256,
        "predecessor_timing": read_json(cache / "metadata/timing.json"),
        "environment": read_json(cache / "metadata/environment.json"),
        "configuration": configuration,
    }


def load_accepted_cache(cache: Path, capture_frames: list[dict]) -> dict:
    """Production path cannot accept a substituted manifest hash or predictions."""
    if tuple(f["source_selection_index"] for f in capture_frames) != SELECTION_INDEXES:
        raise ValueError("Production requires Task17's exact six frames")
    return check_cache(cache, capture_frames, ACCEPTED_MANIFEST_SHA256)
