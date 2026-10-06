"""Supervised tracking-run boundary tests."""

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from experiments.datasets.acquisition import sha256

supervisor = importlib.import_module(
    "experiments.03_camera_pose_estimation.src.supervisor"
)


def _write_complete_run(run_path: Path) -> None:
    from experiments.datasets.acquisition import sha256
    from experiments.shared.runs import _inventory, write_json

    metadata = run_path / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    (run_path / "output").mkdir()
    write_json(metadata / "configuration.json", {"original": True})
    write_json(metadata / "timing.json", {"elapsed_seconds": 0.19})
    write_json(run_path / "output/metrics.json", {"rmse_m": 0.01})
    manifest_path = metadata / "manifest.json"
    write_json(manifest_path, {"schema_version": 1, "files": _inventory(run_path)})
    write_json(
        metadata / "status.json",
        {"status": "complete", "manifest_sha256": sha256(manifest_path)},
    )


def test_final_memory_limit_event_rejects_complete_zero_exit_run(tmp_path):
    class Process:
        pid = 123457
        _handle = 8
        returncode = None

        def __init__(self, run_path):
            self.run_path = run_path

        def poll(self):
            if self.returncode is None:
                _write_complete_run(self.run_path)
                self.returncode = 0
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            self.returncode = -9

    class Job:
        def peak_process_memory(self):
            return 700_000_000

        def poll_memory_limit(self):
            return True

        def close(self):
            pass

    run_paths = []

    def launch(command, **kwargs):
        worker_args = json.loads(command[-1])
        run_path = Path(worker_args[worker_args.index("--_run-path") + 1])
        run_paths.append(run_path)
        return Process(run_path)

    with pytest.raises(RuntimeError, match="rejected by the supervisor"):
        supervisor.supervise(
            dataset_path=tmp_path / "rgbd_dataset_freiburg1_xyz",
            run_root=tmp_path / "runs",
            frames=792,
            sequence_identity={"status": "checked"},
            repo=tmp_path,
            process_factory=launch,
            memory_limit_factory=lambda *_: Job(),
        )

    run_path = run_paths[0]
    supervisor.verify_run(run_path)
    rejection = json.loads(
        run_path.with_name(run_path.name + ".supervisor.json").read_text()
    )
    assert rejection["status"] == "complete_artifact_rejected"
    assert rejection["reason"] == "Worker received a process-memory limit notification"
    assert rejection["worker_exit_code"] == 0
    assert rejection["memory_limit_event_detected"] is True
    assert rejection["run_manifest_sha256"] == sha256(
        run_path / "metadata/manifest.json"
    )
    assert rejection["run_status_sha256"] == sha256(
        run_path / "metadata/status.json"
    )


def test_supervisor_timeout_writes_durable_failed_receipt_without_evaluation(tmp_path):
    class Clock:
        now = 0.0

        def __call__(self):
            return self.now

        def sleep(self, duration):
            self.now += duration

    class Process:
        pid = 123456
        _handle = 7
        returncode = None

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            self.returncode = -9

    class Job:
        def peak_process_memory(self):
            return 1024

        def poll_memory_limit(self):
            return False

        def close(self):
            pass

    clock = Clock()
    process = Process()
    commands = []

    def launch(command, **kwargs):
        commands.append(command)
        return process

    with pytest.raises(RuntimeError, match="incomplete receipt") as error:
        supervisor.supervise(
            dataset_path=tmp_path / "rgbd_dataset_freiburg1_xyz",
            run_root=tmp_path / "runs",
            frames=792,
            sequence_identity={"status": "checked"},
            repo=tmp_path,
            process_factory=launch,
            memory_limit_factory=lambda *_: Job(),
            monotonic=clock,
            sleep=clock.sleep,
            poll_interval_s=0.1,
            wall_clock_limit_s=0.2,
        )

    run_path = Path(str(error.value).split(": ", maxsplit=1)[1])
    status = json.loads((run_path / "metadata/status.json").read_text())
    receipt = json.loads((run_path / "metadata/supervisor.json").read_text())
    assert status["status"] == "failed"
    assert "wall-clock limit" in status["error"]
    assert receipt["wall_clock_limit_seconds"] == supervisor.WALL_CLOCK_LIMIT_S
    assert (
        json.loads((run_path / "metadata/configuration.json").read_text())[
            "execution_limits"
        ]["process_memory_bytes"]
        == 2 * 1024**3
    )
    assert not (run_path / "input/evaluation/groundtruth.txt").exists()
    assert not (run_path / "output/metrics.json").exists()
    assert not list((tmp_path / "runs").glob("*.supervisor-launch.json"))
    assert commands[0][1] == "-c"
    bootstrap = commands[0][2]
    assert bootstrap.index("while not os.path.exists") < bootstrap.index(
        "runpy.run_module"
    )
    with pytest.raises(ValueError, match="not complete"):
        importlib.import_module("experiments.shared.runs").verify_run(run_path)


