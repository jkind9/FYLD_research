"""Clock alignment between the camera (through ARCore's poses) and the gyroscope."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

import clock_check
import recording
from synthetic import rotation_angle, rotation_rate


def test_offset_estimate_recovers_a_known_shift_and_its_sign(make_recording):
    for shift in (0.012, -0.020):
        rec = recording.load(make_recording(name=f"r{shift}", seconds=6.0, imu_offset_s=shift))
        offset_s, peak = clock_check.camera_to_gyro_offset(rec)
        assert offset_s == pytest.approx(shift, abs=0.001) and peak > 0.9


def test_offset_search_on_signals_without_motion_reports_no_peak():
    t = np.arange(0, 5, 0.01)
    flat = np.ones_like(t)
    offset, peak = clock_check.estimate_offset(t, flat, t, flat)
    assert np.isnan(offset) and np.isnan(peak)


def test_angular_speed_from_poses_matches_the_rotation_rate():
    t = np.arange(0, 2, 1 / 30)
    q = Rotation.from_rotvec(np.outer(rotation_angle(t), [1.0, 0, 0])).as_quat()
    mid, speed = clock_check.angular_speed_from_poses(t, q)
    assert np.allclose(speed, np.abs(rotation_rate(mid)), atol=0.05)


def test_report_lists_rates_gaps_and_clock_base(make_recording):
    report = clock_check.report(recording.load(make_recording(seconds=6.0, imu_offset_s=0.012)))
    assert report["camera"]["rate_hz"] == pytest.approx(30, abs=0.1)
    assert report["gyro"]["rate_hz"] == pytest.approx(400, abs=1)
    assert report["accel"]["rate_hz"] == pytest.approx(200, abs=1)
    assert report["gyro"]["gaps_over_1_5x"] == 0
    assert report["same_clock_base"] is True
    assert report["arcore_frames_matching_an_image"] == 1.0
    assert report["camera_to_gyro_offset_ms"] == pytest.approx(12, abs=1)
    assert report["expected_arcore_pose_lag_ms"] == pytest.approx(4 + 10)  # half the 8 ms exposure + half the 20 ms readout
    assert report["problems"] == []


def test_report_for_motion_sensors_alone_skips_the_camera(make_recording):
    report = clock_check.report(recording.load(make_recording(kind="imu_only")))
    assert report["camera"] is None and report["camera_to_gyro_offset_ms"] is None
