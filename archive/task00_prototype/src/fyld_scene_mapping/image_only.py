"""Optional CPU batch sparse structure from motion, with explicitly arbitrary scale."""

import os
from pathlib import Path
from time import perf_counter

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from .geometry import inverse_transform, plane_alignment, transform_points

HYPERPARAMETERS = {
    "frame_limit": {"value": 120, "source": "inherited test.py:22"},
    "stride": {"value": 1, "source": "inherited test.py:23"},
    "timestamp_tolerance_s": {"value": 0.02, "source": "inherited test.py:24"},
    "camera_params": {"value": "525,525,319.5,239.5", "source": "inherited geometry.Intrinsics ROS approximation"},
    "cpu_threads": {"value": 8, "source": "inherited benchmark.py:8"},
    "max_num_features": {"value": 8192, "source": "inherited PyCOLMAP 3.12.6 SiftExtractionOptions default"},
    "matching_overlap": {"value": 10, "source": "inherited PyCOLMAP 3.12.6 SequentialMatchingOptions default"},
    "loop_detection": {"value": False, "source": "inherited PyCOLMAP 3.12.6 SequentialMatchingOptions default"},
    "library_options": {"value": "all effective defaults recorded with todict()", "source": "inherited PyCOLMAP 3.12.6; CPU and fixed calibration explicit"},
    "display_scale": {"value": "divide all points and camera translations by median positive first-camera Z", "source": "n/a arbitrary display normalization only; no metric recovery"},
    "alignment_normal": {"value": [0, -1, 0], "source": "inherited experiments.run_experiment explicit reference axes"},
    "map_limits": {"value": {"resolution": 0.02, "max_extent": 20, "max_cells": 2000000}, "source": "inherited mapping.project defaults; arbitrary units in this run"},
    "preview": {"value": {"cap": 15000, "figure_inches": [13, 8], "dpi": 140}, "source": "inherited reporting.preview defaults"},
}


def arbitrary_map_coordinates(points: NDArray, poses: list[NDArray]) -> tuple:
    """Keep rotations rigid; apply one shared arbitrary scale to XYZ and translations."""
    if not poses or points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite Nx3 points and at least one registered pose")
    first_from_world = inverse_transform(poses[0])
    first_points = transform_points(points, first_from_world)
    positive = first_points[first_points[:, 2] > 0, 2]
    if not len(positive):
        raise ValueError("No positive first-camera Z for arbitrary display normalization")
    divisor = float(np.median(positive))
    transform = plane_alignment(np.array([0., -1., 0.]), 0.) @ first_from_world
    transformed_poses = [transform @ pose for pose in poses]
    normalized_poses = []
    for pose in transformed_poses:
        normalized = pose.copy()
        normalized[:3, 3] /= divisor
        normalized_poses.append(normalized)
    return transform_points(points, transform) / divisor, normalized_poses, divisor, transform


def arbitrary_metadata(metadata: dict) -> dict:
    """Remove metre labels, including nested PNG ranges, without mutating the source."""
    return {
        key[:-2] + "_arbitrary_units" if key.endswith("_m") else key:
        arbitrary_metadata(value) if isinstance(value, dict)
        else "arbitrary units" if key == "units" else value
        for key, value in metadata.items()
    }


