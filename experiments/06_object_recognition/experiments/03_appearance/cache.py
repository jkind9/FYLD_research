"""Source/config/code pins for descriptor reuse after a verified GPU publication."""

import hashlib
import importlib
import json
from pathlib import Path

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

detector = importlib.import_module("experiments.06_object_recognition.pilot.detector")
ACCEPTED_MANIFEST_SHA256: str | None = (
    "f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4"
)


def fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def feature_code() -> dict:
    local = {
        name: sha256(Path(__file__).with_name(name))
        for name in ("adapter.py", "features.py")
    }
    source = detector.__file__
    if source is None:
        raise ValueError("Detector producer source is unavailable")
    return {**local, "pilot/detector.py": sha256(Path(source))}


def read_verified(cache: Path, expected: dict) -> dict:
    if ACCEPTED_MANIFEST_SHA256 is None:
        raise ValueError("No accepted GPU feature cache has been pinned yet")
    if sha256(cache / "metadata/manifest.json") != ACCEPTED_MANIFEST_SHA256:
        raise ValueError("Feature cache is not the accepted completion manifest")
    verify_run(cache)
    payload = json.loads((cache / "output/descriptors.json").read_text())
    receipt = json.loads((cache / "output/feature_receipt.json").read_text())
    if payload["signature"] != expected or payload["synthetic_control"]:
        raise ValueError("Feature cache source/config/code provenance differs")
    if (
        receipt.get("checkpoint_sha256") != detector.CHECKPOINT_SHA256
        or receipt.get("actual_device") != "cuda:0"
        or receipt.get("actual_fp16") is not False
        or receipt.get("requested_embedding_count") != 11
    ):
        raise ValueError("Feature cache lacks the accepted real GPU extraction receipt")
    return payload
