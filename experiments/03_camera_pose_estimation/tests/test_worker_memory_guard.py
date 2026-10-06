"""Tests for the tracking worker's operating-system memory guard."""

import importlib
import json
import os
import subprocess
import sys

import pytest

runner = importlib.import_module("experiments.03_camera_pose_estimation.src.run")


@pytest.mark.parametrize(
    "reported_limit",
    [None, runner.MEMORY_LIMIT_BYTES - 1],
    ids=["no-process-limit", "wrong-process-limit"],
)
def test_worker_rejects_forged_release_without_configured_job_limit(
    monkeypatch, tmp_path, reported_limit
):
    identity = {"sequence": "fixture"}
    release_path = tmp_path / "release.json"
    release_path.write_text(
        json.dumps(
            {
                "worker_pid": runner.os.getpid(),
                "process_memory_limit_bytes": runner.MEMORY_LIMIT_BYTES,
            }
        ),
        encoding="utf-8",
    )
    dataset_path = tmp_path / "dataset"
    run_root = tmp_path / "runs"
    run_path = run_root / "worker-run"
    archive_calls = []
    execution_calls = []

    monkeypatch.setattr(
        runner.WindowsProcessMemoryLimit,
        "is_current_process_in_job",
        classmethod(lambda cls: True),
    )
    monkeypatch.setattr(
        runner.WindowsProcessMemoryLimit,
        "current_process_memory_limit",
        classmethod(lambda cls: reported_limit),
    )
    monkeypatch.delenv("FYLD_TRACKING_JOB_LIMIT_BYTES", raising=False)
    monkeypatch.setattr(
        runner,
        "_archive_provenance",
        lambda *args: archive_calls.append(args) or identity,
    )
    monkeypatch.setattr(
        runner,
        "execute",
        lambda *args, **kwargs: execution_calls.append((args, kwargs)) or run_path,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tracking",
            "--dataset",
            str(dataset_path),
            "--runs",
            str(run_root),
            "--_worker",
            "--_run-path",
            str(run_path),
            "--_release-file",
            str(release_path),
            "--_provenance-json",
            json.dumps(identity),
            "--_deadline-monotonic",
            str(runner.time.monotonic() + 60),
        ],
    )

    with pytest.raises(SystemExit) as error:
        runner.main()

    assert error.value.code == 2
    assert archive_calls == []
    assert execution_calls == []


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration")
def test_current_process_memory_limit_reads_configured_job_limit(tmp_path):
    limit_bytes = 128 * 1024**2
    release_path = tmp_path / "release"
    code = (
        "import importlib,os,sys,time; "
        "deadline=time.monotonic()+10; "
        "exec('while not os.path.exists(sys.argv[1]) and time.monotonic()<deadline: "
        "time.sleep(0.01)'); "
        "limit=importlib.import_module("
        "'experiments.03_camera_pose_estimation.src.memory_limits')"
        ".WindowsProcessMemoryLimit.current_process_memory_limit(); "
        "print(limit,flush=True); "
        "raise SystemExit(0 if limit==int(sys.argv[2]) else 1)"
    )
    process = subprocess.Popen(
        [sys.executable, "-B", "-u", "-c", code, str(release_path), str(limit_bytes)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    job = None
    try:
        job = runner.WindowsProcessMemoryLimit(process._handle, limit_bytes)
        release_path.write_text("assigned", encoding="utf-8")
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr
        assert stdout.strip() == str(limit_bytes)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if job is not None:
            job.close()