def _json_options(value: object) -> object:
    """Convert PyCOLMAP enums from recursive option dictionaries to readable strings."""
    if isinstance(value, dict):
        return {key: _json_options(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_options(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _preview(points: NDArray, colours: NDArray, products: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Match the inherited projection bounds rather than let extreme sparse points hide the scene.
    keep = (np.abs(points) <= 20).all(axis=1)
    xyz, rgb = points[keep], colours[keep]
    indices = np.linspace(0, len(xyz) - 1, min(15000, len(xyz)), dtype=int)
    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(221, projection="3d")
    ax.scatter(*xyz[indices].T, c=rgb[indices], s=0.5)
    ax.set(xlabel="X (arbitrary units)", ylabel="Y (arbitrary units)", zlabel="Z (arbitrary units)", title="Sparse triangulated points; display bounds applied")
    bounds = products["metadata"]["bounds_xy_arbitrary_units"]
    extent = [bounds[0][0], bounds[1][0], bounds[0][1], bounds[1][1]]
    ax = fig.add_subplot(222)
    ax.imshow(products["colour"], origin="lower", extent=extent)
    ax.set(title="Sparse highest-point RGB", xlabel="X (arbitrary units)", ylabel="Y (arbitrary units)")
    ax = fig.add_subplot(223)
    plot = ax.imshow(products["height"], origin="lower", extent=extent, cmap="viridis")
    fig.colorbar(plot, ax=ax, label="Height (arbitrary units)")
    ax.set(title="Blank = no retained sparse sample")
    ax = fig.add_subplot(224)
    plot = ax.imshow(np.log1p(products["count"]), origin="lower", extent=extent)
    fig.colorbar(plot, ax=ax, label="log(1 + triangulated point count)")
    ax.set(title="Sparse sampling; no completeness evidence")
    fig.suptitle("COLMAP RGB-only batch sparse SfM | arbitrary scale | gravity unverified")
    fig.tight_layout()
    fig.savefig(output / "preview.png", dpi=140)
    plt.close(fig)


def _export(model: object, frames: list, output: Path) -> dict:
    import open3d as o3d
    from .mapping import project, save_maps
    from .reporting import write_json

    by_name = {str(frame.rgb.relative_to(frame.rgb.parents[1])).replace("\\", "/"): frame for frame in frames}
    images = sorted(model.images.values(), key=lambda image: by_name[image.name].timestamp)
    images = [image for image in images if image.has_pose]
    poses = []
    for image in images:
        pose = np.eye(4)
        pose[:3, :] = image.cam_from_world().inverse().matrix()
        poses.append(pose)
    raw_points = np.array([point.xyz for point in model.points3D.values()])
    colours = np.array([point.color for point in model.points3D.values()]) / 255.
    points, mapped_poses, divisor, transform = arbitrary_map_coordinates(raw_points, poses)
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    cloud.colors = o3d.utility.Vector3dVector(colours)
    if not o3d.io.write_point_cloud(str(output / "point_cloud.ply"), cloud):
        raise OSError("Sparse point cloud export failed")
    products = project(points, colours)
    save_maps(products, output)
    products["metadata"] = arbitrary_metadata(products["metadata"])
    products["metadata"] = {**products["metadata"], "sample_count_meaning": "retained sparse triangulated points per cell; not fused voxels or complete area", "vertical_reference": "first registered camera origin; explicit up, gravity unverified", "scale_source": "arbitrary"}
    write_json(output / "map_metadata.json", products["metadata"])
    with (output / "trajectory.tum").open("w", encoding="utf-8") as stream:
        stream.write("# timestamp tx ty tz qx qy qz qw; T_map_camera; arbitrary units, seconds\n")
        for image, pose in zip(images, mapped_poses):
            values = [by_name[image.name].timestamp, *pose[:3, 3], *Rotation.from_matrix(pose[:3, :3]).as_quat()]
            stream.write(" ".join(f"{value:.9f}" for value in values) + "\n")
    _preview(points, colours, products, output)
    return {
        "registered_indices": [by_name[image.name].index for image in images],
        "first_registered_rgb": images[0].name,
        "display_scale_divisor_raw_colmap_units": divisor,
        "T_map_colmap_before_scale": transform.tolist(),
        "sparse_points": len(points),
        "mean_reprojection_error_pixels": float(model.compute_mean_reprojection_error()),
        "sampled_cells": int(np.count_nonzero(products["count"])),
        "sparse_grid_sample_fraction": float(np.count_nonzero(products["count"]) / products["count"].size),
        "map_excluded_points": products["metadata"]["rejected_points"],
    }


def run_image_only(sequence: Path, output_root: Path, frame_limit: int = 120, stride: int = 1, tolerance_s: float = 0.02) -> Path:
    """Select the A/B subset, then expose only RGB paths to the batch estimator."""
    import pycolmap
    import psutil
    from .acquisition import sha256
    from .datasets import select_frames
    from .environment import snapshot
    from .reporting import new_run, write_json

    if pycolmap.__version__ != "3.12.6":
        raise RuntimeError("This optional experiment was specified for PyCOLMAP 3.12.6")
    start = perf_counter()
    frames, association = select_frames(sequence, frame_limit, stride, tolerance_s)
    output = new_run(output_root, "colmap_image_only")
    names = [frame.rgb.relative_to(sequence).as_posix() for frame in frames]
    threads = int(os.environ.get("OMP_NUM_THREADS", "8"))
    if threads < 1:
        raise ValueError("OMP_NUM_THREADS must be positive")
    reader = pycolmap.ImageReaderOptions(camera_params="525,525,319.5,239.5")
    extraction = pycolmap.SiftExtractionOptions(num_threads=threads, use_gpu=False)
    matching = pycolmap.SiftMatchingOptions(num_threads=threads, use_gpu=False)
    sequential = pycolmap.SequentialMatchingOptions(num_threads=threads)
    verification = pycolmap.TwoViewGeometryOptions()
    pipeline = pycolmap.IncrementalPipelineOptions(num_threads=threads, ba_refine_focal_length=False, ba_refine_principal_point=False, ba_refine_extra_params=False)
    pipeline.mapper.abs_pose_refine_focal_length = False
    pipeline.mapper.abs_pose_refine_extra_params = False
    pipeline.mapper.num_threads = threads
    manifest = {
        "method": "colmap_image_only", "input_sequence": sequence.name,
        "sequence_path": str(sequence.resolve()), "frame_limit": frame_limit, "stride": stride,
        "timestamp_tolerance_s": tolerance_s, "association": association,
        "frames": [{"index": frame.index, "timestamp_s": frame.timestamp, "rgb": name, "rgb_sha256": sha256(frame.rgb)} for frame, name in zip(frames, names)],
        "selection_table_sha256": {name: sha256(sequence / name) for name in ["rgb.txt", "depth.txt"]},
        "depth_use": "timestamp association only; depth PNGs never read by estimator/export",
        "ground_truth_use": "none; no evaluation or alignment to GT",
        "scale_source": "arbitrary", "gpu_memory": "not used; all stages CPU",
        "software_hardware": {**snapshot(), "pycolmap_version": pycolmap.__version__},
        "calibration": {"model": "PINHOLE", "camera_params_pixels": "525,525,319.5,239.5", "fixed_intrinsics": True, "source": "TUM recommended ROS defaults, inherited A/B approximation; untreated fr1 RGB distortion", "image_orientation": "stored 640x480, no resizing"},
        "effective_library_options": _json_options({"reader": reader.todict(), "extraction": extraction.todict(), "matching": matching.todict(), "sequential": sequential.todict(), "verification": verification.todict(), "pipeline": pipeline.todict()}),
        "hyperparameters": HYPERPARAMETERS,
        "assumptions": ["batch sparse SfM, not SLAM", "no metric scale", "no depth/GT fusion", "static scene", "explicit first-camera up (0,-1,0), gravity unverified", "largest component exported; no bridging", "sparse sampling is not complete surface coverage"],
        "completion_contract": "COMPLETE.json required; missing marker means incomplete",
    }
    write_json(output / "run_manifest.json", {**manifest, "status": "running"})
    timings = {}
    database = str(output / "database.db")
    stages = [
        ("feature_extraction_s", lambda: pycolmap.extract_features(database, str(sequence), image_names=names, camera_mode=pycolmap.CameraMode.SINGLE, camera_model="PINHOLE", reader_options=reader, sift_options=extraction, device=pycolmap.Device.cpu)),
        ("sequential_matching_s", lambda: pycolmap.match_sequential(database, sift_options=matching, matching_options=sequential, verification_options=verification, device=pycolmap.Device.cpu)),
    ]
    try:
        for name, stage in stages:
            tick = perf_counter()
            stage()
            timings[name] = perf_counter() - tick
        tick = perf_counter()
        models = pycolmap.incremental_mapping(database, str(sequence), str(output / "raw_colmap"), options=pipeline)
        timings["incremental_mapping_s"] = perf_counter() - tick
        if not models:
            raise RuntimeError("COLMAP did not register a reconstruction; optional experiment failed")
        component_counts = {str(key): model.num_reg_images() for key, model in models.items()}
        component_id, model = max(models.items(), key=lambda item: item[1].num_reg_images())
        tick = perf_counter()
        diagnostics = _export(model, frames, output)
        timings["export_s"] = perf_counter() - tick
    except (RuntimeError, ValueError, OSError) as error:
        failure = {**manifest, "status": "failed", "error": str(error), "timings": timings}
        write_json(output / "run_manifest.json", failure)
        write_json(output / "metrics.json", {"status": "failed", "error": str(error), "timings": timings})
        (output / "report.md").write_text(f"# Optional COLMAP experiment failed\n\n{error}\n\nNo successful reconstruction is claimed. No COMPLETE marker.\n", encoding="utf-8")
        raise
    memory = psutil.Process().memory_info()
    metrics = {**diagnostics, "status": "complete", "selected_frames": len(frames), "registered_frames": model.num_reg_images(), "registered_frame_fraction": model.num_reg_images() / len(frames), "components_registered_frames": component_counts, "exported_component": component_id, "geometry_accuracy": "not evaluated; no metric scale or surface reference", "trajectory_accuracy": "not evaluated; no GT used", "timings": timings, "end_to_end_runtime_s": perf_counter() - start, "cpu_rss_at_export_bytes": memory.rss, "cpu_peak_working_set_bytes": getattr(memory, "peak_wset", None), "gpu_memory": "not used"}
    final_manifest = {**manifest, "status": "complete", "diagnostics": diagnostics, "timings": timings, "components_registered_frames": component_counts, "exported_component": component_id}
    write_json(output / "run_manifest.json", final_manifest)
    write_json(output / "metrics.json", metrics)
    report = "# COLMAP image-only batch sparse reconstruction\n\nRGB-only sparse structure from motion. Arbitrary scale; no metric accuracy claim.\nDepth timestamps select the same subset as A/B. Depth pixels and ground truth were never used.\nApproximate fixed pinhole calibration; RGB distortion untreated. Explicit first-camera axes; gravity unverified.\nOnly the largest component is exported. Other components remain separate in raw_colmap.\nThe shared display scale divides points and camera translations by median positive first-camera Z. Raw COLMAP models are preserved.\nMap bounds omit extreme sparse points; the PLY keeps all triangulated points. Unknown cells remain NaN. Sparse samples do not show surface completeness.\n\n## Measured diagnostics\n\n"
    import json
    (output / "report.md").write_text(report + "```json\n" + json.dumps(metrics, indent=2) + "\n```\n", encoding="utf-8")
    write_json(output / "COMPLETE.json", {"status": "complete", "method": "colmap_image_only", "manifest_sha256": sha256(output / "run_manifest.json"), "metrics_sha256": sha256(output / "metrics.json")})
    print(f"COLMAP registered {model.num_reg_images()}/{len(frames)}; output: {output}", flush=True)
    return output