def test_supervisor_fails_closed_if_process_memory_limit_cannot_be_installed(
    tmp_path,
):
    class Process:
        pid = 123457
        _handle = 8
        returncode = None

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            self.returncode = -9

    process = Process()

    def no_memory_limit(*_):
        raise OSError("job assignment denied")

    with pytest.raises(RuntimeError, match="incomplete receipt") as error:
        supervisor.supervise(
            dataset_path=tmp_path / "rgbd_dataset_freiburg1_desk",
            run_root=tmp_path / "runs",
            frames=573,
            sequence_identity={"status": "checked"},
            repo=tmp_path,
            process_factory=lambda *args, **kwargs: process,
            memory_limit_factory=no_memory_limit,
        )

    run_path = Path(str(error.value).split(": ", maxsplit=1)[1])
    status = json.loads((run_path / "metadata/status.json").read_text())
    assert status["status"] == "failed"
    assert "verification failed before inference" in status["error"]
    assert not (run_path / "output/poses.json").exists()
    assert not (run_path / "input/evaluation/groundtruth.txt").exists()


def test_supervisor_terminates_worker_when_verified_limit_differs(
    tmp_path, monkeypatch
):
    class Clock:
        now = 0.0

        def __call__(self):
            return self.now

        def sleep(self, duration):
            self.now += duration

    class Process:
        pid = 123458
        _handle = 9
        returncode = None
        terminate_calls = 0

        def poll(self):
            return self.returncode

        def terminate(self):
            self.terminate_calls += 1
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            self.returncode = -9

    class Job:
        poll_calls = 0

        def process_memory_limit(self):
            return 1024

        def poll_memory_limit(self):
            self.poll_calls += 1
            return False

        def peak_process_memory(self):
            return 0

        def close(self):
            pass

    process = Process()
    job = Job()
    clock = Clock()
    monkeypatch.setattr(supervisor, "WindowsProcessMemoryLimit", Job)

    with pytest.raises(RuntimeError, match="incomplete receipt") as error:
        supervisor.supervise(
            dataset_path=tmp_path / "rgbd_dataset_freiburg1_xyz",
            run_root=tmp_path / "runs",
            frames=792,
            sequence_identity={"status": "checked"},
            repo=tmp_path,
            process_factory=lambda *args, **kwargs: process,
            memory_limit_factory=lambda *_: job,
            monotonic=clock,
            sleep=clock.sleep,
            poll_interval_s=0.1,
            wall_clock_limit_s=0.2,
        )

    run_path = Path(str(error.value).split(": ", maxsplit=1)[1])
    status = json.loads((run_path / "metadata/status.json").read_text())
    assert "did not match configuration" in status["error"]
    assert process.terminate_calls == 1
    assert job.poll_calls == 1  # Final cleanup checks once; no deadline polling ran.


