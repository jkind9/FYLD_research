import numpy as np
import pytest

from fyld_scene_mapping.mapping import project


def fixture_surfaces() -> tuple[np.ndarray, np.ndarray]:
    x, y = np.meshgrid(np.arange(0.025, 2.0, 0.05), np.arange(0.025, 1.0, 0.05))
    z = np.zeros_like(x)
    trench = (x >= 0.5) & (x < 1.0)
    z[trench] = -0.6
    box = (x >= 1.5) & (y < 0.5)
    z[box] = 0.4
    p = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    return p, np.tile([0.5, 0.3, 0.1], (len(p), 1))


def test_plane_box_trench_dimensions_and_height() -> None:
    p, c = fixture_surfaces()
    maps = project(p, c, resolution=0.05)
    assert maps["height"].shape == (20, 40)
    np.testing.assert_allclose(maps["height"][:, 10:20], -0.6)
    np.testing.assert_allclose(maps["height"][:10, 30:], 0.4)
    assert np.count_nonzero(maps["height"] == -0.6) * 0.05**2 == pytest.approx(0.5)
    np.testing.assert_allclose(maps["metadata"]["bounds_xy_m"], [[0, 0], [2, 1]])


def test_unknown_cells_and_multilevel_projection() -> None:
    p = np.array([[0.01, 0.01, -0.6], [0.01, 0.01, 0.0], [0.21, 0.21, 0.4]])
    c = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    maps = project(p, c, 0.1)
    assert maps["height"][0, 0] == 0.0
    assert maps["minimum"][0, 0] == -0.6 and maps["count"][0, 0] == 2
    assert np.isnan(maps["height"][1, 1]) and maps["count"][1, 1] == 0
    np.testing.assert_array_equal(maps["colour"][0, 0], [0, 255, 0])


def test_height_slice_exposes_lower_surface() -> None:
    p = np.array([[0.01, 0.01, -0.6], [0.01, 0.01, 0.0]])
    maps = project(p, np.ones_like(p), 0.1, height_slice=(-0.7, -0.5))
    assert maps["height"][0, 0] == -0.6 and maps["count"][0, 0] == 1


def test_median_and_minimum_do_not_change_top_colour_rule() -> None:
    p = np.array([[0.0, 0.0, -1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 2.0]])
    colours = np.eye(3)
    assert project(p, colours, statistic="median")["height"][0, 0] == 0.0
    assert project(p, colours, statistic="minimum")["height"][0, 0] == -1.0


def test_extreme_point_cannot_allocate_enormous_map() -> None:
    p = np.array(
        [[0.0, 0.0, 0.0], [0.1, 0.1, 0.0], [1e100, 1e100, 0.0], [np.nan, 0.0, 0.0]]
    )
    maps = project(p, np.ones_like(p), 0.1)
    assert maps["height"].shape == (2, 2)
    assert maps["metadata"]["rejected_points"] == 2
    with pytest.raises(ValueError, match="budget"):
        project(
            np.array([[-10.0, -10.0, 0.0], [10.0, 10.0, 0.0]]),
            np.ones((2, 3)),
            0.001,
            max_cells=100,
        )
