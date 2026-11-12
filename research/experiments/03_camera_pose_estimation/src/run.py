"""Authorized CPU tracking smoke trial with independent scoring and receipts."""

import argparse
import importlib
import json
import logging
import os
import re
import threading
import time
from pathlib import Path

import psutil

from experiments.datasets.acquisition import sha256
from experiments.shared.geometry import validate_transform
from experiments.shared.runs import Run, verify_run, write_json

from . import dataset, evaluation, reporting, tracking
from .backend import CPUOdometry
from .supervisor import (
    MEMORY_LIMIT_BYTES,
    POLL_INTERVAL_S,
    WALL_CLOCK_LIMIT_S,
    WindowsProcessMemoryLimit,
    supervise,
)

LOGGER = logging.getLogger(__name__)

HYPERPARAMETERS = {
    "frames": {"value": 30, "source": "confirmed 2026-10-02"},
    "sequence": {
        "value": "rgbd_dataset_freiburg1_xyz",
        "source": "confirmed 2026-10-02",
    },
    "selection": {
        "value": "first consecutive associated observations; no stride",
        "source": "confirmed 2026-10-02",
    },
    "intrinsics": {
        "value": [640, 480, 525, 525, 319.5, 239.5],
        "source": "confirmed 2026-10-02; TUM ROS defaults",
    },
    "depth_scale": {"value": 5000, "source": "inherited data/README.md:31"},
    "association_tolerance_s": {"value": 0.02, "source": "confirmed 2026-10-02"},
    "backend": {"value": "Open3D 0.19.0 CPU hybrid", "source": "confirmed 2026-10-02"},
    "iterations": {"value": [20, 10, 5], "source": "confirmed 2026-10-02"},
    "depth_range_m": {"value": [0, 4], "source": "confirmed 2026-10-02"},
    "depth_diff_max_m": {"value": 0.03, "source": "confirmed 2026-10-02"},
    "pair_initialization": {"value": "identity", "source": "confirmed 2026-10-02"},
    "reset_gap_s": {"value": 0.1, "source": "confirmed 2026-10-02"},
    "reset_failure": {
        "value": "next usable observation anchors new segment",
        "source": "confirmed 2026-10-02",
    },
    "alignment": {
        "value": "first matched reference per segment; scale one",
        "source": "confirmed 2026-10-02",
    },
    "relative_error": {
        "value": "adjacent successful matched edges within segment",
        "source": "confirmed 2026-10-02",
    },
    "reference_quaternions": {
        "value": "unit-normalize finite nonzero publisher xyzw quaternions for scoring",
        "source": "n/a rounded reference representation; original bytes preserved",
    },
    "rgbd_representation": {
        "value": "metric float32 depth, scale=1, truncation=4, intensity=True",
        "source": "n/a backend representation",
    },
    "cpu_threads": {
        "value": "existing runtime defaults; no override",
        "source": "n/a observe desktop runtime",
    },
    "reporting": {
        "value": "all statuses and 320x240 thumbnails; desktop trajectory plot",
        "source": "n/a presentation only",
    },
    "wall_clock_limit_s": {
        "value": WALL_CLOCK_LIMIT_S,
        "source": "confirmed 2026-10-03",
    },
    "process_memory_limit_bytes": {
        "value": MEMORY_LIMIT_BYTES,
        "source": "confirmed 2026-10-03; Windows Job Object",
    },
    "supervisor_poll_interval_s": {
        "value": POLL_INTERVAL_S,
        "source": "n/a supervisor scheduling cadence, not an estimator setting",
    },
}

copy_checked = importlib.import_module(
    "experiments.04_surface_reconstruction.src.dataset"
).copy_checked


