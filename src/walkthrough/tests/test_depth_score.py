"""Depth predictions scored against the recording's own sensor depth, after sealing."""

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.shared.runs import write_json
from src.walkthrough import validation
from src.walkthrough.records import StepResult
from src.walkthrough.steps.contracts import DepthPrediction

SHAPE = (4, 5)
TRUE_M = np.linspace(0.5, 3.5, SHAPE[0] * SHAPE[1]).reshape(SHAPE)


def _run(tmp_path: Path, predicted: list[np.ndarray]) -> tuple[StepResult, ...]:
    frames, rows = [], []
    for index, depth_m in enumerate(predicted):
        relative = f"output/predictions/depth/{index:06d}.npz"
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        np.savez(tmp_path / relative, depth=depth_m, valid=np.isfinite(depth_m))
        frames.append({"frame_id": f"f{index}", "arrays": relative})
        rows.append({"frame_id": f"f{index}", "timestamp_s": 10.0 + index})
    write_json(tmp_path / "output/predictions/depth.json", {"frames": frames, "control": None})
    write_json(tmp_path / "output/predictions/capture.json", {"frames": rows})
    return (StepResult("depth", "complete", "saved", "fixture", len(frames), "output/predictions/depth.json"),)


def _recorded(seen: list):
    """Stands in for RecordedSensorDepth: returns the true depth and records what it was asked."""

    def read(frames, *, run):
        for frame in frames:
            seen.append((frame.frame_id, frame.timestamp_s))
            yield DepthPrediction(frame.frame_id, TRUE_M, np.ones(SHAPE, dtype=bool))

    return read


def test_identical_depth_scores_zero_and_frames_are_paired_by_timestamp(tmp_path):
    seen: list = []
    steps = _run(tmp_path, [TRUE_M.copy(), TRUE_M.copy()])

    scores = validation.score(
        tmp_path, steps, (validation.ScoreRequest("depth", lambda: _recorded(seen)),)
    )

    result = scores["depth"]["result"]
    assert scores["depth"]["status"] == "scored"
    assert result["overall"]["abs_rel"] == pytest.approx(0.0)
    assert [row["frame_id"] for row in result["per_frame"]] == ["f0", "f1"]
    assert seen == [("f0", 10.0), ("f1", 11.0)]


def test_per_frame_error_matches_a_known_bias(tmp_path):
    biased = TRUE_M * 1.25  # every pixel 25% too far
    steps = _run(tmp_path, [TRUE_M.copy(), biased])

    result = validation.score(
        tmp_path, steps, (validation.ScoreRequest("depth", lambda: _recorded([])),)
    )["depth"]["result"]

    first, second = result["per_frame"]
    assert first["abs_rel"] == pytest.approx(0.0)
    assert second["abs_rel"] == pytest.approx(0.25)
    assert result["overall"]["abs_rel"] == pytest.approx(0.125)
    assert set(second["distance_bands"]) == {"0-1m", "1-2m", "2-4m"}


def test_missing_reference_for_a_frame_fails_scoring_loudly(tmp_path):
    steps = _run(tmp_path, [TRUE_M.copy()])

    def no_reference(frames, *, run):
        for frame in frames:
            raise ValueError(f"{frame.frame_id}: No sensor depth within 0.02 s")
            yield  # pragma: no cover

    with pytest.raises(ValueError, match="No sensor depth"):
        validation.score(tmp_path, steps, (validation.ScoreRequest("depth", lambda: no_reference),))


def test_depth_score_is_unavailable_when_depth_did_not_complete(tmp_path):
    steps = (StepResult("depth", "unavailable", "no method"),)

    scores = validation.score(
        tmp_path, steps, (validation.ScoreRequest("depth", lambda: pytest.fail("loaded")),)
    )

    assert scores["depth"]["status"] == "unavailable"
    assert "no method" in scores["depth"]["reason"]
    json.dumps(scores)  # saved as JSON


def test_each_frame_reports_its_scale_against_the_reference(tmp_path):
    steps = _run(tmp_path, [TRUE_M * 1.3, TRUE_M * 0.8 + 0.1])

    rows = validation.score(
        tmp_path, steps, (validation.ScoreRequest("depth", lambda: _recorded([])),)
    )["depth"]["result"]["per_frame"]

    assert rows[0]["scale_ratio"] == pytest.approx(1.3)  # 30% too far
    assert rows[0]["fit_scale"] == pytest.approx(1 / 1.3)
    assert rows[0]["fit_shift"] == pytest.approx(0.0, abs=1e-9)
    assert rows[0]["fitted_abs_rel"] == pytest.approx(0.0, abs=1e-9)
    assert rows[1]["fit_scale"] == pytest.approx(1 / 0.8)
    assert rows[1]["fit_shift"] == pytest.approx(-0.1 / 0.8)
    assert rows[1]["fitted_abs_rel"] == pytest.approx(0.0, abs=1e-9)


def test_a_frame_with_no_overlap_gets_empty_scale_fields_and_scores_still_save(tmp_path):
    steps = _run(tmp_path, [np.full(SHAPE, np.nan), TRUE_M.copy()])

    scores = validation.score(
        tmp_path, steps, (validation.ScoreRequest("depth", lambda: _recorded([])),)
    )

    empty = scores["depth"]["result"]["per_frame"][0]
    assert empty["scale_ratio"] is None
    assert empty["fit_scale"] is None and empty["fit_shift"] is None
    assert empty["fitted_abs_rel"] is None
    write_json(tmp_path / "scores.json", scores)  # NaN would make this raise
