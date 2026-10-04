"""CPU tracking contracts, independent reference scoring and publication."""

import gc
import hashlib
import importlib
import json
import os
import subprocess
import sys
import time
import weakref
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

package = "experiments.03_camera_pose_estimation.src"
dataset = importlib.import_module(package + ".dataset")
backend = importlib.import_module(package + ".backend")
tracking = importlib.import_module(package + ".tracking")
evaluation = importlib.import_module(package + ".evaluation")
supervisor = importlib.import_module(package + ".supervisor")


def frame(index, depth=True):
    from experiments.shared.contracts import Calibration

    calibration = Calibration(80, 60, 70, 70, 39.5, 29.5, "x-right_y-down_z-forward")
    rng = np.random.default_rng(12)
    colour = rng.integers(0, 256, (60, 80, 3), dtype=np.uint8)
    values = np.full((60, 80), 2.0 if depth else np.nan)
    return dataset.RGBDFrame(
        str(index),
        index * 0.03,
        index * 0.03,
        calibration,
        colour,
        values,
        np.isfinite(values),
    )


class FakeBackend:
    def __init__(self, transforms):
        self.transforms = iter(transforms)

    def estimate(self, source, target):
        transform = next(self.transforms)
        return backend.PairResult(transform is not None, transform, "fixture")


def translation(x):
    matrix = np.eye(4)
    matrix[0, 3] = x
    return matrix


def test_pose_free_input_and_noncommuting_composition():
    assert not {"pose", "reference_path"} & {
        field.name for field in fields(dataset.RGBDFrame)
    }
    first = translation(-0.1)
    second = np.eye(4)
    second[:3, :3] = Rotation.from_euler("z", 0.2).as_matrix()
    records = tracking.track([frame(i) for i in range(3)], FakeBackend([first, second]))
    assert records[0].status == "initialized"
    np.testing.assert_allclose(records[1].pose.matrix, np.linalg.inv(first))
    np.testing.assert_allclose(
        records[2].pose.matrix, np.linalg.inv(first) @ np.linalg.inv(second)
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
    assert "setup failed before inference" in status["error"]
    assert not (run_path / "output/poses.json").exists()
    assert not (run_path / "input/evaluation/groundtruth.txt").exists()


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
        "raise SystemExit(0 if WindowsProcessMemoryLimit.current_process_memory_limit()==1024**3 else 1)"
    )
    process = subprocess.Popen([sys.executable, "-c", code, str(release)])
    job = None
    try:
        job = supervisor.WindowsProcessMemoryLimit(process._handle, 1024**3)
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
def test_windows_job_reports_memory_cap_event_below_reported_peak_limit(tmp_path):
    release = tmp_path / "release-memory"
    code = (
        "import os,sys,time; deadline=time.monotonic()+10; "
        "exec('while not os.path.exists(sys.argv[1]) and time.monotonic()<deadline: time.sleep(0.01)'); "
        "blocks=[]; "
        "exec('while True:\\n try: blocks.append(bytearray(8*1024**2))\\n except MemoryError: break')"
    )
    process = subprocess.Popen([sys.executable, "-c", code, str(release)])
    job = None
    try:
        job = supervisor.WindowsProcessMemoryLimit(process._handle, 64 * 1024**2)
        release.write_text("assigned", encoding="utf-8")
        assert process.wait(timeout=10) == 0
        assert job.peak_process_memory() < 64 * 1024**2
        assert job.poll_memory_limit() is True
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if job is not None:
            job.close()


def test_failure_zero_depth_and_gap_reset():
    # One failed edge must not connect the next camera to the old origin.
    records = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([None, translation(-0.1)])
    )
    assert [r.status for r in records] == ["initialized", "failed", "reset", "tracked"]
    assert records[1].pose is None
    assert records[0].pose.world_id != records[2].pose.world_id
    records = tracking.track(
        [frame(0), frame(1, False), frame(2), frame(10)], FakeBackend([])
    )
    assert [r.status for r in records] == ["initialized", "failed", "reset", "reset"]


def test_invalid_backend_transform_rejected():
    invalid = np.eye(4)
    invalid[0, 0] = 2
    records = tracking.track([frame(0), frame(1)], FakeBackend([invalid]))
    assert records[1].status == "failed" and records[1].pose is None


