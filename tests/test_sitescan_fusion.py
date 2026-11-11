"""Fragment surfaces retain colours and follow anchor corrections without refusion."""

import numpy as np
import pytest

from sitescan.fusion import Fragments

INTRINSICS = (100.0, 100.0, 32.0, 24.0)


def integrate(fragments, colour=100, depth=1.0):
    fragments.integrate(
        np.full((48, 64), depth, np.float32),
        np.full((48, 64, 3), colour, np.uint8),
        INTRINSICS,
        np.eye(4),
        0,
    )


def test_empty_surface_and_colours_have_three_columns():
    fragments = Fragments(voxel_m=0.02)
    assert fragments.surface().shape == fragments.colours().shape == (0, 3)
    assert fragments.frames_per_fragment() == {}


def test_new_integration_refreshes_extracted_points_and_colours():
    fragments = Fragments(voxel_m=0.02)
    fragments.set_anchor(0, np.eye(4))
    integrate(fragments, colour=100)
    before = fragments.surface().copy()
    np.testing.assert_array_equal(fragments.surface(), before)
    np.testing.assert_allclose(np.median(fragments.colours(), 0) * 255, 100, atol=2)
    integrate(fragments, colour=200)
    assert fragments.frames_per_fragment() == {0: 2}
    assert len(fragments.surface()) > 0
    np.testing.assert_allclose(np.median(fragments.colours(), 0) * 255, 150, atol=2)


def test_anchor_rotation_moves_cached_surface_in_the_same_point_order():
    fragments = Fragments(voxel_m=0.02)
    fragments.set_anchor(0, np.eye(4))
    integrate(fragments)
    before = fragments.surface().copy()
    correction = np.array([[0.0, -1, 0, 1], [1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]])
    fragments.set_anchor(0, correction)
    np.testing.assert_allclose(fragments.surface(), before @ correction[:3, :3].T + [1, 2, 3])
    assert fragments.frames_per_fragment() == {0: 1}


@pytest.mark.parametrize("depth", [0.0, 0.05, np.nan, np.inf, 4.1])
def test_depth_outside_fusion_range_adds_no_surface(depth):
    fragments = Fragments(voxel_m=0.02)
    fragments.set_anchor(0, np.eye(4))
    integrate(fragments, depth=depth)
    assert fragments.surface().shape == (0, 3)