def test_failed_status_is_written_before_detail_receipts(tmp_path, monkeypatch):
    run_path = tmp_path / "run"
    original_write_json = supervisor.write_json

    def fail_configuration(path, data):
        if path.name == "configuration.json":
            raise OSError("disk full")
        original_write_json(path, data)

    monkeypatch.setattr(supervisor, "write_json", fail_configuration)
    with pytest.raises(OSError, match="disk full"):
        supervisor._record_failure(
            run_path,
            {"sequence": "fixture"},
            reason="worker killed",
            elapsed_s=1.0,
            peak_rss_bytes=100,
            peak_commit_bytes=200,
            exit_code=-9,
            started_utc="2026-10-03T00:00:00+00:00",
        )
    status = json.loads((run_path / "metadata/status.json").read_text())
    assert status["status"] == "failed"
    assert status["error"] == "worker killed"


def test_supervisor_records_job_object_memory_limit_termination(tmp_path):
    class Process:
        pid = 123459
        _handle = 10
        returncode = -9

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            self.returncode = -9

    class Job:
        def peak_process_memory(self):
            return 700_000_000

        def poll_memory_limit(self):
            return True

        def close(self):
            pass

    with pytest.raises(RuntimeError, match="incomplete receipt") as error:
        supervisor.supervise(
            dataset_path=tmp_path / "rgbd_dataset_freiburg1_desk",
            run_root=tmp_path / "runs",
            frames=573,
            sequence_identity={"status": "checked"},
            repo=tmp_path,
            process_factory=lambda *args, **kwargs: Process(),
            memory_limit_factory=lambda *_: Job(),
        )
    run_path = Path(str(error.value).split(": ", maxsplit=1)[1])
    status = json.loads((run_path / "metadata/status.json").read_text())
    assert status["status"] == "failed"
    assert "process-memory limit notification" in status["error"]
    assert status["peak_job_process_commit_bytes"] == 700_000_000
    assert status["memory_limit_event_detected"] is True
    assert not (run_path / "input/evaluation/groundtruth.txt").exists()


def test_supervisor_rejects_complete_worker_observed_after_wall_clock_deadline(
    monkeypatch, tmp_path
):
    class Clock:
        now = 0.0

        def __call__(self):
            return self.now

        def sleep(self, duration):
            self.now += duration

    class Process:
        pid = 123458
        _handle = 9
        returncode = None

        def __init__(self, run_path, clock):
            self.run_path = run_path
            self.clock = clock

        def poll(self):
            if self.returncode is None and self.clock.now >= 0.2:
                from experiments.datasets.acquisition import sha256
                from experiments.shared.runs import _inventory, write_json

                metadata = self.run_path / "metadata"
                metadata.mkdir(parents=True, exist_ok=True)
                (self.run_path / "output").mkdir()
                write_json(metadata / "configuration.json", {"original": True})
                write_json(metadata / "timing.json", {"elapsed_seconds": 0.19})
                write_json(self.run_path / "output/metrics.json", {"rmse_m": 0.01})
                manifest_path = metadata / "manifest.json"
                write_json(
                    manifest_path,
                    {"schema_version": 1, "files": _inventory(self.run_path)},
                )
                write_json(
                    metadata / "status.json",
                    {
                        "status": "complete",
                        "manifest_sha256": sha256(manifest_path),
                    },
                )
                self.returncode = 0
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            self.returncode = -9

    class Job:
        def peak_process_memory(self):
            return 1024

        def poll_memory_limit(self):
            return False

        def close(self):
            pass

    clock = Clock()

    completed_run_path = []

    def launch(command, **kwargs):
        worker_args = json.loads(command[-1])
        run_path = Path(worker_args[worker_args.index("--_run-path") + 1])
        completed_run_path.append(run_path)
        return Process(run_path, clock)

    with pytest.raises(RuntimeError, match="rejected by the supervisor") as error:
        supervisor.supervise(
            dataset_path=tmp_path / "rgbd_dataset_freiburg1_xyz",
            run_root=tmp_path / "runs",
            frames=792,
            sequence_identity={"status": "checked"},
            repo=tmp_path,
            process_factory=launch,
            memory_limit_factory=lambda *_: Job(),
            monotonic=clock,
            sleep=clock.sleep,
            poll_interval_s=0.1,
            wall_clock_limit_s=0.2,
        )

    assert "complete artifacts are preserved" in str(error.value)
    run_path = completed_run_path[0]
    status = json.loads((run_path / "metadata/status.json").read_text())
    receipt_path = run_path.with_name(run_path.name + ".supervisor.json")
    assert status["status"] == "complete"
    assert json.loads((run_path / "metadata/configuration.json").read_text()) == {
        "original": True
    }
    assert json.loads((run_path / "metadata/timing.json").read_text()) == {
        "elapsed_seconds": 0.19
    }
    assert (
        json.loads(receipt_path.read_text())["status"] == "complete_artifact_rejected"
    )
    importlib.import_module("experiments.shared.runs").verify_run(run_path)


