"""Analytic controls pin original-pixel support and camera-to-world direction."""

import importlib

import numpy as np
import pytest

from experiments.shared.contracts import Calibration, Pose

localisation = importlib.import_module(
    "experiments.06_object_recognition.pilot.localisation"
)
dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")


def frame(depth=None):
    depth = np.ones((3, 4)) if depth is None else np.array(depth, dtype=float)
    return dataset.RGBDFrame(
        "fixture",
        1.0,
        1.0,
        Calibration(4, 3, 2, 2, 1.5, 1, "x-right_y-down_z-forward"),
        np.zeros((3, 4, 3), dtype=np.uint8),
        depth,
        np.isfinite(depth) & (depth > 0),
    )


def box(xyxy=(1, 1, 3, 2)):
    return localisation.Detection(tuple(xyxy), "cup", 41, 0.9)


def pose(matrix=None):
    return Pose(
        np.eye(4) if matrix is None else matrix,
        "fixture-world",
        "continuous",
        "supplied",
    )


def test_camera_and_world_positions_follow_known_rotated_translated_pose():
    matrix = np.array([[0, -1, 0, 2], [1, 0, 0, 3], [0, 0, 1, 4], [0, 0, 0, 1]])
    result = localisation.localise_detection(frame(), box(), pose(matrix))
    np.testing.assert_allclose(result["box_median"]["camera_m"], [0, 0, 1], atol=1e-10)
    np.testing.assert_allclose(result["box_median"]["world_m"], [2, 3, 5], atol=1e-10)
    np.testing.assert_allclose(
        result["centre_sample"]["camera_m"], [-0.25, 0, 1], atol=1e-10
    )
    np.testing.assert_allclose(
        result["centre_sample"]["world_m"], [2, 2.75, 5], atol=1e-10
    )
    assert result["centre_sample"]["pixel_vu"] == [1, 1]
    assert result["valid_pixel_count"] == 2
    assert result["world_id"] == "fixture-world"


def test_missing_depth_never_invents_a_marker():
    result = localisation.localise_detection(
        frame(np.full((3, 4), np.nan)), box(), pose()
    )
    assert result["status"] == "no_valid_depth"
    assert result["centre_sample"] is None
    assert result["box_median"] is None


def test_missing_pose_retains_camera_sample_without_inventing_world_coordinates():
    result = localisation.localise_detection(frame(), box(), None)
    assert result["status"] == "camera_only"
    assert result["centre_sample"]["world_m"] is None
    assert result["world_id"] is None


def test_background_contamination_changes_box_location_but_centre_is_measured_pixel():
    depth = np.full((3, 4), 3.0)
    depth[1, 1] = 1.0
    result = localisation.localise_detection(frame(depth), box((0, 0, 4, 3)), pose())
    assert result["box_median"]["camera_m"][2] == 3.0
    assert result["centre_sample"]["camera_m"][2] == 1.0
    assert result["depth_range_m"] == [1.0, 3.0]


def test_nearest_valid_sample_reports_offset_when_centre_depth_is_missing():
    depth = np.full((3, 4), np.nan)
    depth[0, 0] = 1
    result = localisation.localise_detection(frame(depth), box((0, 0, 4, 3)), pose())
    assert result["centre_sample"]["pixel_vu"] == [0, 0]
    assert result["centre_sample"]["offset_from_centre_px"] > 0


def test_fractional_box_uses_pixel_centres_and_does_not_admit_background():
    result = localisation.localise_detection(frame(), box((1.6, 0.6, 2.6, 1.6)), pose())
    assert result["box_pixel_count"] == 1
    assert result["centre_sample"]["pixel_vu"] == [1, 2]


def test_asymmetric_box_uses_same_pixel_centres_for_support_and_nearest_sample():
    depth = np.full((3, 4), 3.0)
    depth[1, 1] = 1.0
    result = localisation.localise_detection(
        frame(depth), box((0.2, 0.2, 3.2, 2.2)), pose()
    )
    assert result["centre_sample"]["pixel_vu"] == [1, 1]
    assert result["centre_sample"]["depth_m"] == 1.0
    assert result["centre_sample"]["offset_from_centre_px"] == pytest.approx(
        np.hypot(0.3, 0.2)
    )


@pytest.mark.parametrize(
    "xyxy", [(2, 1, 1, 2), (-1, 0, 1, 2), (0, 0, 5, 3), (0, 0, 4, 4)]
)
def test_invalid_or_out_of_image_boxes_rejected(xyxy):
    with pytest.raises(ValueError):
        localisation.localise_detection(frame(), box(xyxy), pose())


@pytest.mark.parametrize("xyxy", [(0, 0, float("nan"), 2), (0, 0, 0, 2), (0, 0, 1)])
def test_malformed_boxes_rejected(xyxy):
    with pytest.raises(ValueError):
        box(xyxy)


@pytest.mark.parametrize("score", [-0.1, 1.1, float("nan")])
def test_invalid_detection_score_rejected(score):
    with pytest.raises(ValueError):
        localisation.Detection((0, 0, 1, 1), "cup", 41, score)


def test_invalid_transform_rejected():
    with pytest.raises(ValueError):
        pose(np.zeros((4, 4)))


def test_opt_in_box_sample_export_preserves_exact_world_samples_and_lineage():
    result = localisation.localise_box_samples(
        frame(), box(), pose(), pose_revision_id="pose-v1"
    )

    assert result["status"] == "located"
    assert len(result["world_samples_m"]) == 2
    np.testing.assert_allclose(
        result["world_samples_m"], [[-0.25, 0.0, 1.0], [0.25, 0.0, 1.0]]
    )
    assert result["pixel_vu"] == [[1, 1], [1, 2]]
    assert result["pose_revision_id"] == "pose-v1"
    assert result["coordinate_frame"] == "world"


def test_opt_in_box_sample_export_requires_pose_revision_for_world_samples():
    with pytest.raises(ValueError, match="pose revision"):
        localisation.localise_box_samples(frame(), box(), pose())


def test_opt_in_box_sample_export_keeps_missing_pose_explicit():
    result = localisation.localise_box_samples(
        frame(), box(), None, pose_revision_id=None
    )

    assert result["status"] == "camera_only"
    assert result["world_samples_m"] is None
    assert result["camera_samples_m"]
