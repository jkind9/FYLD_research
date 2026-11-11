"""Seeded dominant-plane fitting and principal axes from metric point arrays."""

import numpy as np

from .types import Plane

INLIER_DISTANCE_M = 0.02
ITERATIONS = 500
SAMPLE_POINTS = 50_000
SEED = 0
MIN_CROSS_M2 = 1e-12


def ransac(points: np.ndarray, rng, *, inlier_distance_m: float, iterations: int):
    """The candidate point and normal with the largest sampled plane support."""
    best_count = -1
    best_point = None
    best_normal = None
    for _ in range(iterations):
        first, second, third = points[rng.choice(len(points), size=3, replace=False)]
        normal = np.cross(second - first, third - first)
        length = np.linalg.norm(normal)
        if length < MIN_CROSS_M2:
            continue
        normal = normal / length
        count = int(np.count_nonzero(np.abs((points - first) @ normal) <= inlier_distance_m))
        if count > best_count:
            best_count = count
            best_point = first
            best_normal = normal
    if best_normal is None:
        raise ValueError("Points do not span a plane")
    return best_point, best_normal


def scatter_axes(reference: np.ndarray, relative: np.ndarray):
    """Centre and principal axes of points given relative to a reference point."""
    if len(relative) < 3:
        raise ValueError("Fewer than 3 points lie on the plane")
    mean = relative.sum(axis=0) / len(relative)
    covariance = relative.T @ relative / len(relative) - np.outer(mean, mean)
    _, vectors = np.linalg.eigh(covariance)
    return reference + mean, vectors[:, ::-1].T


def fit_dominant_plane(
    points: np.ndarray,
    *,
    inlier_distance_m: float = INLIER_DISTANCE_M,
    iterations: int = ITERATIONS,
    sample_size: int = SAMPLE_POINTS,
    seed: int = SEED,
) -> Plane:
    """The dominant sampled plane, refitted on all of its inliers."""
    points = np.asarray(points, dtype=np.float64)
    rng = np.random.default_rng(seed)
    subset = (
        points[rng.choice(len(points), size=sample_size, replace=False)]
        if len(points) > sample_size
        else points
    )
    point, normal = ransac(subset, rng, inlier_distance_m=inlier_distance_m, iterations=iterations)
    inliers = points[np.abs((points - point) @ normal) <= inlier_distance_m]
    centre, axes = scatter_axes(point, inliers - point)
    return Plane(centre, axes[2], len(inliers) / len(points), "fitted_dominant_plane")
