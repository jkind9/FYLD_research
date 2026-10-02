"""Shared offline entry point. Ground truth is loaded after estimated reconstruction."""

from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np
import open3d as o3d
import psutil
from numpy.typing import NDArray

from .acquisition import sha256
from .datasets import ground_truth_at, select_frames
from .environment import snapshot
from .evaluation import trajectory_metrics
from .geometry import Intrinsics, plane_alignment
from .mapping import project
from .reconstruction import ReconstructionSettings, reconstruct
from .reporting import export_run, new_run


def baseline_parameters() -> dict:
    """Effective experiment choices, including library defaults, with provenance."""
    return {
        "intrinsics": {"value": asdict(Intrinsics()), "source": "TUM official file-format recommendation: ROS defaults"},
        "reconstruction_defaults": {"value": asdict(ReconstructionSettings()), "source": "inherited initial 2026-10-01 A/B run; heuristic gates, not product requirements"},
        "odometry_iterations": {"value": list(o3d.pipelines.odometry.OdometryOption().iteration_number_per_pyramid_level), "source": "Open3D 0.19.0 library default"},
        "depth_agreement_m": {"value": .07, "source": "inherited first A/B run"},
        "overlap_sample_stride": {"value": 8, "source": "inherited first A/B run"},
        "reprojection_positive_z_m": {"value": .01, "source": "inherited first A/B run"},
        "rgbd_depth_trunc_m": {"value": 100., "source": "inherited Open3D adapter after configured .2–4 m filtering"},
        "outlier_neighbors_std": {"value": [20, 3.], "source": "inherited first A/B run"},
        "map_extent_cells_statistic": {"value": [20., 2_000_000, "maximum"], "source": "inherited bounded projection defaults"},
    }


def source_hashes() -> dict[str, str]:
    """First-party Python content hashes work even before a Git commit exists."""
    package = Path(__file__).resolve().parent
    root = package.parents[1]
    files = sorted(package.glob("*.py")) + [root / "test.py", root / "benchmark.py"]
    return {str(path.relative_to(root)): sha256(path) for path in files if path.exists()}


