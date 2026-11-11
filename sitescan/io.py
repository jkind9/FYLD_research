"""Writing run results: point clouds, JSON records and the per-frame timeline."""

import json
from pathlib import Path

import numpy as np


def write_cloud(path: Path, points: np.ndarray, colours: np.ndarray | None = None) -> None:
    """A PLY point cloud, with RGB colours from 0 to 1 when given."""
    import open3d as o3d

    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    if colours is not None:
        cloud.colors = o3d.utility.Vector3dVector(colours)
    o3d.io.write_point_cloud(str(path), cloud)


def write_json(path: Path, record: dict, indent: int = 1) -> None:
    """A JSON record, UTF-8."""
    Path(path).write_text(json.dumps(record, indent=indent), encoding="utf-8")


def write_timeline(path: Path, frames: list[tuple]) -> None:
    """Each fused frame's camera, sampled learned-depth points with colours, and ARCore depth points.

    Each entry is (seq, world_from_camera, intrinsics, image size, points, colours, arcore points). Points
    of all frames are stored end to end; the offsets arrays say where each frame's points start.
    """
    seq, poses, intrinsics, image_sizes, points, colours, arcore = zip(*frames)
    np.savez_compressed(
        path,
        seq=np.array(seq),
        poses=np.array(poses),
        intrinsics=np.array(intrinsics),
        sizes=np.array(image_sizes),
        points=np.concatenate(points),
        colours=np.concatenate(colours),
        point_offsets=np.cumsum([0, *map(len, points)]),
        arcore=np.concatenate(arcore),
        arcore_offsets=np.cumsum([0, *map(len, arcore)]),
    )
