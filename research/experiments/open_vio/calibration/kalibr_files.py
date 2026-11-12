"""Kalibr's input files (bag-creator folder, IMU noise file, AprilGrid target file) and result comparison.

Kalibr wiki: the bag creator reads `<folder>/cam0/<timestamp_ns>.png` and `<folder>/imu0.csv` with header
`timestamp,omega_x,omega_y,omega_z,alpha_x,alpha_y,alpha_z` (ns, rad/s, m/s^2); the IMU file carries noise
densities and random walks in continuous-time units.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

KALIBR_IMU_HEADER = "timestamp,omega_x,omega_y,omega_z,alpha_x,alpha_y,alpha_z"


def to_kalibr_folder(mav0: Path, out: Path, cameras: tuple[str, ...] = ("cam0",)) -> Path:
    """Kalibr bag-creator folder from an EuRoC/ASL `mav0` folder; images are hard-linked where possible."""
    out = Path(out)
    for camera in cameras:
        (out / camera).mkdir(parents=True, exist_ok=True)
        for image in sorted((Path(mav0) / camera / "data").glob("*.png")):
            target = out / camera / image.name
            if not target.exists():
                try:
                    os.link(image, target)
                except OSError:
                    shutil.copyfile(image, target)
    rows = (Path(mav0) / "imu0" / "data.csv").read_text(encoding="utf-8").splitlines()[1:]
    (out / "imu0.csv").write_text("\n".join([KALIBR_IMU_HEADER, *rows]) + "\n", encoding="utf-8")
    return out


def imu_yaml(noise: dict, *, white_factor: float = 2.0, walk_factor: float = 10.0, topic: str = "/imu0") -> str:
    """Kalibr IMU file from an Allan fit (allan.imu_noise), inflated for effects a rest recording does not show."""
    for name in ("gyro", "accel"):
        if noise[name]["random_walk"] is None:
            raise ValueError(f"{name}: no random walk in the Allan fit; record longer at rest")
    lines = [f"rostopic: {topic}", f"update_rate: {noise['gyro']['rate_hz']:.1f}",
             f"# Allan fit multiplied by {white_factor} (white noise) and {walk_factor} (random walk)"]
    for name, key in (("accel", "accelerometer"), ("gyro", "gyroscope")):
        lines.append(f"{key}_noise_density: {noise[name]['noise_density'] * white_factor:.6g}")
        lines.append(f"{key}_random_walk: {noise[name]['random_walk'] * walk_factor:.6g}")
    return "\n".join(lines) + "\n"


def aprilgrid_yaml(*, cols: int, rows: int, tag_size_m: float, spacing: float) -> str:
    """Kalibr AprilGrid target; spacing is the gap between tags as a fraction of the tag size."""
    return (f"target_type: 'aprilgrid'\ntagCols: {cols}\ntagRows: {rows}\n"
            f"tagSize: {tag_size_m}\ntagSpacing: {spacing}\n")


def read_camchain(path: Path, camera: str = "cam0") -> dict:
    """One camera of a Kalibr camchain file; T_cam_imu and timeshift_cam_imu are None when absent."""
    import yaml

    entry = yaml.safe_load(Path(path).read_text(encoding="utf-8"))[camera]
    transform = entry.get("T_cam_imu")
    return {"T_cam_imu": None if transform is None else np.array(transform, dtype=float),
            "timeshift_cam_imu": entry.get("timeshift_cam_imu"),
            "intrinsics": entry["intrinsics"], "distortion": entry["distortion_coeffs"],
            "model": f"{entry['camera_model']}-{entry['distortion_model']}", "resolution": entry["resolution"]}


def transform_difference(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Rotation angle in degrees and translation distance in metres between two 4 x 4 transforms."""
    angle = (Rotation.from_matrix(a[:3, :3]).inv() * Rotation.from_matrix(b[:3, :3])).magnitude()
    return float(np.degrees(angle)), float(np.linalg.norm(a[:3, 3] - b[:3, 3]))
