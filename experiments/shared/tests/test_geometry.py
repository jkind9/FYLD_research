"""Depth grid validation without constructing a point cloud."""

import numpy as np
import pytest

from experiments.shared import geometry
from experiments.shared.contracts import Calibration


@pytest.mark.parametrize("fault", ["shape", "mask", "zero", "nan"])
def test_check_depth_grid_rejects_invalid_content(fault):
    camera = Calibration(2, 2, 1, 1, 0, 0, "x-right_y-down_z-forward")
    depth, valid = np.ones((2, 2)), np.ones((2, 2), dtype=bool)
    if fault == "shape":
        depth = depth[:1]
    elif fault == "mask":
        valid = valid.astype(np.uint8)
    elif fault == "zero":
        depth[0, 0] = 0
    else:
        depth[0, 0] = np.nan
    with pytest.raises(ValueError):
        geometry.check_depth_grid(depth, valid, camera)


def test_check_depth_grid_accepts_masked_invalid_pixels():
    camera = Calibration(2, 2, 1, 1, 0, 0, "x-right_y-down_z-forward")
    depth = np.array([[np.nan, 2], [3, 4]])
    valid = np.array([[False, True], [True, True]])
    assert geometry.check_depth_grid(depth, valid, camera) is None
    points, pixels = geometry.backproject(depth, valid, camera)
    assert points.shape == (3, 3)
    np.testing.assert_array_equal(pixels, [[0, 1], [1, 0], [1, 1]])
