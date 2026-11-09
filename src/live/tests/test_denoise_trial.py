"""Scoring for the clean-up trials: empty sight lines to ARCore's tracked points, and tracked-point sizing."""

import numpy as np
from scipy.spatial import cKDTree

from src.live import denoise_trial


def test_surface_on_a_sight_line_counts_as_blocked():
    surface = cKDTree(np.array([[0.0, 0.0, 1.0]]))
    cameras = np.zeros((2, 3))
    points = np.array([[0.0, 0.0, 2.0], [1.0, 0.0, 2.0]])  # the first line passes through the surface point
    blocked, samples = denoise_trial.sight_line_hits(surface, cameras, points)
    assert blocked[0] > 0 and blocked[1] == 0
    assert (samples > 0).all()


def test_surface_behind_a_tracked_point_counts_only_when_looking_behind():
    surface = cKDTree(np.array([[0.0, 0.0, 2.5]]))  # a copy 0.5 m behind the tracked point
    cameras, points = np.zeros((1, 3)), np.array([[0.0, 0.0, 2.0]])
    assert denoise_trial.sight_line_hits(surface, cameras, points)[0][0] == 0
    behind, samples = denoise_trial.sight_line_hits(surface, cameras, points, behind=True)
    assert behind[0] > 0 and samples[0] == len(np.arange(0.15, 1.0, 0.04))


def test_tracked_fallback_comes_from_points_in_cells_without_arcore_depth():
    learned, valid = np.full((60, 80), 2.0), np.ones((60, 80), bool)
    u, v = np.meshgrid(np.arange(0, 40, 2), np.arange(0, 60, 2))
    arcore_uv = np.c_[u.ravel(), v.ravel()].astype(float)  # ARCore depth covers the left half only
    pixels = np.array([[50.0, 10.0], [60.0, 30.0], [70.0, 50.0], [75.0, 5.0], [55.0, 45.0], [5.0, 5.0]])
    z = np.array([3.0, 3.0, 3.0, 3.0, 3.0, 9.0])  # the last point is in an ARCore cell, so it is ignored
    fallback = denoise_trial.tracked_fallback(learned, valid, arcore_uv, pixels, z)
    assert np.isclose(np.exp(fallback), 1.5)
    assert denoise_trial.tracked_fallback(learned, valid, arcore_uv, pixels[:2], z[:2]) is None


def test_window_share_counts_only_views_from_frames_near_the_focus():
    blocked, samples = np.array([5, 0, 9]), np.array([10, 10, 10])
    seqs = np.array([60, 70, 200])
    assert denoise_trial.window_share(blocked, samples, seqs, focus=65, half_width=10) == 0.25


def test_far_sizes_change_only_depth_beyond_arcore_reach():
    learned = np.array([1.0, 2.0, 3.0])
    sizes = denoise_trial.far_sizes(learned, near=np.ones(3), far=np.full(3, 1.2))
    assert sizes.tolist() == [1.0, 1.0, 1.2]  # 2.5 m is where ARCore depth runs out
