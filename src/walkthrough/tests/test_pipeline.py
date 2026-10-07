"""Check orchestration, publication and dependency failures independently of models."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from experiments.shared.runs import verify_run, write_json
from src.walkthrough import pipeline
from src.walkthrough.config import STEP_NAMES, PipelineSpec
from src.walkthrough.records import StepResult
from src.walkthrough.steps.capture import PhoneExport
from src.walkthrough.tests.providers import with_controls
from src.walkthrough.validation import ScoreRequest


def _spec(tmp_path: Path) -> PipelineSpec:
    return with_controls(
        PipelineSpec(
            tmp_path / "runs",
            Path.cwd(),
            PhoneExport(tmp_path / "report.json", tmp_path),
        )
    )


def _stub_layers(monkeypatch: Any, calls: list[str]) -> None:
    for name in STEP_NAMES:

        def layer(
            run: Any, *args: Any, _name: str = name, **kwargs: Any
        ) -> tuple[StepResult, dict]:
            for previous in calls:
                assert (run.path / f"output/predictions/{previous}.json").is_file()
            calls.append(_name)
            artifact = f"output/predictions/{_name}.json"
            output = {"fixture": _name}
            write_json(run.path / artifact, output)
            return StepResult(
                _name, "complete", "Fixture saved", _name, 1, artifact
            ), output

        monkeypatch.setattr(getattr(pipeline, name), "run", layer)
        monkeypatch.setattr(getattr(pipeline, name), "validate", lambda *args: None)
        monkeypatch.setattr(pipeline.visualization, name, lambda *args: None)


def test_six_steps_seal_before_scoring(tmp_path: Path, monkeypatch: Any) -> None:
    calls: list[str] = []
    _stub_layers(monkeypatch, calls)

    def score(run_path: Path, steps: Any, requests: Any) -> dict:
        assert (
            json.loads((run_path / "metadata/status.json").read_text())["status"]
            == "running"
        )
        assert (run_path / "metadata/prediction_hashes.json").is_file()
        calls.append("score")
        return {"control": True}

    monkeypatch.setattr(pipeline.validation, "score", score)
    result = pipeline.run(
        _spec(tmp_path), scores=(ScoreRequest("tracking", lambda: "truth", {}),)
    )
    assert calls == [*STEP_NAMES, "score"]
    assert result.complete and not result.is_measurement
    assert verify_run(result.path)["status"] == "complete"


@pytest.mark.parametrize("failure", ["unavailable", "failed"])
def test_missing_or_failed_depth_cannot_publish(
    tmp_path: Path, monkeypatch: Any, failure: str
) -> None:
    calls: list[str] = []
    _stub_layers(monkeypatch, calls)

    def failed_depth(*args: Any, **kwargs: Any) -> tuple[StepResult, None]:
        return StepResult("depth", failure, "deliberate provider failure"), None

    monkeypatch.setattr(pipeline.depth, "run", failed_depth)
    result = pipeline.run(_spec(tmp_path))
    assert not result.complete
    assert len(result.steps) == 6
    assert result.steps[1].status == failure
    assert all(step.status == "skipped" for step in result.steps[2:])
    assert calls == ["capture"]
    with pytest.raises(ValueError, match="not complete"):
        verify_run(result.path)


def test_prediction_mutation_during_scoring_fails_publication(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _stub_layers(monkeypatch, [])

    def corrupt(run_path: Path, *args: Any) -> dict:
        (run_path / "output/predictions/depth.json").write_text("{} changed")
        return {}

    monkeypatch.setattr(pipeline.validation, "score", corrupt)
    with pytest.raises(ValueError, match="Prediction artifacts changed"):
        pipeline.run(_spec(tmp_path), scores=(ScoreRequest("tracking", list, {}),))
    run_path = next((tmp_path / "runs").iterdir())
    assert (
        json.loads((run_path / "metadata/status.json").read_text())["status"]
        == "failed"
    )
    assert not (run_path / "metadata/manifest.json").exists()


def test_skipped_layer_is_never_called(tmp_path: Path, monkeypatch: Any) -> None:
    calls: list[str] = []
    _stub_layers(monkeypatch, calls)
    for name in STEP_NAMES[1:]:
        monkeypatch.setattr(
            getattr(pipeline, name),
            "run",
            lambda *args: pytest.fail("Skipped layer called"),
        )
    result = pipeline.run(replace(_spec(tmp_path), requested=("capture",)))
    assert calls == ["capture"]
    assert [(row.status, row.reason) for row in result.steps[1:]] == [
        ("skipped", "Not requested")
    ] * 5
