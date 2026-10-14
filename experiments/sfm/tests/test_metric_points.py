"""Size from a few metric depth readings: reading extraction and the two size rules."""

import argparse

import numpy as np
import pytest

from experiments.sfm import run_dense
from experiments.sfm.src import metric_points


def readings(ratios_by_frame):
    frames = np.concatenate([np.full(len(r), k) for k, r in enumerate(ratios_by_frame)])
    return {"frame": frames, "ratio": np.concatenate([np.asarray(r, float) for r in ratios_by_frame])}


def test_noiseless_readings_give_the_true_ratio_in_both_modes():
    data = readings([[0.5] * 30] * 6)
    for n in (5, 20, 100, None):
        assert metric_points.run_size(data, n, seed=1) == pytest.approx(0.5)
        assert metric_points.frame_size(data, n, seed=1) == pytest.approx(0.5)


def test_outliers_do_not_move_a_hundred_readings_past_two_percent():
    rng = np.random.default_rng(0)
    ratios = np.where(rng.random(2000) < 0.2, rng.uniform(0.1, 2.0, 2000), 0.5 + rng.normal(0, 0.005, 2000))
    data = readings([ratios[i::10] for i in range(10)])
    assert metric_points.run_size(data, 100, seed=3) == pytest.approx(0.5, rel=0.02)


def test_asking_for_more_than_exists_uses_everything():
    data = readings([[0.4, 0.5, 0.9]])
    assert metric_points.run_size(data, 50, seed=0) == pytest.approx(0.5)
    assert metric_points.run_size(data, None, seed=0) == pytest.approx(0.5)


def test_same_seed_repeats_and_other_seed_differs():
    data = readings([np.linspace(0.3, 0.7, 200)])
    a, b = metric_points.run_size(data, 5, seed=1), metric_points.run_size(data, 5, seed=1)
    assert a == b
    assert len({metric_points.run_size(data, 5, seed=s) for s in range(10)}) > 1


def test_frame_mode_uses_what_a_short_frame_has_and_skips_empty_frames():
    data = readings([[0.5, 0.5, 0.5], [], [0.8] * 10])
    # frame 0 gives 0.5 from its 3 readings, frame 1 has none, frame 2 gives 0.8: median of two
    assert metric_points.frame_size(data, 5, seed=0) == pytest.approx(0.65)


def test_nothing_to_read_gives_none():
    empty = {"frame": np.array([], int), "ratio": np.array([])}
    assert metric_points.run_size(empty, 5, seed=0) is None
    assert metric_points.frame_size(empty, 5, seed=0) is None


def scene():
    """Two frames, identity pose; four points at SfM depth 4 and one at depth 2; depth camera reads 2 m everywhere."""
    pose = np.eye(4)
    rows = [{"T_world_camera": pose.tolist()}, {"T_world_camera": pose.tolist()}]
    xyz = np.array([[0, 0, 4], [0.1, 0, 4], [0, 0.1, 4], [0.1, 0.1, 4], [0, 0, 2.0], [0, 0, 4]], float)
    observations = {"frame_index": np.array([0, 0, 0, 1, 1, 1]), "point_index": np.array([0, 1, 4, 2, 3, 5]),
                    "uv": np.array([[10, 10], [20, 20], [30, 30], [10, 10], [11, 11], [12, 12]], float)}
    return rows, xyz, observations


def test_readings_come_only_from_kept_points_and_valid_depth_pixels():
    rows, xyz, observations = scene()
    depth = np.full((60, 60), 2.0)
    valid = np.ones((60, 60), bool)
    valid[11, 11] = False
    keep = np.array([True, True, True, True, False, True])  # point 4 fails the track or error filter
    got = metric_points.readings(rows, xyz, observations, keep, lambda k: (depth, valid))
    # observations: (f0,p0) (f0,p1) (f0,p4 dropped) (f1,p2) (f1,p3 invalid pixel) (f1,p5)
    assert got["frame"].tolist() == [0, 0, 1, 1]
    assert np.allclose(got["ratio"], 0.5)


def test_sensor_range_and_missing_depth_are_dropped():
    rows, xyz, observations = scene()
    keep = np.ones(6, bool)
    far = np.full((60, 60), 9.0)
    ok = np.ones((60, 60), bool)
    assert len(metric_points.readings(rows, xyz, observations, keep, lambda k: (far, ok))["ratio"]) == 0
    assert len(metric_points.readings(rows, xyz, observations, keep, lambda k: None)["ratio"]) == 0


def test_dense_runner_accepts_a_number_for_the_size_and_refuses_words():
    assert run_dense.size_option("0.25") == 0.25
    assert run_dense.size_option("best-fit") == "best-fit"
    with pytest.raises(argparse.ArgumentTypeError):
        run_dense.size_option("abc")
