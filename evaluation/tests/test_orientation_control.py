"""Task109's turn to upright and back, and its depth score."""

import numpy as np
import pytest

from evaluation import orientation_control as oc


def test_turn_upright_and_back_is_unchanged():
    image = np.arange(12).reshape(3, 4)
    assert np.array_equal(oc.recorded(oc.upright(image)), image)


def test_marked_pixel_lands_where_a_clockwise_turn_puts_it():
    h, w, u, v = 3, 4, 1, 0  # pixel (u, v) on a recorded image w wide and h high
    image = np.zeros((h, w))
    image[v, u] = 1
    turned = oc.upright(image)
    assert turned.shape == (w, h)
    assert turned[u, h - 1 - v] == 1  # clockwise: (u, v) -> (h - 1 - v, u)


def camera(x_axis, y_axis):
    """OpenCV world_from_camera with the given image-right and image-down axes in the world (y up)."""
    T = np.eye(4)
    T[:3, 0], T[:3, 1] = x_axis, y_axis
    T[:3, 2] = np.cross(x_axis, y_axis)
    T[:3, 3] = [0.3, 1.2, -0.5]
    return T


@pytest.mark.parametrize("x_axis, y_axis, turns", [
    ((1, 0, 0), (0, -1, 0), 0),   # landscape, already upright
    ((0, -1, 0), (-1, 0, 0), 1),  # portrait as on the Redmi walks: image right points down
    ((-1, 0, 0), (0, 1, 0), 2),   # upside down
    ((0, 1, 0), (1, 0, 0), 3),    # portrait the other way round
])
def test_quarter_turns_bring_image_down_closest_to_world_down(x_axis, y_axis, turns):
    assert oc.quarter_turns(camera(x_axis, y_axis)) == turns


@pytest.mark.parametrize("turns", [0, 1, 2, 3])
def test_turned_camera_sees_each_point_where_the_turned_image_puts_it(turns):
    T, k, (w, h) = camera((0, -1, 0), (-1, 0, 0)), (500.0, 480.0, 300.0, 250.0), (640, 480)
    point = T[:3, :3] @ [0.4, -0.2, 2.0] + T[:3, 3]

    def pixel(T, k):
        c = np.linalg.inv(T)[:3] @ [*point, 1]
        return round(k[0] * c[0] / c[2] + k[2]), round(k[1] * c[1] / c[2] + k[3])

    u, v = pixel(T, k)
    image = np.zeros((h, w))
    image[v, u] = 1
    turned_T, turned_k, size = oc.turned_camera(T, k, (w, h), turns)
    turned = oc.upright(image, turns)
    assert size == (turned.shape[1], turned.shape[0])
    u2, v2 = pixel(turned_T, turned_k)
    assert turned[v2, u2] == 1


def test_score_fits_size_then_measures_error():
    model = np.full((4, 4), 2.0)
    uv = np.array([[0, 0], [1, 1], [2, 2], [3, 3]], float)
    target = np.array([1.0, 1.0, 1.0, 1.5])
    got = oc.score(model, np.ones_like(model, bool), uv, target, minimum=2)
    assert got["size"] == pytest.approx(0.5)
    assert got["abs_rel"] == pytest.approx((1 / 3) / 4)
    assert got["delta_1_25"] == pytest.approx(0.75)


def test_score_needs_enough_valid_pixels():
    model = np.full((4, 4), 2.0)
    assert oc.score(model, np.zeros_like(model, bool), np.zeros((4, 2)), np.ones(4), minimum=2) is None