def test_independent_fixed_scale_errors_and_anchor_only():
    references = [(i * 0.03, translation(i * 0.1)) for i in range(4)]
    exact = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([translation(-0.1)] * 3)
    )
    doubled = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([translation(-0.2)] * 3)
    )
    reversed_motion = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([translation(0.1)] * 3)
    )
    clean = evaluation.evaluate(exact, references)
    assert clean["position_rmse_m"] == pytest.approx(0, abs=1e-12)
    for wrong in (doubled, reversed_motion):
        assert evaluation.evaluate(wrong, references)["position_rmse_m"] > 0.1
    assert evaluation.evaluate(exact[:1], references)["position_rmse_m"] is None


def test_reference_matching_never_skips_unmatched_observation():
    records = tracking.track(
        [frame(i) for i in range(3)], FakeBackend([translation(-0.1)] * 2)
    )
    scored = evaluation.evaluate(
        records, [(0.0, translation(0)), (0.06, translation(0.2))], tolerance=0.001
    )
    assert scored["relative_pairs"] == 0
    assert scored["unmatched_estimates"] == 1


def test_single_matched_tracked_pose_is_not_independent_accuracy():
    records = tracking.track(
        [frame(i) for i in range(3)], FakeBackend([translation(-0.1)] * 2)
    )
    scored = evaluation.evaluate(records, [(0.03, translation(0.1))], tolerance=0.001)
    assert scored["position_rmse_m"] is None
    assert scored["position_samples"] == 0
    assert scored["segments"][0]["position_rmse_m"] is None


@pytest.mark.parametrize(
    "rows",
    [
        "1 rgb/a.png\n1 rgb/b.png",
        "2 rgb/a.png\n1 rgb/b.png",
        "nan rgb/a.png",
        "1 ../bad.png",
        "1 C:/bad.png",
    ],
)
def test_invalid_timestamp_tables(tmp_path, rows):
    path = tmp_path / "rgb.txt"
    path.write_text(rows)
    with pytest.raises(ValueError):
        dataset.read_table(path)


def test_actual_cpu_backend_known_motion_and_empty_depth():
    engine = backend.CPUOdometry()
    source = frame(0)
    colour = np.roll(source.colour, -1, axis=1)
    target = dataset.RGBDFrame(
        "1", 0.03, 0.03, source.calibration, colour, source.depth, source.valid
    )
    result = engine.estimate(source, target)
    assert result.success
    assert result.transform[0, 3] == pytest.approx(-2 / 70, abs=0.012)
    assert not engine.estimate(source, frame(1, False)).success


def test_missing_or_malformed_reference(tmp_path):
    with pytest.raises(FileNotFoundError):
        evaluation.read_references(tmp_path / "absent")
    path = tmp_path / "groundtruth.txt"
    path.write_text("0 0 0 0 0 0 0 0\n")
    with pytest.raises(ValueError):
        evaluation.read_references(path)


def test_publisher_rounded_quaternion_is_normalized_without_mutating_input(tmp_path):
    path = tmp_path / "groundtruth.txt"
    payload = "0 1 2 3 0 0 0 0.9999\n"
    path.write_text(payload)
    rows = evaluation.read_references(path)
    np.testing.assert_allclose(
        rows[0][1],
        translation(1)
        + np.array([[0, 0, 0, 0], [0, 0, 0, 2], [0, 0, 0, 3], [0, 0, 0, 0]]),
    )
    assert path.read_text() == payload


