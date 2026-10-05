"""Contract tests for the reusable mask pipeline."""

from __future__ import annotations

import importlib

import numpy as np
import pytest

pipeline = importlib.import_module(
    "experiments.06_object_recognition.experiments.02_segmentation.mask_pipeline"
)

LINEAGE = {
    "frame_id": "frame-1",
    "prompt_mode": "detector_box",
    "coordinate_frame": "camera",
    "world_id": "scene-a",
    "segment_id": "segment-1",
    "pose_revision_id": "pose-v1",
}


def test_pipeline_preserves_order_grid_and_lineage():
    rgb = np.zeros((8, 8, 3), dtype=np.uint8)
    result = pipeline.run_methods(rgb, [1, 1, 7, 7], ("rectangle", "canny"), **LINEAGE)

    assert result.frame_id == "frame-1"
    assert [item.method for item in result.results] == ["rectangle", "canny"]
    assert all(item.mask.shape == (8, 8) for item in result.results)
    assert all(not item.mask.flags.writeable for item in result.results)
    assert all(item.prompt_mode == "detector_box" for item in result.results)
    assert all(item.pose_revision_id == "pose-v1" for item in result.results)
    assert result.total_elapsed_seconds >= 0.0
    assert all(item.elapsed_seconds >= 0.0 for item in result.results)


def test_pipeline_reports_empty_result_without_fallback():
    rgb = np.zeros((8, 8, 3), dtype=np.uint8)
    result = pipeline.run_methods(rgb, [1, 1, 7, 7], ("canny",), **LINEAGE)

    assert result.results[0].status == "empty"
    assert result.results[0].error is None
    assert not result.results[0].mask.any()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"methods": ()},
        {"methods": ("rectangle", "rectangle")},
        {"methods": ("unknown",)},
        {"methods": ("rectangle",), "frame_id": ""},
        {"methods": ("rectangle",), "pose_revision_id": ""},
    ],
)
def test_pipeline_rejects_invalid_scope_or_lineage(kwargs):
    rgb = np.zeros((8, 8, 3), dtype=np.uint8)
    values = {**LINEAGE, **kwargs}
    methods = values.pop("methods")
    with pytest.raises(ValueError):
        pipeline.run_methods(rgb, [1, 1, 7, 7], methods, **values)