def run_experiment(
    sequence: Path,
    method: str,
    output_root: Path,
    frame_limit: int = 120,
    stride: int = 1,
    timestamp_tolerance_s: float = 0.02,
    settings: ReconstructionSettings | None = None,
    grid_resolution_m: float = 0.02,
    alignment_normal: tuple[float, float, float] = (0.0, -1.0, 0.0),
    alignment_offset_m: float = 0.0,
    height_slice_m: tuple[float, float] | None = None,
) -> Path:
    """Run A/B on exact RGB-depth-selected subset; all geometry is optical-depth metric."""
    if method not in {"oracle_pose_rgbd", "estimated_pose_rgbd"}:
        raise ValueError("Unknown experiment mode")
    if not (sequence / "rgb.txt").exists():
        raise FileNotFoundError(
            "TUM sample missing. From repository root run: python scripts/download_sample_data.py"
        )
    tick = perf_counter()
    settings = settings or ReconstructionSettings()
    intrinsics = Intrinsics()  # TUM recommended ROS defaults for registered images.
    frames, association = select_frames(
        sequence, frame_limit, stride, timestamp_tolerance_s
    )
    timestamps = np.array([f.timestamp for f in frames])
    supplied = None
    if method == "oracle_pose_rgbd":
        supplied, _ = ground_truth_at(
            sequence / "groundtruth.txt", timestamps, timestamp_tolerance_s
        )
        if any(p is None for p in supplied):
            raise ValueError(
                "Oracle needs GT for every selected frame; adjust subset/tolerance explicitly"
            )
    result = reconstruct(frames, intrinsics, settings, supplied)
    # In B this is the FIRST access to GT: it cannot initialize, gate or fuse tracking.
    reference, gt_association = ground_truth_at(
        sequence / "groundtruth.txt",
        np.array([f.timestamp for f in result["accepted"]]),
        timestamp_tolerance_s,
    )
    evaluation = trajectory_metrics(result["poses"], reference)
    alignment = plane_alignment(np.array(alignment_normal), alignment_offset_m)
    cloud = result["cloud"]
    cloud.transform(alignment)
    map_poses = [alignment @ p for p in result["poses"]]
    project_tick = perf_counter()
    products = project(
        np.asarray(cloud.points),
        np.asarray(cloud.colors),
        grid_resolution_m,
        height_slice=height_slice_m,
    )
    projection_s = perf_counter() - project_tick
    output = new_run(output_root, method)
    sources = [
        {
            "index": f.index,
            "rgb_timestamp_s": f.timestamp,
            "depth_timestamp_s": f.depth_timestamp,
            "rgb": str(f.rgb.relative_to(sequence)),
            "depth": str(f.depth.relative_to(sequence)),
            "rgb_sha256": sha256(f.rgb),
            "depth_sha256": sha256(f.depth),
        }
        for f in frames
    ]
    tables = {
        name: sha256(sequence / name)
        for name in ["rgb.txt", "depth.txt", "groundtruth.txt"]
    }
    observed = int(np.count_nonzero(products["count"]))
    metrics = {
        **evaluation,
        "selected_frames": len(frames),
        "accepted_frames": len(result["accepted"]),
        "rejected_frames": len(result["failures"]),
        "unprocessed_after_break": len(frames)
        - len(result["accepted"])
        - len(result["failures"]),
        "tracking_failures": len(result["failures"]),
        "trajectory_breaks": len(result["failures"]),
        "accepted_frame_fraction": len(result["accepted"]) / len(frames),
        "points": len(cloud.points),
        "raw_depth_samples": result["raw_samples"],
        "outliers_removed": result["outliers_removed"],
        "bounds_xyz_m": [
            np.asarray(cloud.points).min(axis=0).tolist(),
            np.asarray(cloud.points).max(axis=0).tolist(),
        ],
        "observed_cells": observed,
        "observed_projected_area_m2": observed * grid_resolution_m**2,
        "observed_grid_fraction": observed / products["count"].size,
        "runtime_s": perf_counter() - tick,
        "timings": {
            **result["timings"],
            "projection_s": projection_s,
            "depth_estimation_s": 0.0,
            "depth_source": "supplied Kinect depth",
            "runtime_scope": "selection, decode, reconstruction, projection, GT evaluation, hashes; export separately",
        },
        "cpu_rss_at_export_bytes": psutil.Process().memory_info().rss,
        "cpu_peak_working_set_bytes": getattr(
            psutil.Process().memory_info(), "peak_wset", None
        ),
        "gpu_memory": "not used by CPU baseline",
        "geometry_accuracy": "not evaluated; no reference surface",
        "warmup": "no neural inference; first odometry included, no steady-state inference claim",
    }
    manifest = {
        "method": method,
        "input_sequence": sequence.name,
        "sequence_path": str(sequence.resolve()),
        "frame_limit": frame_limit,
        "stride": stride,
        "frames": sources,
        "accepted_indices": [f.index for f in result["accepted"]],
        "source_table_sha256": tables,
        "source_provenance": (
            (sequence / "provenance.json").read_text(encoding="utf-8")
            if (sequence / "provenance.json").exists()
            else None
        ),
        "software_hardware": snapshot(),
        "calibration": {
            **asdict(intrinsics),
            "source": "https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats",
            "choice": "recommended ROS default, no undistortion; approximation to fr1 RGB",
            "rgb_depth_alignment": "publisher pre-registered OpenNI",
            "image_orientation": "stored orientation; no resize",
        },
        "depth_encoding": {
            "kind": "uint16 optical-axis depth",
            "units_per_metre": settings.depth_units_per_metre,
            "invalid": 0,
            "publisher_correction": "already applied; do not multiply by 1.035 again",
        },
        "scale_source": "supplied_rgbd",
        "coordinate_transformations": {
            "T_map_first_camera": alignment.tolist(),
            "first_camera_origin": "GT first pose inverse in oracle only; identity in estimated",
            "map_axis_source": "explicit supplied plane normal/offset in first camera coordinates; not verified floor or gravity",
            "supplied_plane_normal": list(alignment_normal),
            "supplied_plane_offset_m": alignment_offset_m,
            "gravity_verified": False,
            "normal_residual": "not fitted; explicit supplied transform",
            "right_handed": True,
            "pose_convention": "T_map_camera, quaternion xyzw, metres, Unix seconds",
        },
        "ground_truth_use": (
            "poses supplied for control fusion"
            if supplied is not None
            else "evaluation only, SE(3) alignment; no estimator/fusion/init access"
        ),
        "association": association,
        "gt_association": gt_association,
        "settings": asdict(settings),
        "tracking_failures": result["failures"],
        "odometry_steps": result["odometry_steps"],
        "timings": metrics["timings"],
        "model_revision": None,
        "dependency_revision": "Open3D 0.19.0 packaged wheel; no external model",
        "first_party_source_sha256": source_hashes(),
        "hyperparameters": {**baseline_parameters(), "selected_run": {"value": {"frame_limit": frame_limit, "stride": stride, "timestamp_tolerance_s": timestamp_tolerance_s, "settings": asdict(settings), "grid_resolution_m": grid_resolution_m, "alignment_normal": list(alignment_normal), "alignment_offset_m": alignment_offset_m, "height_slice_m": height_slice_m}, "source": "editable experiment entry variables; initial subset inherited from test.py"}},
        "assumptions": [
            "static registered RGB-D",
            "no loop closure",
            "stop at first break",
            "quality gates are engineering defaults, not FYLD requirements",
            "declared up direction is unverified; orthographic view is not a level site map",
            "voxel averages can blur surfaces",
            "2 cm cells do not imply 2 cm accuracy",
        ],
    }
    export_run(
        output,
        cloud,
        products,
        manifest,
        metrics,
        [f.timestamp for f in result["accepted"]],
        map_poses,
        run_started_perf=tick,
    )
    print(
        f"{method}: {len(result['accepted'])}/{len(frames)} accepted, ATE={evaluation.get('ate_rmse_m')}; outputs: {output}",
        flush=True,
    )
    return output