def test_pipeline_reference_separation_and_required_artifacts(tmp_path, monkeypatch):
    from PIL import Image

    from experiments.shared.runs import verify_run

    runner = importlib.import_module(package + ".run")
    root = tmp_path / "rgbd_dataset_freiburg1_desk"
    root.mkdir()
    for name in ("rgb", "depth"):
        (root / name).mkdir()
    for i in range(3):
        Image.fromarray(np.full((480, 640, 3), 128, np.uint8)).save(
            root / f"rgb/{i}.png"
        )
        Image.fromarray(np.full((480, 640), 10000, np.uint16)).save(
            root / f"depth/{i}.png"
        )
    (root / "rgb.txt").write_text(
        "\n".join(f"{i * 0.03} rgb/{i}.png" for i in range(3))
    )
    (root / "depth.txt").write_text(
        "\n".join(f"{i * 0.03} depth/{i}.png" for i in range(3))
    )
    (root / "groundtruth.txt").write_text(
        "\n".join(f"{i * 0.03} {i * 0.1} 0 0 0 0 0 1" for i in range(3))
    )
    original = evaluation.read_references
    called = []

    def guarded(path):
        assert len(called) == 2
        run_path = next(result_path.iterdir())
        saved = json.loads((run_path / "output/poses.json").read_text())
        assert len(saved["records"]) == 3
        assert all(
            row["status"] in {"initialized", "tracked"} for row in saved["records"]
        )
        return original(path)

    class GuardedBackend:
        def estimate(self, source, target):
            called.append(target.frame_id)
            return backend.PairResult(True, translation(-0.1), "test")

    result_path = tmp_path / "runs"
    monkeypatch.setattr(evaluation, "read_references", guarded)
    result = runner.execute(root, result_path, count=3, engine=GuardedBackend())
    assert verify_run(result)["status"] == "complete"
    configuration = json.loads((result / "metadata/configuration.json").read_text())
    assert configuration["sequence"] == "rgbd_dataset_freiburg1_desk"
    assert configuration["selected_frames"] == 3
    assert (
        configuration["hyperparameters"]["sequence"]["value"]
        == configuration["sequence"]
    )
    assert configuration["hyperparameters"]["frames"]["value"] == 3
    manifest = json.loads((result / "metadata/manifest.json").read_text())
    manifest_files = set(manifest["files"])
    for row in json.loads((result / "output/associations.json").read_text())["rows"]:
        for kind in ("rgb", "depth"):
            assert f"input/observations/{row[kind]}" in manifest_files
    assert (result / "review.html").exists()
    (result / "output/metrics.json").unlink()
    with pytest.raises(ValueError):
        runner.validate_outputs(result, 3)

    called.clear()
    validation = runner.validate_outputs

    def missing_output(path, count):
        (path / "output/metrics.json").unlink()
        validation(path, count)

    monkeypatch.setattr(runner, "validate_outputs", missing_output)
    with pytest.raises(ValueError, match="Required tracking artifact"):
        runner.execute(root, tmp_path / "failed_runs", count=3, engine=GuardedBackend())
    failed = next((tmp_path / "failed_runs").iterdir())
    assert (
        json.loads((failed / "metadata/status.json").read_text())["status"] == "failed"
    )


@pytest.mark.parametrize(
    ("dataset_name", "frames"),
    [("rgbd_dataset_freiburg1_xyz", "792"), ("rgbd_dataset_freiburg1_desk", "573")],
)
def test_cli_accepts_full_sequence_counts(monkeypatch, tmp_path, dataset_name, frames):
    runner = importlib.import_module(package + ".run")
    dataset_root = tmp_path / dataset_name
    dataset_root.mkdir()
    run_root = tmp_path / "runs"
    selected = []
    verified_identity = {
        "status": (
            "archive provenance checked; completed runs hash selected inputs "
            "in the run manifest"
        ),
        "sequence": dataset_name,
        "archive_sha256": "a" * 64,
    }

    def execute(**kwargs):
        selected.append(kwargs)
        return run_root

    monkeypatch.setattr(runner, "supervise", execute)
    monkeypatch.setattr(
        runner, "_archive_provenance", lambda root, repo: verified_identity
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "tracking",
            "--dataset",
            str(dataset_root),
            "--frames",
            frames,
            "--runs",
            str(run_root),
        ],
    )
    runner.main()
    assert len(selected) == 1
    call = selected[0]
    assert call["dataset_path"] == dataset_root
    assert call["run_root"] == run_root
    assert call["frames"] == int(frames)
    assert call["repo"] == Path(__file__).resolve().parents[3]
    identity = call["sequence_identity"]
    assert identity["sequence"] == dataset_name
    assert identity["status"].startswith("archive provenance checked")
    assert identity["archive_sha256"]


def test_cli_rejects_named_but_unverified_dataset_path(monkeypatch, tmp_path):
    runner = importlib.import_module(package + ".run")
    dataset_root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    dataset_root.mkdir()
    monkeypatch.setattr(
        "sys.argv",
        ["tracking", "--dataset", str(dataset_root), "--frames", "792"],
    )
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2


