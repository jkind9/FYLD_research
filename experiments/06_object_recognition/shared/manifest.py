"""Validate frozen RGB-D annotations and project method inputs by explicit allowlist."""

from copy import deepcopy
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import numpy as np
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Calibration

from .validation import finite, identifier, pixel_support, sha256_value

PARTITIONS = {"enrollment", "evaluation", "validation"}
DEPTH_POLICY = {
    "units_per_metre": 5000,
    "raw_missing": 0,
    "processed_max_m": 4,
    "registration": "same_pixel_grid",
}
FRAME_KEYS = (
    "session_id",
    "frame_id",
    "timestamp_s",
    "partition",
    "source_frame_id",
    "augmentation_of",
)


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")  # noqa: TRY004 - schema errors
    return value


def _rows(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{name} must be an array of objects")
    return value


def _source(record: Any, repo: Path, verify_sources: bool) -> Path:
    record = _mapping(record, "source")
    relative = identifier(record.get("path"), "source path")
    windows = PureWindowsPath(relative)
    parts = PurePosixPath(relative).parts
    if (
        windows.drive
        or windows.root
        or "\\" in relative
        or ".." in parts
        or ":" in relative
        or PurePosixPath(relative).is_absolute()
    ):
        raise ValueError(f"Unsafe repository-relative source path: {relative}")
    root = repo.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Source path escapes repository: {relative}")
    expected = sha256_value(record.get("sha256"))
    if verify_sources:
        if not path.is_file():
            raise ValueError(
                f"Missing source: {relative}; copy original offline source files"
            )
        if sha256(path) != expected:
            raise ValueError(f"Source SHA256 mismatch: {relative}")
    return path


def _check_images(rgb: Path, depth: Path, calibration: Calibration) -> None:
    expected = (calibration.width, calibration.height)
    with Image.open(rgb) as image:
        if image.size != expected or image.mode != "RGB":
            raise ValueError("RGB dimensions/mode must match calibrated original grid")
    with Image.open(depth) as image:
        if image.size != expected or np.asarray(image).dtype != np.uint16:
            raise ValueError(
                "Raw depth must be unsigned16 on the same calibrated pixel grid"
            )


def _labels(
    frame: dict[str, Any], calibration: Calibration, identities: dict[str, str]
) -> None:
    coverage = _mapping(frame.get("label_coverage"), "label_coverage")
    if any(
        value not in {"complete", "subset", "unlabelled"} for value in coverage.values()
    ):
        raise ValueError("Unknown label coverage")
    seen: set[str] = set()
    for label in _rows(frame.get("labels"), "labels"):
        instance = identifier(label.get("instance_id"), "instance_id")
        category = identifier(label.get("category"), "category")
        if instance in seen:
            raise ValueError("Duplicate frame instance")
        seen.add(instance)
        if category not in coverage or coverage[category] == "unlabelled":
            raise ValueError("Label category requires explicit coverage")
        if identities.get(instance, category) != category:
            raise ValueError("Instance category changed between frames")
        identities[instance] = category
        support = {"cup": "visible_cup", "tv": "visible_display_enclosure"}.get(
            category
        )
        if support is None or label.get("support") != support:
            raise ValueError(
                "Label support must describe visible cup/display enclosure"
            )
        if label.get("mask_status") != "provisional":
            raise ValueError("Schema v1 masks require provisional boundary status")
        pixel_support(label.get("polygon", ()), label.get("bbox_xyxy", ()), calibration)


def _frame(
    frame: dict[str, Any],
    calibration: Calibration,
    repo: Path,
    verify_sources: bool,
    identities: dict[str, str],
) -> None:
    for name in ("session_id", "frame_id", "visit_id"):
        identifier(frame.get(name), name)
    timestamp = finite(frame.get("timestamp_s"), "timestamp_s")
    if frame.get("partition") not in PARTITIONS:
        raise ValueError("Unknown frame partition")
    rgb = _source(frame.get("rgb"), repo, verify_sources)
    depth = _source(frame.get("depth"), repo, verify_sources)
    depth_time = finite(frame["depth"].get("timestamp_s"), "depth timestamp_s")
    if abs(timestamp - depth_time) > 0.020001:
        raise ValueError(
            "RGB/depth timestamp association exceeds inherited 0.02 seconds"
        )
    if verify_sources:
        _check_images(rgb, depth, calibration)
    _labels(frame, calibration, identities)


def _splits(frames: list[dict[str, Any]], repo: Path) -> None:
    by_id = {frame["frame_id"]: frame for frame in frames}
    if len(by_id) != len(frames):
        raise ValueError("Duplicate or ambiguous frame_id")
    source_partitions: dict[tuple[str, str], str] = {}
    for frame in frames:
        partition = frame["partition"]
        for kind in ("rgb", "depth"):
            keys = [(kind + "_path", str((repo / frame[kind]["path"]).resolve()))]
            if kind == "rgb":
                keys.append(("rgb_sha256", frame[kind]["sha256"]))
            for key in keys:
                if source_partitions.get(key, partition) != partition:
                    raise ValueError("Source path/hash leaks between partitions")
                source_partitions[key] = partition
        for field in ("source_frame_id", "augmentation_of"):
            if field in frame:
                parent = identifier(frame[field], field)
                if parent not in by_id or by_id[parent]["partition"] != partition:
                    raise ValueError(
                        "Derived frame needs a source in the same partition"
                    )
                if parent == frame["frame_id"]:
                    raise ValueError("Derived frame cannot reference itself")


def _revisits(rows: Any, frames: list[dict[str, Any]]) -> None:
    by_id = {frame["frame_id"]: frame for frame in frames}
    seen: set[tuple[str, ...]] = set()
    for row in _rows(rows, "revisits"):
        instance = identifier(row.get("instance_id"), "revisit instance")
        keys = tuple(
            identifier(row.get(name), name)
            for name in ("before_frame_id", "gap_frame_id", "return_frame_id")
        )
        if len(set(keys)) != 3 or any(key not in by_id for key in keys):
            raise ValueError("Revisit requires three distinct existing frames")
        before, gap, after = (by_id[key] for key in keys)
        identity_key = (instance, *keys)
        if identity_key in seen:
            raise ValueError("Duplicate revisit")
        seen.add(identity_key)
        if (
            len({frame["session_id"] for frame in (before, gap, after)}) != 1
            or not before["timestamp_s"] < gap["timestamp_s"] < after["timestamp_s"]
        ):
            raise ValueError("Revisit must be ordered within one session")
        labels = [
            {label["instance_id"]: label for label in frame["labels"]}
            for frame in (before, gap, after)
        ]
        if (
            instance not in labels[0]
            or instance not in labels[2]
            or instance in labels[1]
        ):
            raise ValueError(
                "Revisit must have labelled before/return and unlabelled gap"
            )
        category = labels[0][instance]["category"]
        if gap["label_coverage"].get(category) != "complete":
            raise ValueError("Revisit negative requires complete category coverage")


def validate_manifest(
    manifest: dict[str, Any], repo: Path, verify_sources: bool = True
) -> None:
    """Reject invalid annotations, unsafe/tampered sources and partition leakage."""
    manifest = _mapping(manifest, "manifest")
    if manifest.get("schema_version") != 1 or isinstance(
        manifest.get("schema_version"), bool
    ):
        raise ValueError("Expected manifest schema_version 1")
    identifier(manifest.get("name"), "manifest name")
    calibration_values = _mapping(manifest.get("calibration"), "calibration")
    required = {"width", "height", "fx", "fy", "cx", "cy", "axes"}
    if set(calibration_values) != required:
        raise ValueError("Calibration requires the shared schema fields")
    calibration = Calibration(**calibration_values)
    pixel_support(((0, 0), (1, 0), (1, 1)), (0, 0, 1, 1), calibration)
    policy = _mapping(manifest.get("depth_policy"), "depth_policy")
    if policy != DEPTH_POLICY or any(
        isinstance(value, bool) for value in policy.values()
    ):
        raise ValueError(
            "Depth policy must preserve raw /5000 metres, zero missing and grid registration"
        )
    provenance = _mapping(manifest.get("provenance"), "provenance")
    for field in ("annotation_author", "review_status"):
        identifier(provenance.get(field), field)
    split = _mapping(manifest.get("split_policy"), "split_policy")
    if split.get("claim") != "within_session_smoke" or split.get("tuning") is not False:
        raise ValueError("Only untuned within_session_smoke claim is supported")
    seen_sources: set[str] = set()
    for source in _rows(manifest.get("source_records"), "source_records"):
        path = str(_source(source, repo, verify_sources))
        if path in seen_sources:
            raise ValueError("Duplicate metadata source")
        seen_sources.add(path)
    frames = _rows(manifest.get("frames"), "frames")
    if not frames:
        raise ValueError("Manifest needs at least one frame")
    identities: dict[str, str] = {}
    for frame in frames:
        _frame(frame, calibration, repo, verify_sources, identities)
    _splits(frames, repo)
    scenario_names: set[str] = set()
    for scenario in _rows(manifest.get("scenarios"), "scenarios"):
        name = identifier(scenario.get("name"), "scenario name")
        if name in scenario_names or scenario.get("status") not in {
            "present",
            "absent",
            "unusable",
        }:
            raise ValueError("Duplicate scenario or invalid status")
        scenario_names.add(name)
        identifier(scenario.get("evidence"), "scenario evidence")
    _revisits(manifest.get("revisits"), frames)


def method_inputs(manifest: dict[str, Any]) -> dict[str, Any]:
    """Explicit capture-only projection; evaluator answers never reach methods."""
    result = {
        key: deepcopy(manifest[key])
        for key in ("schema_version", "name", "calibration", "depth_policy")
    }
    frames = []
    for frame in manifest["frames"]:
        projected = {key: deepcopy(frame[key]) for key in FRAME_KEYS if key in frame}
        projected["rgb"] = {
            key: deepcopy(frame["rgb"][key]) for key in ("path", "sha256")
        }
        projected["depth"] = {
            key: deepcopy(frame["depth"][key])
            for key in ("path", "sha256", "timestamp_s")
        }
        frames.append(projected)
    return {**result, "frames": frames}
