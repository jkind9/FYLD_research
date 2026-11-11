"""Metric targets support one scale per frame and a blended spatial grid."""

import numpy as np
import pytest

from sitescan import scale
from sitescan.types import ArcoreDepth, Camera


def test_depth_targets_use_both_cameras_and_confidence():
    camera = Camera(4, 4, 0, 0, 4, 4)
    raw = ArcoreDepth(
        0,
        np.array([[1.0, 2.0], [0.0, 3.0]], np.float32),
        np.array([[128, 127], [255, 255]], np.uint8),
        Camera(2, 2, 0, 0, 2, 2),
    )
    uv, metres = scale.depth_targets(raw, camera)
    np.testing.assert_array_equal(uv, [[0, 0], [2, 2]])
    np.testing.assert_array_equal(metres, [1.0, 3.0])


def test_depth_targets_drop_pixels_outside_the_colour_image():
    raw = ArcoreDepth(0, np.ones((2, 2)), np.full((2, 2), 255, np.uint8), Camera(1, 1, 0, 0, 2, 2))
    uv, metres = scale.depth_targets(raw, Camera(10, 10, 0, 0, 2, 2))
    np.testing.assert_array_equal(uv, [[0, 0]])
    np.testing.assert_array_equal(metres, [1.0])


@pytest.mark.parametrize("pose", [None, np.eye(4)])
def test_point_targets_keep_only_points_in_front_of_the_camera(pose):
    world = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, -2.0]])
    uv, metres = scale.point_targets(world, np.array([[2, 3], [4, 5]]), pose)
    if pose is None:
        assert uv.shape == (0, 2) and metres.shape == (0,)
    else:
        np.testing.assert_array_equal(uv, [[2, 3]])
        np.testing.assert_array_equal(metres, [2.0])


@pytest.mark.parametrize("count,expected", [(1, None), (2, 0.5)])
def test_ratio_fit_masks_invalid_pairs_and_needs_two_readings(count, expected):
    learned = np.r_[np.full(count, 4.0), 0, np.nan, np.inf]
    target = np.r_[np.full(count, 2.0), 1, 2, 3]
    assert scale.fit_ratio(learned, target) == expected


def test_fit_one_uses_validity_and_the_required_support():
    learned = np.full((2, 3), 4.0)
    uv = np.array([[0, 0], [1, 0], [2, 0]])
    target = np.array([2.0, 2.0, 9.0])
    valid = np.array([[True, True, False], [True, True, True]])
    assert scale.fit_one(learned, valid, uv, target, minimum=2) == 0.5
    assert scale.fit_one(learned, valid, uv, target, minimum=3) is None


def test_grid_fits_supported_cells_and_blends_between_them():
    learned = np.full((6, 10), 4.0)
    rows, cols = np.indices(learned.shape)
    uv = np.c_[cols.ravel(), rows.ravel()]
    target = np.where(cols.ravel() < 5, 2.0, 4.0)
    field = scale.fit_grid(learned, np.ones_like(learned, bool), uv, target, cells=(2, 1))
    np.testing.assert_allclose(field[:, 0], 0.5)
    np.testing.assert_allclose(field[:, -1], 1.0)
    assert 0.5 < field[0, 5] < 1.0


@pytest.mark.parametrize("fallback,expected", [(None, 0.5), (np.log(0.75), 0.75)])
def test_grid_cells_without_support_take_frame_or_supplied_log_scale(fallback, expected):
    learned = np.full((10, 20), 4.0)
    rows, cols = np.indices((10, 10))
    uv = np.c_[cols.ravel(), rows.ravel()]
    target = np.full(100, 2.0)
    field = scale.fit_grid(
        learned, np.ones_like(learned, bool), uv, target, cells=(2, 1), fallback=fallback
    )
    np.testing.assert_allclose(field[:, -1], expected)
    assert scale.fit_grid(learned, np.zeros_like(learned, bool), uv, target) is None


@pytest.mark.parametrize("age_ns,fresh", [(100_000_000, True), (100_000_001, False), (-1, True)])
def test_fresh_depth_retains_the_existing_one_sided_age_rule(age_ns, fresh):
    assert scale.fresh_depth(1_000_000_000, 1_000_000_000 + age_ns) is fresh
