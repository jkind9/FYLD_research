"""Contract tests for Task32 box-and-depth association."""

from __future__ import annotations

import copy
import importlib
from dataclasses import replace

import numpy as np
import pytest

association = importlib.import_module(
    "experiments.06_object_recognition.experiments.07_spatial_uncertainty.association"
)


LINEAGE = {
    "coordinate_frame": "world",
    "world_id": "world-a",
    "segment_id": "segment-a",
    "pose_revision_id": "pose-a-v1",
}


def observation(
    key: str,
    x: float,
    *,
    samples: list[list[float]] | None = None,
    depths: list[float] | None = None,
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 10.0, 10.0),
    class_id: int = 41,
) -> association.BoxObservation:
    if samples is None:
        samples = [[x, 0.0, 1.0], [x + 0.01, 0.0, 1.0]]
    if depths is None:
        depths = [sample[2] for sample in samples]
    pixels = [(index, index) for index in range(len(samples))]
    return association.BoxObservation(
        observation_id=key,
        class_id=class_id,
        label="book",
        bbox_xyxy=bbox,
        camera_depth_m=tuple(depths),
        pixel_vu=tuple(pixels),
        world_samples_m=tuple(tuple(sample) for sample in samples),
        **LINEAGE,
    )


def test_planar_support_keeps_extent_separate_from_uncalibrated_location_uncertainty():
    row = observation(
        "book-1",
        0.0,
        samples=[[0.0, 0.0, 1.0], [0.1, 0.0, 1.0], [0.2, 0.0, 1.0]],
    )
    candidates = association.surface_candidates(row, depth_gap_m=0.08)

    assert len(candidates) == 1
    assert candidates[0].summary.rank == 1
    assert candidates[0].summary.squared_mahalanobis((0.1, 0.0, 1.0)) is None
    assert candidates[0].visible_extent.span_m == (0.2, 0.0, 0.0)
    assert candidates[0].location_uncertainty_status == "unavailable_calibrated_model"


def test_foreground_and_background_depth_layers_remain_separate_candidates():
    row = observation(
        "book-1",
        0.0,
        samples=[
            [0.0, 0.0, 1.0],
            [0.1, 0.0, 1.02],
            [0.0, 0.0, 2.0],
            [0.1, 0.0, 2.02],
        ],
        depths=[1.0, 1.02, 2.0, 2.02],
    )

    candidates = association.surface_candidates(row, depth_gap_m=0.08)

    assert len(candidates) == 2
    assert [candidate.sample_indexes for candidate in candidates] == [(0, 1), (2, 3)]
    assert [candidate.depth_range_m for candidate in candidates] == [
        (1.0, 1.02),
        (2.0, 2.02),
    ]


def test_missing_support_is_explicit_and_does_not_birth_an_identity():
    row = observation("missing", 0.0, samples=[])
    result = association.associate_frame([row], {}, 1, 0.35, 0.05)

    assert result.decisions[0]["decision"] == "unresolved"
    assert result.decisions[0]["reason"] == "unresolved_no_support"
    assert result.tracks == {}


def test_duplicate_observation_ids_are_rejected_before_assignment():
    rows = [
        observation("same-source", 0.0),
        observation("same-source", 1.0, bbox=(20.0, 0.0, 30.0, 10.0)),
    ]

    with pytest.raises(ValueError, match="unique"):
        association.associate_frame(rows, {}, 1, 0.35, 0.05)


def test_neighbouring_same_class_supports_match_one_to_one():
    first = [observation("a", 0.0), observation("b", 0.3)]
    born = association.associate_frame(first, {}, 1, 0.35, 0.05)
    returned = [observation("d", 0.29), observation("c", 0.01)]

    result = association.associate_frame(
        returned, born.tracks, born.next_number, 0.35, 0.05
    )

    assert [row["object_id"] for row in result.decisions] == [
        born.decisions[1]["object_id"],
        born.decisions[0]["object_id"],
    ]
    assert all(row["decision"] == "matched" for row in result.decisions)


def test_dense_ten_by_ten_assignment_returns_all_feasible_matches():
    tracks = {
        f"object-{index + 1:04d}": {
            "object_id": f"object-{index + 1:04d}",
            "class_id": 41,
            "identity_state": "provisional",
            "last_position_m": [index * 0.01, 0.0, 1.0],
            **LINEAGE,
        }
        for index in range(10)
    }
    rows = [
        observation(
            f"dense-{index}",
            index * 0.01,
            bbox=(index * 20.0, 0.0, index * 20.0 + 10.0, 10.0),
        )
        for index in range(10)
    ]

    result = association.associate_frame(rows, tracks, 11, 0.35, 0.0)

    assert [row["decision"] for row in result.decisions] == ["matched"] * 10
    assert len({row["object_id"] for row in result.decisions}) == 10


