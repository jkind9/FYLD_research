import numpy as np
from scipy.spatial.transform import Rotation

from research.experiments.lingbot_map.compare import (
    nearest_rotations,
    processed_geometry,
    processed_pixels,
    similarity,
)


def test_redmi_frame_geometry_matches_demo_crop():
    # 640 x 480 turned upright is 480 x 640; 518 wide gives 690.7, rounded to 686 (49 patches); crop 84 from the top
    assert processed_geometry((640, 480)) == (518 / 480, 686 / 640, 84)


def test_recorded_centre_lands_on_processed_centre():
    assert np.allclose(processed_pixels(np.array([[320.0, 240.0]]), (640, 480)), [[259.0, 259.0]])


def test_clockwise_turn_matches_numpy_rot90():
    image = np.zeros((480, 640))
    image[50, 100] = 1  # recorded pixel u=100, v=50
    row, col = np.argwhere(np.rot90(image, k=-1))[0]  # orientation_control.upright turns this way
    sx, sy, top = processed_geometry((640, 480))
    x, y = processed_pixels(np.array([[100.5, 50.5]]), (640, 480))[0]  # pixel centre
    assert (int(x / sx), int((y + top) / sy)) == (col, row)


def test_nearest_rotations_undoes_a_small_skew():
    rotation = Rotation.from_euler("xyz", [20, 5, -40], degrees=True).as_matrix()
    skewed = rotation @ np.diag([1.004, 0.997, 1.0])  # as large as the bfloat16 camera head's error
    fixed = nearest_rotations(skewed[None])[0]
    assert np.allclose(fixed @ fixed.T, np.eye(3)) and np.allclose(fixed, rotation, atol=5e-3)


def test_similarity_recovers_size_rotation_and_shift():
    rng = np.random.default_rng(0)
    source = rng.normal(size=(50, 3))
    rotation = Rotation.from_euler("xyz", [10, -35, 70], degrees=True).as_matrix()
    target = 2.5 * source @ rotation.T + [1.0, -2.0, 0.5]
    transform, size = similarity(source, target)
    assert abs(size - 2.5) < 1e-9
    assert np.allclose(source @ transform[:3, :3].T + transform[:3, 3], target)
