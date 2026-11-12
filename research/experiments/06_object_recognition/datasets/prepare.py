"""Prepare a bounded RGB-only reference set without inference or downloads."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import shutil
from copy import deepcopy
from html import escape
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image, ImageDraw

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import write_json

contracts = importlib.import_module("experiments.06_object_recognition.shared.manifest")
ROOT = Path(__file__).resolve().parents[3]
ANNOTATIONS = Path(__file__).with_name("desk_smoke_v1.json")
HYPERPARAMETERS: dict[str, dict[str, Any]] = {
    "selection_indexes": {
        "value": [0, 9, 27, 37, 42, 59],
        "source": "confirmed 2026-10-03 delegated Task17 completion; RGB review corrected gap to index27",
    },
    "partitions": {
        "value": {"enrollment": 2, "evaluation": 4, "validation": 0},
        "source": "confirmed 2026-10-03 delegated completion; within-session smoke control, no tuning",
    },
    "label_policy": {
        "value": "RGB-only cup complete, two monitors subset; provisional visible polygons; agent reviewed",
        "source": "confirmed 2026-10-03 delegated Task17 completion; no human gold claim",
    },
    "depth_policy": {
        "value": {"units_per_metre": 5000, "raw_missing": 0, "processed_max_m": 4},
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:123",
    },
    "calibration": {
        "value": [640, 480, 525, 525, 319.5, 239.5],
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:14",
    },
    "time_tolerance_s": {
        "value": 0.02,
        "source": "inherited experiments/03_camera_pose_estimation/src/dataset.py:78",
    },
    "rigid_tolerances": {
        "value": [1e-10, 1e-5, 0],
        "source": "inherited experiments/shared/geometry.py:67",
    },
    "model_inference": {"value": None, "source": "n/a deterministic data preparation"},
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or Path(relative).is_absolute():
        raise ValueError("Artifact path escapes publication")
    return path


def _filename(value: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is None
    ):
        raise ValueError("Unsafe frame or instance filename identifier")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
    }
    if value.upper() in reserved:
        raise ValueError("Windows reserved device filename identifier")
    return value


def _counts(manifest: dict) -> dict:
    labels = [label for frame in manifest["frames"] for label in frame["labels"]]
    return {
        "frames": len(manifest["frames"]),
        "instances": len(labels),
        "identities": len({label["instance_id"] for label in labels}),
    }


def _hyperparameters(manifest: dict) -> dict:
    settings = deepcopy(HYPERPARAMETERS)
    settings["selection_indexes"]["value"] = [
        f.get("source_selection_index") for f in manifest["frames"]
    ]
    settings["partitions"]["value"] = {
        partition: sum(f["partition"] == partition for f in manifest["frames"])
        for partition in ("enrollment", "evaluation", "validation")
    }
    return settings


def _write_frames(manifest: dict, repo: Path, staging: Path) -> list[str]:
    rows = []
    for frame in manifest["frames"]:
        key = _filename(frame["frame_id"])
        rgb_target = staging / "rgb" / f"{key}.png"
        rgb_target.parent.mkdir(exist_ok=True)
        shutil.copyfile(repo / frame["rgb"]["path"], rgb_target)
        if sha256(rgb_target) != frame["rgb"]["sha256"]:
            raise ValueError("Source changed during RGB copy")
        depth_target = staging / "depth" / f"{key}.png"
        depth_target.parent.mkdir(exist_ok=True)
        shutil.copyfile(repo / frame["depth"]["path"], depth_target)
        if sha256(depth_target) != frame["depth"]["sha256"]:
            raise ValueError("Source changed during depth copy")
        with Image.open(rgb_target) as original:
            overlay = original.convert("RGB")
        draw = ImageDraw.Draw(overlay)
        for label in frame["labels"]:
            mask = Image.new("L", overlay.size)
            polygon = [tuple(point) for point in label["polygon"]]
            ImageDraw.Draw(mask).polygon(polygon, fill=255)
            mask_path = staging / "masks" / key / f"{label['instance_id']}.png"
            mask_path.parent.mkdir(parents=True, exist_ok=True)
            mask.save(mask_path)
            draw.line(polygon + polygon[:1], fill="red", width=2)
            draw.text(polygon[0], label["instance_id"], fill="red")
        overlay_path = staging / "overlays" / f"{key}.png"
        overlay_path.parent.mkdir(exist_ok=True)
        overlay.save(overlay_path)
        labels = (
            ", ".join(label["instance_id"] for label in frame["labels"])
            or "cup out of view"
        )
        rows.append(
            f"<section><h2>{escape(key)}: {frame['timestamp_s']:.6f} s</h2>"
            f"<p>{escape(frame['partition'])}; {escape(labels)}</p>"
            f'<a href="rgb/{escape(key)}.png">Original RGB</a> '
            f'<a href="depth/{escape(key)}.png">Original raw depth</a><br>'
            f'<img width="640" alt="RGB-only provisional labels for {escape(key)}" '
            f'src="overlays/{escape(key)}.png"></section>'
        )
    return rows


def publish(manifest: dict, repo: Path, destination: Path) -> dict:
    """Validate sources before atomically publishing a fresh immutable directory."""
    repo, destination = repo.resolve(), destination.resolve()
    if not destination.is_relative_to(repo) or destination == repo:
        raise ValueError("Destination must be inside repository")
    if destination.exists():
        raise FileExistsError(destination)
    if manifest["provenance"]["review_status"] != "agent_reviewed_with_limits":
        raise ValueError("Annotations require independent agent review")
    contracts.validate_manifest(manifest, repo)
    frame_names = set()
    for frame in manifest["frames"]:
        frame_name = _filename(frame["frame_id"]).casefold()
        if frame_name in frame_names:
            raise ValueError("Windows frame filename collision")
        frame_names.add(frame_name)
        instance_names = set()
        for label in frame["labels"]:
            instance_name = _filename(label["instance_id"]).casefold()
            if instance_name in instance_names:
                raise ValueError("Windows instance filename collision")
            instance_names.add(instance_name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.staging_{uuid4().hex}")
    staging.mkdir()
    write_json(staging / "annotations.json", manifest)
    write_json(staging / "method_inputs.json", contracts.method_inputs(manifest))
    rows = _write_frames(manifest, repo, staging)
    review = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>Recorded object reference review</title><h1>Recorded object reference review</h1>"
        "<p>Agent-authored and independently agent-reviewed RGB labels. No human review. "
        "Masks are coarse provisional visible-pixel supports, excluded from formal segmentation scoring. "
        "Two monitor identities form a non-exhaustive subset. Six previously inspected frames "
        "support a within-session smoke control, not blind accuracy or generalisation.</p>"
        '<p><a href="annotations.json">Evaluator labels and scenario gaps</a> · '
        '<a href="method_inputs.json">Separate method inputs</a></p>'
        + "".join(rows)
        + "</html>"
    )
    (staging / "review.html").write_text(review, encoding="utf-8")
    files = [
        {"path": path.relative_to(staging).as_posix(), "sha256": sha256(path)}
        for path in sorted(staging.rglob("*"))
        if path.is_file()
    ]
    receipt = {
        "schema_version": 1,
        "status": "complete",
        "files": files,
        "annotation_sha256": sha256(staging / "annotations.json"),
        "hyperparameters": _hyperparameters(manifest),
        "counts": _counts(manifest),
    }
    write_json(staging / "publication.json", receipt)
    verify_publication(staging, repo)
    staging.rename(destination)
    return receipt


def verify_publication(destination: Path, repo: Path) -> dict:
    receipt = _read(destination / "publication.json")
    if receipt.get("schema_version") != 1 or receipt.get("status") != "complete":
        raise ValueError("Incomplete reference publication")
    indexed = set()
    for item in receipt["files"]:
        path = _safe_file(destination, item["path"])
        if (
            item["path"] in indexed
            or not path.is_file()
            or sha256(path) != item["sha256"]
        ):
            raise ValueError("Missing, duplicate or changed publication artifact")
        indexed.add(item["path"])
    actual = {
        p.relative_to(destination).as_posix()
        for p in destination.rglob("*")
        if p.is_file() and p.relative_to(destination).as_posix() != "publication.json"
    }
    if indexed != actual:
        raise ValueError("Publication file inventory mismatch")
    manifest = _read(destination / "annotations.json")
    if sha256(destination / "annotations.json") != receipt["annotation_sha256"]:
        raise ValueError("Annotation hash mismatch")
    contracts.validate_manifest(manifest, repo)
    if receipt.get("counts") != _counts(manifest):
        raise ValueError("Publication count receipt mismatch")
    if receipt.get("hyperparameters") != _hyperparameters(manifest):
        raise ValueError("Publication settings receipt mismatch")
    for frame in manifest["frames"]:
        key = _filename(frame["frame_id"])
        for role in ("rgb", "depth"):
            if sha256(destination / role / f"{key}.png") != frame[role]["sha256"]:
                raise ValueError("Copied image differs from original source")
    if _read(destination / "method_inputs.json") != contracts.method_inputs(manifest):
        raise ValueError("Method inputs do not match label-free projection")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination", type=Path, default=ROOT / "data/object_revisits/desk_smoke_v1"
    )
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    receipt = (
        verify_publication(args.destination, ROOT)
        if args.verify
        else publish(_read(ANNOTATIONS), ROOT, args.destination)
    )
    print(json.dumps({"status": receipt["status"], "counts": receipt["counts"]}))


if __name__ == "__main__":
    main()