def test_association_reuses_exact_neighbour_indexes_within_a_frame(monkeypatch):
    initial = association.associate_frame(
        [
            observation("first-a", 0.0, bbox=(0.0, 0.0, 10.0, 10.0)),
            observation("first-b", 0.1, bbox=(20.0, 0.0, 30.0, 10.0)),
        ],
        {},
        1,
        0.35,
        0.0,
    )
    real_tree = association.cKDTree
    builds = []

    def counted_tree(samples, *args, **kwargs):
        builds.append(np.asarray(samples).copy())
        return real_tree(samples, *args, **kwargs)

    monkeypatch.setattr(association, "cKDTree", counted_tree)
    result = association.associate_frame(
        [
            observation("return-a", 0.01, bbox=(0.0, 0.0, 10.0, 10.0)),
            observation("return-b", 0.11, bbox=(20.0, 0.0, 30.0, 10.0)),
        ],
        initial.tracks,
        initial.next_number,
        0.35,
        0.0,
    )

    assert len(builds) == 4  # Two current candidates and two prior tracks.
    assert [row["decision"] for row in result.decisions] == ["matched", "matched"]
    assert [row["object_id"] for row in result.decisions] == [
        initial.decisions[0]["object_id"],
        initial.decisions[1]["object_id"],
    ]


def test_track_tree_cache_keeps_distinct_mapping_entries_separate():
    left = association.associate_frame(
        [observation("left", 0.0)], {}, 1, 0.35, 0.0
    ).tracks["object-0001"]
    right = association.associate_frame(
        [observation("right", 0.5)], {}, 1, 0.35, 0.0
    ).tracks["object-0001"]
    tracks = {
        "entry-a": {**left, "object_id": "shared"},
        "entry-b": {**right, "object_id": "shared"},
    }

    result = association.associate_frame(
        [observation("current", 0.5)], tracks, 2, 0.35, 0.0
    )

    assert result.decisions[0]["decision"] == "matched"
    assert result.decisions[0]["object_id"] == "shared"
    assert result.decisions[0]["support_distance_m"] == pytest.approx(0.0)


def test_support_distance_handles_large_samples_without_dense_pairwise_tensor():
    line = np.column_stack(
        (np.linspace(0.0, 1.0, 20_000), np.zeros(20_000), np.ones(20_000))
    )
    candidate = association.surface_candidates(
        observation("large", 0.0, samples=line.tolist())
    )[0]

    distance = association._support_distance(
        candidate, line + np.asarray([0.0, 0.1, 0.0])
    )

    assert distance == pytest.approx(0.1)


def test_late_same_class_birth_and_return_preserve_task46_policy():
    first = association.associate_frame([observation("a", 0.0)], {}, 1, 0.35, 0.05)
    late = association.associate_frame(
        [observation("late", 1.0)], first.tracks, first.next_number, 0.35, 0.05
    )

    assert late.decisions[0]["decision"] == "new"
    assert late.decisions[0]["identity_state"] == "provisional"
    assert late.next_number == 3

    returned = association.associate_frame(
        [observation("return", 1.01), observation("old-return", 0.01)],
        late.tracks,
        late.next_number,
        0.35,
        0.05,
    )
    assert [row["decision"] for row in returned.decisions] == ["matched", "matched"]
    assert returned.decisions[0]["object_id"] == late.decisions[0]["object_id"]
    assert returned.decisions[1]["object_id"] == first.decisions[0]["object_id"]


def test_stale_next_number_does_not_overwrite_existing_track():
    original_tracks = {
        "object-0001": {
            "object_id": "object-0001",
            "identity_state": "confirmed",
            "class_id": 41,
            "last_position_m": [0.0, 0.0, 1.0],
            "last_observation_id": "old-observation",
            **LINEAGE,
            "pose_revision_id": "pose-old",
        }
    }

    result = association.associate_frame(
        [observation("new-pose", 1.0)], original_tracks, 1, 0.35, 0.05
    )

    assert result.decisions[0]["decision"] == "new"
    assert result.decisions[0]["object_id"] == "object-0002"
    assert result.next_number == 3
    assert result.tracks["object-0001"] == original_tracks["object-0001"]


def test_duplicate_boxes_do_not_force_an_extra_birth():
    rows = [
        observation("a", 0.0),
        observation("b", 0.0, bbox=(0.1, 0.1, 10.1, 10.1)),
    ]

    result = association.associate_frame(rows, {}, 1, 0.35, 0.05)

    assert len(result.tracks) == 1
    assert [row["decision"] for row in result.decisions] == ["new", "unresolved"]
    assert result.decisions[1]["reason"] == "unresolved_duplicate_box"


def test_duplicate_boxes_keep_one_existing_match():
    first = association.associate_frame([observation("seed", 0.0)], {}, 1, 0.35, 0.05)
    rows = [
        observation("a", 0.0),
        observation("b", 0.0, bbox=(0.1, 0.1, 10.1, 10.1)),
    ]

    result = association.associate_frame(
        rows, first.tracks, first.next_number, 0.35, 0.05
    )

    assert result.decisions[0]["decision"] == "matched"
    assert result.decisions[0]["object_id"] == first.decisions[0]["object_id"]
    assert result.decisions[1]["reason"] == "unresolved_duplicate_box"


