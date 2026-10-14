"""Fragments: frames fused per keyframe group in that group's anchor frame; a moved anchor moves its surface."""

import numpy as np

from src.live.fragments import Fragments

K = (100.0, 100.0, 32.0, 24.0)


def wall(fragments, keyframe, world_from_camera):
    depth = np.full((48, 64), 1.0, np.float32)  # a flat wall 1 m in front of the camera
    fragments.integrate(depth, np.full((48, 64, 3), 128, np.uint8), K, world_from_camera, keyframe)


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
