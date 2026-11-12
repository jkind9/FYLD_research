"""Contracts for the isolated support-association latency report."""

import importlib

import pytest

run = importlib.import_module(
    "experiments.06_object_recognition.experiments.08_spatial_uncertainty_latency.run"
)


def test_decision_signature_ignores_only_timing_fields():
    before = [
        {
            "observation_id": "cup-1",
            "decision": "matched",
            "object_id": "object-0001",
            "processing_time_ms": 10.0,
        }
    ]
    after = [
        {
            "observation_id": "cup-1",
            "decision": "matched",
            "object_id": "object-0001",
            "processing_time_ms": 2.0,
        }
    ]

    assert run.decision_signature(before) == run.decision_signature(after)
    after[0]["object_id"] = "object-0002"
    assert run.decision_signature(before) != run.decision_signature(after)


def test_module_loader_registers_dataclass_modules_before_execution():
    module = run._load_module(run.TASK48_ASSOCIATION, "task49_test_baseline_loader")

    assert module.BoxObservation.__name__ == "BoxObservation"


def test_latency_summary_reports_median_and_per_proposal_cost():
    summary = run.summarize_latency([10.0, 20.0, 30.0], proposals=10)

    assert summary == {
        "repeats": 3,
        "median_total_ms": 20.0,
        "median_ms_per_proposal": 2.0,
    }


@pytest.mark.parametrize(
    ("samples", "proposals"),
    [([], 1), ([1.0], 0), ([0.0], 1), ([-1.0], 1)],
)
def test_latency_summary_rejects_missing_or_nonpositive_measurements(samples, proposals):
    with pytest.raises(ValueError, match="positive"):
        run.summarize_latency(samples, proposals)


@pytest.mark.parametrize("sample", [float("nan"), float("inf"), float("-inf")])
def test_latency_summary_rejects_nonfinite_measurements(sample):
    with pytest.raises(ValueError, match="finite"):
        run.summarize_latency([sample], proposals=1)