def test_duplicate_chain_does_not_suppress_non_pairwise_detection():
    rows = [
        observation("left", 0.0),
        observation("middle", 0.015),
        observation("right", 0.03),
    ]

    result = association.associate_frame(rows, {}, 1, 0.35, 0.05)

    assert [row["decision"] for row in result.decisions] == [
        "new",
        "unresolved",
        "new",
    ]
    assert result.decisions[1]["reason"] == "unresolved_duplicate_box"
    assert result.decisions[2]["object_id"] != result.decisions[0]["object_id"]


def test_duplicate_boxes_from_different_segments_remain_separate_births():
    first = observation("segment-a", 0.0)
    second = replace(first, observation_id="segment-b", segment_id="segment-b")

    result = association.associate_frame([first, second], {}, 1, 0.35, 0.05)

    assert [row["decision"] for row in result.decisions] == ["new", "new"]
    assert result.decisions[0]["object_id"] != result.decisions[1]["object_id"]


def test_suppressed_duplicate_cannot_consume_track_feasible_for_another_detection():
    tracks = {
        f"object-{number:04d}": {
            "object_id": f"object-{number:04d}",
            "class_id": 41,
            "identity_state": "provisional",
            "last_position_m": [x, 0.0, 1.0],
            **LINEAGE,
        }
        for number, x in ((1, 0.0), (2, 0.2))
    }
    rows = [
        observation("duplicate-a", 0.0),
        observation("duplicate-b", 0.0),
        observation("distinct", 0.5, bbox=(20.0, 0.0, 30.0, 10.0)),
    ]

    result = association.associate_frame(rows, tracks, 3, 0.35, 0.05)

    assert [row["decision"] for row in result.decisions] == [
        "matched",
        "unresolved",
        "matched",
    ]
    assert result.decisions[1]["reason"] == "unresolved_duplicate_box"
    assert result.decisions[0]["object_id"] == "object-0001"
    assert result.decisions[2]["object_id"] == "object-0002"


def test_competing_candidates_and_ambiguous_match_remain_unresolved():
    mixed = observation(
        "mixed",
        0.0,
        samples=[[0.0, 0.0, 1.0], [0.01, 0.0, 1.0], [0.0, 0.0, 2.0], [0.01, 0.0, 2.0]],
        depths=[1.0, 1.0, 2.0, 2.0],
    )
    result = association.associate_frame([mixed], {}, 1, 0.35, 0.05)
    assert result.decisions[0]["reason"] == "unresolved_competing_support"

    tracks = association.associate_frame(
        [observation("left", 0.0), observation("right", 0.08)], {}, 1, 0.35, 0.05
    )
    midpoint = observation("mid", 0.04)
    ambiguous = association.associate_frame(
        [midpoint], tracks.tracks, tracks.next_number, 0.35, 0.05
    )
    assert ambiguous.decisions[0]["reason"] == "unresolved_ambiguous"


def test_lineage_and_input_immutability_are_enforced():
    row = observation("a", 0.0)
    tracks = association.associate_frame([row], {}, 1, 0.35, 0.05).tracks
    changed = observation("b", 0.0)
    changed = replace(changed, pose_revision_id="pose-a-v2")
    original_row = copy.deepcopy(row)
    original_tracks = copy.deepcopy(tracks)

    result = association.associate_frame([changed], tracks, 2, 0.35, 0.05)

    assert result.decisions[0]["decision"] == "new"
    assert result.decisions[0]["reason"] == "late_or_unmatched_provisional_birth"
    assert row == original_row
    assert tracks == original_tracks


def test_matching_preserves_confirmed_track_state():
    first = association.associate_frame([observation("seed", 0.0)], {}, 1, 0.35, 0.05)
    object_id = first.decisions[0]["object_id"]
    tracks = {
        object_id: {
            **first.tracks[object_id],
            "identity_state": "confirmed",
            "observation_count": 7,
            "custom_state": "keep-me",
        }
    }

    result = association.associate_frame(
        [observation("return", 0.01)], tracks, first.next_number, 0.35, 0.05
    )

    assert result.decisions[0]["identity_state"] == "confirmed"
    assert result.tracks[object_id]["identity_state"] == "confirmed"
    assert result.tracks[object_id]["observation_count"] == 7
    assert result.tracks[object_id]["custom_state"] == "keep-me"


def test_diagnostics_expose_candidates_decisions_and_processing_time():
    result = association.associate_frame([observation("a", 0.0)], {}, 1, 0.35, 0.05)

    assert result.processing_time_ms >= 0.0
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0]["observation_id"] == "a"
    assert result.diagnostics[0]["processing_time_ms"] >= 0.0
    assert result.decisions[0]["candidate_count"] == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"coordinate_frame": "camera"},
        {"world_id": ""},
        {"pose_revision_id": ""},
    ],
)
def test_malformed_lineage_is_rejected(kwargs):
    values = {**LINEAGE, **kwargs}
    with pytest.raises(ValueError):
        association.BoxObservation(
            observation_id="bad",
            class_id=41,
            label="book",
            bbox_xyxy=(0.0, 0.0, 1.0, 1.0),
            camera_depth_m=(1.0,),
            pixel_vu=((0, 0),),
            world_samples_m=((0.0, 0.0, 1.0),),
            **values,
        )
