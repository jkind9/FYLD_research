import numpy as np
import pytest

from fyld_scene_mapping.evaluation import align_trajectory, trajectory_metrics
from fyld_scene_mapping.geometry import pose_matrix


def test_metric_alignment_does_not_hide_scale_error() -> None:
    ref = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]])
    est = 2 * ref + [3.0, 4.0, 5.0]
    rigid, metadata = align_trajectory(est, ref)
    assert metadata["scale_factor"] == 1.0 and np.linalg.norm(rigid - ref) > 1.0
    similarity, metadata = align_trajectory(est, ref, with_scale=True)
    np.testing.assert_allclose(similarity, ref, atol=1e-12)
    assert metadata["scale_factor"] == pytest.approx(0.5)


def test_ate_and_rpe_known_translation() -> None:
    poses = [
        pose_matrix(np.array(p), np.array([0.0, 0.0, 0.0, 1.0]))
        for p in [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 1.0, 1.0]]
    ]
    shifted = [p.copy() for p in poses]
    for p in shifted:
        p[:3, 3] += [3.0, 2.0, 1.0]
    metrics = trajectory_metrics(shifted, poses)
    assert metrics["ate_rmse_m"] < 1e-12
    assert metrics["rpe_adjacent_translation_rmse_m"] < 1e-12


def test_stationary_scale_unobservable() -> None:
    with pytest.raises(ValueError, match="unobservable"):
        align_trajectory(np.ones((3, 3)), np.ones((3, 3)), with_scale=True)
