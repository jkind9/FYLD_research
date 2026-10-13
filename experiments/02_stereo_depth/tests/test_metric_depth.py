"""Offline geometry contracts for comparing raw depth outputs."""

import importlib

import numpy as np
import pytest

geometry = importlib.import_module("experiments.02_stereo_depth.geometry")


@pytest.mark.parametrize(
    "convention,raw",
    [
        ("relative_depth", np.array([[1.0, 2.0], [3.0, 4.0]])),
        ("metric_depth", 3.0 + 2.0 * np.array([[1.0, 2.0], [3.0, 4.0]])),
        (
            "relative_inverse_depth",
            2.0 / np.array([[1.0, 2.0], [3.0, 4.0]]) + 3.0,
        ),
        ("affine_invariant_log_depth", np.log([[1.0, 2.0], [3.0, 4.0]])),
    ],
)
def test_shape_alignment_recovers_known_metric_depth(convention, raw):
    expected_depth_m = np.array([[1.0, 2.0], [3.0, 4.0]])
    reference_valid = np.ones(expected_depth_m.shape, dtype=bool)

    aligned_depth_m, aligned_valid, _ = geometry.align_shape_to_metric(
        raw, convention, expected_depth_m, reference_valid
    )

    np.testing.assert_allclose(aligned_depth_m, expected_depth_m, atol=1e-6, rtol=0)
    np.testing.assert_array_equal(aligned_valid, reference_valid)


def test_metric_conversion_preserves_metres_and_invalid_pixels():
    raw_depth_m = np.array([[1.25, 0.0], [np.nan, 3.5]])

    depth_m, valid = geometry.metric_depth(raw_depth_m)

    np.testing.assert_allclose(depth_m[[0, 1], [0, 1]], [1.25, 3.5])
    np.testing.assert_array_equal(valid, [[True, False], [False, True]])
    assert np.isnan(depth_m[0, 1])
    assert np.isnan(depth_m[1, 0])


@pytest.mark.parametrize(
    "raw,reference,reference_valid",
    [
        (np.ones((2, 2)), np.ones((1, 2)), np.ones((1, 2), dtype=bool)),
        (np.ones((2, 2)), np.ones((2, 2)), np.ones((2, 1), dtype=bool)),
    ],
)
def test_shape_alignment_rejects_mismatched_image_grids(raw, reference, reference_valid):
    with pytest.raises(ValueError, match="shape|grid|resolution"):
        geometry.align_shape_to_metric(
            raw, "relative_depth", reference, reference_valid
        )


def test_shape_alignment_excludes_invalid_reference_and_prediction_pixels():
    reference_depth_m = np.array([[2.0, 4.0], [8.0, 16.0]])
    reference_valid = np.array([[True, True], [False, True]])
    raw_relative_depth = np.array([[1.0, 2.0], [np.nan, 8.0]])

    aligned_depth_m, aligned_valid, _ = geometry.align_shape_to_metric(
        raw_relative_depth,
        "relative_depth",
        reference_depth_m,
        reference_valid,
    )

    np.testing.assert_array_equal(aligned_valid, [[True, True], [False, True]])
    np.testing.assert_allclose(
        aligned_depth_m[aligned_valid], reference_depth_m[aligned_valid], atol=1e-6
    )


def test_shape_alignment_reports_share_of_non_positive_aligned_values():
    reference_depth_m = np.array([[1.0, 1.0, 1.0, 100.0]])
    reference_valid = np.ones(reference_depth_m.shape, dtype=bool)
    raw_relative_depth = np.array([[0.0, 1.0, 2.0, 3.0]])
    scoring = importlib.import_module("experiments.02_stereo_depth.scoring")

    result = scoring.score_shape_to_metric(
        raw_relative_depth,
        "relative_depth",
        reference_depth_m,
        reference_valid,
    )

    assert result["non_positive_aligned_fraction"] == pytest.approx(0.25)
    assert result["overall"]["valid_coverage"] == pytest.approx(0.75)


