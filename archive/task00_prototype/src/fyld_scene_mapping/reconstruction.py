"""Open3D CPU RGB-D odometry and observed point fusion. No GT is accepted by estimator."""

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import open3d as o3d
from numpy.typing import NDArray
from PIL import Image

from .datasets import Frame
from .geometry import (
    Intrinsics,
    backproject,
    depth_metres,
    inverse_transform,
    transform_points,
    validate_transform,
)


@dataclass(frozen=True)
class ReconstructionSettings:
    min_depth_m: float = 0.2
    max_depth_m: float = 4.0
    depth_units_per_metre: float = 5000.0
    pixel_step: int = 3
    voxel_size_m: float = 0.015
    max_translation_step_m: float = 0.3
    max_rotation_step_deg: float = 30.0
    min_depth_overlap: float = 0.2
    max_time_gap_s: float = 0.15
    min_intensity_std: float = 0.01


def read_observation(
    frame: Frame,
    intrinsics: Intrinsics,
    settings: ReconstructionSettings,
    timings: dict[str, float] | None = None,
) -> tuple[NDArray, NDArray]:
    """Read RGB and registered optical depth without implicit resizing or orientation changes."""
    tick = perf_counter()
    with Image.open(frame.rgb) as image:
        rgb = np.asarray(image.convert("RGB")).copy()
    with Image.open(frame.depth) as image:
        encoded = np.asarray(image).copy()
    if (
        rgb.shape != (intrinsics.height, intrinsics.width, 3)
        or encoded.shape != rgb.shape[:2]
    ):
        raise ValueError("RGB/depth/calibration shapes disagree")
    if timings is not None:
        timings["decoding_s"] += perf_counter() - tick
    tick = perf_counter()
    depth = depth_metres(encoded, settings.depth_units_per_metre)
    depth[(depth < settings.min_depth_m) | (depth > settings.max_depth_m)] = np.nan
    if timings is not None:
        timings["depth_s"] += perf_counter() - tick
    return rgb, depth


def rgbd_image(rgb: NDArray, depth: NDArray) -> o3d.geometry.RGBDImage:
    """Open3D gets float optical metres, invalid=0; greyscale conversion for odometry."""
    return o3d.geometry.RGBDImage.create_from_color_and_depth(
        o3d.geometry.Image(np.ascontiguousarray(rgb)),
        o3d.geometry.Image(np.nan_to_num(depth, nan=0.0).astype(np.float32)),
        depth_scale=1.0,
        depth_trunc=100.0,
        convert_rgb_to_intensity=True,
    )


def depth_overlap(
    source: NDArray,
    target: NDArray,
    motion: NDArray,
    intrinsics: Intrinsics,
    min_depth_m: float = 0.2,
    max_depth_m: float = 4.0,
) -> float:
    """Fraction of valid source samples with target optical depth agreement within 7 cm."""
    points, _ = backproject(source, intrinsics, min_depth_m, max_depth_m, step=8)
    if not len(points):
        return 0.0
    q = transform_points(points, motion)
    valid = q[:, 2] > 0.01
    q = q[valid]
    u = np.rint(q[:, 0] * intrinsics.fx / q[:, 2] + intrinsics.cx).astype(int)
    v = np.rint(q[:, 1] * intrinsics.fy / q[:, 2] + intrinsics.cy).astype(int)
    inside = (u >= 0) & (u < intrinsics.width) & (v >= 0) & (v < intrinsics.height)
    agreement = np.abs(target[v[inside], u[inside]] - q[inside, 2]) < 0.07
    return float(np.count_nonzero(agreement) / len(points))


def estimate_motion(
    source: o3d.geometry.RGBDImage,
    target: o3d.geometry.RGBDImage,
    source_depth: NDArray,
    target_depth: NDArray,
    intrinsics: Intrinsics,
    settings: ReconstructionSettings,
) -> tuple[NDArray | None, dict]:
    """Estimate T_target_source; basic texture/overlap gates do not guarantee observability."""
    texture = min(
        float(np.std(np.asarray(source.color))), float(np.std(np.asarray(target.color)))
    )
    if texture < settings.min_intensity_std:
        return None, {
            "reason": "low intensity variation; pose may be unobservable",
            "intensity_std": texture,
        }
    calibration = o3d.camera.PinholeCameraIntrinsic(
        intrinsics.width,
        intrinsics.height,
        intrinsics.fx,
        intrinsics.fy,
        intrinsics.cx,
        intrinsics.cy,
    )
    options = o3d.pipelines.odometry.OdometryOption()
    options.depth_min = settings.min_depth_m
    options.depth_max = settings.max_depth_m
    options.depth_diff_max = 0.07
    success, motion, information = o3d.pipelines.odometry.compute_rgbd_odometry(
        source,
        target,
        calibration,
        np.eye(4),
        o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(),
        options,
    )
    diagnostic: dict[str, object] = {"open3d_success": bool(success)}
    if not success:
        return None, {**diagnostic, "reason": "Open3D odometry failed"}
    try:
        validate_transform(motion)
    except ValueError:
        return None, {**diagnostic, "reason": "nonfinite/non-rigid motion"}
    translation = float(np.linalg.norm(motion[:3, 3]))
    angle = float(
        np.rad2deg(np.arccos(np.clip((np.trace(motion[:3, :3]) - 1) / 2, -1, 1)))
    )
    overlap = depth_overlap(
        source_depth,
        target_depth,
        motion,
        intrinsics,
        settings.min_depth_m,
        settings.max_depth_m,
    )
    diagnostic.update(
        {
            "translation_m": translation,
            "rotation_deg": angle,
            "depth_overlap": overlap,
            "information_trace": float(np.trace(information)),
            "intensity_std": texture,
            "observability": "not guaranteed by these heuristic gates",
        }
    )
    if (
        translation > settings.max_translation_step_m
        or angle > settings.max_rotation_step_deg
        or overlap < settings.min_depth_overlap
    ):
        return None, {**diagnostic, "reason": "motion/overlap quality gate rejected"}
    return motion, diagnostic


