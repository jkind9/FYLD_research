"""One camera plus IMU, from a Kalibr calibration, written in each visual-inertial system's own config format.

`cam` is kalibr_files.read_camchain's result (T_cam_imu maps IMU points into the camera; t_imu = t_cam + timeshift);
`imu` holds Kalibr's IMU file keys. Everything that is not calibration comes from the system's own template
(its shipped TUM-VI or EuRoC config), so only the camera, transform, time shift and noise change.
"""

from __future__ import annotations

import re

import numpy as np
from scipy.spatial.transform import Rotation

_KALIBR_TO_SYSTEM = {"pinhole-equidistant": ("equidistant", "kb4", "equidistant"),
                     "pinhole-radtan": ("radialtangential", "pinhole-radtan8", "radial-tangential")}


def set_value(text: str, key: str, value) -> str:
    """Replace the value of one `key: value` line, keeping indentation and any trailing comment."""
    pattern = re.compile(rf"^(\s*{re.escape(key)}:[ \t]*)([^#\n]*?)([ \t]*(#.*)?)$", re.MULTILINE)
    if not pattern.search(text):
        raise KeyError(key)
    return pattern.sub(lambda m: f"{m.group(1)}{value}{m.group(3)}", text, count=1)


def _numbers(values) -> str:
    return "[" + ", ".join(repr(float(v)) for v in values) + "]"


def _sensor_from_camera(cam: dict) -> np.ndarray:
    return np.linalg.inv(np.asarray(cam["T_cam_imu"], dtype=float))


def basalt_calib(cam: dict, imu: dict) -> dict:
    """Basalt calibration JSON: T_imu_cam as position + quaternion; noise as continuous-time densities."""
    imu_from_camera = _sensor_from_camera(cam)
    q = Rotation.from_matrix(imu_from_camera[:3, :3]).as_quat()
    fx, fy, cx, cy = cam["intrinsics"]
    camera_type = _KALIBR_TO_SYSTEM[cam["model"]][1]
    intrinsics = {"fx": fx, "fy": fy, "cx": cx, "cy": cy}
    if camera_type == "kb4":
        intrinsics |= dict(zip(("k1", "k2", "k3", "k4"), cam["distortion"]))
    else:
        k1, k2, p1, p2 = cam["distortion"]
        intrinsics |= {"k1": k1, "k2": k2, "p1": p1, "p2": p2, "k3": 0.0, "k4": 0.0, "k5": 0.0, "k6": 0.0, "rpmax": 0.0}
    shift = cam.get("timeshift_cam_imu") or 0.0
    return {"value0": {
        "T_imu_cam": [dict(zip(("px", "py", "pz"), imu_from_camera[:3, 3].tolist())) | dict(zip(("qx", "qy", "qz", "qw"), q.tolist()))],
        "intrinsics": [{"camera_type": camera_type, "intrinsics": intrinsics}],
        "resolution": [list(cam["resolution"])],
        "calib_accel_bias": [0.0] * 9, "calib_gyro_bias": [0.0] * 12,
        "imu_update_rate": float(imu["update_rate"]),
        "accel_noise_std": [imu["accelerometer_noise_density"]] * 3, "gyro_noise_std": [imu["gyroscope_noise_density"]] * 3,
        "accel_bias_std": [imu["accelerometer_random_walk"]] * 3, "gyro_bias_std": [imu["gyroscope_random_walk"]] * 3,
        # Basalt adds this to image times; Kalibr's shift moves camera times onto the IMU clock.
        "cam_time_offset_ns": int(round(shift * 1e9)),
        "vignette": []}}


