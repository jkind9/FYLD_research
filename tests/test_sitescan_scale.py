"""Metric targets support one scale per frame and a blended spatial grid."""

import numpy as np
import pytest

from sitescan import scale
from sitescan.types import Camera, MeasuredDepth


def test_depth_targets_use_both_cameras_and_confidence():
    camera = Camera(4, 4, 0, 0, 4, 4)
    raw = MeasuredDepth(
        0,
        np.array([[1.0, 2.0], [0.0, 3.0]], np.float32),
        np.array([[128, 127], [255, 255]], np.uint8),
        Camera(2, 2, 0, 0, 2, 2),
        "arcore",
    )
    uv, metres = scale.depth_targets(raw, camera)
    np.testing.assert_array_equal(uv, [[0, 0], [2, 2]])
    np.testing.assert_array_equal(metres, [1.0, 3.0])


def test_depth_targets_drop_pixels_outside_the_colour_image():
    raw = MeasuredDepth(0, np.ones((2, 2)), np.full((2, 2), 255, np.uint8), Camera(1, 1, 0, 0, 2, 2), "arcore")
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


def targets(w=80, h=60, step=2):
    u, v = np.meshgrid(np.arange(0, w, step), np.arange(0, h, step))
    return np.c_[u.ravel(), v.ravel()].astype(float)


def test_too_few_targets_give_no_scale():
    model = np.ones((60, 80))
    uv = targets()[:10]
    assert scale.fit_grid(model, np.ones_like(model, bool), uv, np.ones(10)) is None


def test_cell_index_numbers_cells_row_by_row():
    uv = np.array([[0, 0], [79, 0], [0, 59], [79, 59]], float)
    assert scale.cell_index(uv, (80, 60), cells=(2, 1)).tolist() == [0, 1, 0, 1]
    assert scale.cell_index(uv, (80, 60), cells=(1, 2)).tolist() == [0, 0, 1, 1]


def test_only_cells_with_enough_arcore_pixels_are_supported():
    uv = targets()
    uv = uv[uv[:, 0] < 40]  # ARCore depth covers only the left half
    mask = scale.supported_pixels(uv, (60, 80), cells=(2, 1))
    assert mask[:, :40].all() and not mask[:, 40:].any()


def test_weighted_median_moves_toward_heavy_values_and_is_the_median_without_weights():
    values = np.array([1.0, 2.0, 3.0, 4.0])
    assert scale.weighted_median(values) == 2.5
    assert scale.weighted_median(values, np.array([1.0, 1.0, 1.0, 5.0])) == 4.0
    assert scale.weighted_median(values, np.ones(4)) == 2.0


def test_weights_steer_one_scale_and_the_grid_toward_trusted_targets():
    learned = np.full((6, 10), 2.0)
    valid = np.ones_like(learned, bool)
    uv = np.c_[np.arange(10), np.zeros(10)]
    target = np.r_[np.full(4, 1.0), np.full(6, 3.0)]  # the six targets at 3 m are distrusted
    weight = np.r_[np.full(4, 10.0), np.full(6, 1.0)]
    assert scale.fit_one(learned, valid, uv, target, minimum=2) == 1.5
    assert scale.fit_one(learned, valid, uv, target, minimum=2, weight=weight) == 0.5
    field = scale.fit_grid(learned, valid, uv, target, cells=(1, 1), minimum=2, min_cell_pixels=2, weight=weight)
    np.testing.assert_allclose(field, 0.5)


def test_target_weights_trust_precise_points_more_but_never_without_limit():
    weights = scale.target_weights(np.array([1.0, 4.0, 1.0]), np.array([0.01, 0.4, 0.0]))
    assert weights[0] > weights[1]
    assert weights[2] == pytest.approx(1 / 0.05**2)


def test_robust_inliers_drop_points_far_from_the_line():
    x = np.linspace(0, 1, 50)
    y = 0.2 + 0.5 * x + np.random.default_rng(1).normal(0, 0.01, 50)
    y[[5, 20, 40]] += [0.5, -0.4, 0.8]
    keep = scale.robust_inliers(x, y)
    assert not keep[[5, 20, 40]].any() and keep.sum() >= 45


def power_targets(count=200, exponent=0.1, outliers=0):
    """Learned depth reads 1 to 6 m; the true depth is 0.8 * learned ** 1.1, so far depth reads too near."""
    rng = np.random.default_rng(2)
    learned = np.tile(np.linspace(1.0, 6.0, 100), (10, 1))
    rows = rng.integers(0, 10, count)
    cols = rng.integers(20, 80, count)  # targets cover learned depth from about 2 to 5 m only
    target = 0.8 * learned[rows, cols] ** (1 + exponent)
    target[:outliers] *= 3.0
    return learned, np.c_[cols, rows].astype(float), target


@pytest.mark.parametrize("outliers", [0, 40])
def test_power_fit_recovers_a_scale_that_grows_with_distance(outliers):
    learned, uv, target = power_targets(outliers=outliers)
    field = scale.fit_power(learned, np.ones_like(learned, bool), uv, target)
    first, last = int(uv[:, 0].min()), int(uv[:, 0].max())
    np.testing.assert_allclose(field[0, first : last + 1], 0.8 * learned[0, first : last + 1] ** 0.1, rtol=1e-6)
    # Beyond the targets the scale stays at the nearest end's value instead of extrapolating.
    np.testing.assert_allclose(field[0, :first], field[0, first], rtol=1e-9)
    np.testing.assert_allclose(field[0, last + 1 :], field[0, last], rtol=1e-9)


def test_power_fit_uses_one_scale_when_targets_span_little_depth_and_needs_enough_of_them():
    learned = np.full((4, 4), 2.0)
    learned[0, 0] = 2.4  # a factor of 1.2: too little span to measure a slope
    uv = np.c_[np.tile(np.arange(4), 4), np.repeat(np.arange(4), 4)].astype(float)
    target = learned[uv[:, 1].astype(int), uv[:, 0].astype(int)] * 1.5
    field = scale.fit_power(learned, np.ones_like(learned, bool), uv, target, minimum=10)
    np.testing.assert_allclose(field, 1.5)
    assert scale.fit_power(learned, np.ones_like(learned, bool), uv[:5], target[:5], minimum=10) is None
