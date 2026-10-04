"""Identity assignment controls for the bounded replay."""

import importlib
import inspect
from itertools import pairwise
from pathlib import Path

import pytest

replay = importlib.import_module("experiments.06_object_recognition.pilot.replay")


def _detection(class_id, position):
    return {
        "class_id": class_id,
        "label": "cup" if class_id == 41 else "tv",
        "world_position_m": position,
    }


def test_injected_detector_metadata_must_report_authorised_gpu_fp32():
    with pytest.raises(ValueError, match="cuda:0 in FP32"):
        replay._validate_inference_metadata(
            {
                "image_shape_hw": [480, 640],
                "actual_device": "cpu",
                "actual_fp16": False,
            }
        )


def test_replay_cannot_accept_detector_adapter_without_checkpoint_provenance():
    assert "detector" not in inspect.signature(replay.replay).parameters


def test_return_after_gap_keeps_id_and_last_position_until_return():
    first, tracks, next_id = replay.associate_frame(
        [_detection(41, [0.0, 0.0, 1.0])], {}, 1, 0.35, 0.05
    )
    assert first[0]["object_id"] == "object-0001"

    missed, during_gap, next_id = replay.associate_frame(
        [], tracks, next_id, 0.35, 0.05
    )
    assert missed == []
    assert during_gap["object-0001"]["last_position_m"] == [0.0, 0.0, 1.0]

    returned, after_return, _ = replay.associate_frame(
        [_detection(41, [0.10, 0.0, 1.0])], during_gap, next_id, 0.35, 0.05
    )
    assert returned[0]["object_id"] == "object-0001"
    assert returned[0]["association"] == "matched"
    assert returned[0]["coordinate_delta_m"] == [0.1, 0.0, 0.0]
    assert after_return["object-0001"]["last_position_m"] == [0.10, 0.0, 1.0]


def test_same_class_objects_keep_distinct_ids_when_detection_order_changes():
    first, tracks, next_id = replay.associate_frame(
        [_detection(62, [0.0, 0.0, 2.0]), _detection(62, [1.0, 0.0, 2.0])],
        {},
        1,
        0.35,
        0.05,
    )
    assert [item["object_id"] for item in first] == ["object-0001", "object-0002"]

    returned, _, _ = replay.associate_frame(
        [_detection(62, [1.05, 0.0, 2.0]), _detection(62, [0.05, 0.0, 2.0])],
        tracks,
        next_id,
        0.35,
        0.05,
    )
    assert [item["object_id"] for item in returned] == ["object-0002", "object-0001"]


def test_assignment_maximizes_feasible_matches_across_same_class_objects():
    _, tracks, next_id = replay.associate_frame(
        [_detection(62, [0.0, 0.0, 0.0]), _detection(62, [0.6, 0.0, 0.0])],
        {},
        1,
        0.35,
        0.05,
    )

    assigned, _, _ = replay.associate_frame(
        [_detection(62, [0.25, 0.0, 0.0]), _detection(62, [-0.3, 0.0, 0.0])],
        tracks,
        next_id,
        0.35,
        0.05,
    )

    assert [item["object_id"] for item in assigned] == ["object-0002", "object-0001"]
    assert all(item["association"] == "matched" for item in assigned)


def test_global_constraints_can_resolve_a_locally_ambiguous_detection():
    _, tracks, next_id = replay.associate_frame(
        [_detection(62, [0.0, 0.0, 0.0]), _detection(62, [0.22, 0.0, 0.0])],
        {},
        1,
        0.35,
        0.05,
    )

    assigned, _, _ = replay.associate_frame(
        [_detection(62, [0.10, 0.0, 0.0]), _detection(62, [-0.15, 0.0, 0.0])],
        tracks,
        next_id,
        0.35,
        0.05,
    )

    assert [item["object_id"] for item in assigned] == ["object-0002", "object-0001"]
    assert all(item["association"] == "matched" for item in assigned)


def test_later_same_class_detection_outside_gate_is_not_counted_as_new():
    first, tracks, next_id = replay.associate_frame(
        [_detection(41, [0.0, 0.0, 1.0])], {}, 1, 0.35, 0.05
    )

    outside_gate, unchanged, next_id = replay.associate_frame(
        [_detection(41, [1.0, 0.0, 1.0])], tracks, next_id, 0.35, 0.05
    )

    assert first[0]["object_id"] == "object-0001"
    assert outside_gate[0]["association"] == "unresolved_outside_gate"
    assert outside_gate[0]["object_id"] is None
    assert unchanged == tracks
    assert next_id == 2


def test_ambiguous_or_missing_geometry_does_not_force_an_identity():
    _, tracks, next_id = replay.associate_frame(
        [_detection(41, [0.0, 0.0, 1.0]), _detection(41, [0.08, 0.0, 1.0])],
        {},
        1,
        0.35,
        0.05,
    )
    ambiguous, tracks_after, next_id = replay.associate_frame(
        [_detection(41, [0.04, 0.0, 1.0])], tracks, next_id, 0.35, 0.05
    )
    assert ambiguous[0]["association"] == "unresolved_ambiguous"
    assert ambiguous[0]["object_id"] is None
    assert tracks_after == tracks

    invalid, unchanged, next_id = replay.associate_frame(
        [_detection(41, None)], tracks_after, next_id, 0.35, 0.05
    )
    assert invalid[0]["association"] == "unresolved_no_position"
    assert invalid[0]["object_id"] is None
    assert unchanged == tracks
    assert next_id == 3


def test_selected_revisit_window_has_a_hard_frame_bound():
    source = Path("data/tum/rgbd_dataset_freiburg1_xyz")
    rows = replay.select_rows(source, 1305031115.879198, 1305031117.479403, 60)
    assert len(rows) == 49
    assert rows[0]["rgb"] == "rgb/1305031115.879198.png"
    assert rows[-1]["rgb"] == "rgb/1305031117.479403.png"
    capped = replay.select_rows(source, 1305031115.879198, 1305031117.479403, 48)
    assert len(capped) == 48
    assert capped[0]["rgb"] == rows[0]["rgb"]
    assert capped[-1]["rgb"] == rows[-1]["rgb"]


def test_long_revisit_span_is_sampled_to_the_frame_cap():
    source = Path("data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk")
    rows = replay.select_rows(source, 1305031454.127701, 1305031472.795640, 60)

    assert len(rows) == 60
    assert rows[0]["timestamp_s"] == 1305031454.127701
    assert rows[-1]["timestamp_s"] == 1305031472.795640
    assert all(
        first["timestamp_s"] < second["timestamp_s"] for first, second in pairwise(rows)
    )
    assert any(
        second["timestamp_s"] - first["timestamp_s"] > 0.1
        for first, second in pairwise(rows)
    )
