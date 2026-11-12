"""Rays, two-view triangulation and its depth error, for cameras with known poses."""

import numpy as np

from sitescan.types import Camera


def rays(uv: np.ndarray, camera: Camera) -> np.ndarray:
    """N x 3 camera-axis directions through pixels, scaled so that z is 1."""
    return np.c_[
        (uv[:, 0] - camera.cx) / camera.fx, (uv[:, 1] - camera.cy) / camera.fy, np.ones(len(uv))
    ]


def project(points_world: np.ndarray, camera: Camera, world_from_camera: np.ndarray):
    """(N x 2 pixels, N camera-plane depths) of world points seen from an OpenCV camera."""
    camera_from_world = np.linalg.inv(world_from_camera)
    local = points_world @ camera_from_world[:3, :3].T + camera_from_world[:3, 3]
    with np.errstate(divide="ignore", invalid="ignore"):
        uv = np.c_[
            camera.fx * local[:, 0] / local[:, 2] + camera.cx,
            camera.fy * local[:, 1] / local[:, 2] + camera.cy,
        ]
    return uv, local[:, 2]


def triangulate(uv_a, uv_b, camera_a: Camera, camera_b: Camera, pose_a, pose_b) -> np.ndarray:
    """N x 3 world points midway between the closest points of each pair of rays.

    Nearly parallel rays give far or undefined points; callers drop them by their parallax.
    """
    da = rays(uv_a, camera_a) @ pose_a[:3, :3].T
    db = rays(uv_b, camera_b) @ pose_b[:3, :3].T
    da /= np.linalg.norm(da, axis=1, keepdims=True)
    db /= np.linalg.norm(db, axis=1, keepdims=True)
    between = pose_a[:3, 3] - pose_b[:3, 3]
    cos = np.einsum("ij,ij->i", da, db)
    along_a = np.einsum("ij,j->i", da, between)
    along_b = np.einsum("ij,j->i", db, between)
    with np.errstate(divide="ignore", invalid="ignore"):
        denominator = 1.0 - cos**2
        s = (cos * along_b - along_a) / denominator
        t = (along_b - cos * along_a) / denominator
    return 0.5 * (pose_a[:3, 3] + s[:, None] * da + pose_b[:3, 3] + t[:, None] * db)


def parallax(points_world: np.ndarray, pose_a: np.ndarray, pose_b: np.ndarray) -> np.ndarray:
    """Angle in radians at each point between the rays from the two camera centres."""
    to_a = pose_a[:3, 3] - points_world
    to_b = pose_b[:3, 3] - points_world
    cos = np.einsum("ij,ij->i", to_a, to_b) / (
        np.linalg.norm(to_a, axis=1) * np.linalg.norm(to_b, axis=1)
    )
    return np.arccos(np.clip(cos, -1.0, 1.0))


def depth_sigma(depth_m, parallax_rad, focal_px: float, sigma_px: float) -> np.ndarray:
    """Standard error of a triangulated depth, in metres: z * sigma_px / (f * sin(parallax)).

    A pixel error turns a ray by sigma_px / f radians; rays crossing at a small angle slide far
    along each other for that turn. For two side-by-side cameras this is the stereo rule
    z^2 sigma / (f b).
    """
    return depth_m * sigma_px / (focal_px * np.sin(parallax_rad))


def epipolar_distance(uv_a, uv_b, camera_a: Camera, camera_b: Camera, pose_a, pose_b) -> np.ndarray:
    """Pixel distance of each point in image b from the epipolar line of its match in image a."""
    b_from_a = np.linalg.inv(pose_b) @ pose_a
    t = b_from_a[:3, 3]
    cross = np.array([[0.0, -t[2], t[1]], [t[2], 0.0, -t[0]], [-t[1], t[0], 0.0]])
    lines = rays(uv_a, camera_a) @ (cross @ b_from_a[:3, :3]).T
    normalised = rays(uv_b, camera_b)
    # The line in normalised coordinates, rescaled to pixels of image b.
    scale = np.hypot(lines[:, 0] / camera_b.fx, lines[:, 1] / camera_b.fy)
    return np.abs(np.einsum("ij,ij->i", lines, normalised)) / scale
