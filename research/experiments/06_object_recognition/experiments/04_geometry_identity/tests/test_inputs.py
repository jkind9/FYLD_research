from __future__ import annotations

import importlib
from pathlib import Path

import pytest

inputs = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.inputs"
)
output_root = inputs.output_root


def test_output_must_not_overlap_frozen_roots(tmp_path):
    repo = Path(__file__).resolve().parents[5]
    with pytest.raises(ValueError, match="protected"):
        output_root(repo, repo / "data/object_revisits/desk_smoke_v1/new-run")
    with pytest.raises(ValueError, match="inside the repository"):
        output_root(repo, Path("C:/outside/task21"))


def test_output_ancestor_cannot_contain_a_protected_input(tmp_path):
    repo = Path(__file__).resolve().parents[5]
    with pytest.raises(ValueError, match="overlaps"):
        output_root(repo, repo)


def test_polygon_and_box_support_differences_preserve_missing_world_geometry():
    comparison = inputs.support_coordinate_difference(
        [1, 2, 3],
        [4, 5, 6],
        {"box_median": {"camera_m": [1.1, 1.8, 3.2], "world_m": [4.1, 4.8, 6.2]}},
    )
    assert comparison["box_minus_polygon_camera_m"] == pytest.approx([0.1, -0.2, 0.2])
    assert comparison["box_minus_polygon_world_m"] == pytest.approx([0.1, -0.2, 0.2])
    missing = inputs.support_coordinate_difference(
        [1, 2, 3], None, {"box_median": {"camera_m": [1.1, 1.8, 3.2], "world_m": None}}
    )
    assert missing["box_minus_polygon_camera_delta_norm_m"] is not None
    assert missing["box_minus_polygon_world_m"] is None
    empty = inputs.support_coordinate_difference(None, None, {"box_median": None})
    assert empty["box_minus_polygon_camera_m"] is None
    assert empty["box_minus_polygon_world_m"] is None
