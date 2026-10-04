from __future__ import annotations

import importlib

import numpy as np

associate_frame = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.association"
).associate_frame


def test_same_class_neighbours_keep_ids_after_reordered_return(observation_factory):
    first = [
        observation_factory("a", "f1", 1.0, 0.0, vector=(1, 0), bbox=(0, 0, 10, 10)),
        observation_factory("b", "f1", 1.0, 0.30, vector=(0, 1), bbox=(20, 0, 30, 10)),
    ]
    tracks, born, _ = associate_frame(first, (), "combined-viewmedian")
    ids = {row["observation_id"]: row["object_id"] for row in born}
    assert len(set(ids.values())) == 2
    returned = [
        observation_factory("d", "f2", 2.0, 0.29, vector=(0, 1), bbox=(20, 0, 30, 10)),
        observation_factory("c", "f2", 2.0, 0.01, vector=(1, 0), bbox=(0, 0, 10, 10)),
    ]
    next_tracks, matched, _ = associate_frame(returned, tracks, "combined-viewmedian")
    assert {row["observation_id"]: row["object_id"] for row in matched} == {
        "c": ids["a"],
        "d": ids["b"],
    }
    assert len(next_tracks) == 2


def test_equal_neighbour_candidates_abstain_without_location_change(
    observation_factory,
):
    first = [
        observation_factory("a", "f1", 1.0, 0.0, bbox=(0, 0, 10, 10)),
        observation_factory("b", "f1", 1.0, 0.30, bbox=(20, 0, 30, 10)),
    ]
    tracks, _, _ = associate_frame(first, (), "appearance-viewmedian")
    midpoint = observation_factory("c", "f2", 2.0, 0.15, bbox=(8, 0, 18, 10))
    updated, decisions, _ = associate_frame([midpoint], tracks, "appearance-viewmedian")
    assert decisions[0]["decision"] == "unresolved"
    assert decisions[0]["reason"] == "near-equal full-cardinality assignment"
    assert [track.location.accepted for track in updated] == [
        track.location.accepted for track in tracks
    ]


def test_frame_wide_near_tie_marks_alternative_unmatched_row_unresolved(
    observation_factory,
):
    first = [
        observation_factory("a", "f1", 1.0, 0.0, bbox=(0, 0, 10, 10)),
        observation_factory("b", "f1", 1.0, 0.3, bbox=(20, 0, 30, 10)),
    ]
    tracks, _, _ = associate_frame(first, (), "appearance-viewmedian")
    queries = [
        observation_factory("c", "f2", 2.0, 0.1, bbox=(0, 0, 10, 10)),
        observation_factory("d", "f2", 2.0, 0.2, bbox=(10, 0, 20, 10)),
        observation_factory("e", "f2", 2.0, 0.15, bbox=(20, 0, 30, 10)),
    ]
    updated, decisions, _ = associate_frame(queries, tracks, "appearance-viewmedian")
    assert [row["decision"] for row in decisions] == ["unresolved"] * 3
    assert all(
        row["reason"] == "near-equal full-cardinality assignment" for row in decisions
    )
    assert [track.location.accepted for track in updated] == [
        track.location.accepted for track in tracks
    ]


def test_duplicate_same_class_boxes_both_unresolved_and_create_no_ids(
    observation_factory,
):
    rows = [
        observation_factory("a", "f1", 1.0, 0.0, bbox=(0, 0, 10, 10)),
        observation_factory("b", "f1", 1.0, 0.01, bbox=(0.1, 0.1, 10.1, 10.1)),
    ]
    tracks, decisions, _ = associate_frame(rows, (), "geometry-last")
    assert tracks == ()
    assert [row["decision"] for row in decisions] == ["unresolved", "unresolved"]
    assert all(
        row["reason"] == "same-class overlapping duplicate suspect" for row in decisions
    )


def test_overlapping_duplicate_cluster_does_not_choose_confidence_winner(
    observation_factory,
):
    rows = [
        observation_factory("a", "f1", 1.0, 0.0, bbox=(0, 0, 10, 10)),
        observation_factory("b", "f1", 1.0, 0.01, bbox=(0.1, 0, 10.1, 10)),
        observation_factory("c", "f1", 1.0, 0.02, bbox=(0.2, 0, 10.2, 10)),
    ]
    tracks, decisions, _ = associate_frame(rows, (), "geometry-last")
    assert tracks == ()
    assert len(decisions) == 3
    assert {row["decision"] for row in decisions} == {"unresolved"}
    assert {row["observation_id"] for row in decisions} == {"a", "b", "c"}


def test_unknown_origin_never_seeds_identity(observation_factory):
    row = observation_factory("a", "f1", 1.0, 0.0, world=None, segment=None)
    tracks, decisions, _ = associate_frame([row], (), "appearance-viewmedian")
    assert tracks == ()
    assert decisions[0]["reason"] == "unknown metric origin"


def test_observation_from_another_session_cannot_reuse_an_object_id(
    observation_factory,
):
    first = observation_factory("a", "f1", 1.0, 0.0, category="cup")
    tracks, born, _ = associate_frame([first], (), "combined-viewmedian")
    original_id = born[0]["object_id"]

    other_session = observation_factory("b", "f2", 2.0, 0.0, category="cup")
    other_session["session_id"] = "different-session"
    updated, decisions, _ = associate_frame(
        [other_session], tracks, "combined-viewmedian"
    )

    assert decisions[0]["decision"] == "unresolved"
    assert decisions[0]["object_id"] is None
    assert decisions[0]["rejected_candidates"] == [
        {"object_id": original_id, "reason": "session mismatch"}
    ]
    assert updated[0].object_id == original_id
    assert updated[0].location.accepted == tracks[0].location.accepted


def test_fixed_anchor_stops_a_chain_of_small_movements(observation_factory):
    first = observation_factory("a", "f1", 1.0, 0.0)
    tracks, _, _ = associate_frame([first], (), "geometry-last")
    near = observation_factory("b", "f2", 2.0, 0.30)
    tracks, matched, _ = associate_frame([near], tracks, "geometry-last")
    assert matched[0]["decision"] == "matched"
    outside = observation_factory("c", "f3", 3.0, 0.60)
    after, result, _ = associate_frame([outside], tracks, "geometry-last")
    assert result[0]["decision"] == "unresolved"
    assert after[0].location.last_m == (0.3, 0.0, 1.0)
    assert np.allclose(after[0].location.anchor_m, [0, 0, 1])