def synthetic_demo(output_root: Path, grid_resolution_m: float = 0.05) -> Path:
    """Clearly labelled known synthetic trench, ground plane and box; no tracking benchmark."""
    started = perf_counter()
    x: NDArray
    y: NDArray
    x, y = np.meshgrid(np.arange(-2, 2.001, 0.025), np.arange(-1.5, 1.501, 0.025))
    z = np.zeros_like(x)
    trench = (np.abs(x) < 0.4) & (np.abs(y) < 1.0)
    z[trench] = -0.6
    box = (x > 1.0) & (x < 1.5) & (np.abs(y) < 0.3)
    z[box] = 0.4
    missing = (x < -1.0) & (y > 0.5)
    xyz = np.column_stack([x[~missing], y[~missing], z[~missing]])
    rgb = np.tile([0.65, 0.5, 0.3], (len(xyz), 1))
    rgb[xyz[:, 2] < 0] = [0.3, 0.2, 0.1]
    cloud = o3d.geometry.PointCloud()
    cloud.points, cloud.colors = o3d.utility.Vector3dVector(
        xyz
    ), o3d.utility.Vector3dVector(rgb)
    products = project(xyz, rgb, grid_resolution_m)
    products["metadata"]["sample_count_meaning"] = "synthetic surface samples per cell"
    output = new_run(output_root, "synthetic_known_trench")
    manifest = {
        "method": "synthetic_known_trench",
        "input_sequence": "synthetic plane, .8 m wide/.6 m deep trench, .4 m high box",
        "scale_source": "other: exact synthetic coordinates",
        "tracking_failures": [],
        "coordinate_transformations": "known synthetic +Z up",
        "assumptions": ["not real site data; no tracking or model execution"],
        "first_party_source_sha256": source_hashes(),
        "hyperparameters": {"synthetic_fixture": {"value": {"x_range_m": [-2., 2.], "y_range_m": [-1.5, 1.5], "spacing_m": .025, "trench": {"abs_x_lt_m": .4, "abs_y_lt_m": 1., "z_m": -.6}, "box": {"x_interval_m": [1., 1.5], "abs_y_lt_m": .3, "z_m": .4}, "missing": {"x_lt_m": -1., "y_gt_m": .5}, "grid_resolution_m": grid_resolution_m}, "source": "inherited synthetic demo fixture"}},
    }
    metrics = {
        "selected_frames": 0,
        "accepted_frames": 0,
        "observed_cells": int(np.count_nonzero(products["count"])),
        "runtime_s": perf_counter() - started,
        "evaluation_status": "synthetic demonstration only",
    }
    export_run(
        output, cloud, products, manifest, metrics, [], [], run_started_perf=started
    )
    print(f"Synthetic output only: {output}")
    return output
