"""Numerical control adapted from archived geometry; no model/backend dependency."""

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

from .contracts import Calibration


def depth_metres(encoded: ArrayLike, units_per_metre: float) -> tuple[NDArray, NDArray]:
    if not np.isfinite(units_per_metre) or units_per_metre <= 0:
        raise ValueError("Depth scale must be positive and finite")
    depth = np.asarray(encoded, dtype=np.float64) / units_per_metre
    if depth.ndim != 2:
        raise ValueError("Depth must be a two-dimensional image")
    valid = np.isfinite(depth) & (depth > 0)
    return np.where(valid, depth, np.nan), valid


def check_depth_grid(depth: NDArray, valid: NDArray, calibration: Calibration) -> None:
    """Check metric depth and its trusted-pixel mask on the calibrated image grid."""
    if depth.shape != (calibration.height, calibration.width) or valid.shape != depth.shape:
        raise ValueError("Depth/mask resolution must match calibration")
    if valid.dtype != np.bool_ or np.any(valid & (~np.isfinite(depth) | (depth <= 0))):
        raise ValueError("Valid mask admits invalid depth")


def backproject(depth: NDArray, valid: NDArray, calibration: Calibration) -> tuple[NDArray, NDArray]:
    check_depth_grid(depth, valid, calibration)
    v, u = np.nonzero(valid)
    z = depth[v, u]
    points = np.column_stack(
        (
            (u - calibration.cx) * z / calibration.fx,
            (v - calibration.cy) * z / calibration.fy,
            z,
        )
    )
    return points, np.column_stack((v, u))


def project(points: ArrayLike, calibration: Calibration) -> NDArray:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all() or np.any(points[:, 2] <= 0):
        raise ValueError("Projection requires finite Nx3 points with positive Z")
    x, y, z = points.T
    return np.column_stack(
        (
            calibration.fx * x / z + calibration.cx,
            calibration.fy * y / z + calibration.cy,
        )
    )


def validate_transform(transform: ArrayLike, *, basis: bool = False) -> None:
    transform = np.asarray(transform, dtype=np.float64)
    if transform.shape != (4, 4) or not np.isfinite(transform).all():
        raise ValueError("Expected finite 4x4 transform")
    r = transform[:3, :3]
    determinant = np.linalg.det(r)
    if (
        not np.allclose(transform[3], [0, 0, 0, 1], atol=1e-10, rtol=0)
        or not np.allclose(r.T @ r, np.eye(3), atol=1e-5, rtol=0)
        or not np.isclose(abs(determinant) if basis else determinant, 1, atol=1e-5, rtol=0)
    ):
        raise ValueError("Expected orthogonal basis" if basis else "Expected proper rigid pose")


def transform_points(points: ArrayLike, transform: ArrayLike, *, basis: bool = False) -> NDArray:
    validate_transform(transform, basis=basis)
    points, transform = np.asarray(points, dtype=float), np.asarray(transform, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite Nx3 points")
    return points @ transform[:3, :3].T + transform[:3, 3]


def pose_matrix(translation: ArrayLike, quaternion_xyzw: ArrayLike) -> NDArray:
    translation, quaternion = np.asarray(translation, dtype=float), np.asarray(quaternion_xyzw, dtype=float)
    if (
        translation.shape != (3,)
        or quaternion.shape != (4,)
        or not np.isfinite(translation).all()
        or not np.isfinite(quaternion).all()
        or not np.isclose(np.linalg.norm(quaternion), 1, atol=1e-5, rtol=0)
    ):
        raise ValueError("Expected metric translation and unit xyzw quaternion")
    rotation = Rotation.from_quat(quaternion).as_matrix()
    return np.block([[rotation, translation[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]])


def associate_times(first: ArrayLike, second: ArrayLike, tolerance_s: float) -> list[tuple[int, int]]:
    """One-to-one nearest match, inclusive tolerance; independent of pose estimation."""
    first, second = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if (
        first.ndim != 1
        or second.ndim != 1
        or not np.isfinite(tolerance_s)
        or tolerance_s < 0
        or not np.isfinite(first).all()
        or not np.isfinite(second).all()
        or np.any(np.diff(first) <= 0)
        or np.any(np.diff(second) <= 0)
    ):
        raise ValueError("Expected finite ordered unique timestamps and nonnegative tolerance")
    candidates: list[tuple[float, int, int]] = []
    for i, timestamp in enumerate(first):
        lo = np.searchsorted(second, timestamp - tolerance_s, side="left")
        hi = np.searchsorted(second, timestamp + tolerance_s, side="right")
        candidates.extend((abs(timestamp - second[j]), i, j) for j in range(lo, hi))
    used_first, used_second, matches = set(), set(), []
    for _, i, j in sorted(candidates):
        if i not in used_first and j not in used_second:
            matches.append((i, j))
            used_first.add(i)
            used_second.add(j)
    return sorted(matches)
