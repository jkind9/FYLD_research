"""Prompt maps built from SfM points: filtering, units and filling."""

import numpy as np

from experiments.sfm.src import prompt

IMAGE = (480, 640)
GRID = (192, 256)


def plane(uv):
    """Depth that grows from 1.5 m at the left edge to 3.0 m at the right edge."""
    return 1.5 + 1.5 * uv[:, 0] / 640


def sample(count=100, seed=0):
    rng = np.random.default_rng(seed)
    uv = np.column_stack([rng.uniform(0, 639, count), rng.uniform(0, 479, count)])
    return uv, plane(uv)


def test_linear_fill_recovers_a_plane_inside_the_points():
    uv, depth = sample()
    got = prompt.prompt_map(uv, depth, IMAGE, GRID, "linear")
    assert got.shape == GRID and not np.isnan(got).any()
    centre = got[48:144, 64:192]
    expected = plane(np.column_stack([(np.arange(64, 192) + 0.5) / 0.4, np.zeros(128)]))
    assert np.allclose(centre, expected[None, :], rtol=0.01)


def test_nearest_fill_takes_the_closest_points_depth():
    uv, depth = sample()
    got = prompt.prompt_map(uv, depth, IMAGE, GRID, "nearest")
    column, row = int(uv[0, 0] * 0.4), int(uv[0, 1] * 0.4)
    assert abs(got[row, column] - depth[0]) < 0.05  # another point may share the cell
    assert all(np.abs(depth - value).min() < 1e-5 for value in np.unique(got))  # no value that is not a point's depth


def test_too_few_points_gives_nothing():
    uv, depth = sample(3)
    assert prompt.prompt_map(uv, depth, IMAGE, GRID, "linear") is None
    assert prompt.prompt_map(uv[:0], depth[:0], IMAGE, GRID, "nearest") is None


def scene():
    pose = np.eye(4)
    rows = [{"T_world_camera": pose.tolist()}]
    xyz = np.array([[0, 0, 4.0], [0.1, 0, 4.0], [0, 0, 2.0], [0, 0, 4.0]])
    observations = {"frame_index": np.array([0, 0, 0, 0]), "point_index": np.array([0, 1, 2, 3]),
                    "uv": np.array([[10.0, 10.0], [20, 20], [30, 30], [700, 30]])}
    return rows, xyz, observations


def test_frame_points_filter_and_convert_to_metres():
    rows, xyz, observations = scene()
    keep = np.array([True, True, False, True])
    uv, depth = prompt.frame_points(rows, xyz, observations, keep, 0, size=0.5, width=640, height=480)
    assert depth.tolist() == [2.0, 2.0]  # 4 SfM units at size 0.5; the failed-filter and off-image points are gone
    assert uv.shape == (2, 2)