def validate_outputs(root: Path, count: int) -> None:
    required = [
        "output/poses.json",
        "output/metrics.json",
        "output/associations.json",
        "review.html",
        "debug/trajectory.png",
        "input/evaluation/groundtruth.txt",
        "viewer.html",
        "metadata/artifact_roles.json",
    ]
    for relative in required:
        if not (root / relative).is_file():
            raise ValueError(f"Required tracking artifact missing: {relative}")
    records = json.loads((root / "output/poses.json").read_text())["records"]
    if len(records) != count or len({r["frame_id"] for r in records}) != count:
        raise ValueError("Selected observations need exactly one status")
    for record in records:
        if record["status"] == "tracked" and record["pose"] is None:
            raise ValueError("Tracked record requires pose")
        if record["pose"] is not None:
            validate_transform(record["pose"]["T_world_camera"])
        for kind in ("rgb", "depth"):
            if not (root / "debug" / f"{record['frame_id']}_{kind}.png").is_file():
                raise ValueError("Missing observation thumbnail")
    links = re.findall(
        r'(?:href|src)="([^"]+)"', (root / "review.html").read_text(encoding="utf-8")
    )
    for link in links:
        # Timing is written by Run immediately before its publication manifest.
        if link == "metadata/timing.json":
            continue
        target = root / link
        if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Report link does not resolve: {link}")
    associations = json.loads((root / "output/associations.json").read_text())["rows"]
    for row in associations:
        for kind in ("rgb", "depth"):
            if not (root / "input/observations" / row[kind]).is_file():
                raise ValueError("Required observation snapshot missing")


def _verify_reference_snapshot(path: Path, expected_sha256: str) -> None:
    if sha256(path) != expected_sha256:
        raise ValueError("Reference trajectory differs from verified archive")


def _observations(root: Path, rows: list[dict], run: Run, member_hashes=None):
    for row in rows:
        with run.measure("observation_load", frames=1):
            for key in ("rgb", "depth"):
                source = root / row[key]
                if source.is_symlink() or not source.resolve().is_relative_to(
                    root.resolve()
                ):
                    raise ValueError("Observation escapes dataset")
                copy_checked(source, run.path / "input/observations" / row[key])
                if member_hashes is not None:
                    relative = row[key]
                    copied = run.path / "input/observations" / relative
                    if sha256(copied) != member_hashes[relative]["sha256"]:
                        raise ValueError(
                            f"Observation changed after archive verification: {relative}"
                        )
            frame = dataset.load_frame(run.path / "input/observations", row)
            reporting.thumbnail(frame, run.path)
        yield frame


def _selected_hyperparameters(sequence: str, count: int) -> dict:
    selected = {name: dict(value) for name, value in HYPERPARAMETERS.items()}
    selected.update(
        {
            "frames": {
                "value": count,
                "source": "actual selected observations recorded in run metadata",
            },
            "sequence": {
                "value": sequence,
                "source": "dataset directory name recorded in run metadata",
            },
            "selection": {
                "value": f"first {count} consecutive associated observations; no stride",
                "source": "actual association rows recorded in run metadata",
            },
        }
    )
    return selected


