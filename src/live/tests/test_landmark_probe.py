"""The cushion probe: one red object placed from each frame by two depth sources."""

import numpy as np

from src.live.landmark_probe import ray_split, red_mask


def test_red_mask_keeps_the_largest_saturated_red_blob():
    rgb = np.full((40, 60, 3), 128, np.uint8)
    rgb[5:20, 5:25] = (220, 20, 20)  # the cushion: 300 pixels
    rgb[30:34, 40:44] = (220, 20, 20)  # a small red toy: 16 pixels
    rgb[22:28, 30:38] = (200, 120, 120)  # pale pink: not saturated enough
    mask = red_mask(rgb)
    assert mask.sum() == 300 and mask[10, 10] and not mask[31, 41] and not mask[25, 33]


def test_no_red_gives_an_empty_mask():
    assert not red_mask(np.full((10, 10, 3), 128, np.uint8)).any()


def test_ray_split_separates_depth_error_from_sideways_error():
    along, across = ray_split(np.zeros(3), np.array([0, 0, 2.0]), np.array([0.03, 0, 2.5]))
    assert np.isclose(along, 0.5) and np.isclose(across, 0.03)
