"""Calibration helpers: Allan noise fit, Kalibr input files, the ARCore cross-check and transform comparison."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

import allan
import arcore_extrinsics
import kalibr_files
import recording

RATE = 400.0


def _gyro_at_rest(seconds, density, random_walk, seed=0):
    """White noise of the given density (rad/s/sqrt(Hz)) plus a bias that random-walks (rad/s^2/sqrt(Hz))."""
    rng = np.random.default_rng(seed)
    n, dt = int(seconds * RATE), 1 / RATE
    bias = np.cumsum(rng.normal(0, random_walk * np.sqrt(dt), n))
    return rng.normal(0, density / np.sqrt(dt), n) + bias


def test_allan_fit_recovers_noise_density_and_random_walk():
    taus, deviation = allan.allan_deviation(_gyro_at_rest(4000, 0.004, 0.0002), 1 / RATE)
    density, walk = allan.fit_noise(taus, deviation)
    assert density == pytest.approx(0.004, rel=0.10)
    assert walk == pytest.approx(0.0002, rel=0.25)


def test_short_recording_has_no_random_walk_estimate():
    taus, deviation = allan.allan_deviation(_gyro_at_rest(60, 0.004, 0.0), 1 / RATE)
    density, walk = allan.fit_noise(taus, deviation)
    assert density == pytest.approx(0.004, rel=0.10) and walk is None


def test_imu_noise_reads_both_sensors_of_a_recording(make_recording):
    rec = recording.load(make_recording(kind="imu_only", seconds=30.0))
    rng = np.random.default_rng(1)
    rec.gyro = rng.normal(0, 0.004 * np.sqrt(400), rec.gyro.shape)
    rec.accel = rng.normal(0, 0.02 * np.sqrt(200), rec.accel.shape)
    noise = allan.imu_noise(rec)
    assert noise["gyro"]["noise_density"] == pytest.approx(0.004, rel=0.10)
    assert noise["accel"]["noise_density"] == pytest.approx(0.02, rel=0.10)
    assert noise["gyro"]["rate_hz"] == pytest.approx(400, rel=0.01)


def test_kalibr_folder_from_an_euroc_folder(make_recording, tmp_path):
    pytest.importorskip("cv2")
    euroc = recording.to_euroc(recording.load(make_recording(seconds=1.0)), tmp_path / "euroc")
    out = kalibr_files.to_kalibr_folder(euroc / "mav0", tmp_path / "kalibr")
    images = sorted((out / "cam0").glob("*.png"))
    assert len(images) == 30 and images[0].stem.isdigit()
    lines = (out / "imu0.csv").read_text().splitlines()
    assert lines[0] == "timestamp,omega_x,omega_y,omega_z,alpha_x,alpha_y,alpha_z"
    euroc_rows = (euroc / "mav0" / "imu0" / "data.csv").read_text().splitlines()[1:]
    assert lines[1:] == euroc_rows


def test_imu_yaml_applies_the_inflation():
    noise = {"gyro": {"noise_density": 1e-4, "random_walk": 2e-6, "rate_hz": 400.0},
             "accel": {"noise_density": 2e-3, "random_walk": 5e-5, "rate_hz": 400.0}}
    text = kalibr_files.imu_yaml(noise, white_factor=2, walk_factor=10)
    values = dict(line.split(": ") for line in text.splitlines() if ": " in line)
    assert values["rostopic"] == "/imu0" and float(values["update_rate"]) == 400.0
    assert float(values["gyroscope_noise_density"]) == pytest.approx(2e-4)
    assert float(values["gyroscope_random_walk"]) == pytest.approx(2e-5)
    assert float(values["accelerometer_noise_density"]) == pytest.approx(4e-3)
    assert float(values["accelerometer_random_walk"]) == pytest.approx(5e-4)


def test_imu_yaml_refuses_a_missing_random_walk():
    noise = {"gyro": {"noise_density": 1e-4, "random_walk": None, "rate_hz": 400.0},
             "accel": {"noise_density": 2e-3, "random_walk": 5e-5, "rate_hz": 400.0}}
    with pytest.raises(ValueError, match="random walk"):
        kalibr_files.imu_yaml(noise)


def test_target_yaml_uses_the_measured_tag_size():
    text = kalibr_files.aprilgrid_yaml(cols=6, rows=8, tag_size_m=0.0237, spacing=0.3)
    assert "target_type: 'aprilgrid'" in text and "tagCols: 6" in text and "tagRows: 8" in text
    assert "tagSize: 0.0237" in text and "tagSpacing: 0.3" in text


def _pose(r: Rotation, t) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = r.as_matrix(), t
    return m


def test_arcore_cross_check_recovers_the_camera_to_device_transform():
    camera_from_device = _pose(Rotation.from_euler("xyz", [178, 2, 91], degrees=True), [0.01, -0.03, 0.005])
    rows = []
    for k in range(40):
        world_camera_cv = _pose(Rotation.from_rotvec([0.02 * k, -0.01 * k, 0.3]), [0.1 * k, 0.0, 1.0])
        world_device = world_camera_cv @ camera_from_device
        gl = Rotation.from_matrix(world_camera_cv[:3, :3]) * Rotation.from_quat([1.0, 0, 0, 0])
        cells = {"t_ns": str(k), "camera_t_ns": str(k), "tracking": "TRACKING"}
        cells |= dict(zip(["tx", "ty", "tz", "qx", "qy", "qz", "qw"], map(str, [*world_camera_cv[:3, 3], *gl.as_quat()])))
        dq = Rotation.from_matrix(world_device[:3, :3]).as_quat()
        cells |= dict(zip(["dev_tx", "dev_ty", "dev_tz", "dev_qx", "dev_qy", "dev_qz", "dev_qw"], map(str, [*world_device[:3, 3], *dq])))
        rows.append(cells)
    rec = recording.Recording(root=None, meta={"kind": "walk"}, image_times=np.zeros(0, np.int64), arcore=rows)
    estimate, spread_deg = arcore_extrinsics.camera_from_device(rec)
    assert np.allclose(estimate, camera_from_device, atol=1e-6) and spread_deg < 1e-4


def test_read_camchain_gives_transform_offset_and_intrinsics(tmp_path):
    path = tmp_path / "data-camchain-imucam.yaml"
    path.write_text("cam0:\n  T_cam_imu:\n  - [0.0, -1.0, 0.0, 0.01]\n  - [1.0, 0.0, 0.0, 0.02]\n  - [0.0, 0.0, 1.0, 0.03]\n"
                    "  - [0.0, 0.0, 0.0, 1.0]\n  camera_model: pinhole\n  distortion_coeffs: [0.1, 0.01, 0.0, 0.0]\n"
                    "  distortion_model: radtan\n  intrinsics: [500.0, 501.0, 320.0, 240.0]\n  resolution: [640, 480]\n"
                    "  timeshift_cam_imu: -0.0125\n")
    chain = kalibr_files.read_camchain(path)
    assert chain["T_cam_imu"].shape == (4, 4) and chain["T_cam_imu"][1, 3] == 0.02
    assert chain["timeshift_cam_imu"] == -0.0125 and chain["intrinsics"] == [500.0, 501.0, 320.0, 240.0]
    path.write_text(path.read_text().replace("  timeshift_cam_imu: -0.0125\n", ""))
    assert kalibr_files.read_camchain(path)["timeshift_cam_imu"] is None


def test_transform_difference_reports_angle_and_distance():
    a = _pose(Rotation.from_euler("z", 10, degrees=True), [0, 0, 0])
    b = _pose(Rotation.from_euler("z", 12, degrees=True), [0.03, 0.04, 0])
    angle, distance = kalibr_files.transform_difference(a, b)
    assert angle == pytest.approx(2.0) and distance == pytest.approx(0.05)
