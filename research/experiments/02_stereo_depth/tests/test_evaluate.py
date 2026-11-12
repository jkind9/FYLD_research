"""TUM selection and frame-ID scoring contracts."""

import importlib
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

dataset = importlib.import_module("experiments.02_stereo_depth.dataset")
evaluation = importlib.import_module("experiments.02_stereo_depth.evaluate")


@pytest.fixture
def selection():
    frames = (
        _frame("0", np.array([[1.0, 2.0], [3.0, 4.0]])),
        _frame("10", np.array([[2.0, 3.0], [4.0, 5.0]])),
    )
    return dataset.TumDepthSelection("fixture", Path("fixture"), 11, 10, frames)


@pytest.mark.parametrize(
    "sequence_name",
    ["rgbd_dataset_freiburg1_xyz", "rgbd_dataset_freiburg1_desk"],
)
def test_both_tum_sequence_fixtures_sample_every_tenth_match(
    monkeypatch, sequence_name
):
    root = Path(sequence_name)
    rows = [
        {
            "frame_id": str(index),
            "timestamp_s": index * 0.033,
            "depth_timestamp_s": index * 0.033,
            "rgb": f"rgb/{index:06}.png",
            "depth": f"depth/{index:06}.png",
        }
        for index in range(21)
    ]
    fake_frames = {
        row["frame_id"]: SimpleNamespace(
            frame_id=row["frame_id"],
            timestamp_s=row["timestamp_s"],
            colour=np.zeros((480, 640, 3), dtype=np.uint8),
            depth=np.ones((480, 640), dtype=np.float64),
            valid=np.ones((480, 640), dtype=bool),
        )
        for row in rows
    }
    calls = []
    monkeypatch.setattr(
        dataset._tum_reader,
        "associations",
        lambda actual_root, count: (
            calls.append((actual_root, count))
            or (rows[:1] if count == 1 else rows),
            {"matched_rows": 21},
        ),
    )
    monkeypatch.setattr(
        dataset._tum_reader,
        "load_frame",
        lambda actual_root, row: (
            calls.append(row["frame_id"]) or fake_frames[row["frame_id"]]
        ),
    )

    chosen = dataset.select_tum_frames(root)

    assert chosen.matched_pair_count == 21
    assert [frame.frame_id for frame in chosen.frames] == ["0", "10", "20"]
    assert all(frame.colour.shape == (480, 640, 3) for frame in chosen.frames)
    assert all(frame.reference_valid.all() for frame in chosen.frames)
    assert chosen.sequence == sequence_name
    assert calls[:2] == [(root, 1), (root, 21)]
    assert calls[2:] == ["0", "10", "20"]


def test_prediction_ids_align_independently_of_mapping_order(selection):
    predictions = {
        "10": selection.frames[1].reference_depth_m.copy(),
        "0": selection.frames[0].reference_depth_m.copy(),
    }

    result = evaluation.evaluate_predictions(selection, predictions, "metric_depth")

    assert result["frame_ids"] == ["0", "10"]
    assert [row["frame_id"] for row in result["metric"]["per_frame"]] == [
        "0",
        "10",
    ]
    assert result["metric"]["aggregate"]["overall"]["abs_rel"] == 0.0


def test_swapped_prediction_arrays_score_against_wrong_frame_references(selection):
    predictions = {
        "0": selection.frames[1].reference_depth_m.copy(),
        "10": selection.frames[0].reference_depth_m.copy(),
    }

    result = evaluation.evaluate_predictions(selection, predictions, "metric_depth")

    assert result["metric"]["per_frame"][0]["overall"]["abs_rel"] > 0
    assert result["metric"]["per_frame"][1]["overall"]["abs_rel"] > 0


@pytest.mark.parametrize(
    "predictions,expected",
    [({"0": np.ones((2, 2))}, "missing=['10']"),
     (
         {"0": np.ones((2, 2)), "10": np.ones((2, 2)), "extra": np.ones((2, 2))},
         "extra=['extra']",
     )],
)
def test_rejects_missing_or_extra_prediction_frame_ids(
    selection, predictions, expected
):
    with pytest.raises(ValueError, match=re.escape(expected)):
        evaluation.evaluate_predictions(selection, predictions, "metric_depth")


def test_relative_predictions_get_shape_view_but_no_raw_metric_claim(selection):
    predictions = {
        frame.frame_id: frame.reference_depth_m.copy()
        for frame in selection.frames
    }

    result = evaluation.evaluate_predictions(selection, predictions, "relative_depth")

    assert result["metric"]["available"] is False
    assert result["metric"]["aggregate"] is None
    shape = result["reference_aligned_shape"]
    assert shape["aggregate"]["view"] == "reference_aligned_shape"
    assert all(row["overall"]["abs_rel"] < 1e-10 for row in shape["per_frame"])


def test_inverse_depth_predictions_align_in_inverse_space(selection):
    predictions = {
        frame.frame_id: 1.0 / frame.reference_depth_m
        for frame in selection.frames
    }

    result = evaluation.evaluate_predictions(
        selection, predictions, "relative_inverse_depth"
    )

    assert result["metric"]["available"] is False
    assert result["reference_aligned_shape"]["aggregate"]["overall"]["abs_rel"] < 1e-10
    assert result["reference_aligned_shape"]["aggregate"]["overall"]["rmse_m"] < 1e-10


def test_native_prediction_grid_must_match_tum_reference(selection):
    predictions = {
        "0": np.ones((1, 2)),
        "10": np.ones((2, 2)),
    }

    with pytest.raises(ValueError, match="grid"):
        evaluation.evaluate_predictions(selection, predictions, "relative_depth")


def test_metric_view_keeps_scale_error_and_shape_view_names_reference_fit(selection):
    predictions = {
        frame.frame_id: 2.0 * frame.reference_depth_m for frame in selection.frames
    }

    result = evaluation.evaluate_predictions(selection, predictions, "metric_depth")

    assert result["metric"]["aggregate"]["overall"]["abs_rel"] == 1.0
    assert result["reference_aligned_shape"]["aggregate"]["view"] == (
        "reference_aligned_shape"
    )


def _frame(frame_id, reference_depth_m):
    shape = reference_depth_m.shape
    return dataset.TumDepthFrame(
        frame_id=frame_id,
        timestamp_s=float(frame_id),
        colour=np.zeros((*shape, 3), dtype=np.uint8),
        reference_depth_m=reference_depth_m,
        reference_valid=np.ones(shape, dtype=bool),
    )
