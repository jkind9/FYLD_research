"""Only visibility voting and largest connected pieces form the adopted cleanup."""

import numpy as np

from sitescan.cleanup import (
    clean_room,
    largest_pieces,
    piece_ranks,
    visibility_vote,
    vote_tallies,
)

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


# Three pieces on a 2 cm grid: three touching points, two, and one.
THREE_PIECES = np.array([[0.0, 0, 0], [0.01, 0, 0], [0.02, 0, 0], [1.0, 0, 0], [1.01, 0, 0], [2.0, 0, 0]])


def test_piece_ranks_number_pieces_from_the_largest_and_count_their_points():
    rank, sizes = piece_ranks(THREE_PIECES, 0.02)
    np.testing.assert_array_equal(rank, [0, 0, 0, 1, 1, 2])
    np.testing.assert_array_equal(sizes, [3, 2, 1])


def test_a_neighbour_count_splits_a_thin_streak_from_the_sheet_it_touches():
    sheet = [(i, j) for i in range(10) for j in range(10)]
    streak = [(i, 0) for i in range(10, 20)]  # one cell wide; its cells have 1 to 3 filled neighbours
    points = np.array([(i, j, 0.0) for i, j in sheet + streak])  # one point per 1 m cell
    np.testing.assert_array_equal(piece_ranks(points, 1.0)[1], [110])
    rank, sizes = piece_ranks(points, 1.0, neighbours=4)
    np.testing.assert_array_equal(sizes, [101, 9])  # the streak's first cell touches the sheet and joins it
    assert (rank[:101] == 0).all() and (rank[101:] == 1).all()


def test_largest_pieces_retains_original_order_and_respects_size_and_count():
    points = THREE_PIECES
    np.testing.assert_array_equal(
        largest_pieces(points, 0.02, keep=1, min_points=2), [True, True, True, False, False, False]
    )
    np.testing.assert_array_equal(
        largest_pieces(points, 0.02, keep=3, min_points=2), [True, True, True, True, True, False]
    )


def test_clean_room_combines_vote_and_component_masks_without_reordering():
    points = np.array([[0.0, 0.0, 2.0], [0.01, 0.0, 2.0], [0.0, 0.0, 1.0], [2.0, 0.0, 2.0]])
    views = [(np.eye(4), CAMERA, np.full((3, 3), 2.0))]
    voted, kept = clean_room(points, views, cell=0.02, min_points=2)
    np.testing.assert_array_equal(voted, [True, True, False, True])
    np.testing.assert_array_equal(kept, [True, True, False, False])


def test_clean_room_returns_empty_when_no_points_survive_the_vote():
    assert clean_room(np.empty((0, 3)), []).kept.shape == (0,)
    cleaned = clean_room(np.array([[0.0, 0.0, 1.0]]), [(np.eye(4), CAMERA, np.full((3, 3), 2.0))])
    np.testing.assert_array_equal(cleaned.kept, [False])
