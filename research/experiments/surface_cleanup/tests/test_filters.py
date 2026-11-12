"""Clean-up trials: per-frame depth masks, near-first fusion passes and the visibility vote."""

import numpy as np
import pytest

from experiments.surface_cleanup.filters import keep_after, piece_majority
from experiments.surface_cleanup.masks import (
    edge_mask,
    near_first_passes,
    view_angle_mask,
)
from experiments.surface_cleanup.support import (
    spot_evidence,
    views_measuring,
    wide_support,
)
from sitescan.cleanup import largest_pieces, visibility_vote

K = (100.0, 100.0, 32.0, 24.0)


def test_edge_mask_flags_only_pixels_beside_a_depth_step():
    depth = np.full((48, 64), 1.0)
    depth[:, 32:] = 3.0
    mask = edge_mask(depth)
    assert mask[:, 31:33].all()
    assert not mask[:, :30].any() and not mask[:, 34:].any()


def test_view_angle_mask_flags_a_plane_seen_side_on_but_not_one_facing_the_camera():
    assert not view_angle_mask(np.full((48, 64), 2.0), K).any()
    u = np.arange(40)
    steep = np.tile(2.0 / (1.0 - 10.0 * (u - 32) / 100.0), (48, 1))  # the plane z = 2 + 10 x
    mask = view_angle_mask(steep, K)
    assert mask[10:-10, 20:36].all()  # rays meet the plane more than 75 degrees from its normal
    assert not mask[10:-10, 3:8].any()  # 68-70 degrees here


def test_near_first_passes_repeat_near_depth_more_often():
    depth = np.array([[0.5, 3.5], [0.0, 1.5]])
    passes = near_first_passes(depth)
    assert [(np.count_nonzero(d), repeats) for d, repeats in passes] == [(1, 16), (1, 4), (1, 1)]


def test_visibility_vote_drops_points_a_view_sees_through():
    wall = (np.eye(4), K, np.full((48, 64), 2.0))  # camera at the origin, a wall 2 m ahead
    points = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 1.0], [0.0, 0.0, 5.0]])
    assert visibility_vote(points, [wall]).tolist() == [True, False, True]


@pytest.mark.parametrize("kind", ["sor", "radius", "clusters"])
def test_point_filters_drop_an_isolated_point_and_keep_the_surface(kind):
    u, v = np.meshgrid(np.arange(50) * 0.02, np.arange(50) * 0.02)
    wall = np.c_[u.ravel(), v.ravel(), np.zeros(2500)]  # 1 m x 1 m at 2 cm spacing
    patch = wall[:25] + [0.0, 0.0, 1.0]  # half a row of points, 1 m off the wall
    points = np.vstack([wall, patch, [[0.5, 0.5, 0.5]]])
    keep = keep_after(points, kind)
    assert not keep[-1]
    centre = (np.abs(points[:, 0] - 0.5) < 0.3) & (np.abs(points[:, 1] - 0.5) < 0.3) & (points[:, 2] == 0)
    assert keep[centre].all()
    if kind == "clusters":
        assert not keep[2500:2525].any()  # under CLUSTER_MIN_POINTS, so a floating piece


def test_observation_count_is_the_number_of_views_measuring_a_point():
    wall = (np.eye(4), K, np.full((48, 64), 2.0))
    points = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 1.0]])  # on the wall; a speck in front of it
    assert views_measuring(points, [wall, wall, wall]).tolist() == [3, 0]


def test_near_views_outvote_far_ones():
    near = (np.eye(4), K, np.full((48, 64), 2.0))  # sees through a point 1 m ahead: weight 1 / 2^2
    behind = np.eye(4)
    behind[2, 3] = 3.0  # a camera 3 m further back, measuring that point at 4 m: weight 1 / 4^2 each
    far = (behind, K, np.full((48, 64), 4.0))
    point = np.array([[0.0, 0.0, 1.0]])
    assert not visibility_vote(point, [near] + [far] * 3)[0]
    assert visibility_vote(point, [near] + [far] * 5)[0]


def _camera_at(x: float) -> np.ndarray:
    camera_from_world = np.eye(4)
    camera_from_world[0, 3] = -x  # a camera at (x, 0, 0) looking along +z
    return camera_from_world