def test_per_image_scores_report_errors_coverage_and_reference_distance_bands():
    scoring = importlib.import_module("experiments.02_stereo_depth.scoring")
    reference_depth_m = np.array([[0.5, 1.0, 1.5, 2.0], [2.5, 3.0, 4.0, 0.0]])
    reference_valid = np.array(
        [[True, True, True, True], [True, True, True, False]]
    )
    predicted_depth_m = np.array([[1.0, 1.0, 3.0, 2.0], [5.0, np.nan, 0.0, 1.0]])
    predicted_valid = np.array(
        [[True, True, True, True], [True, True, True, True]]
    )

    result = scoring.score_depth(
        predicted_depth_m,
        predicted_valid,
        reference_depth_m,
        reference_valid,
    )

    overall = result["overall"]
    assert overall["abs_rel"] == pytest.approx(0.6)
    assert overall["rmse_m"] == pytest.approx(np.sqrt(1.75))
    assert overall["delta1"] == pytest.approx(2 / 5)
    assert overall["valid_coverage"] == pytest.approx(5 / 7)
    assert overall["reference_pixels"] == 7
    assert overall["scored_pixels"] == 5

    bands = result["distance_bands"]
    assert set(bands) == {"0-1m", "1-2m", "2-4m"}
    assert bands["0-1m"]["reference_pixels"] == 1
    assert bands["0-1m"]["scored_pixels"] == 1
    assert bands["0-1m"]["abs_rel"] == pytest.approx(1.0)
    assert bands["0-1m"]["rmse_m"] == pytest.approx(0.5)
    assert bands["0-1m"]["delta1"] == pytest.approx(0.0)
    assert bands["0-1m"]["valid_coverage"] == pytest.approx(1.0)
    assert bands["1-2m"]["reference_pixels"] == 2
    assert bands["1-2m"]["scored_pixels"] == 2
    assert bands["1-2m"]["abs_rel"] == pytest.approx(0.5)
    assert bands["1-2m"]["rmse_m"] == pytest.approx(np.sqrt(1.125))
    assert bands["1-2m"]["delta1"] == pytest.approx(0.5)
    assert bands["1-2m"]["valid_coverage"] == pytest.approx(1.0)
    assert bands["2-4m"]["reference_pixels"] == 4
    assert bands["2-4m"]["scored_pixels"] == 2
    assert bands["2-4m"]["abs_rel"] == pytest.approx(0.5)
    assert bands["2-4m"]["rmse_m"] == pytest.approx(np.sqrt(3.125))
    assert bands["2-4m"]["delta1"] == pytest.approx(0.5)
    assert bands["2-4m"]["valid_coverage"] == pytest.approx(2 / 4)


def test_per_image_scores_exclude_invalid_predictions_from_errors_and_coverage():
    scoring = importlib.import_module("experiments.02_stereo_depth.scoring")
    reference_depth_m = np.array([[1.0, 2.0, 3.0]])
    reference_valid = np.ones(reference_depth_m.shape, dtype=bool)
    predicted_depth_m = np.array([[1.0, np.nan, 0.0]])
    predicted_valid = np.ones(predicted_depth_m.shape, dtype=bool)

    result = scoring.score_depth(
        predicted_depth_m,
        predicted_valid,
        reference_depth_m,
        reference_valid,
    )["overall"]

    assert result["abs_rel"] == pytest.approx(0.0)
    assert result["rmse_m"] == pytest.approx(0.0)
    assert result["delta1"] == pytest.approx(1.0)
    assert result["valid_coverage"] == pytest.approx(1 / 3)
    assert result["reference_pixels"] == 3
    assert result["scored_pixels"] == 1


def test_metric_and_reference_aligned_shape_scores_are_separate_views():
    scoring = importlib.import_module("experiments.02_stereo_depth.scoring")
    reference_depth_m = np.array([[1.0, 2.0], [3.0, 4.0]])
    reference_valid = np.ones(reference_depth_m.shape, dtype=bool)
    raw_relative_depth = 2.0 * reference_depth_m
    prediction_valid = np.ones(raw_relative_depth.shape, dtype=bool)

    metric_result = scoring.score_depth(
        raw_relative_depth,
        prediction_valid,
        reference_depth_m,
        reference_valid,
    )
    shape_result = scoring.score_shape_to_metric(
        raw_relative_depth,
        "relative_depth",
        reference_depth_m,
        reference_valid,
    )

    assert metric_result["view"] == "metric"
    assert metric_result["overall"]["abs_rel"] == pytest.approx(1.0)
    assert shape_result["view"] == "reference_aligned_shape"
    assert shape_result["overall"]["abs_rel"] == pytest.approx(0.0)
    assert shape_result["overall"]["rmse_m"] == pytest.approx(0.0)
    assert metric_result is not shape_result


def test_metric_depth_can_enter_shape_view_without_changing_metric_view():
    scoring = importlib.import_module("experiments.02_stereo_depth.scoring")
    reference_depth_m = np.array([[1.0, 2.0], [3.0, 4.0]])
    reference_valid = np.ones(reference_depth_m.shape, dtype=bool)
    raw_metric_depth_m = 3.0 + 2.0 * reference_depth_m

    shape_result = scoring.score_shape_to_metric(
        raw_metric_depth_m,
        "metric_depth",
        reference_depth_m,
        reference_valid,
    )

    assert shape_result["view"] == "reference_aligned_shape"
    assert shape_result["overall"]["abs_rel"] == pytest.approx(0.0)
    assert shape_result["non_positive_aligned_fraction"] == 0.0


def test_invalid_metric_predictions_do_not_affect_shape_alignment():
    reference_depth_m = np.array([[1.0, 2.0, 4.0]])
    reference_valid = np.ones(reference_depth_m.shape, dtype=bool)
    raw_metric_depth_m = np.array([[2.0, 4.0, -100.0]])
    scoring = importlib.import_module("experiments.02_stereo_depth.scoring")

    result = scoring.score_shape_to_metric(
        raw_metric_depth_m,
        "metric_depth",
        reference_depth_m,
        reference_valid,
    )

    assert result["overall"]["valid_coverage"] == pytest.approx(2 / 3)
    assert result["non_positive_aligned_fraction"] == 0.0
    assert result["overall"]["abs_rel"] == pytest.approx(0.0)
