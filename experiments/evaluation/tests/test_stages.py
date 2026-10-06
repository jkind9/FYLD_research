"""The identity report calls the public experiment validation owner."""

import importlib

from experiments.evaluation.stages import identity
from experiments.evaluation.tests import fixtures


def test_identity_report_uses_public_validation_without_private_runner(tmp_path, monkeypatch):
    fixtures.identity_run(tmp_path)
    validation = importlib.import_module(
        "experiments.06_object_recognition.experiments.04_geometry_identity.validation"
    )
    original = validation.score_identity
    calls = []

    def record_score(decisions, truth, observations):
        calls.append(len(decisions))
        return original(decisions, truth, observations)

    def refuse_private_score(*args):
        raise AssertionError("Report called the historical runner's private scorer")

    monkeypatch.setattr(validation, "score_identity", record_score)
    monkeypatch.setattr(fixtures.identity_run_module, "_score", refuse_private_score)
    result = identity.identity_section(tmp_path, dataset="fixture")
    assert calls == [3, 3]
    assert [row["condition"] for row in result["rows"]] == ["good", "merged"]
