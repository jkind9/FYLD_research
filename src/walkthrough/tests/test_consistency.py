"""Surface gap: how far one frame's surface sits from another's once both are placed in the world."""

import numpy as np
import pytest

from experiments.shared.contracts import Calibration, Pose
from src.walkthrough import consistency

CAMERA = Calibration(40, 30, 30.0, 30.0, 19.5, 14.5, "x-right_y-down_z-forward")
FINE = Calibration(80, 60, 60.0, 60.0, 39.5, 29.5, "x-right_y-down_z-forward")


def _pose(x=0.0, z=0.0, world="w", segment="0", turn=False):
    matrix = np.eye(4)
    if turn:  # half a turn about the vertical axis: the camera looks backwards
        matrix[:3, :3] = np.diag([-1.0, 1.0, -1.0])
    matrix[:3, 3] = [x, 0.0, z]
    return Pose(matrix, world, segment, "estimated")


def _plane(depth_m, camera=CAMERA):
    depth = np.full((camera.height, camera.width), depth_m)
    return depth, np.ones(depth.shape, dtype=bool)


def test_same_view_of_the_same_surface_has_no_gap():
    depth, valid = _plane(2.0)

    gap = consistency.surface_gap(depth, valid, _pose(), CAMERA, depth.copy(), valid.copy(), _pose(), CAMERA)

    assert gap["median_signed_m"] == pytest.approx(0.0, abs=1e-9)
    assert gap["median_abs_m"] == pytest.approx(0.0, abs=1e-9)
    assert gap["overlap"] > 0.9


def test_a_frame_read_ten_percent_too_far_sits_behind_the_other():
    depth_a, valid = _plane(2.0)
    depth_b, _ = _plane(2.2)

    gap = consistency.surface_gap(depth_a, valid, _pose(), CAMERA, depth_b, valid, _pose(), CAMERA)

    assert gap["median_signed_m"] == pytest.approx(0.2, abs=0.01)
    assert gap["median_abs_m"] == pytest.approx(0.2, abs=0.01)


def test_a_sideways_move_with_consistent_depth_has_no_gap():
    depth, valid = _plane(2.0)

    gap = consistency.surface_gap(depth, valid, _pose(), CAMERA, depth, valid, _pose(x=0.1), CAMERA)

    assert abs(gap["median_signed_m"]) < 1e-3
    assert 0.0 < gap["overlap"] < 1.0  # part of B's view is outside A's picture


def test_only_the_nearest_point_per_pixel_counts():
    # B sees the same view at twice the resolution: alternate rows are a near surface (1 m)
    # and a far one (2 m), so every A pixel receives both. A z-buffer keeps the near one.
    depth_a, valid_a = _plane(2.0)
    depth_b = np.where(np.arange(FINE.height)[:, None] % 2 == 0, 1.0, 2.0) * np.ones((1, FINE.width))
    valid_b = np.ones(depth_b.shape, dtype=bool)

    gap = consistency.surface_gap(depth_a, valid_a, _pose(), CAMERA, depth_b, valid_b, _pose(), FINE)

    assert gap["median_signed_m"] == pytest.approx(-1.0, abs=1e-9)


def test_frames_with_nothing_in_common_report_no_gap_rather_than_zero():
    depth, valid = _plane(2.0)

    gap = consistency.surface_gap(depth, valid, _pose(), CAMERA, depth, valid, _pose(turn=True), CAMERA)

    assert gap["overlap"] == 0.0
    assert gap["median_signed_m"] is None
    assert gap["median_abs_m"] is None
    assert gap["pixels"] == 0


def test_inputs_are_not_changed():
    depth, valid = _plane(2.0)
    before = depth.copy(), valid.copy()

    consistency.surface_gap(depth, valid, _pose(), CAMERA, depth, valid, _pose(x=0.1), CAMERA)

    assert np.array_equal(depth, before[0]) and np.array_equal(valid, before[1])


def test_gap_by_lag_pairs_each_frame_with_the_one_lag_frames_earlier_in_the_same_origin():
    depths = [_plane(2.0), _plane(2.0), _plane(2.4), _plane(2.0)]
    poses = [_pose(), _pose(), _pose(), _pose(world="other")]
    loaded: list[int] = []

    def load(index):
        loaded.append(index)
        return depths[index]

    series = consistency.gap_by_lag(load, poses, [CAMERA] * 4, lags=(1, 2))

    assert series[1][0] is None  # no frame before the first
    assert series[1][1]["median_abs_m"] == pytest.approx(0.0, abs=1e-9)
    assert series[1][2]["median_signed_m"] == pytest.approx(0.4, abs=0.01)
    assert series[1][3] is None  # different tracking world: never compared
    assert series[2][2]["median_signed_m"] == pytest.approx(0.4, abs=0.01)
    assert sorted(set(loaded)) == [0, 1, 2, 3]
    assert len(loaded) == 4  # each frame read once


def test_median_gap_ignores_missing_pairs():
    series = [None, {"median_abs_m": 0.1}, {"median_abs_m": None}, {"median_abs_m": 0.3}]

    assert consistency.median_gap(series) == pytest.approx(0.2)
    assert consistency.median_gap([None, None]) is None


def test_lags_must_be_positive_integers():
    with pytest.raises(ValueError, match="lag"):
        consistency.gap_by_lag(lambda i: _plane(2.0), [_pose()], [CAMERA], lags=(0,))
