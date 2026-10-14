"""The camera-to-IMU transform implied by ARCore's own poses in a raw recording, to compare with Kalibr's.

ARCore reports, per frame, the camera pose and the pose of the Android sensor coordinate system (the axes the
gyroscope and accelerometer use). Their relation is ARCore's internal camera-to-IMU calibration as it applies it.
This reads public outputs only; it says nothing about how ARCore estimates them.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

import recording


def _matrix(position, quaternion) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = Rotation.from_quat(quaternion).as_matrix(), position
    return m


def camera_from_device(rec: recording.Recording) -> tuple[np.ndarray, float]:
    """T_cam_device (OpenCV camera axes, Kalibr's T_cam_imu convention) and the spread of its rotation in degrees."""
    estimates = []
    for row in rec.arcore:
        if row["tracking"] != "TRACKING":
            continue
        camera = [float(row[k]) for k in ("tx", "ty", "tz", "qx", "qy", "qz", "qw")]
        device = [float(row[k]) for k in ("dev_tx", "dev_ty", "dev_tz", "dev_qx", "dev_qy", "dev_qz", "dev_qw")]
        world_camera = _matrix(camera[:3], recording.opencv_quaternion(np.array(camera[3:])))
        estimates.append(np.linalg.inv(world_camera) @ _matrix(device[:3], device[3:]))
    rotations = Rotation.from_matrix([e[:3, :3] for e in estimates])
    mean = rotations.mean()
    out = np.eye(4)
    out[:3, :3], out[:3, 3] = mean.as_matrix(), np.median([e[:3, 3] for e in estimates], axis=0)
    spread = float(np.degrees(np.max((mean.inv() * rotations).magnitude())))
    return out, spread