def okvis2_yaml(template: str, cam: dict, imu: dict, *, template_noise: bool = False) -> str:
    """OKVIS2 config: the template's cameras list replaced by this camera (T_SC: camera to IMU sensor).

    template_noise keeps the template's own IMU noise values instead of the calibration's.
    """
    fx, fy, cx, cy = cam["intrinsics"]
    camera = (f"     - {{T_SC: {_numbers(_sensor_from_camera(cam).ravel())},\n"
              f"        image_dimension: {list(cam['resolution'])},\n"
              f"        distortion_coefficients: {_numbers(cam['distortion'])},\n"
              f"        distortion_type: {_KALIBR_TO_SYSTEM[cam['model']][0]},\n"
              f"        focal_length: [{fx}, {fy}],\n        principal_point: [{cx}, {cy}],\n"
              f"        camera_type: gray,\n        slam_use: okvis}}\n\n")
    start = template.index("cameras:\n") + len("cameras:\n")
    text = template[:start] + camera + template[template.index("# additional camera parameters"):]
    text = set_value(text, "sync_cameras", "[0]")
    text = set_value(text, "image_delay", -(cam.get("timeshift_cam_imu") or 0.0))
    text = set_value(text, "use_cnn", "false")
    if template_noise:
        return text
    for key, source in (("sigma_g_c", "gyroscope_noise_density"), ("sigma_a_c", "accelerometer_noise_density"),
                        ("sigma_gw_c", "gyroscope_random_walk"), ("sigma_aw_c", "accelerometer_random_walk")):
        text = set_value(text, key, imu[source])
    return text


def openvins_files(estimator_template: str, imu_template: str, cam: dict, imu: dict) -> dict[str, str]:
    """OpenVINS reads Kalibr's own formats; the estimator template is set to one camera without a mask."""
    estimator = set_value(estimator_template, "max_cameras", 1)
    estimator = set_value(set_value(estimator, "use_stereo", "false"), "use_mask", "false")
    rows = "\n".join(f"    - {_numbers(row)}" for row in np.asarray(cam["T_cam_imu"], dtype=float))
    chain = (f"%YAML:1.0\n\ncam0:\n  T_cam_imu:\n{rows}\n  cam_overlaps: []\n  camera_model: pinhole\n"
             f"  distortion_coeffs: {_numbers(cam['distortion'])}\n  distortion_model: {cam['model'].split('-')[1]}\n"
             f"  intrinsics: {_numbers(cam['intrinsics'])}\n  resolution: {list(cam['resolution'])}\n"
             f"  timeshift_cam_imu: {cam.get('timeshift_cam_imu') or 0.0}\n  rostopic: /cam0/image_raw\n")
    imu_text = imu_template
    for key in ("accelerometer_noise_density", "accelerometer_random_walk", "gyroscope_noise_density",
                "gyroscope_random_walk", "update_rate"):
        imu_text = set_value(imu_text, key, imu[key])
    return {"estimator_config.yaml": estimator, "kalibr_imucam_chain.yaml": chain, "kalibr_imu_chain.yaml": imu_text}


def kimera_files(left_template: str, imu_template: str, cam: dict, imu: dict, *, camera_rate_hz: float,
                 template_noise: bool = False) -> dict[str, str]:
    """Kimera's left camera (T_BS: camera to body, the body being the IMU) and IMU parameter files.

    template_noise keeps the template's own IMU noise values instead of the calibration's.
    """
    rows = _sensor_from_camera(cam)
    data = ",\n         ".join(", ".join(repr(float(v)) for v in row) for row in rows)
    start = left_template.index("data: [") + len("data: [")
    left = left_template[:start] + data + left_template[left_template.index("]", start):]
    left = set_value(left, "rate_hz", camera_rate_hz)
    left = set_value(left, "resolution", list(cam["resolution"]))
    left = set_value(left, "intrinsics", _numbers(cam["intrinsics"]))
    left = set_value(left, "distortion_model", _KALIBR_TO_SYSTEM[cam["model"]][2])
    left = set_value(left, "distortion_coefficients", _numbers(cam["distortion"]))
    imu_text = set_value(imu_template, "rate_hz", imu["update_rate"])
    for key in () if template_noise else ("gyroscope_noise_density", "gyroscope_random_walk",
                                          "accelerometer_noise_density", "accelerometer_random_walk"):
        imu_text = set_value(imu_text, key, imu[key])
    imu_text = set_value(imu_text, "imu_time_shift", cam.get("timeshift_cam_imu") or 0.0)
    return {"LeftCameraParams.yaml": left, "ImuParams.yaml": imu_text}
