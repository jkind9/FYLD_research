"""Best-fit trajectory scores: known transforms give known answers."""

import copy
import importlib

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.shared.contracts import Pose

package = "experiments.03_camera_pose_estimation.src"
tracking = importlib.import_module(package + ".tracking")
evaluation = importlib.import_module(package + ".evaluation")


def matrix(position, rotation=None):
    out = np.eye(4)
    out[:3, :3] = np.eye(3) if rotation is None else rotation
    out[:3, 3] = position
    return out


def curve(count, step_s=0.1):
    times = np.arange(count) * step_s
    positions = np.stack([np.cos(times), np.sin(times), 0.3 * times], axis=1)
    return times, positions


def records(times, positions, segment="s", rotations=None):
    out = []
    for i, (t, p) in enumerate(zip(times, positions)):
        rotation = None if rotations is None else rotations[i]
        pose = Pose(matrix(p, rotation), "w", segment, "estimated")
        out.append(tracking.Record(f"f{segment}{i}", float(t), "tracked", pose, ""))
    return out


def references(times, positions):
    return [(float(t), matrix(p)) for t, p in zip(times, positions)]


def transformed(positions, scale, angle_deg, shift):
    rotation = Rotation.from_euler("z", angle_deg, degrees=True).as_matrix()
    return scale * positions @ rotation.T + np.asarray(shift)


def test_scaled_fit_recovers_rotation_shift_and_size():
    times, truth = curve(50)
    estimate = transformed(truth, 0.5, 30, (1, 2, 3))
    result = evaluation.evaluate(records(times, estimate), references(times, truth))
    assert result["ate_scaled_rmse_m"] < 1e-9
    assert result["ate_scaled_size"] == pytest.approx(2.0, abs=1e-9)
    assert result["ate_rigid_rmse_m"] > 0.1


def test_rigid_fit_is_exact_for_a_rigid_copy_and_keeps_first_pose_score():
    times, truth = curve(50)
    estimate = transformed(truth, 1.0, 30, (1, 2, 3))
    result = evaluation.evaluate(records(times, estimate), references(times, truth))
    assert result["ate_rigid_rmse_m"] < 1e-9
    # Only positions are rotated here, so first-pose alignment cannot undo the turn.
    assert result["position_rmse_m"] > 0.1


def test_rigid_fit_matches_known_noise_size():
    rng = np.random.default_rng(0)
    times, truth = curve(2000, 0.01)
    noise = rng.normal(0, 0.01, truth.shape)
    result = evaluation.evaluate(records(times, truth + noise), references(times, truth))
    assert result["ate_rigid_rmse_m"] == pytest.approx(0.01 * np.sqrt(3), rel=0.1)


@pytest.mark.parametrize("count", [2])
def test_too_few_poses_give_none(count):
    times, truth = curve(count)
    result = evaluation.evaluate(records(times, truth), references(times, truth))
    assert result["ate_rigid_rmse_m"] is None
    assert result["ate_scaled_rmse_m"] is None
    assert result["ate_scaled_size"] is None


def test_positions_on_one_line_give_none():
    times = np.arange(10) * 0.1
    truth = np.stack([times, np.zeros(10), np.zeros(10)], axis=1)
    result = evaluation.evaluate(records(times, truth), references(times, truth))
    assert result["ate_rigid_rmse_m"] is None


def test_relative_error_over_one_second_measures_speed_error():
    times = np.arange(31) * 0.1
    truth = np.stack([times, np.zeros_like(times), np.zeros_like(times)], axis=1)
    estimate = truth * 1.1
    result = evaluation.evaluate(records(times, estimate), references(times, truth))
    assert result["rpe_1s_translation_rmse_m"] == pytest.approx(0.1, abs=1e-9)
    assert result["rpe_1s_rotation_rmse_rad"] == pytest.approx(0.0, abs=1e-9)


def test_segments_are_aligned_separately():
    times, truth = curve(40)
    first = records(times[:20], transformed(truth[:20], 1, 45, (0, 0, 0)), "a")
    second = records(times[20:], transformed(truth[20:], 1, 0, (5, 0, 0)), "b")
    result = evaluation.evaluate(first + second, references(times, truth))
    assert result["ate_rigid_rmse_m"] < 1e-9
    assert {s["segment_id"] for s in result["segments"]} == {"a", "b"}
    assert all(s["ate_rigid_rmse_m"] < 1e-9 for s in result["segments"])


def test_inputs_are_not_changed():
    times, truth = curve(20)
    estimate = records(times, transformed(truth, 0.5, 10, (1, 0, 0)))
    refs = references(times, truth)
    before = copy.deepcopy([(r.frame_id, r.pose.matrix.copy()) for r in estimate]), copy.deepcopy(refs)
    evaluation.evaluate(estimate, refs)
    assert all(np.array_equal(r.pose.matrix, m) for r, (_, m) in zip(estimate, before[0]))
    assert all(np.array_equal(a[1], b[1]) for a, b in zip(refs, before[1]))
