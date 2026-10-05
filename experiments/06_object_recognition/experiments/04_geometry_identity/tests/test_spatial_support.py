"""Contract tests for immutable 3D support summaries."""

from __future__ import annotations

import importlib

import numpy as np
import pytest

spatial_support = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.spatial_support"
)
LINEAGE = {
    "coordinate_frame": "world",
    "world_id": "site-a",
    "segment_id": "segment-1",
    "pose_revision_id": "pose-v1",
}


def test_summary_is_immutable_and_regularises_covariance():
    samples = np.asarray(
        [[0.0, 0.0, 1.0], [0.1, 0.0, 1.0], [0.0, 0.2, 1.0], [0.0, 0.0, 1.1]]
    )
    summary = spatial_support.summarise(samples, **LINEAGE)

    assert summary.mean_m == (0.025, 0.05, 1.025)
    assert summary.sample_count == 4
    assert summary.covariance_m2[0][0] > 0.0
    assert summary.covariance_m2[1][1] > 0.0
    assert np.allclose(summary.covariance_m2, np.asarray(summary.covariance_m2).T)
    with pytest.raises(AttributeError):
        summary.mean_m = (1.0, 1.0, 1.0)


def test_mahalanobis_distance_is_zero_at_mean_and_known_for_axis_offset():
    samples = np.asarray(
        [[0.0, 0.0, 1.0], [0.1, 0.0, 1.0], [0.0, 0.2, 1.0], [0.0, 0.0, 1.1]]
    )
    summary = spatial_support.summarise(samples, **LINEAGE)

    assert summary.squared_mahalanobis(summary.mean_m) == pytest.approx(0.0)
    assert summary.squared_mahalanobis((0.025, 0.05, 1.025)) == pytest.approx(0.0)
    assert summary.squared_mahalanobis((0.125, 0.05, 1.025)) == pytest.approx(
        5.995279214810051
    )


@pytest.mark.parametrize("samples", [None, [], [[0.0, 0.0]], [[0.0, 0.0, np.nan]]])
def test_invalid_support_is_rejected(samples):
    with pytest.raises(ValueError):
        spatial_support.summarise(samples, **LINEAGE)


def test_distance_is_unavailable_below_minimum_independent_samples():
    summary = spatial_support.summarise(
        [[0.0, 0.0, 1.0], [0.1, 0.0, 1.0], [0.0, 0.1, 1.0]], **LINEAGE
    )

    assert summary.squared_mahalanobis((0.0, 0.0, 1.0)) is None


def test_rank_deficient_support_is_unavailable_even_with_four_samples():
    summary = spatial_support.summarise(
        [[0.0, 0.0, 1.0], [0.1, 0.0, 1.0], [0.2, 0.0, 1.0], [0.3, 0.0, 1.0]],
        **LINEAGE,
    )

    assert summary.rank == 1
    assert summary.squared_mahalanobis((0.1, 0.0, 1.0)) is None


@pytest.mark.parametrize("minimum", [1.5, True, float("nan"), float("inf")])
def test_non_integer_minimum_is_rejected(minimum):
    with pytest.raises(ValueError):
        spatial_support.summarise(
            [[0.0, 0.0, 1.0]], min_samples_for_distance=minimum, **LINEAGE
        )


@pytest.mark.parametrize("regularisation", [None, "bad", 0.0, float("nan")])
def test_invalid_regularisation_is_rejected(regularisation):
    with pytest.raises(ValueError):
        spatial_support.summarise(
            [[0.0, 0.0, 1.0]], regularisation_m2=regularisation, **LINEAGE
        )


def test_lineage_is_stored_on_support_summary():
    summary = spatial_support.summarise(
        [[0.0, 0.0, 1.0]],
        coordinate_frame="world",
        world_id="site-a",
        segment_id="segment-1",
        pose_revision_id="pose-v2",
    )

    assert (summary.coordinate_frame, summary.world_id, summary.segment_id,
            summary.pose_revision_id) == ("world", "site-a", "segment-1", "pose-v2")


def test_public_summary_rejects_invalid_covariance_and_query_types():
    with pytest.raises(ValueError, match="positive definite"):
        spatial_support.SupportSummary(
            mean_m=(0.0, 0.0, 1.0),
            covariance_m2=((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
            sample_count=4,
            regularisation_m2=1e-6,
            min_samples_for_distance=4,
            coordinate_frame="world",
            world_id="w",
            segment_id="s",
            pose_revision_id="p",
            rank=3,
        )
    summary = spatial_support.summarise([[0.0, 0.0, 1.0]], **LINEAGE)
    with pytest.raises(ValueError, match="three finite"):
        summary.squared_mahalanobis(None)
    with pytest.raises(ValueError, match="rank"):
        spatial_support.SupportSummary(
            mean_m=(0.0, 0.0, 1.0),
            covariance_m2=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            sample_count=1,
            regularisation_m2=1e-6,
            min_samples_for_distance=1,
            coordinate_frame="world",
            world_id="w",
            segment_id="s",
            pose_revision_id="p",
            rank=3,
        )
