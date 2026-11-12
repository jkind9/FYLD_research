"""Exact numerical and ambiguous-neighbour controls, independent of recordings."""

import importlib

import numpy as np
import pytest

adapter = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.adapter"
)
compare = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.compare"
)
evaluator = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.evaluator"
)


def patch():
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, (128, 128, 3), dtype=np.uint8)


def test_crop_floor_ceil_mask_and_channels():
    rgb = np.full((20, 30, 3), [255, 0, 30], np.uint8)
    mask = np.zeros((20, 30), np.uint8)
    mask[5:15, 8:18] = 255
    crop = adapter.prepare_crop(rgb, mask, [7.2, 4.2, 18.1, 15.1])
    assert crop.bounds == (7, 4, 19, 16)
    assert crop.rgb.shape == (128, 128, 3)
    assert crop.mask.shape == (128, 128)
    assert np.all(crop.rgb[crop.mask == 0] == 0)
    assert crop.rgb[64, 64].tolist() == [255, 0, 30]
    assert not crop.rgb.flags.writeable and not crop.mask.flags.writeable


@pytest.mark.parametrize("bounds", [[1, 1, 1, 5], [np.nan, 1, 5, 5], [0, 0, 1]])
def test_invalid_bounds(bounds):
    with pytest.raises(ValueError):
        adapter.prepare_crop(patch(), np.ones((128, 128), np.uint8), bounds)


@pytest.mark.parametrize(
    "bad", [np.ones((128, 128), float), np.ones((2, 2, 3), np.uint8)]
)
def test_invalid_rgb(bad):
    with pytest.raises(ValueError):
        adapter.prepare_crop(bad, np.ones((128, 128), np.uint8), [0, 0, 128, 128])


def test_zncc_identical_inverse_constant_and_empty():
    rgb = patch()
    mask = np.ones((128, 128), np.uint8) * 255
    assert compare.zncc(rgb, mask, rgb, mask)["score"] == pytest.approx(1)
    assert compare.zncc(rgb, mask, 255 - rgb, mask)["score"] == pytest.approx(-1)
    assert compare.zncc(rgb, mask * 0, rgb, mask)["score"] is None
    assert compare.zncc(rgb * 0, mask, rgb * 0, mask)["score"] is None
    assert compare.zncc(rgb, mask, rgb, mask)["pixels"] == 16384


def test_cosine_zero_nonfinite_and_dimensions():
    assert compare.cosine([1, 2], [1, 2])["score"] == pytest.approx(1)
    assert compare.cosine([1, 0], [-1, 0])["score"] == -1
    assert compare.cosine([0, 0], [1, 0])["score"] is None
    assert compare.cosine([np.nan, 0], [1, 0])["score"] is None
    with pytest.raises(ValueError):
        compare.cosine([1, 2], [1])


def test_classical_feature_exact_self_and_empty():
    rgb = patch()
    mask = np.ones((128, 128), np.uint8) * 255
    crop = adapter.prepare_crop(rgb, mask, [0, 0, 128, 128])
    descriptors = adapter.describe_classical(crop)
    for method in ("orb", "sift"):
        result = compare.local_features(
            descriptors[method], descriptors[method], method
        )
        assert result["score"] == pytest.approx(1)
        assert result["inliers"] >= 4
        assert result["reprojection_median_px"] < 1e-5
    empty = adapter.describe_classical(
        adapter.prepare_crop(rgb, mask * 0, [0, 0, 128, 128])
    )
    assert compare.local_features(empty["orb"], empty["orb"], "orb")["score"] is None


def test_rank_one_points_do_not_become_match():
    points = [[i, i] for i in range(8)]
    desc = {"points": points, "descriptors": np.eye(8, 128).tolist()}
    result = compare.local_features(desc, desc, "sift")
    assert result["score"] is None and result["reason"] == "degenerate_points"


def test_identical_neighbours_remain_tie_and_truth_does_not_enter_scores():
    records = [
        {"key": "o0", "category": "tv", "partition": "enrollment", "identity": "a"},
        {"key": "o1", "category": "tv", "partition": "enrollment", "identity": "b"},
        {"key": "o2", "category": "tv", "partition": "evaluation", "identity": "a"},
    ]
    pairs = [
        {"left": "o0", "right": "o2", "scores": {"yolo": {"score": 1}}},
        {"left": "o1", "right": "o2", "scores": {"yolo": {"score": 1}}},
    ]
    result = evaluator.rank_queries(records, pairs, methods=("yolo",))
    assert result[0]["status"] == "ambiguous"
    assert result[0]["top_keys"] == ["o0", "o1"]
    assert result[0]["assigned_identity"] is None
    assert evaluator.label_pairs(records, pairs)[0]["same_identity"] is True
    assert evaluator.label_pairs(records, pairs)[1]["same_identity"] is False
