"""Metres, column-vector transforms T_world_camera, optical +X right/+Y down/+Z forward."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation


@dataclass(frozen=True)
class Intrinsics:
    """Pinhole intrinsics in pixels at the stored image resolution."""

    width: int = 640
    height: int = 480
    fx: float = 525.0
    fy: float = 525.0
    cx: float = 319.5
    cy: float = 239.5

    def __post_init__(self) -> None:
        if (
            self.width < 1
            or self.height < 1
            or not np.isfinite([self.fx, self.fy, self.cx, self.cy]).all()
            or min(self.fx, self.fy) <= 0
        ):
            raise ValueError("Invalid image dimensions or intrinsics")

    def resized(self, width: int, height: int) -> "Intrinsics":
        """Resize with pixel-centre convention; no rotation/crop implied."""
        sx, sy = width / self.width, height / self.height
        return Intrinsics(
            width,
            height,
            self.fx * sx,
            self.fy * sy,
            (self.cx + 0.5) * sx - 0.5,
            (self.cy + 0.5) * sy - 0.5,
        )


def depth_metres(encoded: NDArray, units_per_metre: float = 5000.0) -> NDArray:
    """Convert optical-axis depth; zero, negative and nonfinite values become NaN."""
    if not np.isfinite(units_per_metre) or units_per_metre <= 0:
        raise ValueError("Depth scale must be positive and finite")
    depth = np.asarray(encoded, dtype=np.float64) / units_per_metre
    return np.where(np.isfinite(depth) & (depth > 0), depth, np.nan)


def backproject(
    depth: NDArray,
    intrinsics: Intrinsics,
    min_depth: float = 0.2,
    max_depth: float = 4.0,
    step: int = 1,
) -> tuple[NDArray, NDArray]:
    """Return camera XYZ and original [row,column] indices for valid optical depth."""
    if depth.shape != (intrinsics.height, intrinsics.width):
        raise ValueError("Depth shape must match intrinsics")
    if step < 1 or not 0 <= min_depth < max_depth:
        raise ValueError("Invalid sampling step or depth interval")
    v, u = np.mgrid[0 : intrinsics.height : step, 0 : intrinsics.width : step]
    z = depth[v, u]
    good = np.isfinite(z) & (z >= min_depth) & (z <= max_depth)
    u, v, z = u[good], v[good], z[good]
    xyz = np.column_stack(
        (
            (u - intrinsics.cx) * z / intrinsics.fx,
            (v - intrinsics.cy) * z / intrinsics.fy,
            z,
        )
    )
    return xyz, np.column_stack((v, u))


def validate_transform(transform: NDArray) -> None:
    """Reject non-rigid, reflected or nonfinite SE(3) transforms."""
    if transform.shape != (4, 4) or not np.isfinite(transform).all():
        raise ValueError("Expected a finite 4x4 transform")
    r = transform[:3, :3]
    if (
        not np.allclose(transform[3], [0, 0, 0, 1])
        or not np.allclose(r.T @ r, np.eye(3), atol=1e-5)
        or not np.isclose(np.linalg.det(r), 1, atol=1e-5)
    ):
        raise ValueError("Expected a proper rigid transform")


def transform_points(points: NDArray, transform: NDArray) -> NDArray:
    """Apply T_destination_source to Nx3 source points."""
    validate_transform(transform)
    return points @ transform[:3, :3].T + transform[:3, 3]


def inverse_transform(transform: NDArray) -> NDArray:
    """Invert SE(3) without a general matrix inverse."""
    validate_transform(transform)
    result = np.eye(4)
    result[:3, :3] = transform[:3, :3].T
    result[:3, 3] = -result[:3, :3] @ transform[:3, 3]
    return result


def pose_matrix(translation: NDArray, quaternion_xyzw: NDArray) -> NDArray:
    """TUM translation in metres and quaternion qx,qy,qz,qw -> T_world_camera."""
    pose = np.eye(4)
    pose[:3, :3] = Rotation.from_quat(quaternion_xyzw).as_matrix()
    pose[:3, 3] = translation
    validate_transform(pose)
    return pose


def plane_alignment(normal: NDArray, offset: float) -> NDArray:
    """Align an explicitly supplied signed plane n·p+d=0 to Z=0, +normal up."""
    normal = np.asarray(normal, dtype=float)
    norm = np.linalg.norm(normal)
    if not np.isfinite(normal).all() or not np.isfinite(offset) or norm < 1e-9:
        raise ValueError("Invalid plane")
    n = normal / norm
    # Project camera X onto plane to retain an interpretable heading.
    x = np.array([1.0, 0.0, 0.0])
    if abs(n @ x) > 0.95:
        x = np.array([0.0, 1.0, 0.0])
    x -= n * (n @ x)
    x /= np.linalg.norm(x)
    y = np.cross(n, x)
    t = np.eye(4)
    t[:3, :3] = np.stack([x, y, n])
    t[2, 3] = offset / norm
    validate_transform(t)
    return t