def execute(
    root: Path,
    run_root: Path,
    count: int = 30,
    engine=None,
    sequence_identity: dict | None = None,
    run_path: Path | None = None,
    supervised: bool = False,
) -> Path:
    repo = Path(__file__).resolve().parents[3]
    selected_rows, selected_counts = dataset.associations(root, count)
    sequence = root.name
    member_hashes = None
    if sequence_identity is not None:
        member_hashes = _verified_member_hashes(
            root, selected_rows, sequence_identity, repo
        )
    configuration = {
        "hyperparameters": _selected_hyperparameters(sequence, len(selected_rows)),
        "sequence": sequence,
        "selection": "first consecutive associated observations; no stride",
        "selected_frames": len(selected_rows),
        "dataset": str(root.resolve()),
        "dataset_provenance": sequence_identity
        or {"status": "unverified direct runner input"},
        "reference_sha256": (
            None
            if member_hashes is None
            else member_hashes["groundtruth.txt"]["sha256"]
        ),
        "device": "CPU",
        "gpu": "not used",
        "execution_limits": {
            "wall_clock_seconds": WALL_CLOCK_LIMIT_S,
            "wall_clock_scope": "worker launch through source capture, backend, estimation, scoring and reports",
            "process_memory_bytes": MEMORY_LIMIT_BYTES,
            "process_memory_measure": "Windows Job Object per-process commit limit",
            "monitor_poll_interval_seconds": POLL_INTERVAL_S,
            "enforced_by_supervisor": supervised,
        },
    }
    process = psutil.Process()
    run = Run(run_root, repo, configuration)
    if run_path is not None:
        run.path = run_path
    with run:
        for name in ("rgb.txt", "depth.txt"):
            copy_checked(root / name, run.path / "input/observations" / name)
            if (
                member_hashes is not None
                and sha256(run.path / "input/observations" / name)
                != member_hashes[name]["sha256"]
            ):
                raise ValueError(
                    f"Dataset table changed after archive verification: {name}"
                )
        rows, counts = dataset.associations(run.path / "input/observations", count)
        if rows != selected_rows or counts != selected_counts:
            raise ValueError("Dataset associations changed after run configuration")
        write_json(
            run.path / "output/associations.json", {"rows": rows, "counts": counts}
        )
        with run.measure("backend_load", frames=0):
            engine = CPUOdometry() if engine is None else engine
        records = tracking.track(
            _observations(root, rows, run, member_hashes),
            engine,
            run,
            origin_namespace=run.path.name,
        )
        run.set_processed_frames(len(records))
        write_json(
            run.path / "output/poses.json",
            {"schema_version": 1, "records": [r.to_dict() for r in records]},
        )
        # Reference file is deliberately first opened after all estimator output is persisted.
        with run.measure("evaluation", frames=len(records)):
            reference_path = run.path / "input/evaluation/groundtruth.txt"
            copy_checked(root / "groundtruth.txt", reference_path)
            if member_hashes is not None:
                _verify_reference_snapshot(
                    reference_path, member_hashes["groundtruth.txt"]["sha256"]
                )
            references = evaluation.read_references(reference_path)
            metrics = evaluation.evaluate(records, references)
        write_json(run.path / "output/metrics.json", metrics)
        with run.measure("reporting", frames=count):
            reporting.report(run.path, records, metrics)
        memory = process.memory_info()
        job_memory = WindowsProcessMemoryLimit.current_process_memory_info()
        write_json(
            run.path / "metadata/resources.json",
            {
                "rss_bytes_after_report": memory.rss,
                "peak_wset_bytes": getattr(memory, "peak_wset", None),
                "peak_job_process_commit_bytes": (
                    None if job_memory is None else job_memory[1]
                ),
                "process_threads": process.num_threads(),
                "cpu_count": os.cpu_count(),
                "thread_environment": {
                    k: os.environ.get(k)
                    for k in (
                        "OMP_NUM_THREADS",
                        "OPENBLAS_NUM_THREADS",
                        "MKL_NUM_THREADS",
                    )
                },
                "scope": "desktop process including backend import, evaluation and reporting; not mobile memory",
                "backend_build": getattr(engine, "build", None),
                "estimator_retention": "bounded current image pair",
            },
        )
        validate_outputs(run.path, count)
    verify_run(run.path)
    return run.path


