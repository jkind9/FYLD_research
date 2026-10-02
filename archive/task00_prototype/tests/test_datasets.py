from pathlib import Path

import numpy as np
import pytest

from fyld_scene_mapping.datasets import associate, contained_path, ground_truth_at


def test_association_offsets_and_no_duplicate_reuse() -> None:
    a, b = np.array([1.0, 1.02, 2.0]), np.array([1.011, 2.04])
    assert associate(a, b, 0.015) == [(1, 0)]
    assert associate(a, b, 0.05) == [(1, 0), (2, 1)]


def test_tolerance_boundary_empty_and_invalid_order() -> None:
    assert associate(np.array([1.0]), np.array([1.125]), 0.125) == [(0, 0)]
    assert associate(np.array([]), np.array([]), 0.02) == []
    with pytest.raises(ValueError):
        associate(np.array([1.0, 1.0]), np.array([1.0]), 0.02)


def test_gt_interpolation_no_extrapolation_and_bracket_limit(tmp_path: Path) -> None:
    path = tmp_path / "groundtruth.txt"
    path.write_text("# seconds, metres, xyzw\n1.0 0 0 0 0 0 0 1\n1.1 1 0 0 0 0 1 0\n")
    poses, info = ground_truth_at(path, np.array([0.99, 1.05, 1.2]), 0.06)
    assert poses[0] is None and poses[2] is None and info["matched"] == 1
    np.testing.assert_allclose(poses[1][:3, 3], [0.5, 0, 0])
    np.testing.assert_allclose(poses[1][:3, :3] @ [1, 0, 0], [0, 1, 0], atol=1e-12)
    rejected, _ = ground_truth_at(path, np.array([1.05]), 0.02)
    assert rejected == [None]


def test_dataset_paths_cannot_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        contained_path(tmp_path, "../secret.png")
