"""Site summary from the thinned surface and observed camera positions."""

import numpy as np

from .footprint import CELL_SIZE_M, footprint
from .plane import (
    INLIER_DISTANCE_M,
    ITERATIONS,
    SAMPLE_POINTS,
    SEED,
    fit_dominant_plane,
)

MIN_MAP_POINTS = 1000


def measure_site(
    surface: np.ndarray,
    cameras,
    *,
    cell_size_m: float = CELL_SIZE_M,
    inlier_distance_m: float = INLIER_DISTANCE_M,
    iterations: int = ITERATIONS,
    sample_size: int = SAMPLE_POINTS,
    seed: int = SEED,
    min_points: int = MIN_MAP_POINTS,
) -> dict:
    """Area, extent and height measurements, or a reason to skip the surface."""
    if len(surface) < min_points:
        return {"skipped": f"fewer than {min_points} surface points"}
    import open3d as o3d

    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(surface))
    surface = np.asarray(cloud.voxel_down_sample(cell_size_m / 2).points)
    try:
        plane = fit_dominant_plane(
            surface,
            inlier_distance_m=inlier_distance_m,
            iterations=iterations,
            sample_size=sample_size,
            seed=seed,
        )
        measured = footprint(
            surface,
            plane,
            np.mean(cameras, 0) - plane.point,
            cell_size_m=cell_size_m,
            band_m=inlier_distance_m,
        )
    except ValueError as error:
        return {"skipped": str(error)}
    return {
        "observed_area_m2": measured.observed_area_m2,
        "plane_area_m2": measured.plane_area_m2,
        "length_m": measured.length_m,
        "width_m": measured.width_m,
        "highest_m": measured.highest_m,
        "plane_normal": measured.plane.normal.tolist(),
    }
