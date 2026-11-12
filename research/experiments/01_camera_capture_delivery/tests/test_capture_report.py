"""Contract controls for capture reports and exported files."""

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location("capture_report", APP / "capture_report.py")
capture_report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_report)


@pytest.fixture
def valid_report():
    return {
        "schema_version": 1,
        "session_id": "session_001",
        "status": "complete",
        "device": {
            "manufacturer": "Xiaomi",
            "model": "Redmi Note 11 Pro",
            "device": "veux",
            "product": "veux_global",
            "android_release": "13",
            "sdk_int": 33,
        },
        "checks": [{"id": "camera_inventory", "status": "PASS", "reason": ""}],
        "captures": [{
            "camera_id": "0",
            "file": "images/camera_0_0001.jpg",
            "sha256": "a" * 64,
            "width": 640,
            "height": 480,
            "crop_region": [0, 0, 640, 480],
            "rotation_degrees": 0,
            "sensor_timestamp_ns": 1700000000,
            "timestamp_source": "SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME",
            "frame_number": 1,
        }],
        "files": {"images/camera_0_0001.jpg": {"sha256": "a" * 64, "bytes": 4}},
    }


def test_accepts_report_with_missing_optional_metadata_recorded_as_a_check(valid_report):
    valid_report["checks"].append({
        "id": "calibration", "status": "SKIPPED", "reason": "LENS_INTRINSIC_CALIBRATION absent",
    })
    assert capture_report.validate_report(valid_report) == valid_report


@pytest.mark.parametrize("status", ["SKIPPED", "FAIL"])
def test_nonpassing_checks_require_a_reason(valid_report, status):
    valid_report["checks"][0] = {"id": "camera_inventory", "status": status, "reason": ""}
    with pytest.raises(ValueError, match="reason"):
        capture_report.validate_report(valid_report)


def test_rejects_unknown_check_status(valid_report):
    valid_report["checks"][0]["status"] = "WARN"
    with pytest.raises(ValueError, match="status"):
        capture_report.validate_report(valid_report)


def test_rejects_boolean_schema_version(valid_report):
    valid_report["schema_version"] = True
    with pytest.raises(ValueError, match="schema version"):
        capture_report.validate_report(valid_report)


def test_rejects_unhashable_session_status(valid_report):
    valid_report["status"] = []
    with pytest.raises(ValueError, match="session status"):
        capture_report.validate_report(valid_report)


@pytest.mark.parametrize("field,value", [
    ("sensor_timestamp_ns", None),
    ("timestamp_source", ""),
    ("width", 0),
    ("rotation_degrees", 45),
    ("rotation_degrees", []),
])
def test_capture_requires_original_timing_and_image_geometry(valid_report, field, value):
    valid_report["captures"][0][field] = value
    with pytest.raises(ValueError):
        capture_report.validate_report(valid_report)


def test_incomplete_session_cannot_be_exported(valid_report, tmp_path):
    valid_report["status"] = "incomplete"
    with pytest.raises(ValueError, match="incomplete"):
        capture_report.validate_export(valid_report, tmp_path)


def test_bundle_validation_checks_bytes_and_rejects_path_escape(valid_report, tmp_path):
    image = tmp_path / "images" / "camera_0_0001.jpg"
    image.parent.mkdir()
    image.write_bytes(b"jpeg")
    valid_report["files"][image.relative_to(tmp_path).as_posix()] = {
        "sha256": hashlib.sha256(b"jpeg").hexdigest(), "bytes": 4,
    }
    valid_report["captures"][0]["sha256"] = hashlib.sha256(b"jpeg").hexdigest()
    assert capture_report.validate_export(valid_report, tmp_path) == valid_report

    valid_report["files"]["../outside.jpg"] = {"sha256": "b" * 64, "bytes": 1}
    with pytest.raises(ValueError, match="path"):
        capture_report.validate_export(valid_report, tmp_path)


def test_bundle_validation_rejects_hash_mismatch(valid_report, tmp_path):
    image = tmp_path / "images" / "camera_0_0001.jpg"
    image.parent.mkdir()
    image.write_bytes(b"jpeg")
    valid_report["files"][image.relative_to(tmp_path).as_posix()] = {
        "sha256": "b" * 64, "bytes": 4,
    }
    valid_report["captures"][0]["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="hash"):
        capture_report.validate_export(valid_report, tmp_path)


def test_bundle_validation_rejects_empty_capture_file(valid_report, tmp_path):
    image = tmp_path / "images" / "camera_0_0001.jpg"
    image.parent.mkdir()
    image.write_bytes(b"")
    empty_hash = hashlib.sha256(b"").hexdigest()
    valid_report["files"][image.relative_to(tmp_path).as_posix()] = {
        "sha256": empty_hash, "bytes": 0,
    }
    valid_report["captures"][0]["sha256"] = empty_hash
    with pytest.raises(ValueError, match="empty"):
        capture_report.validate_export(valid_report, tmp_path)


def test_bundle_validation_rejects_symlink_outside_bundle(valid_report, tmp_path):
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"jpeg")
    image = bundle_root / "images" / "camera_0_0001.jpg"
    image.parent.mkdir()
    try:
        image.symlink_to(outside)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"Symlinks are unavailable in this environment: {error}")
    digest = hashlib.sha256(b"jpeg").hexdigest()
    valid_report["files"][image.relative_to(bundle_root).as_posix()] = {
        "sha256": digest, "bytes": 4,
    }
    valid_report["captures"][0]["sha256"] = digest
    with pytest.raises(ValueError, match="escapes root"):
        capture_report.validate_export(valid_report, bundle_root)
