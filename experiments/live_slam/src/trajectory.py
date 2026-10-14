"""Files exchanged with the native SLAM runners, and per-frame rows for experiments/sfm scoring.

A runner writes one line per frame: `time segment x y z qx qy qz qw` (camera-to-world, the
system's own units) or `time lost`. A segment is one map; a reset starts a new one.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from experiments.shared.geometry import pose_matrix


def to_wsl(path: Path) -> str:
    """Windows path as WSL sees it (`C:/a/b` -> `/mnt/c/a/b`)."""
    path = Path(path) if Path(path).drive else Path(path).resolve()
    drive, _, rest = path.as_posix().partition(":")
    return f"/mnt/{drive.lower()}{rest}"


def frame_list(times: list[float], images: list[Path]) -> str:
    """The runner's input: one `time path` line per frame, in order."""
    return "".join(f"{t:.6f} {to_wsl(p)}\n" for t, p in zip(times, images))


def read_poses(path: Path) -> list[tuple[float, int | None, np.ndarray | None]]:
    """(time, segment, camera-to-world) per line; segment and pose are None for a lost frame."""
    out = []
    for text in Path(path).read_text(encoding="utf-8").splitlines():
        values = text.split()
        if not values:
            continue
        if values[1] == "lost":
            out.append((float(values[0]), None, None))
            continue
        numbers = np.array([float(v) for v in values[2:9]])
        out.append((float(values[0]), int(values[1]), pose_matrix(numbers[:3], numbers[3:] / np.linalg.norm(numbers[3:]))))
    return out


def read_trajectory(path: Path, *, time_scale: float = 1.0) -> list[tuple[float, int, np.ndarray]]:
    """A system's own final trajectory (`time x y z qx qy qz qw`, one map) in read_poses' form."""
    out = []
    for text in Path(path).read_text(encoding="utf-8").splitlines():
        values = [float(v) for v in text.split()]
        if len(values) == 8:
            q = np.array(values[4:])
            out.append((values[0] * time_scale, 0, pose_matrix(values[1:4], q / np.linalg.norm(q))))
    return out


def rows(frame_ids: list[str], times: list[float], poses: list, *, tolerance_s: float = 0.001) -> list[dict]:
    """One row per input frame in the form `experiments/sfm/src/scoring.py` reads; unmatched frames are unplaced."""
    stamps = np.array([t for t, _, _ in poses]) if poses else np.array([])
    out = []
    for frame_id, t in zip(frame_ids, times):
        segment, matrix = None, None
        if len(stamps):
            i = int(np.argmin(np.abs(stamps - t)))
            if abs(stamps[i] - t) <= tolerance_s:
                _, segment, matrix = poses[i]
        out.append({"frame_id": frame_id, "timestamp_s": t, "model_id": segment,
                    "T_world_camera": None if matrix is None else matrix.tolist()})
    return out
