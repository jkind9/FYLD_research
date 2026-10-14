"""Frame windows and sized world-to-camera poses for pose-conditioned depth."""

from __future__ import annotations

import numpy as np


def windows(count: int, size: int, stride: int = 1) -> list[tuple[list[int], list[int]]]:
    """(members, kept) position lists covering 0..count-1 once. A short last window moves back to hold `size` members.

    With stride > 1, each block of size × stride frames is split into `stride` windows whose members are
    `stride` apart, so every window spans the whole block: a wider baseline at the same cost.
    """
    if stride > 1 and count >= size * stride:
        span = size * stride
        starts = list(range(0, count - span + 1, span))
        if starts[-1] + span < count:
            starts.append(count - span)
        out, covered = [], set()
        for start in starts:
            for offset in range(stride):
                members = [start + offset + stride * j for j in range(size)]
                kept = [m for m in members if m not in covered]
                if kept:
                    out.append((members, kept))
                    covered.update(kept)
        return out
    if count == 0:
        return []
    if count <= size:
        everything = list(range(count))
        return [(everything, everything)]
    out = [(list(range(start, start + size)), list(range(start, start + size))) for start in range(0, count - size + 1, size)]
    covered = out[-1][1][-1] + 1
    if covered < count:
        out.append((list(range(count - size, count)), list(range(covered, count))))
    return out


def sized_extrinsics(world_from_camera: list[list[list[float]]], size: float) -> np.ndarray:
    """World-to-camera 4 x 4 matrices (N, 4, 4) from camera-to-world poses whose translation is multiplied by `size`."""
    out = []
    for pose in world_from_camera:
        matrix = np.array(pose, dtype=np.float64)
        matrix[:3, 3] *= size
        out.append(np.linalg.inv(matrix))
    return np.array(out)