def test_abandoned_supervisor_launch_is_reconciled_before_new_work(tmp_path):
    run_path = tmp_path / "runs" / "abandoned"
    launch_path = tmp_path / "runs" / "abandoned.supervisor-launch.json"
    launch_path.parent.mkdir(parents=True)
    launch_path.write_text(
        json.dumps(
            {
                "status": "running",
                "supervisor_pid": 2147483647,
                "supervisor_create_time": 1.0,
                "worker_pid": None,
                "worker_create_time": None,
                "run_path": str(run_path),
                "configuration": {"sequence": "fixture"},
                "started_utc": "2026-10-03T00:00:00+00:00",
                "started_epoch_s": time.time() - 5.0,
                "peak_sampled_rss_bytes": 100,
                "peak_job_process_commit_bytes": 200,
                "worker_exit_code": None,
            }
        ),
        encoding="utf-8",
    )

    supervisor._reconcile_abandoned_launches(launch_path.parent)

    status = json.loads((run_path / "metadata/status.json").read_text())
    assert status["status"] == "failed"
    assert "exited before finalizing" in status["error"]
    assert status["peak_sampled_rss_bytes"] == 100
    assert status["peak_job_process_commit_bytes"] == 200
    assert not launch_path.exists()


def test_reconciliation_refuses_to_replace_an_active_supervisor_record(tmp_path):
    launch_root = tmp_path / "runs"
    launch_root.mkdir()
    launch_path = launch_root / "active.supervisor-launch.json"
    launch_path.write_text(
        json.dumps(
            {
                "supervisor_pid": os.getpid(),
                "supervisor_create_time": supervisor.psutil.Process().create_time(),
                "run_path": str(launch_root / "active"),
                "configuration": {},
                "started_utc": "2026-10-03T00:00:00+00:00",
                "started_epoch_s": time.time(),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="already active"):
        supervisor._reconcile_abandoned_launches(launch_root)


def test_reconciliation_rejects_launch_path_outside_run_root(tmp_path):
    launch_root = tmp_path / "runs"
    launch_root.mkdir()
    launch_path = launch_root / "tampered.supervisor-launch.json"
    launch_path.write_text(
        json.dumps(
            {
                "supervisor_pid": 2147483647,
                "supervisor_create_time": 1.0,
                "run_path": str(tmp_path / "outside"),
                "configuration": {},
                "started_utc": "2026-10-03T00:00:00+00:00",
                "started_epoch_s": time.time(),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="Invalid supervisor launch record"):
        supervisor._reconcile_abandoned_launches(launch_root)
    assert not (tmp_path / "outside").exists()


def test_reconciliation_rejects_run_directory_symlink_escape(tmp_path):
    launch_root = tmp_path / "runs"
    outside = tmp_path / "outside"
    launch_root.mkdir()
    outside.mkdir()
    linked_run = launch_root / "victim"
    try:
        linked_run.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable on this machine")
    launch_path = launch_root / "victim.supervisor-launch.json"
    launch_path.write_text(
        json.dumps(
            {
                "supervisor_pid": 2147483647,
                "supervisor_create_time": 1.0,
                "run_path": str(linked_run),
                "configuration": {},
                "started_utc": "2026-10-03T00:00:00+00:00",
                "started_epoch_s": time.time(),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="Invalid supervisor launch record"):
        supervisor._reconcile_abandoned_launches(launch_root)
    assert not (outside / "metadata").exists()


def test_reconciliation_rejects_metadata_symlink_escape(tmp_path):
    launch_root = tmp_path / "runs"
    run_path = launch_root / "victim"
    outside = tmp_path / "outside"
    launch_root.mkdir()
    run_path.mkdir()
    outside.mkdir()
    try:
        (run_path / "metadata").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable on this machine")
    launch_path = launch_root / "victim.supervisor-launch.json"
    launch_path.write_text(
        json.dumps(
            {
                "supervisor_pid": 2147483647,
                "supervisor_create_time": 1.0,
                "run_path": str(run_path),
                "configuration": {},
                "started_utc": "2026-10-03T00:00:00+00:00",
                "started_epoch_s": time.time(),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="Unsafe recovery directory"):
        supervisor._reconcile_abandoned_launches(launch_root)
    assert not list(outside.iterdir())


def test_run_root_lock_excludes_a_second_process(tmp_path):
    run_root = tmp_path / "runs"
    ready = tmp_path / "lock-ready"
    code = (
        "import importlib,sys,time; "
        "lock=importlib.import_module("
        "'experiments.03_camera_pose_estimation.src.supervisor').RunRootLock; "
        "guard=lock(__import__('pathlib').Path(sys.argv[1])); "
        "guard.__enter__(); open(sys.argv[2],'w').close(); time.sleep(10)"
    )
    process = subprocess.Popen([sys.executable, "-c", code, str(run_root), str(ready)])
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists()
        with (
            pytest.raises(RuntimeError, match="Another tracking supervisor"),
            supervisor.RunRootLock(run_root),
        ):
            pass
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration")
def test_windows_process_memory_limit_assigns_and_reaps_worker(tmp_path):
    release = tmp_path / "release"
    code = (
        "import importlib,os,sys,time; "
        "WindowsProcessMemoryLimit=importlib.import_module("
        "'experiments.03_camera_pose_estimation.src.supervisor').WindowsProcessMemoryLimit; "
        "deadline=time.monotonic()+10; "
        "exec('while not os.path.exists(sys.argv[1]) and time.monotonic()<deadline: time.sleep(0.01)'); "
        "raise SystemExit(0 if WindowsProcessMemoryLimit.is_current_process_in_job() else 1)"
    )
    process = subprocess.Popen([sys.executable, "-c", code, str(release)])
    job = None
    try:
        job = supervisor.WindowsProcessMemoryLimit(process._handle, 1024**3)
        assert job.process_memory_limit() == 1024**3
        release.write_text("assigned", encoding="utf-8")
        assert process.wait(timeout=10) == 0
        assert job.peak_process_memory() is not None
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if job is not None:
            job.close()


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration")
def test_windows_job_reports_memory_cap_event_below_reported_peak_limit():
    code = (
        "import sys; sys.stdin.buffer.read(1); blocks=[]; "
        "exec('for _ in range(32):\\n try: blocks.append(bytearray(8*1024**2))\\n "
        "except MemoryError: break'); "
        "print(len(blocks)*8*1024**2, flush=True)"
    )
    process = subprocess.Popen(
        [sys.executable, "-B", "-u", "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    job = None
    try:
        job = supervisor.WindowsProcessMemoryLimit(process._handle, 64 * 1024**2)
        assert job.process_memory_limit() == 64 * 1024**2
        assert process.stdin is not None
        process.stdin.write("x")
        process.stdin.flush()
        assert process.wait(timeout=10) == 0
        assert process.stdout is not None
        allocated_bytes = int(process.stdout.read())
        assert 0 < allocated_bytes < 32 * 8 * 1024**2
        assert job.peak_process_memory() < 64 * 1024**2
        assert job.poll_memory_limit() is True
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if job is not None:
            job.close()