@pytest.mark.parametrize(
    ("dataset_name", "archive_name"),
    [
        ("rgbd_dataset_freiburg1_xyz", "rgbd_dataset_freiburg1_xyz.tgz"),
        ("rgbd_dataset_freiburg1_desk", "rgbd_dataset_freiburg1_desk.tgz"),
    ],
)
def test_archive_provenance_binds_receipts_to_archive_bytes(
    tmp_path, dataset_name, archive_name
):
    from pathlib import Path

    runner = importlib.import_module(package + ".run")
    repo = tmp_path
    relative_root = (
        Path("data/tum/rgbd_dataset_freiburg1_xyz")
        if dataset_name == "rgbd_dataset_freiburg1_xyz"
        else Path("data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk")
    )
    relative_secondary = (
        relative_root / "provenance.json"
        if dataset_name == "rgbd_dataset_freiburg1_xyz"
        else relative_root.parent / "EXTRACTION.json"
    )
    relative_acquisition = Path("data/archives") / f"{archive_name}.json"
    dataset_root = repo / relative_root
    dataset_root.mkdir(parents=True)
    archive_path = repo / "data/archives" / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive = b"verified archive fixture"
    archive_path.write_bytes(archive)
    digest = hashlib.sha256(archive).hexdigest()
    official_url = "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/" + archive_name
    resolved_url = (
        "https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/" + archive_name
    )
    acquisition = {
        "source_url": official_url,
        "resolved_url": resolved_url,
        "local_sha256": digest,
    }
    secondary = {"local_sha256": digest}
    if dataset_name == "rgbd_dataset_freiburg1_xyz":
        acquisition["size_bytes"] = len(archive)
        secondary.update({"source_url": official_url, "size_bytes": len(archive)})
    else:
        acquisition["bytes"] = len(archive)
        secondary.update({"archive": archive_name, "compressed_bytes": len(archive)})
    (repo / relative_acquisition).write_text(json.dumps(acquisition))
    secondary_path = repo / relative_secondary
    secondary_path.parent.mkdir(parents=True, exist_ok=True)
    secondary_path.write_text(json.dumps(secondary))
    member_manifest = repo / "experiments/datasets/tum_freiburg1_member_hashes.json"
    member_manifest.parent.mkdir(parents=True, exist_ok=True)
    member_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sequences": {
                    dataset_name: {
                        "archive_sha256": digest,
                        "archive_bytes": len(archive),
                        "members": {
                            "rgb.txt": {"bytes": 1, "sha256": "a" * 64},
                            "depth.txt": {"bytes": 1, "sha256": "b" * 64},
                            "groundtruth.txt": {"bytes": 1, "sha256": "c" * 64},
                        },
                    }
                },
            }
        )
    )

    identity = runner._archive_provenance(dataset_root, repo)
    assert identity["sequence"] == dataset_name
    assert identity["archive_sha256"] == digest
    assert (
        identity["member_manifest_sha256"]
        == hashlib.sha256(member_manifest.read_bytes()).hexdigest()
    )
    acquisition["source_url"] = "https://untrusted.example/" + archive_name
    (repo / relative_acquisition).write_text(json.dumps(acquisition))
    with pytest.raises(ValueError, match="receipts do not match"):
        runner._archive_provenance(dataset_root, repo)


