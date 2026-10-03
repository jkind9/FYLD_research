"""Build and independently score a CPU surface using explicit supplied ICL inputs."""

import argparse
import logging
from pathlib import Path
from time import perf_counter

import numpy as np
import psutil

from experiments.geometry_validation.src.icl import select_ids
from experiments.shared.contracts import Pose
from experiments.shared.runs import Run, verify_run, write_json

from .backend import fault_points, reconstruct
from .dataset import copy_checked, read_reference, snapshot_frame, snapshot_metadata
from .evaluation import DistanceTotals, SurfaceScorer, distance_summary
from .export import export_shard
from .review import build_review

HYPERPARAMETERS = {
    "scene": {
        "value": "clean ICL living-room trajectory2",
        "source": "inherited data/icl_nuim/conventions.json:3",
    },
    "depth_units_per_metre": {
        "value": 5000,
        "source": "inherited experiments/geometry_validation/src/control.py:37",
    },
    "depth_validity": {
        "value": "positive finite; all pixels; no clipping",
        "source": "inherited experiments/geometry_validation/src/run.py:31",
    },
    "backend": {
        "value": "direct_cpu_point_accumulation",
        "source": "n/a independent geometry control",
    },
    "reference_selection": {
        "value": "all published vertices; no fitted transform or scale",
        "source": "n/a explicitly global reference coverage",
    },
    "negative_controls": {
        "value": ["double_depth", "inverse_pose"],
        "source": "n/a deliberate analytic faults",
    },
    "query_batch": {"value": 100000, "source": "n/a exact-query memory scheduling"},
    "query_workers": {"value": 1, "source": "n/a CPU scheduling"},
}
LOGGER = logging.getLogger(__name__)


def _process_frame(
    run: Run,
    dataset: Path,
    frame_id: int,
    origin: Pose | None,
    scorer: SurfaceScorer,
    faults: dict[str, DistanceTotals],
) -> tuple[dict, Pose]:
    started = perf_counter()
    snapshot = run.path / "input/dataset"
    frame = snapshot_frame(dataset, snapshot, frame_id)
    origin = frame.observation.pose if origin is None else origin
    key = str(frame_id)
    for kind in ("rgb", "depth"):
        copy_checked(
            snapshot / f"trajectory2/{kind}/{key}.png",
            run.path / f"input/{key}/{kind}.png",
        )
    write_json(run.path / f"input/{key}/observation.json", frame.observation.to_dict())
    loaded = perf_counter()
    stages = reconstruct(frame, origin)
    built = perf_counter()
    distances = scorer.observe(stages.model)
    fault_scores = {}
    for fault, totals in faults.items():
        errors = scorer.distances(fault_points(frame, fault))
        totals.add(errors)
        fault_scores[fault] = distance_summary(errors) if len(errors) else None
    scored = perf_counter()
    shard = export_shard(
        run.path / f"output/{key}", run.path / f"debug/{key}", frame, stages, distances
    )
    metadata = {
        **shard,
        "accuracy": distance_summary(distances) if len(distances) else None,
        "negative_controls": fault_scores,
        "pose_source": "supplied",
        "model_from_world": (
            frame.model_from_first @ np.linalg.inv(frame.world_from_first)
        ).tolist(),
        "timings_seconds": {
            "copy_decode": loaded - started,
            "geometry": built - loaded,
            "scoring": scored - built,
            "export": perf_counter() - scored,
        },
    }
    write_json(run.path / f"output/{key}/stages.json", metadata)
    LOGGER.info(
        "Frame %s: %s points, %.2f s", key, shard["points"], perf_counter() - started
    )
    return metadata, origin


def execute(
    dataset: Path, ids: list[int], threshold_m: float, runs: Path, repo: Path
) -> Path:
    ids = select_ids(ids)
    if not np.isfinite(threshold_m) or threshold_m <= 0:
        raise ValueError("Reporting threshold must be positive finite metres")
    configuration = {
        "experiment": "04_surface_reconstruction",
        "frame_ids": ids,
        "dataset_source": str(dataset.resolve()),
        "pose_role": "supplied",
        "hyperparameters": {
            **HYPERPARAMETERS,
            "frame_ids": {"value": ids, "source": "explicit caller selection"},
            "threshold_m": {
                "value": threshold_m,
                "source": "explicit caller reporting distance",
            },
        },
        "device": "CPU",
        "reference_enters_backend": False,
    }
    started = perf_counter()
    with Run(runs, repo, configuration) as run:
        snapshot_metadata(dataset, run.path / "input/dataset")
        reference_path = run.path / "input/evaluation/living-room.ply"
        copy_checked(dataset / "reference_surface/living-room.ply", reference_path)
        scorer = SurfaceScorer(read_reference(reference_path), threshold_m)
        reference_loaded = perf_counter()
        frames: list[dict] = []
        origin: Pose | None = None
        faults = {name: DistanceTotals() for name in ("double_depth", "inverse_pose")}
        for frame_id in ids:
            record, origin = _process_frame(
                run, dataset, frame_id, origin, scorer, faults
            )
            frames.append(record)
        metrics = {
            **scorer.summary(),
            "negative_controls": {
                name: total.summary() for name, total in faults.items()
            },
            "timings_seconds": {
                "reference_copy_load_index": reference_loaded - started,
                "frames": sum(sum(f["timings_seconds"].values()) for f in frames),
                "geometry": sum(f["timings_seconds"]["geometry"] for f in frames),
                "scoring": sum(f["timings_seconds"]["scoring"] for f in frames),
                "before_publication": perf_counter() - started,
            },
        }
        memory = psutil.Process().memory_info()
        metrics["memory"] = {
            "rss_bytes_at_end": memory.rss,
            "peak_working_set_bytes": getattr(memory, "peak_wset", None),
            "scope": "whole process including reference scorer and imports; Windows lifetime peak when available",
        }
        metrics["representation_bytes"] = sum(
            (run.path / f"output/{f['frame_id']}/surface.ply").stat().st_size
            for f in frames
        )
        write_json(run.path / "output/metrics.json", metrics)
        np.save(
            run.path / "output/reference_distance.npy",
            scorer.reference_distances,
            allow_pickle=False,
        )
        write_json(
            run.path / "output/surface.json",
            {
                "representation": "observed point shards; no fusion or filled holes",
                "coordinates": "publisher_reference_surface",
                "units": "metres",
                "shards": frames,
            },
        )
        write_json(run.path / "metadata/frames.json", frames)
        build_review(run.path, metrics, frames)
        # Required semantic outputs must exist before the shared lifecycle publishes complete.
        if sum(f["points"] for f in frames) != metrics["reconstruction_points"]:
            raise ValueError("Surface index point count mismatch")
        if not (run.path / "review.html").is_file() or len(frames) != len(ids):
            raise ValueError("Missing required surface outputs")
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--frame-ids", type=int, nargs="+", required=True)
    parser.add_argument("--threshold-m", type=float, required=True)
    parser.add_argument(
        "--runs", type=Path, default=Path(__file__).resolve().parents[1] / "runs"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    LOGGER.info(
        "Complete run: %s",
        execute(
            args.dataset,
            args.frame_ids,
            args.threshold_m,
            args.runs,
            Path(__file__).resolve().parents[3],
        ),
    )


if __name__ == "__main__":
    main()
