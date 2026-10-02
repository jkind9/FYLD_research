"""Mathematical coordinate tests; PyCOLMAP is optional in the default test environment."""

import numpy as np
import pytest
from fyld_scene_mapping.image_only import arbitrary_map_coordinates, arbitrary_metadata


def test_shared_normalization_and_first_camera_axes():
    first = np.eye(4)
    first[:3, 3] = [10, 0, 0]
    second = first.copy()
    second[2, 3] = 2
    points = np.array([[12.0, -2.0, 4.0], [10.0, 2.0, 2.0], [10.0, 0.0, -1.0]])
    mapped, poses, divisor, transform = arbitrary_map_coordinates(
        points, [first, second]
    )
    assert divisor == 3
    np.testing.assert_allclose(mapped[0], [2 / 3, 4 / 3, 2 / 3])
    np.testing.assert_allclose(poses[0], np.eye(4) @ transform @ first)
    np.testing.assert_allclose(poses[0][:3, 3], 0)
    np.testing.assert_allclose(poses[1][:3, 3], [0, 2 / 3, 0])
    assert np.linalg.det(poses[1][:3, :3]) == pytest.approx(1)


def test_no_positive_depth_fails_and_inputs_unchanged():
    points = np.array([[0.0, 0.0, -1.0]])
    pose = np.eye(4)
    with pytest.raises(ValueError, match="positive"):
        arbitrary_map_coordinates(points, [pose])
    np.testing.assert_array_equal(points, [[0, 0, -1]])
    np.testing.assert_array_equal(pose, np.eye(4))


def test_metadata_renames_units_recursively():
    original = {
        "bounds_xy_m": [0, 1],
        "height_png": {"range_1_255_m": [0, 2]},
        "units": "metres",
    }
    result = arbitrary_metadata(original)
    assert result["bounds_xy_arbitrary_units"] == [0, 1]
    assert result["height_png"]["range_1_255_arbitrary_units"] == [0, 2]
    assert result["units"] == "arbitrary units"
    assert original["units"] == "metres"
