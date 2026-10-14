"""Many depth images and camera poses to one surface, and per-frame depth sizes from SfM points."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DepthFrame:
    depth_m: np.ndarray  # camera-axis z in metres, NaN or anything where valid is False
    valid: np.ndarray
    world_from_camera: np.ndarray
    colour: np.ndarray | None = None


@dataclass(frozen=True)
class Pinhole:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float


def fuse_tsdf(frames: Iterable[DepthFrame], camera: Pinhole, *, voxel_m: float, truncation_voxels: float,
              min_depth_m: float, max_depth_m: float) -> tuple[np.ndarray, dict]:
    """Open3D signed-distance fusion; returns surface points (N x 3, metres) and counts."""
    import open3d as o3d

    volume = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=voxel_m, sdf_trunc=truncation_voxels * voxel_m,
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
    intrinsic = o3d.camera.PinholeCameraIntrinsic(camera.width, camera.height, camera.fx, camera.fy, camera.cx, camera.cy)
    used = skipped = 0
    for frame in frames:
        depth = np.where(frame.valid & np.isfinite(frame.depth_m) & (frame.depth_m >= min_depth_m), frame.depth_m, 0.0)
        if not np.any(depth > 0):
            skipped += 1
            continue
        colour = frame.colour if frame.colour is not None else np.full((*depth.shape, 3), 128, np.uint8)
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(np.ascontiguousarray(colour)), o3d.geometry.Image(depth.astype(np.float32)),
            depth_scale=1.0, depth_trunc=max_depth_m, convert_rgb_to_intensity=False)
        volume.integrate(rgbd, intrinsic, np.linalg.inv(frame.world_from_camera))
        used += 1
    cloud = volume.extract_point_cloud()
    return np.asarray(cloud.points, dtype=np.float64), {"frames_fused": used, "frames_without_depth": skipped}


def accumulate(frames: Iterable[DepthFrame], camera: Pinhole, *, voxel_m: float, min_depth_m: float,
               max_depth_m: float) -> np.ndarray:
    """Every valid pixel as a world point, then one point per voxel (what the walkthrough builds, thinned)."""
    import open3d as o3d

    u, v = np.meshgrid(np.arange(camera.width), np.arange(camera.height))
    rays = np.stack([(u - camera.cx) / camera.fx, (v - camera.cy) / camera.fy, np.ones_like(u, float)], -1)
    cloud = o3d.geometry.PointCloud()
    for frame in frames:
        keep = frame.valid & np.isfinite(frame.depth_m) & (frame.depth_m >= min_depth_m) & (frame.depth_m <= max_depth_m)
        points = rays[keep] * frame.depth_m[keep][:, None]
        world = points @ frame.world_from_camera[:3, :3].T + frame.world_from_camera[:3, 3]
        cloud += o3d.geometry.PointCloud(o3d.utility.Vector3dVector(world))
        cloud = cloud.voxel_down_sample(voxel_m)
    return np.asarray(cloud.points, dtype=np.float64)


def fit_size(model_depth: np.ndarray, target_depth: np.ndarray, *, with_shift: bool = False,
             drop_fraction: float = 0.1) -> tuple[float, float] | None:
    """Size (and optional shift) taking model depth onto target depth at matched points.

    Size only: median of target / model, robust to outliers. With shift: least squares, refit
    after dropping the largest residuals of a first fit.
    """
    good = np.isfinite(model_depth) & np.isfinite(target_depth) & (model_depth > 0) & (target_depth > 0)
    model, target = model_depth[good], target_depth[good]
    if len(model) < 2:
        return None
    if not with_shift:
        return float(np.median(target / model)), 0.0
    design = np.column_stack([model, np.ones_like(model)])
    size, shift = np.linalg.lstsq(design, target, rcond=None)[0]
    residual = np.abs(design @ (size, shift) - target)
    keep = residual <= np.quantile(residual, 1 - drop_fraction)
    size, shift = np.linalg.lstsq(design[keep], target[keep], rcond=None)[0]
    return float(size), float(shift)


def frame_sizes(frame_count: int, observations: dict[str, np.ndarray], camera_depth_of_point: np.ndarray,
                model_depth_at: callable, *, min_points: int, with_shift: bool = False) -> list[dict]:
    """One size per frame from its observed SfM points; frames short of points borrow the nearest fitted frame."""
    fitted: dict[int, tuple[float, float, int]] = {}
    for k in range(frame_count):
        mask = observations["frame_index"] == k
        if mask.sum() < min_points:
            continue
        model = model_depth_at(k, observations["uv"][mask])
        if model is None:
            continue
        result = fit_size(model, camera_depth_of_point[mask], with_shift=with_shift)
        if result is not None:
            fitted[k] = (*result, int(mask.sum()))
    rows = []
    known = np.array(sorted(fitted))
    for k in range(frame_count):
        if k in fitted:
            size, shift, count = fitted[k]
            rows.append({"frame": k, "size": size, "shift": shift, "points": count, "borrowed_from": None})
        elif len(known):
            nearest = int(known[np.argmin(np.abs(known - k))])
            size, shift, _ = fitted[nearest]
            rows.append({"frame": k, "size": size, "shift": shift, "points": 0, "borrowed_from": nearest})
        else:
            rows.append({"frame": k, "size": None, "shift": None, "points": 0, "borrowed_from": None})
    return rows
