"""TUM RGB/depth association, independent of ground-truth evaluation."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation, Slerp

from .geometry import pose_matrix


@dataclass(frozen=True)
class Frame:
    index: int
    timestamp: float
    depth_timestamp: float
    rgb: Path
    depth: Path


def read_table(path: Path) -> list[list[str]]:
    """Read comments/whitespace-delimited TUM tables, preserving row identities."""
    return [
        line.split()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def associate(
    first: NDArray, second: NDArray, tolerance: float
) -> list[tuple[int, int]]:
    """One-to-one nearest-offset greedy association; inclusive tolerance in seconds."""
    first, second = np.asarray(first), np.asarray(second)
    if (
        tolerance < 0
        or not np.isfinite(tolerance)
        or not np.isfinite(first).all()
        or not np.isfinite(second).all()
    ):
        raise ValueError("Invalid timestamps/tolerance")
    if np.any(np.diff(first) <= 0) or np.any(np.diff(second) <= 0):
        raise ValueError("Timestamps must be strictly increasing")
    candidates: list[tuple[float, int, int]] = []
    for i, t in enumerate(first):
        lo = np.searchsorted(second, t - tolerance, side="left")
        hi = np.searchsorted(second, t + tolerance, side="right")
        candidates.extend((abs(t - second[j]), i, j) for j in range(lo, hi))
    used_a, used_b, matches = set(), set(), []
    for _, i, j in sorted(candidates):
        if i not in used_a and j not in used_b:
            matches.append((i, j))
            used_a.add(i)
            used_b.add(j)
    return sorted(matches)


def contained_path(root: Path, relative: str) -> Path:
    """Prevent dataset index files from referencing outside the sequence."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Dataset path escapes sequence")
    return path


def select_frames(
    sequence: Path, limit: int, stride: int, tolerance: float
) -> tuple[list[Frame], dict]:
    """Select associated observations before loading any ground truth."""
    if limit < 1 or stride < 1:
        raise ValueError("Frame limit and stride must be positive")
    rgb, depth = read_table(sequence / "rgb.txt"), read_table(sequence / "depth.txt")
    matches = associate(
        np.array([float(x[0]) for x in rgb]),
        np.array([float(x[0]) for x in depth]),
        tolerance,
    )
    selected = matches[::stride][:limit]
    frames = [
        Frame(
            i,
            float(rgb[i][0]),
            float(depth[j][0]),
            contained_path(sequence, rgb[i][1]),
            contained_path(sequence, depth[j][1]),
        )
        for i, j in selected
    ]
    if not frames:
        raise ValueError("No associated frames within tolerance")
    return frames, {
        "rgb_rows": len(rgb),
        "depth_rows": len(depth),
        "associated_pairs": len(matches),
        "unassociated_rgb": len(rgb) - len(matches),
        "max_rgb_depth_offset_s": max(
            abs(f.timestamp - f.depth_timestamp) for f in frames
        ),
    }


def ground_truth_at(
    path: Path, timestamps: NDArray, tolerance: float
) -> tuple[list[NDArray | None], dict]:
    """Interpolate GT only between bracketing samples, each within tolerance; no extrapolation."""
    rows = np.asarray(read_table(path), dtype=float)
    times = rows[:, 0]
    if np.any(np.diff(times) <= 0):
        raise ValueError("Ground truth timestamps are not strictly increasing")
    rotations = Slerp(times, Rotation.from_quat(rows[:, 4:8]))
    poses, offsets = [], []
    for t in timestamps:
        j = int(np.searchsorted(times, t))
        if j < len(times) and times[j] == t:
            poses.append(pose_matrix(rows[j, 1:4], rows[j, 4:8]))
            offsets.append(0.0)
        elif 0 < j < len(times) and max(t - times[j - 1], times[j] - t) <= tolerance:
            alpha = (t - times[j - 1]) / (times[j] - times[j - 1])
            xyz = (1 - alpha) * rows[j - 1, 1:4] + alpha * rows[j, 1:4]
            poses.append(pose_matrix(xyz, rotations([t]).as_quat()[0]))
            offsets.append(max(t - times[j - 1], times[j] - t))
        else:
            poses.append(None)
    return poses, {
        "association": "linear translation + quaternion SLERP; no extrapolation",
        "tolerance_s": tolerance,
        "matched": len(offsets),
        "max_bracket_offset_s": max(offsets, default=None),
    }
