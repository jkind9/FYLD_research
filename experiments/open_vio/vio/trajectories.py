"""Read each system's trajectory file as (time in seconds, 4 x 4 IMU-to-world) rows."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def _pose(position, quaternion_xyzw) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = Rotation.from_quat(quaternion_xyzw).as_matrix()
    m[:3, 3] = position
    return m


def read_tum(path: Path) -> list[tuple[float, np.ndarray]]:
    """`time x y z qx qy qz qw` (seconds), extra columns ignored: Basalt's and OpenVINS's pose files."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            v = [float(x) for x in line.split()[:8]]
            out.append((v[0], _pose(v[1:4], v[4:8])))
    return out


def read_csv(path: Path, *, quaternion: str, time_scale: float = 1e-9, columns: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 7)
             ) -> list[tuple[float, np.ndarray]]:
    """Comma-separated rows with a nanosecond time, position and a quaternion in `xyzw` or `wxyz` order.

    `columns` picks time, x, y, z and the four quaternion values from wider files (Kimera, OKVIS2, EuRoC ground truth).
    """
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or not line.lstrip()[0].isdigit():
            continue
        cells = line.split(",")
        v = [float(cells[i]) for i in columns]
        q = v[4:8] if quaternion == "xyzw" else [v[5], v[6], v[7], v[4]]
        out.append((v[0] * time_scale, _pose(v[1:4], q)))
    return out
