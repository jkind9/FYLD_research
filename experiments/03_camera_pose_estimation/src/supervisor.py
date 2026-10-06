"""Apply per-run process limits and preserve receipts after worker termination."""

import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar
from uuid import uuid4

import psutil

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run, write_json

from .memory_limits import WindowsProcessMemoryLimit

WALL_CLOCK_LIMIT_S = 30 * 60
MEMORY_LIMIT_BYTES = 2 * 1024**3
POLL_INTERVAL_S = 0.1
TERMINATE_GRACE_S = 5.0
_WORKER_BOOTSTRAP = """\
import json
import os
import runpy
import sys
import time

release_file = sys.argv[1]
deadline = time.monotonic() + 60.0
while not os.path.exists(release_file):
    if time.monotonic() >= deadline:
        raise SystemExit("supervisor did not release worker")
    time.sleep(0.02)
with open(release_file, encoding="utf-8") as stream:
    release = json.load(stream)
os.environ["FYLD_TRACKING_JOB_LIMIT_BYTES"] = str(
    release["process_memory_limit_bytes"]
)
sys.argv = ["tracking-worker", *json.loads(sys.argv[2])]
runpy.run_module("experiments.03_camera_pose_estimation.src.run", run_name="__main__")
"""
_P = ParamSpec("_P")
_T = TypeVar("_T")


class RunRootLock:
    """Hold one OS file lock across recovery and a complete supervised run."""

    def __init__(self, run_root: Path) -> None:
        self.path = run_root / ".supervisor.lock"
        self._file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a+b")
        self._file.seek(0, os.SEEK_END)
        if self._file.tell() == 0:
            self._file.write(b"\0")
            self._file.flush()
        self._file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._file.close()
            self._file = None
            raise RuntimeError(
                f"Another tracking supervisor holds {self.path}"
            ) from error
        return self

    def __exit__(self, *_exc) -> None:
        if self._file is None:
            return
        self._file.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()
        self._file = None


def _serialize_run_root(function: Callable[_P, _T]) -> Callable[_P, _T]:
    @wraps(function)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        run_root = kwargs.get("run_root")
        if not isinstance(run_root, Path):
            raise TypeError("run_root must be a pathlib.Path")
        run_root.mkdir(parents=True, exist_ok=True)
        with RunRootLock(run_root):
            return function(*args, **kwargs)

    return wrapped


def _configuration(sequence_identity: dict, sequence: str, frames: int) -> dict:
    from .run import HYPERPARAMETERS, _selected_hyperparameters

    parameters = _selected_hyperparameters(sequence, frames)
    return {
        "hyperparameters": parameters,
        "sequence": sequence,
        "selection": "first consecutive associated observations; no stride",
        "selected_frames": frames,
        "dataset_provenance": sequence_identity,
        "device": "CPU",
        "gpu": "not used",
        "execution_limits": {
            "wall_clock_seconds": WALL_CLOCK_LIMIT_S,
            "wall_clock_scope": "worker launch through source capture, backend, estimation, scoring and reports",
            "process_memory_bytes": MEMORY_LIMIT_BYTES,
            "process_memory_measure": "Windows Job Object per-process commit limit",
            "monitor_poll_interval_seconds": POLL_INTERVAL_S,
        },
        "frozen_backend_settings": {
            key: value
            for key, value in HYPERPARAMETERS.items()
            if key
            not in {
                "frames",
                "sequence",
                "selection",
                "wall_clock_limit_s",
                "process_memory_limit_bytes",
            }
        },
    }


