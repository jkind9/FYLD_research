import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from fyld_scene_mapping.geometry import (
    Intrinsics,
    backproject,
    depth_metres,
    inverse_transform,
    plane_alignment,
    pose_matrix,
    transform_points,
)


def test_optical_depth_backprojection_and_indices() -> None:
    k = Intrinsics(3, 2, 2.0, 2.0, 1.0, 0.0)
    xyz, vu = backproject(np.array([[2.0, 2.0, 2.0], [0.0, np.nan, 4.0]]), k)
    np.testing.assert_allclose(xyz, [[-1, 0, 2], [0, 0, 2], [1, 0, 2], [2, 2, 4]])
    np.testing.assert_array_equal(vu, [[0, 0], [0, 1], [0, 2], [1, 2]])
    # Off-axis ray distance is greater than optical-axis Z.
    assert np.linalg.norm(xyz[0]) > xyz[0, 2]


def test_depth_units_and_invalid_values() -> None:
    d = depth_metres(np.array([0.0, 5000.0, 10000.0, -1.0, np.inf]))
    np.testing.assert_allclose(d[1:3], [1.0, 2.0])
    assert np.isnan(d[[0, 3, 4]]).all()
    with pytest.raises(ValueError):
        depth_metres(np.array([1]), 0)


def test_depth_limits_and_empty_depth() -> None:
    k = Intrinsics(2, 2)
    p, vu = backproject(np.array([[0.0, np.nan], [np.inf, -1.0]]), k)
    assert p.shape == (0, 3) and vu.shape == (0, 2)
    with pytest.raises(ValueError):
        backproject(np.ones((3, 3)), k)


def test_transform_composition_and_inverse() -> None:
    a = pose_matrix(
        np.array([2.0, 3.0, 1.0]), Rotation.from_euler("z", 90, degrees=True).as_quat()
    )
    b = pose_matrix(np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0, 1.0]))
    p = np.array([[1.0, 2.0, 3.0]])
    np.testing.assert_allclose(
        transform_points(transform_points(p, b), a),
        transform_points(p, a @ b),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        transform_points(transform_points(p, a), inverse_transform(a)), p
    )
    np.testing.assert_allclose(a @ inverse_transform(a), np.eye(4), atol=1e-12)


def test_source_target_odometry_inverse_convention() -> None:
    # Camera moves +1 world X -> static scene moves -1 in target camera.
    target_source = pose_matrix(
        np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0, 1.0])
    )
    world_target = np.eye(4) @ inverse_transform(target_source)
    np.testing.assert_allclose(world_target[:3, 3], [1.0, 0.0, 0.0])


def test_quaternion_xyzw_and_right_handed_alignment() -> None:
    pose = pose_matrix(np.zeros(3), np.array([0.0, 0.0, np.sqrt(0.5), np.sqrt(0.5)]))
    np.testing.assert_allclose(
        transform_points(np.array([[1.0, 0.0, 0.0]]), pose),
        [[0.0, 1.0, 0.0]],
        atol=1e-12,
    )
    alignment = plane_alignment(np.array([0.0, -2.0, 0.0]), 4.0)
    np.testing.assert_allclose(
        transform_points(np.array([[0.0, 2.0, 1.0]]), alignment)[0, 2], 0.0
    )
    assert np.isclose(np.linalg.det(alignment[:3, :3]), 1.0)


def test_resized_intrinsics_pixel_centres() -> None:
    k = Intrinsics(640, 480).resized(320, 240)
    np.testing.assert_allclose([k.fx, k.fy, k.cx, k.cy], [262.5, 262.5, 159.5, 119.5])
