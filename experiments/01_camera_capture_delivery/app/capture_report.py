"""Validate versioned camera reports before they are shown or exported."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Any

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_STATUSES = {"PASS", "FAIL", "SKIPPED"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _safe_relative_path(value: Any) -> PurePosixPath:
    _require(isinstance(value, str) and "\\" not in value, "Invalid bundle path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and bool(path.parts), "Invalid bundle path")
    _require(all(part not in {".", ".."} for part in path.parts), "Invalid bundle path")
    return path


def _validate_files(files: Any) -> dict[str, dict[str, Any]]:
    _require(isinstance(files, dict) and files, "Report files must be a non-empty object")
    validated: dict[str, dict[str, Any]] = {}
    for name, record in files.items():
        path = _safe_relative_path(name)
        _require(isinstance(record, dict), f"Invalid file record: {name}")
        digest, size = record.get("sha256"), record.get("bytes")
        _require(isinstance(digest, str) and _HASH.fullmatch(digest) is not None,
                 f"Invalid file hash: {name}")
        _require(type(size) is int and size >= 0, f"Invalid file size: {name}")
        validated[path.as_posix()] = {"sha256": digest, "bytes": size}
    return validated


def _file_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def validate_report(report: Any) -> dict[str, Any]:
    """Check required report fields and return a shallow copy."""
    _require(isinstance(report, dict), "Report must be an object")
    _require(type(report.get("schema_version")) is int and report["schema_version"] == 1,
             "Unsupported report schema version")
    session = report.get("session_id")
    _require(isinstance(session, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", session),
             "Invalid session ID")
    _require(isinstance(report.get("status"), str)
             and report["status"] in {"complete", "incomplete"}, "Invalid session status")

    device = report.get("device")
    _require(isinstance(device, dict), "Device information is required")
    for field in ("manufacturer", "model", "device", "product", "android_release"):
        _require(isinstance(device.get(field), str) and device[field].strip(),
                 f"Invalid device field: {field}")
    _require(type(device.get("sdk_int")) is int and device["sdk_int"] > 0,
             "Invalid device field: sdk_int")

    checks = report.get("checks")
    _require(isinstance(checks, list) and checks, "Report checks must be a non-empty list")
    check_ids: set[str] = set()
    for check in checks:
        _require(isinstance(check, dict), "Invalid check record")
        check_id, status, reason = check.get("id"), check.get("status"), check.get("reason")
        _require(isinstance(check_id, str) and check_id.strip() and check_id not in check_ids,
                 "Invalid or duplicate check ID")
        _require(isinstance(status, str) and status in _STATUSES,
                 f"Invalid status for check {check_id}")
        _require(isinstance(reason, str), f"Invalid reason for check {check_id}")
        _require(status == "PASS" or bool(reason.strip()), f"Missing reason for check {check_id}")
        check_ids.add(check_id)

    files = _validate_files(report.get("files"))
    captures = report.get("captures")
    _require(isinstance(captures, list), "Report captures must be a list")
    for capture in captures:
        _require(isinstance(capture, dict), "Invalid capture record")
        for field in ("camera_id", "timestamp_source"):
            _require(isinstance(capture.get(field), str) and capture[field].strip(),
                     f"Invalid capture field: {field}")
        timestamp = capture.get("sensor_timestamp_ns")
        _require(type(timestamp) is int and timestamp >= 0, "Invalid sensor timestamp")
        for field in ("width", "height"):
            _require(type(capture.get(field)) is int and capture[field] > 0,
                     f"Invalid capture field: {field}")
        crop = capture.get("crop_region")
        _require(isinstance(crop, list) and len(crop) == 4
                 and all(type(value) is int for value in crop)
                 and crop[2] > crop[0] and crop[3] > crop[1], "Invalid crop region")
        _require(type(capture.get("frame_number")) is int and capture["frame_number"] >= 0,
                 "Invalid frame number")
        name = _safe_relative_path(capture.get("file")).as_posix()
        _require(name in files, f"Capture file is absent from report files: {name}")
        _require(files[name]["bytes"] > 0, f"Capture file is empty: {name}")
        _require(capture.get("sha256") == files[name]["sha256"],
                 f"Capture file hash disagrees with report files: {name}")
        rotation = capture.get("rotation_degrees")
        _require(type(rotation) is int and rotation in {0, 90, 180, 270},
                 "Invalid image rotation")
    return {**report, "files": files}


def validate_export(report: Any, bundle_root: Path) -> dict[str, Any]:
    """Reject incomplete sessions, unsafe paths, missing files, and changed bytes."""
    validated = validate_report(report)
    _require(validated["status"] == "complete", "Cannot export an incomplete session")
    root = Path(bundle_root).resolve(strict=True)
    for name, expected in validated["files"].items():
        relative = _safe_relative_path(name)
        candidate = root.joinpath(*relative.parts)
        resolved = candidate.resolve(strict=True)
        _require(resolved.is_relative_to(root) and candidate.is_file(),
                 f"Bundle path escapes root or is not a file: {name}")
        digest, size = _file_digest(resolved)
        _require(size == expected["bytes"], f"Bundle size mismatch: {name}")
        _require(digest == expected["sha256"],
                 f"Bundle hash mismatch: {name}")
    return validated


def validate_phone_session_export(report: Any, bundle_root: Path) -> dict[str, Any]:
    """Require an actual passing single-camera recording for phone-session use."""
    validated = validate_export(report, bundle_root)
    _require(bool(validated["captures"]), "Phone session must contain at least one image")
    passed_single_camera = any(
        check["id"] == "single_camera_control" and check["status"] == "PASS"
        for check in validated["checks"]
    )
    _require(passed_single_camera, "single-camera capture did not pass")
    single_camera_check = next(
        check for check in validated["checks"]
        if check["id"] == "single_camera_control" and check["status"] == "PASS"
    )
    details = single_camera_check.get("details")
    _require(isinstance(details, list), "Single-camera capture details are missing")
    fields = (
        "camera_id", "file", "sha256", "width", "height", "crop_region",
        "rotation_degrees", "distortion_correction_mode", "distortion_correction_mode_name",
        "sensor_timestamp_ns", "timestamp_source", "frame_number",
    )
    for capture in validated["captures"]:
        _require("distortion_correction_mode" in capture
                 and isinstance(capture.get("distortion_correction_mode_name"), str),
                 "Capture distortion-correction mode is missing")
        matched = any(
            isinstance(frame, dict)
            and all(frame.get(field) == capture.get(field) for field in fields)
            for frame in details
        )
        _require(matched, "single-camera check does not identify the exported frames")
    return validated