def _record_failure(
    run_path: Path,
    configuration: dict,
    *,
    reason: str,
    elapsed_s: float,
    peak_rss_bytes: int | None,
    peak_commit_bytes: int | None,
    exit_code: int | None,
    started_utc: str,
    memory_limit_event: bool = False,
) -> None:
    status_path = run_path / "metadata/status.json"
    existing_status = None
    if status_path.is_file():
        try:
            existing = json.loads(status_path.read_text(encoding="utf-8"))
            existing_status = existing if isinstance(existing, dict) else None
            if existing.get("status") == "complete":
                verify_run(run_path)
                return
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    metadata = run_path / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    (run_path / "input").mkdir(exist_ok=True)
    (run_path / "output").mkdir(exist_ok=True)
    (run_path / "debug").mkdir(exist_ok=True)
    ended_utc = datetime.now(UTC).isoformat()
    worker_failed = (
        existing_status is not None and existing_status.get("status") == "failed"
    )
    write_json(
        status_path,
        {
            "status": "failed",
            "started_utc": (
                existing_status.get("started_utc", started_utc)
                if worker_failed
                else started_utc
            ),
            "ended_utc": ended_utc,
            "elapsed_seconds": (
                existing_status.get("elapsed_seconds", elapsed_s)
                if worker_failed
                else elapsed_s
            ),
            "error_type": (
                existing_status.get("error_type", "WorkerTerminated")
                if worker_failed
                else "WorkerTerminated"
            ),
            "error": (
                existing_status.get("error", reason) if worker_failed else reason
            ),
            "supervisor_reason": reason,
            "worker_exit_code": exit_code,
            "peak_sampled_rss_bytes": peak_rss_bytes,
            "peak_job_process_commit_bytes": peak_commit_bytes,
            "memory_limit_event_detected": memory_limit_event,
        },
    )
    write_json(metadata / "configuration.json", configuration)
    write_json(
        metadata / "supervisor.json",
        {
            "status": "terminated",
            "started_utc": started_utc,
            "reason": reason,
            "wall_clock_limit_seconds": WALL_CLOCK_LIMIT_S,
            "process_memory_limit_bytes": MEMORY_LIMIT_BYTES,
            "process_memory_measure": "Windows Job Object per-process commit limit",
            "peak_sampled_rss_bytes": peak_rss_bytes,
            "peak_job_process_commit_bytes": peak_commit_bytes,
            "memory_limit_event_detected": memory_limit_event,
            "worker_exit_code": exit_code,
        },
    )
    write_json(
        metadata / "timing.json",
        {
            "started_utc": started_utc,
            "ended_utc": ended_utc,
            "elapsed_seconds": elapsed_s,
            "completed": False,
            "supervisor_wall_clock_limit_seconds": WALL_CLOCK_LIMIT_S,
        },
    )


def _record_rejected_complete(
    run_path: Path,
    *,
    reason: str,
    elapsed_s: float,
    started_utc: str,
    exit_code: int | None,
    memory_limit_event: bool = False,
) -> Path:
    """Record supervisor rejection beside a complete run without changing it."""
    receipt_path = run_path.with_name(run_path.name + ".supervisor.json")
    write_json(
        receipt_path,
        {
            "status": "complete_artifact_rejected",
            "reason": reason,
            "started_utc": started_utc,
            "observed_exit_utc": datetime.now(UTC).isoformat(),
            "observed_elapsed_seconds": elapsed_s,
            "wall_clock_limit_seconds": WALL_CLOCK_LIMIT_S,
            "process_memory_limit_bytes": MEMORY_LIMIT_BYTES,
            "process_memory_measure": "Windows Job Object per-process commit limit",
            "worker_exit_code": exit_code,
            "memory_limit_event_detected": memory_limit_event,
            "run_manifest_sha256": sha256(run_path / "metadata/manifest.json"),
            "run_status_sha256": sha256(run_path / "metadata/status.json"),
        },
    )
    return receipt_path


