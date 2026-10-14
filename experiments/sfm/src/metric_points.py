"""Real-world size of an SfM world from a few metric depth readings at its points.

A reading is one depth-camera depth at the pixel where an SfM point was seen, divided by that
point's depth in the SfM world: metres per SfM unit. A phone would take the same kind of
reading from ARCore's depth at tracked points.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def readings(rows: list[dict], xyz: np.ndarray, observations: dict[str, np.ndarray], keep_point: np.ndarray,
             depth_for_frame: Callable[[int], tuple[np.ndarray, np.ndarray] | None], *,
             min_depth_m: float = 0.1, max_depth_m: float = 4.0) -> dict[str, np.ndarray]:
    """Frame index and metres-per-SfM-unit ratio for every usable observation of a kept point."""
    frames, ratios = [], []
    for k in np.unique(observations["frame_index"]):
        pose, loaded = rows[int(k)]["T_world_camera"], depth_for_frame(int(k))
        if pose is None or loaded is None:
            continue
        depth, valid = loaded
        mask = (observations["frame_index"] == k) & keep_point[observations["point_index"]]
        world_from_camera = np.array(pose)
        camera = (xyz[observations["point_index"][mask]] - world_from_camera[:3, 3]) @ world_from_camera[:3, :3]
        u = np.rint(observations["uv"][mask, 0]).astype(int)
        v = np.rint(observations["uv"][mask, 1]).astype(int)
        inside = (u >= 0) & (v >= 0) & (u < depth.shape[1]) & (v < depth.shape[0]) & (camera[:, 2] > 0)
        u, v, z = u[inside], v[inside], camera[inside, 2]
        read = depth[v, u]
        good = valid[v, u] & np.isfinite(read) & (read >= min_depth_m) & (read <= max_depth_m)
        frames.append(np.full(int(good.sum()), int(k)))
        ratios.append(read[good] / z[good])
    if not frames:
        return {"frame": np.array([], int), "ratio": np.array([])}
    return {"frame": np.concatenate(frames), "ratio": np.concatenate(ratios)}


def _draw(ratio: np.ndarray, n: int | None, rng: np.random.Generator) -> np.ndarray:
    if n is None or n >= len(ratio):
        return ratio
    return ratio[rng.choice(len(ratio), size=n, replace=False)]


def run_size(data: dict[str, np.ndarray], n: int | None, seed: int) -> float | None:
    """Median ratio of n readings drawn from the whole run (all of them when n is None)."""
    if len(data["ratio"]) == 0:
        return None
    return float(np.median(_draw(data["ratio"], n, np.random.default_rng(seed))))


def frame_size(data: dict[str, np.ndarray], n: int | None, seed: int) -> float | None:
    """Median over frames of the median ratio of n readings drawn in each frame."""
    rng = np.random.default_rng(seed)
    sizes = [float(np.median(_draw(data["ratio"][data["frame"] == k], n, rng))) for k in np.unique(data["frame"])]
    return float(np.median(sizes)) if sizes else None
