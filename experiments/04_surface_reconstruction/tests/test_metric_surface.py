"""Metric method boundary with independent camera/world coordinate fixtures."""

import importlib

import numpy as np
import pytest

from experiments.shared.contracts import Calibration, Pose


def method():
    return importlib.import_module(
        "experiments.04_surface_reconstruction.src.metric_surface"
    ).reconstruct_metric


def calibration():
    return Calibration(2, 2, 2.0, 2.0, 0.0, 0.0, "x-right_y-down_z-forward")


def pose(source="estimated"):
    matrix = np.array([[0, -1, 0, 1], [1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]])
    return Pose(matrix, "method-world", "segment-1", source)


def test_metric_points_preserve_every_valid_pixel_and_camera_to_world_direction():
    depth = np.array([[1.0, 2.0], [np.nan, 4.0]])
    valid = np.array([[True, True], [False, True]])
    before_depth, before_valid = depth.copy(), valid.copy()
    result = method()(depth, valid, calibration(), pose())
    np.testing.assert_array_equal(result, [[1, 2, 4], [1, 3, 5], [-1, 4, 7]])
    np.testing.assert_array_equal(depth, before_depth)
    np.testing.assert_array_equal(valid, before_valid)
    assert not np.shares_memory(result, depth)


def test_metric_surface_requires_estimated_pose():
    with pytest.raises(ValueError, match="estimated"):
        method()(
            np.ones((2, 2)),
            np.ones((2, 2), dtype=bool),
            calibration(),
            pose("supplied"),
        )


@pytest.mark.parametrize(
    "depth, valid",
    [
        (np.ones((1, 2)), np.ones((1, 2), dtype=bool)),
        (np.ones((2, 2)), np.ones((2, 1), dtype=bool)),
        (np.ones((2, 2)), np.ones((2, 2), dtype=int)),
        (np.array([[0.0, 1], [1, 1]]), np.ones((2, 2), dtype=bool)),
        (np.array([[np.nan, 1], [1, 1]]), np.ones((2, 2), dtype=bool)),
        (np.array([[-1.0, 1], [1, 1]]), np.ones((2, 2), dtype=bool)),
        (np.array([[np.inf, 1], [1, 1]]), np.ones((2, 2), dtype=bool)),
    ],
)
def test_metric_surface_rejects_bad_grid_mask_or_valid_depth(depth, valid):
    with pytest.raises(ValueError):
        method()(depth, valid, calibration(), pose())


def test_metric_surface_empty_has_full_point_shape():
    result = method()(
        np.full((2, 2), np.nan), np.zeros((2, 2), dtype=bool), calibration(), pose()
    )
    assert result.shape == (0, 3)


def test_metric_surface_full_resolution_is_not_viewer_sampling():
    cal = Calibration(5, 3, 1.0, -1.0, 0.0, 0.0, "x-right_y-up_z-forward")
    result = method()(
        np.ones((3, 5)),
        np.ones((3, 5), dtype=bool),
        cal,
        Pose(np.eye(4), "w", "s", "estimated"),
    )
    assert len(result) == 15
    np.testing.assert_array_equal(result[-1], [4, -2, 1])
