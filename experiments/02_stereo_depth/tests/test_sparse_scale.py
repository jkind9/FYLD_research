"""Contracts for fitting depth scale from a few reference points and scoring every pixel."""

import importlib

import numpy as np
import pytest

geometry = importlib.import_module("experiments.02_stereo_depth.geometry")
scoring = importlib.import_module("experiments.02_stereo_depth.scoring")
sparse_scale = importlib.import_module("experiments.02_stereo_depth.sparse_scale")


def _scene(height=20, width=30):
    rows, cols = np.mgrid[0:height, 0:width]
    depth_m = 0.6 + 0.05 * rows + 0.02 * cols
    valid = np.ones_like(depth_m, dtype=bool)
    valid[0, :5] = False  # sensor holes must never be chosen or scored
    return depth_m, valid


def test_ten_point_inverse_depth_fit_recovers_geometry_and_scores_every_valid_pixel():
    depth_m, valid = _scene()
    raw_inverse = 2.5 / depth_m + 0.7  # unknown scale and shift in inverse-depth space
    eligible = geometry.alignment_fit_pixels(
        raw_inverse, "relative_inverse_depth", depth_m, valid
    )
    fit_mask = sparse_scale.choose_fit_pixels(eligible, 10, np.random.default_rng(3))

    result = scoring.score_sparse_fit(
        raw_inverse, "relative_inverse_depth", depth_m, valid, fit_mask
    )

    assert np.count_nonzero(fit_mask) == 10
    assert result["view"] == "sparse_point_fit"
    assert result["fit_pixels"] == 10
    assert result["overall"]["scored_pixels"] == np.count_nonzero(valid)
    assert result["overall"]["abs_rel"] < 1e-6


def test_scale_only_metric_fit_recovers_a_known_factor_without_shift():
    depth_m, valid = _scene()
    raw_metric = 1.37 * depth_m
    fit_mask = np.zeros_like(valid)
    fit_mask[5, 5] = fit_mask[10, 20] = True

    scale, shift = geometry.fit_native_alignment(
        raw_metric, "metric_depth", depth_m, fit_mask, scale_only=True
    )

    assert scale == pytest.approx(1 / 1.37, abs=1e-12)
    assert shift == 0.0


def test_scale_only_is_refused_for_relative_conventions():
    depth_m, valid = _scene()
    with pytest.raises(ValueError, match="scale-only"):
        geometry.fit_native_alignment(
            1 / depth_m, "relative_inverse_depth", depth_m, valid, scale_only=True
        )


def test_fewer_than_two_fit_pixels_raises():
    depth_m, valid = _scene()
    fit_mask = np.zeros_like(valid)
    fit_mask[3, 3] = True
    with pytest.raises(ValueError, match="two"):
        scoring.score_sparse_fit(depth_m, "relative_depth", depth_m, valid, fit_mask)


def test_fit_pixels_outside_the_valid_reference_are_refused():
    depth_m, valid = _scene()
    fit_mask = np.zeros_like(valid)
    fit_mask[0, 0] = fit_mask[5, 5] = True  # (0, 0) is a sensor hole
    with pytest.raises(ValueError, match="valid reference"):
        scoring.score_sparse_fit(depth_m, "relative_depth", depth_m, valid, fit_mask)


def test_point_choice_is_deterministic_and_stays_inside_eligible_pixels():
    _, valid = _scene()
    first = sparse_scale.choose_fit_pixels(valid, 50, np.random.default_rng([2, 7]))
    second = sparse_scale.choose_fit_pixels(valid, 50, np.random.default_rng([2, 7]))
    other_seed = sparse_scale.choose_fit_pixels(valid, 50, np.random.default_rng([3, 7]))

    np.testing.assert_array_equal(first, second)
    assert not np.array_equal(first, other_seed)
    assert not np.any(first & ~valid)


def test_requesting_more_points_than_eligible_pixels_raises():
    eligible = np.zeros((4, 4), dtype=bool)
    eligible[0, :3] = True
    with pytest.raises(ValueError, match="only 3"):
        sparse_scale.choose_fit_pixels(eligible, 10, np.random.default_rng(0))


def test_full_frame_alignment_is_unchanged_by_the_fit_split():
    depth_m, valid = _scene()
    raw = np.log(depth_m) * 0.8 - 0.2

    aligned, aligned_valid, non_positive = geometry.align_shape_to_metric(
        raw, "affine_invariant_log_depth", depth_m, valid
    )

    np.testing.assert_allclose(aligned[valid], depth_m[valid], rtol=1e-9)
    np.testing.assert_array_equal(aligned_valid, valid)
    assert non_positive == 0.0


def test_a_recording_without_saved_results_is_recorded_as_not_run(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    depth_m, valid = _scene()
    frame = SimpleNamespace(frame_id="f0", reference_depth_m=depth_m, reference_valid=valid)
    selections = {
        name: SimpleNamespace(sequence=name, frames=(frame,)) for name in ("done", "missing")
    }
    monkeypatch.setattr(sparse_scale, "SEQUENCE_NAMES", ("done", "missing"))
    monkeypatch.setattr(sparse_scale, "_resolve_sequence_root", lambda root, name: name)
    monkeypatch.setattr(sparse_scale, "select_tum_frames", lambda name, stride: selections[name])
    monkeypatch.setattr(sparse_scale, "POINT_COUNTS", (10,))
    monkeypatch.setattr(sparse_scale, "SEEDS", (0,))
    monkeypatch.setattr(
        sparse_scale,
        "evaluate_predictions",
        lambda selection, predictions, convention: {
            "reference_aligned_shape": {"aggregate": {"overall": {"abs_rel": 0.0}}},
            "metric": {"available": False},
        },
    )
    method_dir = tmp_path / "method"
    (method_dir / "done").mkdir(parents=True)
    np.save(method_dir / "done" / "f0.npy", 1.0 / depth_m)
    (method_dir / "done" / "results.json").write_text(
        json.dumps({"convention": "relative_inverse_depth", "frames": [{"frame_id": "f0", "prediction_file": "f0.npy"}]})
    )
    output = tmp_path / "sparse.json"

    assert sparse_scale.main(["--set", f"m={method_dir}", "--output", str(output)]) == 0

    rows = json.loads(output.read_text())["results"]
    assert [row["sequence"] for row in rows] == ["done", "missing"]
    assert "point_counts" in rows[0]
    assert rows[1]["not_run"] == "no results.json for this recording"