def _archive_provenance(root: Path, repo: Path) -> dict[str, str]:
    known_sequences = {
        "rgbd_dataset_freiburg1_xyz": (
            Path("data/tum/rgbd_dataset_freiburg1_xyz"),
            Path("data/archives/rgbd_dataset_freiburg1_xyz.tgz.json"),
            Path("data/tum/rgbd_dataset_freiburg1_xyz/provenance.json"),
            "rgbd_dataset_freiburg1_xyz.tgz",
        ),
        "rgbd_dataset_freiburg1_desk": (
            Path("data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk"),
            Path("data/archives/rgbd_dataset_freiburg1_desk.tgz.json"),
            Path("data/tum/rgbd_dataset_freiburg1_desk/EXTRACTION.json"),
            "rgbd_dataset_freiburg1_desk.tgz",
        ),
    }
    selected_root = root.resolve(strict=True)
    for sequence, (
        relative_root,
        relative_acquisition_receipt,
        relative_secondary_receipt,
        archive_name,
    ) in known_sequences.items():
        expected_root = (repo / relative_root).resolve()
        if selected_root != expected_root:
            continue
        acquisition_path = repo / relative_acquisition_receipt
        secondary_path = repo / relative_secondary_receipt
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        secondary = json.loads(secondary_path.read_text(encoding="utf-8"))
        if not isinstance(acquisition, dict) or not isinstance(secondary, dict):
            raise TypeError("Dataset receipts must contain JSON objects")
        declared_sha256 = acquisition.get("local_sha256")
        declared_bytes = acquisition.get("bytes", acquisition.get("size_bytes"))
        secondary_sha256 = secondary.get("local_sha256")
        if (
            not isinstance(declared_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", declared_sha256)
            or type(declared_bytes) is not int
            or declared_bytes < 1
            or not isinstance(secondary_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", secondary_sha256)
        ):
            raise ValueError("Dataset receipt has invalid hash or byte-count fields")
        official_url = "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/" + archive_name
        resolved_url = (
            "https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/" + archive_name
        )
        archive_path = repo / "data/archives" / archive_name
        actual_bytes = archive_path.stat().st_size
        actual_sha256 = sha256(archive_path)
        if sequence == "rgbd_dataset_freiburg1_xyz":
            secondary_matches = secondary.get("source_url") == official_url
            secondary_bytes = secondary.get("size_bytes")
        else:
            secondary_matches = (
                secondary.get("archive") == archive_name
                and secondary.get("compressed_bytes") == declared_bytes
            )
            secondary_bytes = secondary.get("compressed_bytes")
        if (
            acquisition.get("source_url") != official_url
            or acquisition.get("resolved_url") != resolved_url
            or actual_bytes != declared_bytes
            or actual_sha256 != declared_sha256
            or not secondary_matches
            or secondary_sha256 != actual_sha256
            or type(secondary_bytes) is not int
            or secondary_bytes != actual_bytes
        ):
            raise ValueError("Dataset archive and acquisition receipts do not match")
        member_manifest_path = (
            repo / "experiments/datasets/tum_freiburg1_member_hashes.json"
        )
        member_manifest = json.loads(member_manifest_path.read_text(encoding="utf-8"))
        member_sequence = member_manifest.get("sequences", {}).get(sequence)
        if (
            member_manifest.get("schema_version") != 1
            or not isinstance(member_sequence, dict)
            or member_sequence.get("archive_sha256") != actual_sha256
            or member_sequence.get("archive_bytes") != actual_bytes
            or not isinstance(member_sequence.get("members"), dict)
        ):
            raise ValueError("Archive member hashes do not match the verified archive")
        return {
            "status": (
                "archive provenance checked; completed runs hash selected inputs "
                "in the run manifest"
            ),
            "sequence": sequence,
            "acquisition_receipt": relative_acquisition_receipt.as_posix(),
            "acquisition_receipt_sha256": sha256(acquisition_path),
            "secondary_receipt": relative_secondary_receipt.as_posix(),
            "secondary_receipt_sha256": sha256(secondary_path),
            "archive_bytes": str(actual_bytes),
            "archive_sha256": actual_sha256,
            "member_manifest": "experiments/datasets/tum_freiburg1_member_hashes.json",
            "member_manifest_sha256": sha256(
                repo / "experiments/datasets/tum_freiburg1_member_hashes.json"
            ),
        }
    raise ValueError(
        "Dataset must use one of the configured local Freiburg1 data paths"
    )


def _verified_member_hashes(
    root: Path, rows: list[dict], identity: dict, repo: Path
) -> dict:
    """Check source tables and selected images against the hash-verified archive."""
    manifest_relative = identity.get("member_manifest")
    expected_manifest_hash = identity.get("member_manifest_sha256")
    if not isinstance(manifest_relative, str) or not isinstance(
        expected_manifest_hash, str
    ):
        raise TypeError("Archive member hash manifest is missing from provenance")
    manifest_path = (repo / manifest_relative).resolve(strict=True)
    if not manifest_path.is_relative_to(repo.resolve()):
        raise ValueError("Archive member hash manifest escapes repository")
    if sha256(manifest_path) != expected_manifest_hash:
        raise ValueError("Archive member hash manifest changed after preflight")
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    sequence = identity.get("sequence")
    sequence_record = document.get("sequences", {}).get(sequence)
    if (
        document.get("schema_version") != 1
        or not isinstance(sequence_record, dict)
        or sequence_record.get("archive_sha256") != identity.get("archive_sha256")
        or sequence_record.get("archive_bytes")
        != int(identity.get("archive_bytes", -1))
        or not isinstance(sequence_record.get("members"), dict)
    ):
        raise ValueError("Archive member hash manifest does not match verified archive")
    members = sequence_record["members"]
    selected = {"rgb.txt", "depth.txt"}
    selected.update(path for row in rows for path in (row["rgb"], row["depth"]))
    for relative in sorted(selected):
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ValueError("Selected dataset member path is invalid")
        expected = members.get(relative)
        source = root / relative
        if (
            not isinstance(expected, dict)
            or type(expected.get("bytes")) is not int
            or expected["bytes"] < 1
            or not isinstance(expected.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected["sha256"])
        ):
            raise ValueError(f"Archive hash is missing for selected input: {relative}")
        if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Selected input escapes dataset: {relative}")
        if (
            not source.is_file()
            or source.stat().st_size != expected["bytes"]
            or sha256(source) != expected["sha256"]
        ):
            raise ValueError(
                f"Selected input differs from verified archive: {relative}"
            )
    reference = members.get("groundtruth.txt")
    if (
        not isinstance(reference, dict)
        or type(reference.get("bytes")) is not int
        or reference["bytes"] < 1
        or not isinstance(reference.get("sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"])
    ):
        raise TypeError("Archive hash is missing or invalid for reference trajectory")
    return members


def _worker_deadline_exit(_: Path) -> None:
    """Stop the worker even if its supervisor stops polling or disappears."""
    os._exit(124)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument(
        "--runs", type=Path, default=Path(__file__).resolve().parents[1] / "runs"
    )
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_run-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_release-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_provenance-json", help=argparse.SUPPRESS)
    parser.add_argument("--_deadline-monotonic", type=float, help=argparse.SUPPRESS)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.frames < 1:
        parser.error("--frames must be a positive integer")
    repo = Path(__file__).resolve().parents[3]
    if args._worker:
        if (
            args._run_path is None
            or args._release_file is None
            or args._provenance_json is None
            or args._deadline_monotonic is None
        ):
            parser.error("supervised worker requires a run path and release file")
        deadline = time.monotonic() + 60
        while not args._release_file.exists():
            if time.monotonic() >= deadline:
                parser.error(
                    "supervisor did not release worker before startup deadline"
                )
            time.sleep(0.02)
        try:
            release = json.loads(args._release_file.read_text(encoding="utf-8"))
            worker_pid = release["worker_pid"]
            process_memory_limit_bytes = release["process_memory_limit_bytes"]
            if worker_pid != os.getpid():
                parser.error("supervisor release does not name this worker process")
            if process_memory_limit_bytes != MEMORY_LIMIT_BYTES:
                parser.error("supervisor release has an unexpected process limit")
            if (
                WindowsProcessMemoryLimit.current_process_memory_limit()
                != MEMORY_LIMIT_BYTES
            ):
                parser.error(
                    "worker is not under the configured Windows process memory limit"
                )
            os.environ["FYLD_TRACKING_JOB_LIMIT_BYTES"] = str(
                process_memory_limit_bytes
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            parser.error(f"invalid supervisor release: {error}")
        sequence_identity = json.loads(args._provenance_json)
        if not isinstance(sequence_identity, dict):
            parser.error("supervisor provenance must be a JSON object")
        try:
            if (
                os.environ.get("FYLD_TRACKING_JOB_LIMIT_BYTES")
                != str(MEMORY_LIMIT_BYTES)
            ):
                parser.error("worker is not under the approved process memory limit")
            verified_identity = _archive_provenance(args.dataset, repo)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            parser.error(str(error))
        if sequence_identity != verified_identity:
            parser.error(
                "supervisor provenance does not match current dataset receipts"
            )
        watchdog = threading.Timer(
            max(
                0.0,
                min(
                    args._deadline_monotonic,
                    time.monotonic() + WALL_CLOCK_LIMIT_S,
                )
                - time.monotonic(),
            ),
            _worker_deadline_exit,
            args=(args._run_path,),
        )
        watchdog.daemon = True
        watchdog.start()
        try:
            path = execute(
                args.dataset,
                args.runs,
                args.frames,
                sequence_identity=sequence_identity,
                run_path=args._run_path,
                supervised=True,
            )
        finally:
            watchdog.cancel()
        LOGGER.info("Review: %s", path / "review.html")
        LOGGER.info("Metrics: %s", path / "output/metrics.json")
        LOGGER.info("Timing: %s", path / "metadata/timing.json")
        return
    try:
        sequence_identity = _archive_provenance(args.dataset, repo)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    path = supervise(
        dataset_path=args.dataset,
        run_root=args.runs,
        frames=args.frames,
        sequence_identity=sequence_identity,
        repo=repo,
    )
    LOGGER.info("Review: %s", path / "review.html")
    LOGGER.info("Metrics: %s", path / "output/metrics.json")
    LOGGER.info("Timing: %s", path / "metadata/timing.json")


if __name__ == "__main__":
    main()
