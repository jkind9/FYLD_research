"""Only visibility voting and largest connected pieces form the adopted cleanup."""

import numpy as np

from sitescan.cleanup import clean_room, largest_pieces, visibility_vote, vote_tallies

CAMERA = (10.0, 10.0, 1.0, 1.0)


def test_vote_distinguishes_support_free_space_occlusion_and_missing_evidence():
    points = np.array(
        [[0.0, 0.0, 2.0], [0.0, 0.0, 1.0], [0.0, 0.0, 3.0], [100.0, 0.0, 2.0], [0.0, 0.0, -1.0]]
    )
    views = [(np.eye(4), CAMERA, np.full((3, 3), 2.0))]
    support, against = vote_tallies(points, views)
    np.testing.assert_array_equal(support, [0.25, 0, 0, 0, 0])
    np.testing.assert_array_equal(against, [0, 0.25, 0, 0, 0])
    np.testing.assert_array_equal(visibility_vote(points, views), [True, False, True, True, True])


def test_vote_keeps_equal_support_and_opposition_and_ignores_unmeasured_pixels():
    point = np.array([[0.0, 0.0, 1.0]])
    views = [(np.eye(4), CAMERA, np.ones((3, 3)))]
    views += [(np.eye(4), CAMERA, np.full((3, 3), 2.0))] * 4
    support, against = vote_tallies(point, views)
    assert support[0] == against[0] == 1
    assert visibility_vote(point, views)[0]
    support, against = vote_tallies(point, [(np.eye(4), CAMERA, np.zeros((3, 3)))])
    assert support[0] == against[0] == 0
    assert visibility_vote(point, [])[0]


def test_near_view_weights_are_capped_at_the_existing_half_metre_floor():
    support, against = vote_tallies(
        np.array([[0.0, 0.0, 0.2]]), [(np.eye(4), CAMERA, np.full((3, 3), 0.2))]
    )
    assert support[0] == 4 and against[0] == 0


def test_largest_pieces_retains_original_order_and_respects_size_and_count():
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.01, 0.0, 0.0],
            [0.02, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.01, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ]
    )
    np.testing.assert_array_equal(
        largest_pieces(points, 0.02, keep=1, min_points=2), [True, True, True, False, False, False]
    )
    np.testing.assert_array_equal(
        largest_pieces(points, 0.02, keep=3, min_points=2), [True, True, True, True, True, False]
    )


def test_clean_room_combines_vote_and_component_masks_without_reordering():
    points = np.array([[0.0, 0.0, 2.0], [0.01, 0.0, 2.0], [0.0, 0.0, 1.0], [2.0, 0.0, 2.0]])
    views = [(np.eye(4), CAMERA, np.full((3, 3), 2.0))]
    np.testing.assert_array_equal(
        clean_room(points, views, cell=0.02, min_points=2), [True, True, False, False]
    )


def test_clean_room_returns_empty_when_no_points_survive_the_vote():
    assert clean_room(np.empty((0, 3)), []).shape == (0,)
    keep = clean_room(np.array([[0.0, 0.0, 1.0]]), [(np.eye(4), CAMERA, np.full((3, 3), 2.0))])
    np.testing.assert_array_equal(keep, [False])