def _reconcile_abandoned_launches(run_root: Path) -> None:
    """Finalize receipts left by a supervisor process that no longer exists."""
    for launch_path in sorted(run_root.glob("*.supervisor-launch.json")):
        launch = json.loads(launch_path.read_text(encoding="utf-8"))
        if not isinstance(launch, dict):
            raise TypeError(f"Invalid supervisor launch record: {launch_path}")
        expected_run_path = run_root / launch_path.name.removesuffix(
            ".supervisor-launch.json"
        )
        resolved_run_root = run_root.resolve()
        resolved_expected = expected_run_path.resolve()
        is_junction = getattr(expected_run_path, "is_junction", lambda: False)()
        if (
            not isinstance(launch.get("run_path"), str)
            or Path(launch["run_path"]).resolve() != resolved_expected
            or resolved_expected.parent != resolved_run_root
            or expected_run_path.is_symlink()
            or is_junction
            or not isinstance(launch.get("configuration"), dict)
            or not isinstance(launch.get("started_utc"), str)
            or not isinstance(launch.get("started_epoch_s"), (float, int))
            or isinstance(launch.get("started_epoch_s"), bool)
        ):
            raise TypeError(f"Invalid supervisor launch record: {launch_path}")
        supervisor_pid = launch.get("supervisor_pid")
        supervisor_created = launch.get("supervisor_create_time")
        if (
            not isinstance(supervisor_pid, int)
            or isinstance(supervisor_pid, bool)
            or supervisor_pid <= 0
            or not isinstance(supervisor_created, (float, int))
            or isinstance(supervisor_created, bool)
        ):
            raise TypeError(f"Invalid supervisor identity: {launch_path}")
        try:
            supervisor = psutil.Process(supervisor_pid)
            if abs(supervisor.create_time() - supervisor_created) < 0.01:
                raise RuntimeError(
                    "A tracking supervisor is already active for this run root"
                )
        except psutil.NoSuchProcess:
            pass
        worker_pid = launch.get("worker_pid")
        worker_created = launch.get("worker_create_time")
        if isinstance(worker_pid, bool) or isinstance(worker_created, bool):
            raise TypeError(f"Invalid worker identity: {launch_path}")
        if worker_pid is not None and (
            not isinstance(worker_pid, int)
            or worker_pid <= 0
            or not isinstance(worker_created, (float, int))
        ):
            raise TypeError(f"Invalid worker identity: {launch_path}")
        if isinstance(worker_pid, int) and isinstance(worker_created, (float, int)):
            run_path = Path(launch["run_path"])
            try:
                worker = psutil.Process(worker_pid)
                if abs(worker.create_time() - worker_created) < 0.01:
                    command = worker.cmdline()
                    worker_args = json.loads(command[-1]) if command else None
                    worker_run = (
                        Path(worker_args[worker_args.index("--_run-path") + 1])
                        if isinstance(worker_args, list)
                        and "--_run-path" in worker_args
                        else None
                    )
                    expected_release = run_root / ("." + run_path.name + ".release")
                    if (
                        worker.ppid() != supervisor_pid
                        or len(command) < 5
                        or command[1] != "-c"
                        or command[2] != _WORKER_BOOTSTRAP
                        or Path(command[3]).resolve() != expected_release.resolve()
                        or worker_run is None
                        or worker_run.resolve() != run_path.resolve()
                    ):
                        raise RuntimeError(
                            "Recorded worker identity does not match this launch: "
                            f"{launch_path}"
                        )
                    worker.terminate()
                    try:
                        worker.wait(timeout=TERMINATE_GRACE_S)
                    except psutil.TimeoutExpired:
                        worker.kill()
                        worker.wait()
            except psutil.NoSuchProcess:
                pass
        run_path = Path(launch["run_path"])
        _validate_recovery_directories(run_path)
        elapsed = max(0.0, time.time() - float(launch["started_epoch_s"]))
        try:
            verify_run(run_path)
        except (OSError, ValueError, json.JSONDecodeError):
            _record_failure(
                run_path,
                launch["configuration"],
                reason="Supervisor exited before finalizing the worker receipt",
                elapsed_s=elapsed,
                peak_rss_bytes=launch.get("peak_sampled_rss_bytes"),
                peak_commit_bytes=launch.get("peak_job_process_commit_bytes"),
                exit_code=launch.get("worker_exit_code"),
                started_utc=launch["started_utc"],
                memory_limit_event=launch.get("memory_limit_event_detected", False),
            )
        else:
            _record_rejected_complete(
                run_path,
                reason="Supervisor exited before confirming wall-clock compliance",
                elapsed_s=elapsed,
                started_utc=launch["started_utc"],
                exit_code=launch.get("worker_exit_code"),
                memory_limit_event=launch.get("memory_limit_event_detected", False),
            )
        launch_path.unlink()


