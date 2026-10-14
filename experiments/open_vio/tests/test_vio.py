"""Config writers, trajectory readers and scoring for the open visual-inertial systems."""

import json
import re

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

import configs
import score
import trajectories

T_CAM_IMU = np.array([[0.0, -1.0, 0.0, 0.01], [0.0, 0.0, -1.0, 0.02], [1.0, 0.0, 0.0, 0.03], [0.0, 0.0, 0.0, 1.0]])
EQUI = {"T_cam_imu": T_CAM_IMU, "timeshift_cam_imu": 0.002, "intrinsics": [190.0, 191.0, 254.0, 256.0],
        "distortion": [0.1, 0.01, -0.02, 0.003], "model": "pinhole-equidistant", "resolution": [512, 512]}
RADTAN = EQUI | {"model": "pinhole-radtan", "distortion": [-0.2, 0.05, 0.001, -0.002], "resolution": [640, 480]}
def _matrix_after(text, key):
    """The first 16 numbers inside the brackets after key, as a 4 x 4 matrix."""
    inside = text.split(key, 1)[1].split("[", 1)[1].split("]", 1)[0]
    return np.array([float(v) for v in re.findall(r"-?[\d.]+(?:e-?\d+)?", inside)]).reshape(4, 4)


IMU = {"accelerometer_noise_density": 0.0028, "accelerometer_random_walk": 0.00086,
       "gyroscope_noise_density": 0.00016, "gyroscope_random_walk": 2.2e-05, "update_rate": 200.0}


def test_set_value_replaces_one_yaml_line_and_keeps_its_comment():
    text = "a: 1\n    sigma_g_c: 0.0008 #0.001 # gyro noise\nb: 2\n"
    assert configs.set_value(text, "sigma_g_c", 0.5) == "a: 1\n    sigma_g_c: 0.5 #0.001 # gyro noise\nb: 2\n"
    with pytest.raises(KeyError):
        configs.set_value(text, "missing", 1)


def test_basalt_calibration_uses_the_inverse_transform_and_kb4_for_equidistant():
    calib = configs.basalt_calib(EQUI, IMU)["value0"]
    pose = calib["T_imu_cam"][0]
    imu_from_camera = np.eye(4)
    imu_from_camera[:3, :3] = Rotation.from_quat([pose["qx"], pose["qy"], pose["qz"], pose["qw"]]).as_matrix()
    imu_from_camera[:3, 3] = [pose["px"], pose["py"], pose["pz"]]
    assert np.allclose(imu_from_camera @ T_CAM_IMU, np.eye(4))
    camera = calib["intrinsics"][0]
    assert camera["camera_type"] == "kb4" and camera["intrinsics"]["k4"] == 0.003 and camera["intrinsics"]["fy"] == 191.0
    assert calib["resolution"] == [[512, 512]] and calib["imu_update_rate"] == 200.0
    assert calib["gyro_noise_std"] == [0.00016] * 3 and calib["accel_bias_std"] == [0.00086] * 3
    assert calib["cam_time_offset_ns"] == 2_000_000
    json.dumps(calib)


def test_basalt_calibration_maps_radtan_to_its_eight_coefficient_model():
    camera = configs.basalt_calib(RADTAN, IMU)["value0"]["intrinsics"][0]
    assert camera["camera_type"] == "pinhole-radtan8"
    assert [camera["intrinsics"][k] for k in ("k1", "k2", "p1", "p2", "k3")] == [-0.2, 0.05, 0.001, -0.002, 0.0]


OKVIS_TEMPLATE = """%YAML:1.0
cameras:
     - {T_SC:
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        image_dimension: [512, 512],
        distortion_type: equidistant,
        slam_use: okvis}
     - {T_SC: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], slam_use: okvis}


# additional camera parameters
camera_parameters:
    image_delay: 0.00 # [s] timestamp_camera_correct = timestamp_camera - image_delay
    sync_cameras: [0,1] # the cameras that will be synchronised
imu_parameters:
    sigma_g_c: 0.0008 # gyro
    sigma_a_c: 0.01 # acc
    sigma_gw_c: 0.00022 # gyro drift
    sigma_aw_c: 0.001 # acc drift
frontend_parameters:
    use_cnn: true # sky
"""


def test_okvis2_config_has_one_camera_with_the_sensor_from_camera_transform():
    text = configs.okvis2_yaml(OKVIS_TEMPLATE, RADTAN, IMU)
    assert text.count("T_SC") == 1 and "distortion_type: radialtangential" in text
    t_sc = _matrix_after(text, "T_SC:")
    assert np.allclose(t_sc @ T_CAM_IMU, np.eye(4), atol=1e-9)
    assert "sync_cameras: [0]" in text and "image_delay: -0.002" in text and "use_cnn: false" in text
    assert "sigma_g_c: 0.00016" in text and "sigma_aw_c: 0.00086" in text and "focal_length: [190.0, 191.0]" in text


def test_okvis2_config_can_keep_the_template_noise():
    text = configs.okvis2_yaml(OKVIS_TEMPLATE, RADTAN, IMU, template_noise=True)
    assert "sigma_g_c: 0.0008" in text and "sigma_aw_c: 0.001 " in text and text.count("T_SC") == 1


