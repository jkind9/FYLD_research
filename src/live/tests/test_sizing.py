"""Learned depth is sized per frame to ARCore's confident raw depth, else to tracked points, else the last size."""

import numpy as np
import pytest

from src.live import sizing
from src.live.stream import session_v1

IMAGE_K = (400.0, 400.0, 320.0, 240.0)
POSE = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)  # ARCore camera at the origin, looking along -z


def depth_image(value_mm=2000, confidence=200, width=160, height=120):
    k = tuple(v / 4 for v in IMAGE_K)  # the image intrinsics scaled to the depth size
    return session_v1.Depth(1, np.full((height, width), value_mm / 1000.0, np.float32),
                            np.full((height, width), confidence, np.uint8), k)


def frame(depth=None, points_world=np.zeros((0, 3))):
    pixels = session_v1.project(POSE, IMAGE_K, points_world) if len(points_world) else np.zeros((0, 2))
    return session_v1.Frame(1, 1, 0, "TRACKING", "NONE", POSE, IMAGE_K, b"\xff\xd8", (640, 480),
                            np.arange(len(points_world)), points_world, pixels, np.ones(len(points_world)), depth, None, {})


def test_depth_pixels_map_into_the_image_through_both_intrinsics():
    uv, z = sizing.depth_targets(depth_image(), IMAGE_K, (640, 480))
    assert len(uv) == 160 * 120
    assert np.allclose(uv[1], [4.0, 0.0]) and np.allclose(z, 2.0)


def test_low_confidence_depth_is_ignored():
    uv, _ = sizing.depth_targets(depth_image(confidence=127), IMAGE_K, (640, 480))
    assert len(uv) == 0


def test_size_comes_from_arcore_depth_first():
    model = np.full((480, 640), 3.0)
    size, source = sizing.frame_size(model, np.ones_like(model, bool), frame(depth_image()), previous=None)
    assert source == "arcore_depth" and size == pytest.approx(2.0 / 3.0)


def test_size_falls_back_to_tracked_points_then_to_the_last_size():
    model = np.full((480, 640), 4.0)
    rng = np.random.default_rng(0)
    points = np.c_[rng.uniform(-0.5, 0.5, (25, 2)), np.full(25, -2.0)]
    size, source = sizing.frame_size(model, np.ones_like(model, bool), frame(points_world=points), previous=None)
    assert source == "tracked_points" and size == pytest.approx(0.5)
    size, source = sizing.frame_size(model, np.ones_like(model, bool), frame(points_world=points[:5]), previous=0.7)
    assert (size, source) == (0.7, "previous")
    assert sizing.frame_size(model, np.ones_like(model, bool), frame(), previous=None) == (None, "none")