def _process_create_time(pid: int) -> float | None:
    try:
        return psutil.Process(pid).create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def _validate_recovery_directories(run_path: Path) -> None:
    root = run_path.resolve()
    for name in ("metadata", "input", "output", "debug"):
        directory = run_path / name
        is_junction = getattr(directory, "is_junction", lambda: False)()
        if (
            directory.is_symlink()
            or is_junction
            or (directory.exists() and directory.resolve().parent != root)
        ):
            raise TypeError(f"Unsafe recovery directory: {directory}")


@_serialize_run_root
def supervise(
    *,
    dataset_path: Path,
    run_root: Path,
    frames: int,
    sequence_identity: dict,
    repo: Path,
    process_factory=subprocess.Popen,
    memory_limit_factory=WindowsProcessMemoryLimit,
    monotonic=time.monotonic,
    sleep=time.sleep,
    poll_interval_s: float = POLL_INTERVAL_S,
    wall_clock_limit_s: float = WALL_CLOCK_LIMIT_S,
    memory_limit_bytes: int = MEMORY_LIMIT_BYTES,
    terminate_grace_s: float = TERMINATE_GRACE_S,
) -> Path:
    """Run one worker under hard process memory and wall-clock limits."""
    sequence = dataset_path.name
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid4().hex
    run_path = run_root / run_id
    release_file = run_root / ("." + run_id + ".release")
    configuration = _configuration(sequence_identity, sequence, frames)
    configuration["dataset"] = str(dataset_path.resolve())
    run_root.mkdir(parents=True, exist_ok=True)
    _reconcile_abandoned_launches(run_root)
    start = monotonic()
    worker_args = [
        "--dataset",
        str(dataset_path),
        "--frames",
        str(frames),
        "--runs",
        str(run_root),
        "--_worker",
        "--_run-path",
        str(run_path),
        "--_release-file",
        str(release_file),
        "--_provenance-json",
        json.dumps(sequence_identity, separators=(",", ":")),
        "--_deadline-monotonic",
        str(start + wall_clock_limit_s),
    ]
    command = [
        sys.executable,
        "-c",
        _WORKER_BOOTSTRAP,
        str(release_file),
        json.dumps(worker_args, separators=(",", ":")),
    ]
    started_utc = datetime.now(UTC).isoformat()
    launch_path = run_root / f"{run_id}.supervisor-launch.json"
    launch_record = {
        "status": "starting",
        "supervisor_pid": os.getpid(),
        "supervisor_create_time": psutil.Process().create_time(),
        "worker_pid": None,
        "worker_create_time": None,
        "run_path": str(run_path),
        "configuration": configuration,
        "started_utc": started_utc,
        "started_epoch_s": time.time(),
        "wall_clock_limit_seconds": wall_clock_limit_s,
        "process_memory_limit_bytes": memory_limit_bytes,
        "peak_sampled_rss_bytes": None,
        "peak_job_process_commit_bytes": None,
        "memory_limit_event_detected": False,
        "worker_exit_code": None,
    }
    write_json(launch_path, launch_record)
    process = None
    job = None
    peak_rss = 0
    peak_commit = 0
    reason = None
    deadline = None
    last_launch_write = start
    try:
        try:
            process = process_factory(command, cwd=repo)
        except OSError as error:
            reason = f"Worker launch failed: {error}"
        if process is None:
            pass
        else:
            launch_record.update(
                {
                    "status": "worker_started",
                    "worker_pid": process.pid,
                    "worker_create_time": _process_create_time(process.pid),
                }
            )
            write_json(launch_path, launch_record)
            try:
                job = memory_limit_factory(process._handle, memory_limit_bytes)
                process_memory_limit = (
                    job.process_memory_limit()
                    if isinstance(job, WindowsProcessMemoryLimit)
                    else memory_limit_bytes
                )
            except (OSError, AttributeError, TypeError, ValueError) as error:
                reason = f"Memory limit setup or verification failed before inference: {error}"
            else:
                run_root.mkdir(parents=True, exist_ok=True)
                if process_memory_limit != memory_limit_bytes:
                    reason = "Job Object process-memory limit did not match configuration"
                else:
                    write_json(
                        release_file,
                        {
                            "worker_pid": process.pid,
                            "process_memory_limit_bytes": process_memory_limit,
                        },
                    )
                deadline = start + wall_clock_limit_s
                while process.poll() is None and reason is None:
                    now = monotonic()
                    if now >= deadline:
                        reason = f"Worker exceeded {wall_clock_limit_s} second wall-clock limit"
                        break
                    if job.poll_memory_limit():
                        launch_record["memory_limit_event_detected"] = True
                        write_json(launch_path, launch_record)
                        reason = "Worker received a process-memory limit notification"
                        break
                    try:
                        peak_rss = max(
                            peak_rss,
                            int(psutil.Process(process.pid).memory_info().rss),
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    sampled_peak = int(job.peak_process_memory() or 0)
                    commit_changed = sampled_peak > peak_commit
                    peak_commit = max(peak_commit, sampled_peak)
                    if commit_changed or now - last_launch_write >= 1.0:
                        launch_record["peak_sampled_rss_bytes"] = peak_rss or None
                        launch_record["peak_job_process_commit_bytes"] = (
                            peak_commit or None
                        )
                        launch_record["worker_exit_code"] = process.poll()
                        launch_record["status"] = "running"
                        write_json(launch_path, launch_record)
                        last_launch_write = now
                    sleep(min(poll_interval_s, max(0.0, deadline - now)))
                if (
                    reason is None
                    and process.poll() is not None
                    and process.returncode != 0
                ):
                    peak_commit = int(job.peak_process_memory() or 0)
                    if job.poll_memory_limit():
                        launch_record["memory_limit_event_detected"] = True
                        reason = "Worker received a process-memory limit notification"
                    else:
                        reason = f"Worker exited with code {process.returncode}"
                if reason is None and deadline is not None and monotonic() >= deadline:
                    reason = (
                        f"Worker exceeded {wall_clock_limit_s} second wall-clock limit"
                    )
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=terminate_grace_s)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if job is not None:
            if job.poll_memory_limit():
                launch_record["memory_limit_event_detected"] = True
                if reason is None:
                    reason = "Worker received a process-memory limit notification"
            peak_commit = max(peak_commit, int(job.peak_process_memory() or 0))
            job.close()
        release_file.unlink(missing_ok=True)

    elapsed = max(0.0, monotonic() - start)
    launch_record["peak_sampled_rss_bytes"] = peak_rss or None
    launch_record["peak_job_process_commit_bytes"] = peak_commit or None
    launch_record["worker_exit_code"] = None if process is None else process.returncode
    complete = False
    try:
        verify_run(run_path)
        complete = True
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    if complete:
        if reason is None:
            launch_path.unlink(missing_ok=True)
            return run_path
        receipt_path = _record_rejected_complete(
            run_path,
            reason=reason,
            elapsed_s=elapsed,
            started_utc=started_utc,
            exit_code=None if process is None else process.returncode,
            memory_limit_event=launch_record["memory_limit_event_detected"],
        )
        launch_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Tracking run was rejected by the supervisor; complete artifacts "
            f"are preserved at {run_path}; receipt: {receipt_path}"
        )
    if reason is None and process is not None and process.returncode == 0:
        reason = "Worker returned success without a valid complete receipt"
    _record_failure(
        run_path,
        configuration,
        reason=reason or "Worker failed before publishing a complete run",
        elapsed_s=elapsed,
        peak_rss_bytes=peak_rss or None,
        peak_commit_bytes=peak_commit or None,
        exit_code=None if process is None else process.returncode,
        started_utc=started_utc,
        memory_limit_event=launch_record["memory_limit_event_detected"],
    )
    launch_path.unlink(missing_ok=True)
    raise RuntimeError(f"Tracking run failed; incomplete receipt: {run_path}")
