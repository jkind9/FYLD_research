"""Expected-answer controls; real provisional polygons are never accuracy truth."""

import importlib

import numpy as np
import pytest

api = importlib.import_module(
    "experiments.06_object_recognition.experiments.02_segmentation.masks"
)
scorer = importlib.import_module(
    "experiments.06_object_recognition.experiments.02_segmentation.scoring"
)


def test_rounded_clipped_rectangle():
    assert api.rectangle_bounds([-1.2, 1.2, 5.1, 7.9], 8, 8) == (0, 1, 6, 8)
    result = api.segment(
        np.zeros((8, 8, 3), np.uint8), [1.2, 1.2, 5.1, 7.9], "rectangle"
    )
    assert result["status"] == "ok"
    assert np.count_nonzero(result["mask"]) == 35
    assert set(np.unique(result["mask"])) == {0, 255}


@pytest.mark.parametrize("box", [[0, 0, 8, 8], [1, 1, 2, 2], [20, 20, 30, 30]])
def test_unusable_prompt_never_rectangle_fallback(box):
    result = api.segment(np.zeros((8, 8, 3), np.uint8), box, "grabcut")
    assert result["status"] == "unusable_prompt"
    assert not result["mask"].any()


def test_empty_canny_and_unknown_method():
    rgb = np.zeros((8, 8, 3), np.uint8)
    assert api.segment(rgb, [1, 1, 7, 7], "canny")["status"] == "empty"
    with pytest.raises(ValueError, match="method"):
        api.segment(rgb, [1, 1, 7, 7], "unknown")


@pytest.mark.parametrize(
    "box", [[0, 0, float("nan"), 3], [3, 1, 2, 4], [True, 0, 3, 3], [1, 2]]
)
def test_invalid_box(box):
    with pytest.raises(ValueError):
        api.rectangle_bounds(box, 8, 8)


def test_synthetic_overlap_boundary_and_real_reference_exclusion():
    a = np.zeros((8, 8), np.uint8)
    a[1:4, 1:4] = 255
    b = np.zeros_like(a)
    b[4:7, 4:7] = 255
    assert scorer.mask_scores(a, a, synthetic=True)["iou"] == 1
    assert scorer.mask_scores(a, a, synthetic=True)["boundary_f1"] == 1
    assert scorer.mask_scores(a, b, synthetic=True)["iou"] == 0
    assert scorer.mask_scores(a, a, synthetic=False)["iou"] is None
    assert (
        scorer.mask_scores(a, a, synthetic=False)["status"]
        == "unavailable_provisional_reference"
    )
    assert (
        scorer.mask_scores(np.zeros_like(a), np.zeros_like(a), synthetic=True)["iou"]
        == 1
    )
    with pytest.raises(ValueError):
        scorer.mask_scores(a, b[:2], synthetic=True)


def test_split_merge_touching_and_empty_controls():
    a = np.zeros((8, 8), np.uint8)
    a[1:4, 1:3] = 255
    b = np.zeros_like(a)
    b[1:4, 3:5] = 255
    joined = np.maximum(a, b)
    assert scorer.instance_events([joined], [a, b], synthetic=True) == {
        "merges": 1,
        "splits": 0,
    }
    assert scorer.instance_events([a, b], [joined], synthetic=True) == {
        "merges": 0,
        "splits": 1,
    }
    assert scorer.instance_events([], [a], synthetic=True) == {"merges": 0, "splits": 0}
    with pytest.raises(ValueError, match="synthetic"):
        scorer.instance_events([a], [a], synthetic=False)


def test_depth_support_holes_range_and_component_statistics():
    support = importlib.import_module(
        "experiments.06_object_recognition.experiments.02_segmentation.support"
    )
    from experiments.shared.contracts import Calibration

    calibration = Calibration(4, 4, 2, 2, 1.5, 1.5, "x-right_y-down_z-forward")
    raw = np.full((4, 4), 5000, np.uint16)
    raw[0, 0], raw[0, 1] = 0, 20000
    mask = np.full((4, 4), 255, np.uint8)
    summary = support.summarise(mask, raw, calibration)
    assert summary["area_pixels"] == 16
    assert summary["raw_valid_pixels"] == 15
    assert summary["processed_valid_pixels"] == 14
    assert summary["camera_median_m"][2] == 1
    assert summary["camera_iqr_m"][2] == 0
    assert support.coordinate_difference(summary, summary) == [0, 0, 0]
    empty = support.summarise(np.zeros_like(mask), raw, calibration)
    assert empty["camera_median_m"] is None
    assert empty["camera_iqr_m"] is None
    assert support.coordinate_difference(empty, summary) is None
    with pytest.raises(ValueError):
        support.summarise(mask, raw.astype(float), calibration)


def test_grabcut_and_canny_finite_binary_original_grid():
    rgb = np.full((32, 32, 3), 10, np.uint8)
    rgb[8:24, 8:24] = [220, 100, 40]
    for method in ("grabcut", "canny"):
        result = api.segment(rgb, [5, 5, 27, 27], method)
        assert result["status"] == "ok"
        assert result["mask"].shape == (32, 32)
        assert result["mask"].dtype == np.uint8
        assert not result["mask"][:5].any()
        assert np.array_equal(
            result["mask"], api.segment(rgb, [5, 5, 27, 27], method)["mask"]
        )


def test_failed_grabcut_explicit(monkeypatch):
    def failed(*args):
        raise api.cv2.error("synthetic failure")

    monkeypatch.setattr(api.cv2, "grabCut", failed)
    result = api.segment(np.zeros((8, 8, 3), np.uint8), [1, 1, 7, 7], "grabcut")
    assert result["status"] == "failed" and not result["mask"].any()
    assert "synthetic failure" in result["error"]


def test_malformed_masks_rgb_and_dimensions():
    with pytest.raises(ValueError):
        api.segment(np.zeros((8, 8), np.uint8), [1, 1, 7, 7], "rectangle")
    with pytest.raises(ValueError):
        scorer.binary(np.ones((8, 8), np.uint8))
    with pytest.raises(ValueError):
        scorer.instance_events(
            [np.zeros((2, 2), np.uint8)], [np.zeros((3, 3), np.uint8)], synthetic=True
        )
