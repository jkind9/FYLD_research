"""A small synthetic recording in the phone app's format, shared by the host tests."""

import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

START_NS = 5_000_000_000_000  # elapsedRealtime about 83 minutes after boot
WIDTH, HEIGHT = 8, 6


def rotation_angle(t_s):
    """Angle in radians about one fixed axis; smooth, with speed changes the offset search can lock on to."""
    return 0.4 * np.sin(2 * np.pi * 0.7 * t_s) + 0.25 * np.sin(2 * np.pi * 1.9 * t_s + 0.5)


def rotation_rate(t_s):
    return 0.4 * 2 * np.pi * 0.7 * np.cos(2 * np.pi * 0.7 * t_s) + 0.25 * 2 * np.pi * 1.9 * np.cos(2 * np.pi * 1.9 * t_s + 0.5)


def _write_csv(path: Path, header: str, rows) -> None:
    path.write_text(header + "\n" + "".join(",".join(str(v) for v in row) + "\n" for row in rows), encoding="utf-8")


def write_recording(root: Path, *, seconds=4.0, imu_offset_s=0.0, camera_clock_shift_ns=0, kind="walk", stopped=True) -> Path:
    """Writes a recording; the gyroscope stamps a motion `imu_offset_s` later than the camera does."""
    root.mkdir(parents=True)
    axis = np.array([0.0, 0.6, 0.8])
    meta = {"schema": 1, "kind": kind, "device": {"model": "test"},
            "clock": {"start": {"elapsed_realtime_ns": START_NS, "nano_time_ns": START_NS - 10**9, "wall_ms": 0}},
            "imu": {"gyro": {"type": "android.sensor.gyroscope_uncalibrated"}, "accel": {"type": "android.sensor.accelerometer_uncalibrated"}}}
    if stopped:
        meta["clock"]["end"] = {"elapsed_realtime_ns": START_NS + int(seconds * 1e9) + 10**6, "nano_time_ns": 0, "wall_ms": 0}
    gyro_t = START_NS + 2_000_000 + np.arange(int(seconds * 400)) * 2_500_000
    gyro_rows = [[t, *(axis * rotation_rate((t - START_NS) * 1e-9 - imu_offset_s)), 0.001, 0.002, 0.003] for t in gyro_t]
    _write_csv(root / "gyro.csv", "t_ns,x,y,z,bx,by,bz", gyro_rows)
    accel_t = START_NS + 3_000_000 + np.arange(int(seconds * 200)) * 5_000_000
    _write_csv(root / "accel.csv", "t_ns,x,y,z,bx,by,bz", [[t, 0.0, 9.81, (t - START_NS) * 1e-9, 0, 0, 0] for t in accel_t])
    if kind == "walk":
        meta["camera"] = {"id": "0", "timestamp_source": "REALTIME", "size": [WIDTH, HEIGHT]}
        frame_t = START_NS + camera_clock_shift_ns + 10_000_000 + np.arange(int(seconds * 30)) * 33_333_333
        (root / "cam0").mkdir()
        for i, t in enumerate(frame_t):
            pixels = bytes((i + k) % 256 for k in range(WIDTH * HEIGHT))
            (root / "cam0" / f"{t}.pgm").write_bytes(f"P5\n{WIDTH} {HEIGHT}\n255\n".encode() + pixels)
        _write_csv(root / "cam0.csv", "t_ns,exposure_ns,frame_duration_ns,rolling_shutter_skew_ns,focus_distance_dpt,iso",
                   [[t, 8_000_000, 33_333_333, 20_000_000, 0.5, 400] for t in frame_t])
        rows = []
        for t in frame_t:
            q = Rotation.from_rotvec(axis * rotation_angle((t - START_NS - camera_clock_shift_ns) * 1e-9)).as_quat()
            camera = [0.1, 0.2, 0.3, *q]
            device = [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0]
            rows.append([t + 7, t, "TRACKING", *camera, *device])
        _write_csv(root / "arcore.csv", "t_ns,camera_t_ns,tracking,tx,ty,tz,qx,qy,qz,qw,dev_tx,dev_ty,dev_tz,dev_qx,dev_qy,dev_qz,dev_qw", rows)
    (root / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return root