def test_far_points_need_agreeing_views_from_more_than_one_spot():
    far = np.array([[0.0, 0.0, 4.0]])  # beyond ARCore depth's reach, so sized by a guess
    spot = (_camera_at(0.0), K, np.full((48, 64), 4.0))
    left, right = (_camera_at(-0.5), K, np.full((48, 64), 4.0)), (_camera_at(0.5), K, np.full((48, 64), 4.0))
    assert not wide_support(far, [spot] * 5)[0]  # one spot, one size guess, however many frames
    assert not wide_support(far, [spot, left])[0]  # COLMAP needs two views at 3 degrees or more
    assert wide_support(far, [spot, left, right])[0]  # 0.5 m apart at 4 m: about 7 degrees


def test_near_points_measured_by_one_spot_are_kept():
    near = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 1.0]])  # on a wall 2 m ahead; a speck nobody measures
    assert wide_support(near, [(_camera_at(0.0), K, np.full((48, 64), 2.0))]).tolist() == [True, False]


def _sheet(origin, across, down, normal, n_across, n_down):
    i, j = np.meshgrid(np.arange(n_across), np.arange(n_down))
    points = np.asarray(origin) + 0.02 * (i.ravel()[:, None] * np.asarray(across) + j.ravel()[:, None] * np.asarray(down))
    return points, np.tile(normal, (len(points), 1)).astype(float)


def test_piece_test_drops_a_mostly_suspect_echo_that_a_corner_joins_to_the_wall():
    wall, wall_n = _sheet([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], 50, 50)  # 1 m square at 2 cm spacing
    side, side_n = _sheet([1.0, 0, 0.02], [0, 0, 1], [0, 1, 0], [1, 0, 0], 25, 50)  # side-on strip at its edge
    echo, echo_n = _sheet([1.02, 0, 0.5], [1, 0, 0], [0, 1, 0], [0, 0, 1], 25, 50)  # a copy, joined via the strip
    points, normals = np.vstack([wall, side, echo]), np.vstack([wall_n, side_n, echo_n])
    suspect = np.zeros(len(points), bool)
    suspect[-len(echo):][: int(0.6 * len(echo))] = True  # 60% of the echo lacks support
    suspect[0] = True  # one stray wall point does too
    keep = piece_majority(points, normals, suspect)
    assert not keep[-len(echo):].any()  # the whole echo goes, not just its suspect 60%
    assert keep[1:len(wall) + len(side)].all() and not keep[0]
    joined = piece_majority(points, normals, suspect, max_angle_deg=91.0)  # every neighbour joins
    assert joined[-len(echo):].sum() == len(echo) - suspect[-len(echo):].sum()  # one piece: only suspects go


def test_spot_evidence_is_the_nearest_measured_depth_and_the_second_widest_angle():
    points = np.array([[0.0, 0.0, 4.0], [0.0, 0.0, 1.0]])  # on a wall 4 m ahead; a speck nobody measures
    views = [(_camera_at(x), K, np.full((48, 64), 4.0)) for x in (0.0, 0.1, -0.5, 0.5)]
    nearest, second = spot_evidence(points, views)
    assert nearest[0] == 4.0 and np.isinf(nearest[1])
    assert np.isclose(second[0], np.degrees(np.arctan2(0.5, 4.0)))  # the two cameras 0.5 m to the sides
    assert second[1] == 0.0


def _patch(x0: float, side: int, z: float = 0.0) -> np.ndarray:
    """A flat square of side x side points at 1 cm spacing, its corner at (x0, 0, z)."""
    u, v = np.meshgrid(np.arange(side) * 0.01, np.arange(side) * 0.01)
    return np.c_[x0 + u.ravel(), v.ravel(), np.full(side * side, z)]


def test_largest_pieces_keeps_big_touching_pieces_and_drops_small_ones():
    room, shelf = _patch(0.0, 20), _patch(0.0, 10, z=0.02)  # the shelf sits one 2 cm cell above the room: it touches
    floater, island = _patch(2.0, 5), _patch(5.0, 10)  # 25 points; 100 points, both apart from the room
    points = np.vstack([room, shelf, floater, island])
    keep = largest_pieces(points, 0.02, keep=50, min_points=50)
    assert keep.tolist() == [True] * 500 + [False] * 25 + [True] * 100
    assert largest_pieces(points, 0.02, keep=1, min_points=50).tolist() == [True] * 500 + [False] * 125


def test_bigger_cells_link_pieces_across_wider_gaps():
    points = np.vstack([_patch(0.0, 20), _patch(0.24, 20)])  # a 5 cm gap between two 20 cm squares
    assert largest_pieces(points, 0.02, keep=1, min_points=1).sum() == 400
    assert largest_pieces(points, 0.06, keep=1, min_points=1).sum() == 800