def test_selected_observation_hash_must_match_archive_member_manifest(tmp_path):
    runner = importlib.import_module(package + ".run")
    root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    root.mkdir()
    (root / "rgb").mkdir()
    (root / "depth").mkdir()
    members = {}
    for relative, payload in {
        "rgb.txt": b"0 rgb/frame.png\n",
        "depth.txt": b"0 depth/frame.png\n",
        "groundtruth.txt": b"0 0 0 0 0 0 0 1\n",
        "rgb/frame.png": b"rgb pixels",
        "depth/frame.png": b"depth pixels",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        members[relative] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    member_document = {
        "schema_version": 1,
        "sequences": {
            root.name: {
                "archive_sha256": "d" * 64,
                "archive_bytes": 123,
                "members": members,
            }
        },
    }
    manifest_path = tmp_path / "experiments/datasets/tum_freiburg1_member_hashes.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(member_document))
    identity = {
        "sequence": root.name,
        "archive_sha256": "d" * 64,
        "archive_bytes": "123",
        "member_manifest": "experiments/datasets/tum_freiburg1_member_hashes.json",
        "member_manifest_sha256": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
    }
    selected = [{"rgb": "rgb/frame.png", "depth": "depth/frame.png"}]
    assert (
        runner._verified_member_hashes(root, selected, identity, tmp_path)[
            "groundtruth.txt"
        ]
        == members["groundtruth.txt"]
    )
    runner._verify_reference_snapshot(
        root / "groundtruth.txt", members["groundtruth.txt"]["sha256"]
    )
    (root / "groundtruth.txt").write_bytes(b"1 0 0 0 0 0 0 1\n")
    with pytest.raises(ValueError, match="Reference trajectory differs"):
        runner._verify_reference_snapshot(
            root / "groundtruth.txt", members["groundtruth.txt"]["sha256"]
        )
    (root / "rgb/frame.png").write_bytes(b"RGB pixels")
    with pytest.raises(ValueError, match="differs from verified archive"):
        runner._verified_member_hashes(root, selected, identity, tmp_path)


def test_archive_provenance_rejects_archive_receipt_hash_mismatch(tmp_path):
    runner = importlib.import_module(package + ".run")
    repo = tmp_path
    dataset_root = repo / "data/tum/rgbd_dataset_freiburg1_xyz"
    dataset_root.mkdir(parents=True)
    archive_path = repo / "data/archives/rgbd_dataset_freiburg1_xyz.tgz"
    archive_path.parent.mkdir(parents=True)
    archive_path.write_bytes(b"changed archive")
    official_url = (
        "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz"
    )
    resolved_url = (
        "https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/"
        "rgbd_dataset_freiburg1_xyz.tgz"
    )
    receipt = {
        "source_url": official_url,
        "resolved_url": resolved_url,
        "local_sha256": "a" * 64,
        "size_bytes": len(b"changed archive"),
    }
    (repo / "data/archives/rgbd_dataset_freiburg1_xyz.tgz.json").write_text(
        json.dumps(receipt)
    )
    (dataset_root / "provenance.json").write_text(
        json.dumps(
            {
                "source_url": official_url,
                "local_sha256": "a" * 64,
                "size_bytes": len(b"changed archive"),
            }
        )
    )

    with pytest.raises(ValueError, match="receipts do not match"):
        runner._archive_provenance(dataset_root, repo)


@pytest.mark.parametrize(
    ("acquisition", "secondary"),
    [([], {}), ({"local_sha256": None}, {}), ({}, [])],
)
def test_archive_provenance_rejects_malformed_receipt_fields(
    tmp_path, acquisition, secondary
):
    runner = importlib.import_module(package + ".run")
    repo = tmp_path
    dataset_root = repo / "data/tum/rgbd_dataset_freiburg1_xyz"
    dataset_root.mkdir(parents=True)
    acquisition_path = repo / "data/archives/rgbd_dataset_freiburg1_xyz.tgz.json"
    secondary_path = dataset_root / "provenance.json"
    acquisition_path.parent.mkdir(parents=True)
    acquisition_path.write_text(json.dumps(acquisition))
    secondary_path.write_text(json.dumps(secondary))

    with pytest.raises((TypeError, ValueError), match="Dataset receipt"):
        runner._archive_provenance(dataset_root, repo)


def test_runner_rejects_more_frames_than_available_before_backend_calls(tmp_path):
    from PIL import Image

    runner = importlib.import_module(package + ".run")
    root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    root.mkdir()
    for name in ("rgb", "depth"):
        (root / name).mkdir()
    for index in range(2):
        Image.fromarray(np.full((480, 640, 3), 128, np.uint8)).save(
            root / f"rgb/{index}.png"
        )
        Image.fromarray(np.full((480, 640), 10000, np.uint16)).save(
            root / f"depth/{index}.png"
        )
    (root / "rgb.txt").write_text("0 rgb/0.png\n0.03 rgb/1.png\n")
    (root / "depth.txt").write_text("0 depth/0.png\n0.03 depth/1.png\n")

    class MustNotRun:
        def estimate(self, source, target):
            raise AssertionError("backend ran before selection validation")

    with pytest.raises(ValueError, match="Insufficient associated frames"):
        runner.execute(root, tmp_path / "runs", count=3, engine=MustNotRun())
    assert not (tmp_path / "runs").exists()


def test_tracking_consumes_long_stream_without_retaining_old_images():
    references = {"colour": [], "depth": [], "valid": []}
    maximum_live_arrays = {name: 0 for name in references}

    def frames():
        for index in range(80):
            current = frame(index)
            for name, rows in references.items():
                rows.append(weakref.ref(getattr(current, name)))
            yield current

    class StreamingBackend:
        def estimate(self, source, target):
            gc.collect()
            for name, rows in references.items():
                live_arrays = sum(reference() is not None for reference in rows)
                maximum_live_arrays[name] = max(maximum_live_arrays[name], live_arrays)
            return backend.PairResult(True, translation(-0.1), "streaming fixture")

    records = tracking.track(frames(), StreamingBackend())
    assert len(records) == 80
    assert all(count <= 3 for count in maximum_live_arrays.values())


def test_dataset_association_resolution_and_zero_count(tmp_path):
    from PIL import Image

    (tmp_path / "rgb.txt").write_text("0 rgb.png\n.1 rgb2.png\n")
    (tmp_path / "depth.txt").write_text(".02 depth.png\n.119 depth2.png\n")
    rows, counts = dataset.associations(tmp_path, 1)
    assert rows[0]["depth_timestamp_s"] == 0.02 and counts["matched_rows"] == 2
    with pytest.raises(ValueError):
        dataset.associations(tmp_path, 0)
    Image.fromarray(np.zeros((2, 2, 3), np.uint8)).save(tmp_path / "rgb.png")
    Image.fromarray(np.full((2, 2), 5000, np.uint16)).save(tmp_path / "depth.png")
    with pytest.raises(ValueError):
        dataset.load_frame(tmp_path, rows[0])


def test_invalid_frame_arrays_and_duplicate_ids():
    source = frame(0)
    with pytest.raises(ValueError):
        dataset.RGBDFrame(
            "bad",
            float("nan"),
            0,
            source.calibration,
            source.colour,
            source.depth,
            source.valid,
        )
    with pytest.raises(ValueError):
        dataset.RGBDFrame(
            "bad",
            0,
            0,
            source.calibration,
            source.colour,
            source.depth * 3,
            source.valid,
        )
    with pytest.raises(ValueError):
        tracking.track([source, source], FakeBackend([]))


def test_all_failed_and_empty_tracking():
    records = tracking.track([frame(0, False), frame(1, False)], FakeBackend([]))
    scored = evaluation.evaluate(records, [(0, translation(0)), (0.03, translation(0))])
    assert scored["failed_observations"] == 2
    assert scored["position_rmse_m"] is None
    assert scored["tracked_fraction"] == 0
    assert tracking.track([], FakeBackend([])) == []


def test_independent_runs_have_distinct_origins():
    from experiments.shared.contracts import require_same_origin

    first = tracking.track([frame(0)], FakeBackend([]))
    second = tracking.track([frame(0)], FakeBackend([]))
    with pytest.raises(ValueError):
        require_same_origin(first[0].pose, second[0].pose)


def test_runner_associations_use_snapshot_tables(tmp_path, monkeypatch):
    runner = importlib.import_module(package + ".run")
    root = tmp_path / "dataset"
    root.mkdir()
    for name in ("rgb.txt", "depth.txt"):
        (root / name).write_text("0 rgb.png\n")
    seen = []
    original = dataset.associations

    def association(path, count):
        seen.append(path)
        if path == root:
            return original(path, count)
        assert (path / "rgb.txt").read_bytes() == (root / "rgb.txt").read_bytes()
        raise ValueError("fixture stop")

    monkeypatch.setattr(dataset, "associations", association)
    with pytest.raises(ValueError, match="fixture stop"):
        runner.execute(root, tmp_path / "runs", count=1, engine=FakeBackend([]))
    assert seen == [root, next((tmp_path / "runs").iterdir()) / "input/observations"]


def test_depth_truncation_boundary_is_not_usable():
    source = frame(0)
    with pytest.raises(ValueError):
        dataset.RGBDFrame(
            "boundary",
            0,
            0,
            source.calibration,
            source.colour,
            np.full(source.depth.shape, 4.0),
            source.valid,
        )


def test_backend_rejects_empty_converted_images(monkeypatch):
    from types import SimpleNamespace

    engine = backend.CPUOdometry()
    monkeypatch.setattr(
        engine,
        "_image",
        lambda frame: SimpleNamespace(depth=np.zeros(frame.depth.shape)),
    )
    result = engine.estimate(frame(0), frame(1))
    assert not result.success and result.reason == "no usable converted depth"
