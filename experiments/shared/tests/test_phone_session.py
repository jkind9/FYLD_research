"""Contract tests for distinguishing capability reports from phone recordings."""

import hashlib
import importlib.util
import shutil
import sys
import uuid
from pathlib import Path

import pytest
from PIL import Image

from experiments.shared.phone_session import read_phone_session

APP = Path(__file__).resolve().parents[2] / "01_camera_capture_delivery" / "app"
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location("capture_report", APP / "capture_report.py")
capture_report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_report)
TEST_ROOT = Path(__file__).resolve().parent
PAYLOAD_NAME = "images/frame_0001.jpg"


@pytest.fixture
def phone_bundle():
    root = TEST_ROOT / ".pytest-temp" / f"phone_session_{uuid.uuid4().hex}"
    image_path = root / PAYLOAD_NAME
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (640, 480), (10, 20, 30)).save(image_path, format="JPEG")
    payload = image_path.read_bytes()
    record = {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
    capture = {
        "camera_id": "0",
        "file": PAYLOAD_NAME,
        "sha256": record["sha256"],
        "width": 640,
        "height": 480,
        "crop_region": [0, 0, 640, 480],
        "rotation_degrees": 0,
        "distortion_correction_mode": 0,
        "distortion_correction_mode_name": "OFF",
        "sensor_timestamp_ns": 1700000000,
        "timestamp_source": "SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME",
        "frame_number": 1,
    }
    report = {
        "schema_version": 1,
        "session_id": "phone_session_001",
        "status": "complete",
        "device": {
            "manufacturer": "Xiaomi",
            "model": "Redmi Note 11 Pro",
            "device": "veux",
            "product": "veux_global",
            "android_release": "13",
            "sdk_int": 33,
        },
        "checks": [
            {
                "id": "single_camera_control", "status": "PASS", "reason": "",
                "details": [{**capture, "bytes": len(payload)}],
            },
            {
                "id": "arcore_depth_and_pose", "status": "SKIPPED",
                "reason": "This APK does not include ARCore",
            },
        ],
        "cameras": [{
            "id": "0",
            "pixel_array_size": [4200, 3200],
            "active_array_rect": [100, 100, 4000, 3000],
            "pre_correction_active_array_rect": [0, 0, 4100, 3100],
            "intrinsic_calibration_grid": "pre_correction_active_array",
            "intrinsic_calibration": {"available": True, "value": [500.0, 500.0, 320.0, 240.0, 0.0]},
            "lens_distortion": {"available": True, "value": [0.0, 0.0, 0.0, 0.0, 0.0]},
        }],
        "captures": [capture],
        "files": {PAYLOAD_NAME: record},
    }
    try:
        yield report, root
    finally:
        shutil.rmtree(root, ignore_errors=False)


def test_legacy_export_still_accepts_empty_camera_capability_report(phone_bundle):
    _, root = phone_bundle
    record = {"sha256": hashlib.sha256((root / PAYLOAD_NAME).read_bytes()).hexdigest(),
              "bytes": (root / PAYLOAD_NAME).stat().st_size}
    report = {
        "schema_version": 1,
        "session_id": "capability_only",
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
        "captures": [],
        "files": {PAYLOAD_NAME: record},
    }

    assert capture_report.validate_export(report, root)["captures"] == []


def test_phone_session_export_rejects_empty_capability_report(phone_bundle):
    _, root = phone_bundle
    record = {"sha256": hashlib.sha256((root / PAYLOAD_NAME).read_bytes()).hexdigest(),
              "bytes": (root / PAYLOAD_NAME).stat().st_size}
    report = {
        "schema_version": 1,
        "session_id": "capability_only",
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
        "captures": [],
        "files": {PAYLOAD_NAME: record},
    }

    with pytest.raises(ValueError, match="at least one image"):
        capture_report.validate_phone_session_export(report, root)


def test_phone_session_export_rejects_failed_single_camera_capture(phone_bundle):
    report, root = phone_bundle
    report["checks"][0] = {
        "id": "single_camera_control", "status": "FAIL", "reason": "Camera stream failed",
    }

    with pytest.raises(ValueError, match="single-camera capture did not pass"):
        capture_report.validate_phone_session_export(report, root)


def test_phone_session_export_accepts_hashed_single_camera_image(phone_bundle):
    report, root = phone_bundle

    checked = capture_report.validate_phone_session_export(report, root)

    assert len(checked["captures"]) == 1
    assert checked["checks"][0]["id"] == "single_camera_control"


def test_reader_preserves_rgb_calibration_grid_and_marks_missing_streams(phone_bundle):
    report, root = phone_bundle

    frames = read_phone_session(report, root, capture_report.validate_phone_session_export)

    assert len(frames) == 1
    frame = frames[0]
    assert frame.image_bytes == (root / PAYLOAD_NAME).read_bytes()
    assert (frame.image_width, frame.image_height) == (640, 480)
    assert frame.intrinsics == (500.0, 500.0, 320.0, 240.0, 0.0)
    assert frame.intrinsics_pixel_grid == "pre_correction_active_array"
    assert frame.active_array_rect == (100, 100, 4000, 3000)
    assert frame.pre_correction_active_array_rect == (0, 0, 4100, 3100)
    assert frame.distortion_correction_mode == 0
    assert frame.geometry_ready is True
    assert frame.sensor_to_image_crop_scale == (1.0, 1.0)
    assert frame.sensor_pixel_array_size == (4200, 3200)
    assert frame.crop_region == (0, 0, 640, 480)
    assert frame.timestamp_ns == 1700000000
    assert frame.timestamp_source == "SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME"
    assert frame.depth_bytes is None
    assert frame.depth_unavailable_reason == "This APK does not include ARCore"
    assert frame.pose is None
    assert frame.pose_unavailable_reason == "This APK does not include ARCore"
    assert frame.world_id is None
    assert frame.segment_id is None


def test_reader_keeps_frame_but_marks_missing_intrinsics_unavailable(phone_bundle):
    report, root = phone_bundle
    report["cameras"][0]["intrinsic_calibration"] = {
        "available": False, "value": None, "reason": "Camera2 did not report this field",
    }

    with pytest.raises(ValueError, match="intrinsic calibration"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)


def test_reader_rejects_capture_without_matching_camera_metadata(phone_bundle):
    report, root = phone_bundle
    report["cameras"] = []

    with pytest.raises(ValueError, match="camera metadata"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)


def test_reader_rejects_bytes_that_are_not_a_decodable_image(phone_bundle):
    report, root = phone_bundle
    image_path = root / PAYLOAD_NAME
    image_path.write_bytes(b"not an image")
    record = {"sha256": hashlib.sha256(b"not an image").hexdigest(), "bytes": 12}
    report["files"][PAYLOAD_NAME] = record
    report["captures"][0]["sha256"] = record["sha256"]
    report["checks"][0]["details"][0]["sha256"] = record["sha256"]

    with pytest.raises(ValueError, match="not a readable image"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)


def test_reader_rejects_capture_grid_outside_selected_active_array(phone_bundle):
    report, root = phone_bundle
    report["captures"][0]["crop_region"] = [0, 0, 5000, 480]
    report["checks"][0]["details"][0]["crop_region"] = [0, 0, 5000, 480]

    with pytest.raises(ValueError, match="active array rectangle"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)


def test_phone_export_rejects_passing_check_without_matching_frame(phone_bundle):
    report, root = phone_bundle
    report["checks"][0]["details"] = []

    with pytest.raises(ValueError, match="does not identify the exported frames"):
        capture_report.validate_phone_session_export(report, root)


def test_reader_rejects_image_size_that_disagrees_with_capture_record(phone_bundle):
    report, root = phone_bundle
    report["captures"][0]["width"] = 320
    report["checks"][0]["details"][0]["width"] = 320

    with pytest.raises(ValueError, match="image grid disagrees"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)


@pytest.mark.parametrize(
    ("mode", "mode_name", "geometry_ready"),
    [(0, "OFF", True), (1, "FAST", False), (None, "UNAVAILABLE", False)],
)
def test_reader_marks_metric_readiness_from_recorded_distortion_mode(
        phone_bundle, mode, mode_name, geometry_ready):
    report, root = phone_bundle
    capture = report["captures"][0]
    details = report["checks"][0]["details"][0]
    capture["distortion_correction_mode"] = mode
    capture["distortion_correction_mode_name"] = mode_name
    details["distortion_correction_mode"] = mode
    details["distortion_correction_mode_name"] = mode_name
    if mode == 1:
        capture["crop_region"] = [100, 100, 740, 580]
        details["crop_region"] = [100, 100, 740, 580]

    frame = read_phone_session(report, root, capture_report.validate_phone_session_export)[0]

    assert frame.distortion_correction_mode == mode
    assert frame.geometry_ready is geometry_ready
    if not geometry_ready:
        assert frame.geometry_unavailable_reason


def test_reader_accepts_pre_correction_crop_outside_active_but_inside_pre_correction_array(phone_bundle):
    report, root = phone_bundle
    crop = [50, 50, 690, 530]
    report["captures"][0]["crop_region"] = crop
    report["checks"][0]["details"][0]["crop_region"] = crop

    frame = read_phone_session(report, root, capture_report.validate_phone_session_export)[0]

    assert frame.geometry_ready is True
    assert frame.crop_region == tuple(crop)


def test_reader_rejects_crop_outside_active_array_when_correction_is_on(phone_bundle):
    report, root = phone_bundle
    crop = [50, 50, 690, 530]
    report["captures"][0]["crop_region"] = crop
    report["checks"][0]["details"][0]["crop_region"] = crop
    report["captures"][0]["distortion_correction_mode"] = 1
    report["captures"][0]["distortion_correction_mode_name"] = "FAST"
    report["checks"][0]["details"][0]["distortion_correction_mode"] = 1
    report["checks"][0]["details"][0]["distortion_correction_mode_name"] = "FAST"

    with pytest.raises(ValueError, match="active array rectangle"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)


def test_reader_rejects_truncated_image_data(phone_bundle):
    report, root = phone_bundle
    image_path = root / PAYLOAD_NAME
    original = image_path.read_bytes()
    payload = original[:len(original) // 2]
    image_path.write_bytes(payload)
    record = {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
    report["files"][PAYLOAD_NAME] = record
    report["captures"][0]["sha256"] = record["sha256"]
    report["checks"][0]["details"][0]["sha256"] = record["sha256"]

    with pytest.raises(ValueError, match="not a readable image"):
        read_phone_session(report, root, capture_report.validate_phone_session_export)
