"""A small synthetic recording in the capture app's format (phone session v2), shared by the host tests."""

from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

import fake_phone  # experiment 01's stand-in for the capture app; conftest puts it on the import path

START_NS = 5_000_000_000_000  # elapsedRealtime about 83 minutes after boot
WIDTH, HEIGHT = 8, 6
IMU_BATCH_NS = 100_000_000


def rotation_angle(t_s):
    """Angle in radians about one fixed axis; smooth, with speed changes the offset search can lock on to."""
    return 0.4 * np.sin(2 * np.pi * 0.7 * t_s) + 0.25 * np.sin(2 * np.pi * 1.9 * t_s + 0.5)


def rotation_rate(t_s):
    return 0.4 * 2 * np.pi * 0.7 * np.cos(2 * np.pi * 0.7 * t_s) + 0.25 * 2 * np.pi * 1.9 * np.cos(2 * np.pi * 1.9 * t_s + 0.5)


def _imu_batches(rows):
    """Rows in time order, cut into one batch per 100 ms as the app sends them."""
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    batch, start = [], rows[0][0]
    for row in rows:
        if row[0] - start >= IMU_BATCH_NS:
            yield fake_phone.imu(batch)
            batch, start = [], row[0]
        batch.append(row)
    yield fake_phone.imu(batch)


def write_recording(root: Path, *, seconds=4.0, imu_offset_s=0.0, camera_clock_shift_ns=0, kind="walk", stopped=True) -> Path:
    """Writes a session folder and returns it; the gyroscope stamps a motion `imu_offset_s` later than the camera does."""
    axis = np.array([0.0, 0.6, 0.8])
    messages = []
    gyro_t = START_NS + 2_000_000 + np.arange(int(seconds * 400)) * 2_500_000
    rows = [(int(t), 0, *(axis * rotation_rate((t - START_NS) * 1e-9 - imu_offset_s)), 0.001, 0.002, 0.003) for t in gyro_t]
    accel_t = START_NS + 3_000_000 + np.arange(int(seconds * 200)) * 5_000_000
    rows += [(int(t), 1, 0.0, 9.81, (t - START_NS) * 1e-9, 0.0, 0.0, 0.0) for t in accel_t]
    messages += list(_imu_batches(rows))
    if kind == "walk":
        frame_t = START_NS + camera_clock_shift_ns + 10_000_000 + np.arange(int(seconds * 30)) * 33_333_333
        for i, t in enumerate(frame_t):
            grey = np.array([(i + k) % 256 for k in range(WIDTH * HEIGHT)], np.uint8).reshape(HEIGHT, WIDTH)
            q = Rotation.from_rotvec(axis * rotation_angle((t - START_NS - camera_clock_shift_ns) * 1e-9)).as_quat()
            record = fake_phone.arcore(int(t) + 7, [0.1, 0.2, 0.3, *q])
            record["device_pose"] = [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0]
            messages.append(fake_phone.frame(i, int(t), grey, record=record))
    if stopped:
        messages.append(fake_phone.end(end_ns=START_NS + int(seconds * 1e9) + 10**6, frames=len(messages), frames_dropped=0))
    session = f"rec_{kind}"
    return fake_phone.write_session(Path(root), fake_phone.numbered(messages), session=session,
                                    session_info=fake_phone.info(kind, start_ns=START_NS))
