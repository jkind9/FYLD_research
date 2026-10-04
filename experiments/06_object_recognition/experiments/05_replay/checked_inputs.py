"""Read hash-pinned geometry, detections and appearance inputs for Task22."""

from __future__ import annotations

import json
from pathlib import Path

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

BASELINE_RELATIVE = Path(
    "experiments/06_object_recognition/pilot/runs/20261003T200418.845966Z_f20e5b1de3744f47a850ffa3b3ba396b"
)
DETECTION_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/01_detection/runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd"
)
APPEARANCE_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/03_appearance/runs/20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d"
)
IDENTITY_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/04_geometry_identity/runs/20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb"
)
BASELINE_SHA256 = "e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3"
DETECTION_SHA256 = "7ee60f385871eeb6288c007bc03a548a233a2fee3e6dcf7cca9a5f583a15e39c"
APPEARANCE_SHA256 = "f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4"
IDENTITY_SHA256 = "75a1b943ab087d846a87d71289b4e118063fad8bac2010694e1521499046d6f7"
SELECTED = (0, 9, 27, 37, 42, 59)
CLASSES = {41: "cup", 62: "tv"}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verified(repo: Path, relative: Path, expected: str) -> Path:
    path = repo / relative
    if sha256(path / "metadata/manifest.json") != expected:
        raise ValueError(f"Accepted run manifest differs: {relative}")
    verify_run(path)
    return path


def load(repo: Path) -> dict:
    """Verify every predecessor before returning a minimal joined view."""
    baseline = _verified(repo, BASELINE_RELATIVE, BASELINE_SHA256)
    detections = _verified(repo, DETECTION_RELATIVE, DETECTION_SHA256)
    appearance = _verified(repo, APPEARANCE_RELATIVE, APPEARANCE_SHA256)
    identity = _verified(repo, IDENTITY_RELATIVE, IDENTITY_SHA256)
    base_rows = _json(baseline / "output/observations.json")["frames"]
    baseline_selection = _json(baseline / "output/selection.json")["selected_frames"]
    detector_payload = _json(detections / "output/cached_proposals.json")
    automatic_by_index = {
        row["source_selection_index"]: row for row in detector_payload["frames"]
    }
    proposal_rows = []
    for index in SELECTED:
        frame = automatic_by_index.get(index)
        if frame is None or frame["frame_id"] != base_rows[index]["frame_id"]:
            raise ValueError(
                "Task18 proposal frame does not join to the accepted replay"
            )
        proposal_rows.append(frame)
    if [
        sum(p["class_id"] in CLASSES for p in frame["proposals"])
        for frame in proposal_rows
    ] != [6, 2, 0, 5, 3, 1]:
        raise ValueError("Selected Task18 cup/monitor proposal inventory changed")
    descriptor_file = appearance / "output/descriptors.json"
    identity_receipts = _json(identity / "output/summary.json")
    return {
        "baseline": baseline,
        "baseline_rows": base_rows,
        "selection": baseline_selection,
        "proposal_frames": proposal_rows,
        "appearance": appearance,
        "identity": identity,
        "pins": {
            "baseline_manifest_sha256": BASELINE_SHA256,
            "detection_manifest_sha256": DETECTION_SHA256,
            "appearance_manifest_sha256": APPEARANCE_SHA256,
            "identity_manifest_sha256": IDENTITY_SHA256,
            "descriptor_sha256": sha256(descriptor_file),
            "identity_schema_version": 1,
            "identity_conditions": sorted(identity_receipts["conditions"]),
        },
    }
