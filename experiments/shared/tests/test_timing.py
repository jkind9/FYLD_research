"""Throughput uses explicit counts and monotonic elapsed time."""

import json

import pytest

from experiments.shared.runs import Run, verify_run
from experiments.shared.timing import TimingLedger


def clock(values):
    iterator = iter(values)
    return lambda: next(iterator)


def test_weighted_stage_fps_and_separate_observation_count():
    ledger = TimingLedger(clock([0, 1, 1, 4]))
    with ledger.measure("odometry_pairs", frames=1):
        pass
    with ledger.measure("odometry_pairs", frames=1):
        pass
    ledger.set_processed_frames(3)
    result = ledger.summary(10, completed=True)
    assert result["stages"]["odometry_pairs"]["fps"] == 0.5
    assert result["stages"]["odometry_pairs"]["elapsed_seconds"] == 4
    assert result["stages"]["odometry_pairs"]["frames"] == 2
    assert result["processed_frames"] == 3
    assert result["end_to_end_fps"] == 0.3
    assert [row["fps"] for row in result["samples"]] == [1, 1 / 3]


def test_exception_visible_and_excluded_from_successful_throughput():
    ledger = TimingLedger(clock([0, 2, 2, 5]))
    with pytest.raises(ValueError, match="injected"), ledger.measure("load", frames=10):
        raise ValueError("injected")
    with ledger.measure("load", frames=3):
        pass
    result = ledger.summary(8, completed=True)
    assert result["samples"][0]["status"] == "failed"
    assert result["samples"][0]["fps"] is None
    assert result["stages"]["load"]["failed_samples"] == 1
    assert result["stages"]["load"]["frames"] == 3
    assert result["stages"]["load"]["fps"] == 1


@pytest.mark.parametrize("frames", [-1, True, 1.5, "2"])
def test_invalid_counts_rejected(frames):
    ledger = TimingLedger()
    with pytest.raises(ValueError):
        ledger.set_processed_frames(frames)
    with pytest.raises(ValueError), ledger.measure("stage", frames=frames):
        pass


def test_unknown_counts_and_zero_time_do_not_invent_throughput():
    ledger = TimingLedger(clock([0, 0, 0, 1]))
    with ledger.measure("zero", frames=1):
        pass
    with ledger.measure("unknown"):
        pass
    result = ledger.summary(0, completed=True)
    assert result["end_to_end_fps"] is None
    assert result["stages"]["zero"]["fps"] is None
    assert result["stages"]["unknown"]["fps"] is None
    assert result["processed_frames"] is None


@pytest.mark.parametrize("times", [[2, 1], [0, float("nan")]])
def test_invalid_clock_elapsed_rejected(times):
    ledger = TimingLedger(clock(times))
    with pytest.raises(ValueError), ledger.measure("stage", frames=1):
        pass


def test_summary_refuses_active_scope_and_blank_stage():
    ledger = TimingLedger(clock([0, 1]))
    with pytest.raises(ValueError), ledger.measure(" ", frames=1):
        pass
    with ledger.measure("stage", frames=1), pytest.raises(ValueError, match="active"):
        ledger.summary(1, completed=True)


def test_run_publishes_timing_before_manifest(tmp_path, monkeypatch):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    with Run(tmp_path / "runs", tmp_path, {}) as run:
        run.set_processed_frames(2)
        with run.measure("load", frames=2):
            pass
    timing = json.loads((run.path / "metadata/timing.json").read_text())
    assert timing["processed_frames"] == 2
    assert timing["end_to_end_fps"] == 2 / timing["elapsed_seconds"]
    assert timing["samples"][0]["stage"] == "load"
    assert timing["elapsed_seconds"] >= 0
    assert "started_utc" in timing and "ended_utc" in timing
    assert verify_run(run.path)["status"] == "complete"
    with pytest.raises(ValueError, match="running"):
        run.set_processed_frames(3)


def test_failed_run_keeps_timing_but_has_no_end_to_end_fps(tmp_path, monkeypatch):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    with pytest.raises(RuntimeError, match="injected"), Run(
        tmp_path / "runs", tmp_path, {}
    ) as run:
        run.set_processed_frames(2)
        with run.measure("load", frames=2):
            raise RuntimeError("injected")
    timing = json.loads((run.path / "metadata/timing.json").read_text())
    assert timing["end_to_end_fps"] is None
    assert timing["samples"][0]["status"] == "failed"
    assert (
        json.loads((run.path / "metadata/status.json").read_text())["status"]
        == "failed"
    )
    with pytest.raises(ValueError, match="not complete"):
        verify_run(run.path)


def test_legacy_run_without_wrapper_has_no_invented_frame_count(tmp_path, monkeypatch):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    with Run(tmp_path / "runs", tmp_path, {}) as run:
        pass
    timing = json.loads((run.path / "metadata/timing.json").read_text())
    assert timing["processed_frames"] is None
    assert timing["end_to_end_fps"] is None
    assert timing["samples"] == []


def test_deferred_scope_cannot_start_after_run_completion(tmp_path, monkeypatch):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    with Run(tmp_path / "runs", tmp_path, {}) as run:
        deferred = run.measure("load", frames=1)
    with pytest.raises(ValueError, match="running"), deferred:
        pass
    assert verify_run(run.path)["status"] == "complete"


def test_timing_write_failure_cannot_leave_run_running(tmp_path, monkeypatch):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    original_write = runs.write_json

    def refuse_timing(path, data):
        if path.name == "timing.json":
            raise OSError("injected timing write")
        original_write(path, data)

    monkeypatch.setattr(runs, "write_json", refuse_timing)
    with pytest.raises(OSError, match="timing write"), Run(
        tmp_path / "runs", tmp_path, {}
    ) as run:
        pass
    assert (
        json.loads((run.path / "metadata/status.json").read_text())["status"]
        == "failed"
    )


def test_unclosed_scope_cannot_leave_run_running(tmp_path, monkeypatch):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    with pytest.raises(ValueError, match="active"), Run(
        tmp_path / "runs", tmp_path, {}
    ) as run:
        scope = run.measure("unclosed", frames=1)
        scope.__enter__()
    assert (
        json.loads((run.path / "metadata/status.json").read_text())["status"]
        == "failed"
    )
    scope.__exit__(None, None, None)


@pytest.mark.parametrize("frames, seconds", [(1, 5e-324), (10**400, 1)])
def test_unrepresentable_fps_is_unavailable(frames, seconds):
    ledger = TimingLedger(clock([0, seconds]))
    ledger.set_processed_frames(frames)
    with ledger.measure("stage", frames=frames):
        pass
    result = ledger.summary(seconds, completed=True)
    assert result["end_to_end_fps"] is None
    assert result["stages"]["stage"]["fps"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("output_relative", [".", "experiments", "experiments/example"])
def test_source_snapshot_survives_output_root_containing_source(
    tmp_path, monkeypatch, output_relative
):
    from experiments.shared import runs

    monkeypatch.setattr(runs, "_git", lambda *_: "test-repository")
    source = tmp_path / "experiments/example/module.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    for _ in range(2):
        with Run(tmp_path / output_relative, tmp_path, {}) as run:
            pass
        receipt = json.loads((run.path / "metadata/source_snapshot.json").read_text())
        assert list(receipt["files"]) == ["experiments/example/module.py"]
        assert verify_run(run.path)["status"] == "complete"
