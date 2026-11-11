"""Placing, matching and counting objects, on hand-made boxes and positions."""

import numpy as np
import pytest

from sitescan.objects import Detection, Objects, associate_frame, box_position
from sitescan.types import Camera

CAMERA = Camera(50.0, 50.0, 32.0, 24.0, 64, 48)


def placed(position, class_id=41, label="cup"):
    return {"xyxy": (0, 0, 1, 1), "label": label, "class_id": class_id, "confidence": 0.9, "frame_index": 0,
            "world_position_m": position}


def test_box_position_is_the_median_surface_point_inside_the_box_in_world_metres():
    depth = np.full((48, 64), 2.0)
    shifted = np.eye(4)
    shifted[:3, 3] = [1.0, 0.0, 0.0]
    # A box centred on the principal point sees the wall straight ahead, 2 m along the camera axis.
    position = box_position(depth, np.ones_like(depth, bool), CAMERA, (28.0, 20.0, 36.0, 28.0), shifted)
    np.testing.assert_allclose(position, [1.0, 0.0, 2.0], atol=0.03)


def test_box_without_valid_depth_has_no_position():
    depth = np.full((48, 64), 2.0)
    assert box_position(depth, np.zeros_like(depth, bool), CAMERA, (0.0, 0.0, 10.0, 10.0), np.eye(4)) is None


def test_first_sighting_is_new_and_a_close_repeat_matches_it():
    rows, tracks, number = associate_frame([placed([0.0, 0.0, 1.0])], {}, 1)
    assert [r["association"] for r in rows] == ["new"] and number == 2
    rows, tracks, _ = associate_frame([placed([0.1, 0.0, 1.0])], tracks, number)
    assert rows[0]["association"] == "matched" and rows[0]["object_id"] == "object-0001"
    assert rows[0]["association_distance_m"] == pytest.approx(0.1)
    assert tracks["object-0001"]["observation_count"] == 2


def test_far_or_other_class_detections_start_new_objects():
    _, tracks, number = associate_frame([placed([0.0, 0.0, 1.0])], {}, 1)
    rows, tracks, _ = associate_frame([placed([1.0, 0.0, 1.0]), placed([0.0, 0.0, 1.0], 39, "bottle")], tracks, number)
    assert [r["association"] for r in rows] == ["new", "new"] and len(tracks) == 3


def test_missing_position_is_unresolved_and_counts_nothing():
    rows, tracks, _ = associate_frame([placed(None)], {}, 1)
    assert rows[0]["association"] == "unresolved_no_position" and rows[0]["object_id"] is None and not tracks


def test_two_equally_close_objects_leave_the_match_ambiguous():
    _, tracks, number = associate_frame([placed([-0.1, 0.0, 1.0]), placed([0.1, 0.0, 1.0])], {}, 1)
    rows, _, _ = associate_frame([placed([0.0, 0.0, 1.0])], tracks, number)
    assert rows[0]["association"] == "unresolved_ambiguous"


def test_a_second_detection_near_an_already_matched_object_is_not_counted_again():
    _, tracks, number = associate_frame([placed([0.0, 0.0, 1.0])], {}, 1)
    rows, tracks, _ = associate_frame([placed([0.0, 0.0, 1.0]), placed([0.2, 0.0, 1.0])], tracks, number)
    assert [r["association"] for r in rows] == ["matched", "unresolved_track_already_assigned"] and len(tracks) == 1


def test_counted_objects_follow_their_anchor_correction():
    objects = Objects()
    depth = np.full((48, 64), 2.0)
    valid = np.ones_like(depth, bool)
    cup = [Detection((28.0, 20.0, 36.0, 28.0), "cup", 41, 0.9)]
    objects.update(cup, depth, valid, CAMERA, np.eye(4), 0, {0: np.eye(4)}, 1)
    moved = np.eye(4)
    moved[:3, 3] = [0.5, 0.0, 0.0]
    # ARCore moves the anchor 0.5 m; the camera, now in the corrected world, sees the cup where it moved to.
    [row] = objects.update(cup, depth, valid, CAMERA, moved, 0, {0: moved}, 2)
    assert row["outcome"] == "matched" and row["nearest_same_class_m"] == pytest.approx(0.0, abs=1e-9)
    assert objects.counts() == {"cup": 1}
