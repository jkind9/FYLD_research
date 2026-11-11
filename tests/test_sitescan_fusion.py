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


def wall(fragments, keyframe, world_from_camera):
    depth = np.full((48, 64), 1.0, np.float32)  # a flat wall 1 m in front of the camera
    fragments.integrate(depth, np.full((48, 64, 3), 128, np.uint8), INTRINSICS, world_from_camera, keyframe)


def test_frames_join_the_fragment_of_their_keyframe_group():
    fragments = Fragments(voxel_m=0.02, keyframes_per_fragment=10)
    for keyframe in range(10):
        fragments.set_anchor(keyframe, np.eye(4))
    wall(fragments, 0, np.eye(4))
    wall(fragments, 9, np.eye(4))
    fragments.set_anchor(10, np.eye(4))
    wall(fragments, 10, np.eye(4))
    assert sorted(fragments.frames_per_fragment().items()) == [(0, 2), (1, 1)]
    z = fragments.surface()[:, 2]
    assert len(z) > 0 and np.abs(np.median(z) - 1.0) < 0.02


def test_surface_colours_are_the_fused_photo_colours():
    fragments = Fragments(voxel_m=0.02)
    fragments.set_anchor(0, np.eye(4))
    fragments.integrate(np.full((48, 64), 1.0, np.float32), np.full((48, 64, 3), (200, 40, 10), np.uint8), INTRINSICS, np.eye(4), 0)
    colours = fragments.colours()
    assert colours.shape == fragments.surface().shape
    np.testing.assert_allclose(np.median(colours, 0) * 255, [200, 40, 10], atol=2)


def test_moving_the_group_anchor_moves_its_surface():
    fragments = Fragments(voxel_m=0.02, keyframes_per_fragment=10)
    fragments.set_anchor(0, np.eye(4))
    wall(fragments, 0, np.eye(4))
    before = fragments.surface()
    moved = np.eye(4)
    moved[:3, 3] = [0.0, 0.0, 0.5]
    fragments.set_anchor(0, moved)
    after = fragments.surface()
    assert len(after) == len(before)
    assert np.allclose(np.median(after, 0) - np.median(before, 0), [0.0, 0.0, 0.5], atol=1e-6)


def test_a_keyframe_reports_the_current_pose_of_the_anchor_placing_it():
    fragments = Fragments(voxel_m=0.02, keyframes_per_fragment=10)
    fragments.set_anchor(1, np.eye(4))
    wall(fragments, 1, np.eye(4))
    moved = np.eye(4)
    moved[:3, 3] = [0.0, 0.0, 0.5]
    fragments.set_anchor(0, np.eye(4))
    fragments.set_anchor(1, moved)
    assert np.allclose(fragments.placing_anchor(2), moved)


def test_missing_group_start_uses_a_received_anchor_and_keeps_that_binding():
    fragments = Fragments(voxel_m=0.02, keyframes_per_fragment=10)
    fragments.set_anchor(1, np.eye(4))
    wall(fragments, 1, np.eye(4))
    before = fragments.surface()
    moved = np.eye(4)
    moved[:3, 3] = [0.0, 0.0, 0.5]
    fragments.set_anchor(0, np.eye(4))
    fragments.set_anchor(1, moved)
    after = fragments.surface()
    assert len(after) == len(before) > 0
    assert np.allclose(np.median(after, 0) - np.median(before, 0), [0.0, 0.0, 0.5], atol=1e-6)
    wall(fragments, 2, moved)
    assert fragments.frames_per_fragment() == {0: 2}
