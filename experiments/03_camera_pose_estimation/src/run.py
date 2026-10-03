"""Authorized CPU tracking smoke trial with independent scoring and receipts."""

import argparse
import importlib
import json
import logging
import os
import re
from pathlib import Path

import psutil

from experiments.datasets.acquisition import sha256
from experiments.shared.geometry import validate_transform
from experiments.shared.runs import Run, verify_run, write_json

from . import dataset, evaluation, reporting, tracking
from .backend import CPUOdometry

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


def _observations(root: Path, rows: list[dict], run: Run):
    for row in rows:
        with run.measure("observation_load", frames=1):
            for key in ("rgb", "depth"):
                source = root / row[key]
                if source.is_symlink() or not source.resolve().is_relative_to(
                    root.resolve()
                ):
                    raise ValueError("Observation escapes dataset")
                copy_checked(source, run.path / "input/observations" / row[key])
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
) -> Path:
    repo = Path(__file__).resolve().parents[3]
    selected_rows, selected_counts = dataset.associations(root, count)
    sequence = root.name
    configuration = {
        "hyperparameters": _selected_hyperparameters(sequence, len(selected_rows)),
        "sequence": sequence,
        "selection": "first consecutive associated observations; no stride",
        "selected_frames": len(selected_rows),
        "dataset": str(root.resolve()),
        "dataset_provenance": sequence_identity
        or {"status": "unverified direct runner input"},
        "device": "CPU",
        "gpu": "not used",
    }
    process = psutil.Process()
    with Run(run_root, repo, configuration) as run:
        for name in ("rgb.txt", "depth.txt"):
            copy_checked(root / name, run.path / "input/observations" / name)
        rows, counts = dataset.associations(run.path / "input/observations", count)
        if rows != selected_rows or counts != selected_counts:
            raise ValueError("Dataset associations changed after run configuration")
        write_json(
            run.path / "output/associations.json", {"rows": rows, "counts": counts}
        )
        with run.measure("backend_load", frames=0):
            engine = CPUOdometry() if engine is None else engine
        records = tracking.track(
            _observations(root, rows, run), engine, run, origin_namespace=run.path.name
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
            references = evaluation.read_references(reference_path)
            metrics = evaluation.evaluate(records, references)
        write_json(run.path / "output/metrics.json", metrics)
        with run.measure("reporting", frames=count):
            reporting.report(run.path, records, metrics)
        memory = process.memory_info()
        write_json(
            run.path / "metadata/resources.json",
            {
                "rss_bytes_after_report": memory.rss,
                "peak_wset_bytes": getattr(memory, "peak_wset", None),
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
        }
    raise ValueError(
        "Dataset must use one of the configured local Freiburg1 data paths"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument(
        "--runs", type=Path, default=Path(__file__).resolve().parents[1] / "runs"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.frames < 1:
        parser.error("--frames must be a positive integer")
    repo = Path(__file__).resolve().parents[3]
    try:
        sequence_identity = _archive_provenance(args.dataset, repo)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    path = execute(
        args.dataset,
        args.runs,
        args.frames,
        sequence_identity=sequence_identity,
    )
    LOGGER.info("Review: %s", path / "review.html")
    LOGGER.info("Metrics: %s", path / "output/metrics.json")
    LOGGER.info("Timing: %s", path / "metadata/timing.json")


if __name__ == "__main__":
    main()