def test_openvins_files_are_kalibr_format_with_one_camera():
    template = "max_cameras: 2 # n\nuse_stereo: true # s\nuse_mask: true # m\n"
    imu_template = "imu0:\n  accelerometer_noise_density: 1\n  accelerometer_random_walk: 1\n  gyroscope_noise_density: 1\n  gyroscope_random_walk: 1\n  update_rate: 1\n"
    files = configs.openvins_files(template, imu_template, EQUI, IMU)
    assert "max_cameras: 1" in files["estimator_config.yaml"] and "use_stereo: false" in files["estimator_config.yaml"]
    assert "use_mask: false" in files["estimator_config.yaml"]
    chain = files["kalibr_imucam_chain.yaml"]
    assert chain.startswith("%YAML:1.0") and "cam1" not in chain and "distortion_model: equidistant" in chain
    assert "timeshift_cam_imu: 0.002" in chain
    assert "gyroscope_random_walk: 2.2e-05" in files["kalibr_imu_chain.yaml"]


def test_kimera_camera_file_has_body_from_sensor_and_its_distortion_name():
    left = "T_BS:\n  cols: 4\n  rows: 4\n  data: [1, 0, 0, 0,\n         0, 1, 0, 0,\n         0, 0, 1, 0,\n         0.0, 0.0, 0.0, 1.0]\n\nrate_hz: 20\nresolution: [752, 480]\nintrinsics: [1, 1, 1, 1] #fu\ndistortion_model: radial-tangential\ndistortion_coefficients: [0, 0, 0, 0]\n"
    imu = "rate_hz: 200\ngyroscope_noise_density: 1 # g\ngyroscope_random_walk: 1\naccelerometer_noise_density: 1\naccelerometer_random_walk: 1\nimu_time_shift: 0.0\n"
    files = configs.kimera_files(left, imu, EQUI, IMU, camera_rate_hz=20)
    camera = files["LeftCameraParams.yaml"]
    data = _matrix_after(camera, "data:")
    assert np.allclose(data @ T_CAM_IMU, np.eye(4), atol=1e-9)
    assert "distortion_model: equidistant" in camera and "resolution: [512, 512]" in camera
    assert "imu_time_shift: 0.002" in files["ImuParams.yaml"] and "gyroscope_noise_density: 0.00016" in files["ImuParams.yaml"]
    kept = configs.kimera_files(left, imu, EQUI, IMU, camera_rate_hz=20, template_noise=True)["ImuParams.yaml"]
    assert "gyroscope_noise_density: 1 # g" in kept and "imu_time_shift: 0.002" in kept


def test_trajectory_readers_give_seconds_and_imu_to_world(tmp_path):
    q = Rotation.from_euler("z", 30, degrees=True).as_quat()  # x, y, z, w
    (tmp_path / "tum.txt").write_text(f"# t x y z qx qy qz qw\n1.5 1 2 3 {q[0]} {q[1]} {q[2]} {q[3]} 9 9\n")
    (tmp_path / "kimera.csv").write_text(f"#timestamp,x,y,z,qw,qx,qy,qz,vx\n1500000000,1,2,3,{q[3]},{q[0]},{q[1]},{q[2]},0\n")
    (tmp_path / "euroc.csv").write_text(f"#timestamp [ns],p_x,p_y,p_z,q_w,q_x,q_y,q_z\n1500000000,1,2,3,{q[3]},{q[0]},{q[1]},{q[2]}\n")
    for poses in (trajectories.read_tum(tmp_path / "tum.txt"), trajectories.read_csv(tmp_path / "kimera.csv", quaternion="wxyz"),
                  trajectories.read_csv(tmp_path / "euroc.csv", quaternion="wxyz")):
        (t, matrix), = poses
        assert t == pytest.approx(1.5) and np.allclose(matrix[:3, 3], [1, 2, 3])
        assert np.allclose(matrix[:3, :3], Rotation.from_euler("z", 30, degrees=True).as_matrix())


def _path(scale=1.0):
    out = []
    for k in range(50):
        m = np.eye(4)
        m[:3, :3] = Rotation.from_euler("xyz", [0.01 * k, 0.02 * k, 0.03 * k]).as_matrix()
        m[:3, 3] = scale * np.array([0.1 * k, np.sin(0.2 * k), 0.05 * k ** 1.5])
        out.append((0.1 * k, m))
    return out


def test_score_is_zero_against_itself_and_scaled_copy_is_caught_only_without_a_scale_fit():
    exact = score.score(_path(), _path(), tolerance_s=0.01)
    assert exact["ate_rigid_rmse_m"] == pytest.approx(0, abs=1e-9) and exact["matched"] == 50
    scaled = score.score(_path(1.1), _path(), tolerance_s=0.01)
    assert scaled["ate_rigid_rmse_m"] > 0.05 and scaled["ate_scaled_rmse_m"] == pytest.approx(0, abs=1e-6)


def test_imu_poses_move_to_the_camera_frame():
    (_, world_camera), = score.to_camera([(0.0, np.eye(4))], T_CAM_IMU)
    assert np.allclose(world_camera @ T_CAM_IMU, np.eye(4))


def test_report_lists_scored_and_failed_runs(tmp_path):
    import vio_report as report
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "scores.json").write_text(json.dumps({"exit_code": 0, "ate_rigid_rmse_m": 0.1234, "ate_scaled_rmse_m": 0.1,
                                                            "rpe_1s_translation_rmse_m": 0.02, "tracked_fraction": 0.95,
                                                            "ms_per_frame_whole_run": 12.4}))
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "scores.json").write_text(json.dumps({"exit_code": 139, "error": "no trajectory"}))
    (tmp_path / "c").mkdir()
    lines = report.table(tmp_path).splitlines()
    assert len(lines) == 4 and "| a | 0.123 | 0.100 | 0.020 | 95% | 12 |" in lines
    assert "| b | failed: no trajectory (exit 139) | | | | |" in lines
