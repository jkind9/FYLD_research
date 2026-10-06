"""Deterministic software controls, never physical accuracy evidence."""

import json
from pathlib import Path

import pytest


def test_six_steps_seal_before_scoring(tmp_path, monkeypatch):
    from src.walkthrough import pipeline
    from src.walkthrough.config import Configuration
    from src.walkthrough.validation import ScoreRequest

    calls = []
    for name in ("capture", "depth", "tracking", "surface", "mapping", "objects"):

        def step(*args, _name=name, **kwargs):
            from experiments.shared.runs import write_json
            from src.walkthrough.records import StepResult

            state = kwargs["state"]
            if state.status != "pending":
                return state, None
            run = args[0]
            # Each prior layer must export before the next method runs.
            for previous in calls:
                assert (run.path / f"output/predictions/{previous}.json").is_file()
            calls.append(_name)
            artifact = f"output/predictions/{_name}.json"
            output = {"fixture": _name}
            write_json(run.path / artifact, output)
            return StepResult(_name, "complete", "Fixture saved", artifact), output

        monkeypatch.setattr(getattr(pipeline, name), "run", step)

    def score(*args):
        run = args[0]
        assert (
            json.loads((run.path / "metadata/status.json").read_text())["status"]
            == "running"
        )
        assert (run.path / "metadata/prediction_hashes.json").is_file()
        calls.append("score")
        return {"software_control": True}

    monkeypatch.setattr(pipeline.validation, "score", score)
    result = pipeline.run(
        Configuration(tmp_path, Path.cwd(), tmp_path / "report.json", tmp_path),
        scores=(ScoreRequest("tracking", lambda: "truth", {}),),
    )
    assert calls == [
        "capture",
        "depth",
        "tracking",
        "surface",
        "mapping",
        "objects",
        "score",
    ]
    assert result.complete
    from experiments.shared.runs import verify_run

    assert verify_run(result.path)["status"] == "complete"


@pytest.mark.parametrize("failure", ["unavailable", "failed"])
def test_missing_or_failed_depth_cannot_publish(tmp_path, monkeypatch, failure):
    from experiments.shared.runs import verify_run
    from src.walkthrough import pipeline
    from src.walkthrough.config import Configuration

    calls = []
    from src.walkthrough.records import StepResult

    monkeypatch.setattr(
        pipeline.capture,
        "run",
        lambda *args, **kwargs: (StepResult("capture", "complete", "Fixture"), {}),
    )

    def depth(*args, **kwargs):
        calls.append("depth")
        return StepResult("depth", failure, "deliberate provider failure"), None

    monkeypatch.setattr(pipeline.depth, "run", depth)
    result = pipeline.run(
        Configuration(tmp_path, Path.cwd(), tmp_path / "report.json", tmp_path)
    )
    assert not result.complete
    assert len(result.steps) == 6
    assert result.steps[1].status == failure
    assert all(s.status == "skipped" for s in result.steps[2:])
    assert calls == ["depth"]
    with pytest.raises(ValueError, match="not complete"):
        verify_run(result.path)


def test_prediction_mutation_during_scoring_fails_publication(tmp_path, monkeypatch):
    from src.walkthrough import pipeline
    from src.walkthrough.config import Configuration
    from src.walkthrough.validation import ScoreRequest

    for name in ("capture", "depth", "tracking", "surface", "mapping", "objects"):

        def layer(run, *args, _name=name, **kwargs):
            from experiments.shared.runs import write_json
            from src.walkthrough.records import StepResult

            artifact = f"output/predictions/{_name}.json"
            write_json(run.path / artifact, {})
            return StepResult(_name, "complete", "Fixture", artifact), {}

        monkeypatch.setattr(getattr(pipeline, name), "run", layer)

    def corrupt(run, *args):
        (run.path / "output/predictions/depth.json").write_text("{} changed")
        return {}

    monkeypatch.setattr(pipeline.validation, "score", corrupt)
    with pytest.raises(ValueError, match="Prediction artifacts changed"):
        pipeline.run(
            Configuration(tmp_path, Path.cwd(), tmp_path / "report.json", tmp_path),
            scores=(ScoreRequest("tracking", list, {}),),
        )


@pytest.mark.parametrize(
    "name", ["capture", "depth", "tracking", "surface", "mapping", "objects"]
)
def test_skipped_layer_does_not_access_run_inputs_or_import_methods(name, monkeypatch):
    import importlib

    from src.walkthrough import pipeline
    from src.walkthrough.records import StepResult

    layer = getattr(pipeline, name)
    monkeypatch.setattr(
        importlib, "import_module", lambda *a: pytest.fail("Method imported")
    )
    arguments = {
        "capture": (None, None),
        "depth": (None, None, None),
        "tracking": (None, None, None, None),
        "surface": (None, None, None, None),
        "mapping": (None, None, None),
        "objects": (None, None, None, None, None),
    }
    skipped = StepResult(name, "skipped", "Not requested")
    assert layer.run(*arguments[name], state=skipped) == (skipped, None)
