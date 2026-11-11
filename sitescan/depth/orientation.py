"""Image and camera rotation between recorded and upright pixel grids."""

import numpy as np

CLOCKWISE = np.array([[0.0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def upright(image: np.ndarray, turns: int = 1) -> np.ndarray:
    """The recorded array rotated clockwise by the requested quarter turns."""
    return np.rot90(image, k=-turns)


def recorded(image: np.ndarray, turns: int = 1) -> np.ndarray:
    """The upright array restored to its recorded pixel grid."""
    return np.rot90(image, k=turns)


def quarter_turns(world_from_camera_cv: np.ndarray) -> int:
    """Clockwise turns that bring image down closest to world down."""
    right = world_from_camera_cv[:3, 0]
    down = world_from_camera_cv[:3, 1]
    candidates = [down, right, -down, -right]
    return int(np.argmax([-axis[1] for axis in candidates]))


def turned_camera(world_from_camera_cv: np.ndarray, intrinsics, size, turns: int):
    """Pose, intrinsics and dimensions for the rotated pixel grid."""
    pose = np.asarray(world_from_camera_cv, float)
    fx, fy, cx, cy = intrinsics
    width, height = size
    for _ in range(turns % 4):
        pose = pose @ CLOCKWISE
        fx, fy = fy, fx
        cx, cy = height - 1 - cy, cx
        width, height = height, width
    return pose, (fx, fy, cx, cy), (width, height)