def reconstruct(
    frames: list[Frame],
    intrinsics: Intrinsics,
    settings: ReconstructionSettings,
    supplied_poses: list[NDArray] | None = None,
) -> dict:
    """Return first-camera-frame geometry; stop on first tracking break, never bridge it."""
    if settings.voxel_size_m <= 0 or settings.pixel_step < 1:
        raise ValueError("Invalid voxel/sampling settings")
    if supplied_poses is not None and len(supplied_poses) != len(frames):
        raise ValueError("Supplied pose count differs from frame count")
    times = {"decoding_s": 0.0, "pose_s": 0.0, "depth_s": 0.0, "fusion_s": 0.0}
    poses: list[NDArray] = []
    points, colours, accepted, failures, steps = [], [], [], [], []
    previous, previous_depth = None, None
    first_inverse = (
        inverse_transform(supplied_poses[0]) if supplied_poses is not None else None
    )
    for frame_number, frame in enumerate(frames):
        rgb, depth = read_observation(frame, intrinsics, settings, times)
        tick = perf_counter()
        if supplied_poses is not None:
            pose = first_inverse @ supplied_poses[frame_number]
        elif frame_number == 0:
            pose = np.eye(4)
        else:
            gap = frame.timestamp - frames[frame_number - 1].timestamp
            if gap > settings.max_time_gap_s:
                failures.append(
                    {
                        "frame_index": frame.index,
                        "timestamp": frame.timestamp,
                        "reason": "input timestamp gap exceeds threshold",
                        "gap_s": gap,
                    }
                )
                times["pose_s"] += perf_counter() - tick
                break
            current = rgbd_image(rgb, depth)
            motion, diagnostic = estimate_motion(
                previous, current, previous_depth, depth, intrinsics, settings
            )
            steps.append({"frame_index": frame.index, **diagnostic})
            if motion is None:
                failures.append(
                    {
                        "frame_index": frame.index,
                        "timestamp": frame.timestamp,
                        **diagnostic,
                    }
                )
                times["pose_s"] += perf_counter() - tick
                break
            # Open3D maps previous/source camera into current/target camera.
            # Camera-to-world must compose the INVERSE of that motion.
            pose = poses[-1] @ inverse_transform(motion)
        times["pose_s"] += perf_counter() - tick
        if supplied_poses is None:
            previous = rgbd_image(rgb, depth)
            previous_depth = depth
        tick = perf_counter()
        xyz, vu = backproject(
            depth,
            intrinsics,
            settings.min_depth_m,
            settings.max_depth_m,
            settings.pixel_step,
        )
        if not len(xyz):
            failures.append(
                {"frame_index": frame.index, "reason": "no valid depth; stopped"}
            )
            break
        points.append(transform_points(xyz, pose))
        colours.append(rgb[vu[:, 0], vu[:, 1]] / 255.0)
        poses.append(pose)
        accepted.append(frame)
        times["fusion_s"] += perf_counter() - tick
        if (frame_number + 1) % 25 == 0:
            print(f"Accepted {frame_number + 1}/{len(frames)} frames", flush=True)
    if not points:
        raise ValueError("No geometry reconstructed")
    tick = perf_counter()
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.concatenate(points))
    cloud.colors = o3d.utility.Vector3dVector(np.concatenate(colours))
    raw_count = len(cloud.points)
    cloud = cloud.voxel_down_sample(settings.voxel_size_m)
    before_filter = len(cloud.points)
    if before_filter >= 21:
        cloud, _ = cloud.remove_statistical_outlier(nb_neighbors=20, std_ratio=3.0)
    times["fusion_s"] += perf_counter() - tick
    return {
        "cloud": cloud,
        "poses": poses,
        "accepted": accepted,
        "failures": failures,
        "odometry_steps": steps,
        "timings": times,
        "raw_samples": raw_count,
        "voxel_samples": before_filter,
        "outliers_removed": before_filter - len(cloud.points),
    }
