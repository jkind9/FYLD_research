"""Complete a small CPU inspection with exact batch scoring and checked recovery."""

import argparse
import json
import logging
from pathlib import Path
from time import perf_counter

import numpy as np
import psutil

from experiments.geometry_validation.src.icl import select_ids
from experiments.shared.contracts import Pose
from experiments.shared.exporting import _cloud_preview
from experiments.shared.runs import Run, verify_run, write_json

from .backend import reconstruct
from .dataset import copy_checked, read_reference, snapshot_frame, snapshot_metadata
from .evaluation import SurfaceScorer, distance_summary
from .export import export_shard
from .recovery import combine_summaries, recover_frame, validate_prior
from .review import build_review
from .run import HYPERPARAMETERS as CONTROL_SETTINGS

HYPERPARAMETERS = {
    **CONTROL_SETTINGS,
    "coverage_query_layout": {
        "value": "exact joined-cloud query, desktop memory",
        "source": "n/a equivalent distance algorithm",
    },
    "preview": {
        "value": "all selected points, no thinning",
        "source": "n/a display only",
    },
}
LOGGER = logging.getLogger(__name__)


def _frame(
    run: Run,
    dataset: Path,
    key: int,
    origin: Pose | None,
    scorer: SurfaceScorer,
    prior: Path,
    prior_verified: bool,
    verified_hashes: dict[str, str] | None,
) -> tuple[dict, Pose]:
    started = perf_counter()
    frame = snapshot_frame(dataset, run.path / "input/dataset", key)
    origin = frame.observation.pose if origin is None else origin
    for kind in ("rgb", "depth"):
        copy_checked(
            run.path / f"input/dataset/trajectory2/{kind}/{key}.png",
            run.path / f"input/{key}/{kind}.png",
        )
    write_json(run.path / f"input/{key}/observation.json", frame.observation.to_dict())
    loaded = perf_counter()
    stages = reconstruct(frame, origin)
    built = perf_counter()
    distances = scorer.observe(stages.model, update_reference=False)
    accuracy = distance_summary(distances) if len(distances) else None
    recovered = recover_frame(
        prior,
        str(key),
        run.path / "input/dataset",
        stages.model,
        accuracy,
        run.path / "metadata/recovered",
        verified_hashes,
    )
    scored = perf_counter()
    record = {
        **export_shard(
            run.path / f"output/{key}",
            run.path / f"debug/{key}",
            frame,
            stages,
            distances,
        ),
        "accuracy": accuracy,
        "pose_source": "supplied",
        "negative_controls": (
            recovered["negative_controls"] if recovered and prior_verified else None
        ),
        "negative_control_source": (
            "verified complete-run record"
            if recovered and prior_verified
            else "not measured; incomplete prior records are diagnostic only"
        ),
        "model_from_world": (
            frame.model_from_first @ np.linalg.inv(frame.world_from_first)
        ).tolist(),
        "timings_seconds": {
            "copy_decode": loaded - started,
            "geometry": built - loaded,
            "forward_scoring_and_recovery": scored - built,
            "export": perf_counter() - scored,
        },
    }
    write_json(run.path / f"output/{key}/stages.json", record)
    LOGGER.info("Frame %s reconstructed and scored: %s points", key, len(stages.model))
    return record, origin


def execute(
    dataset: Path,
    ids: list[int],
    threshold_m: float,
    prior: Path,
    runs: Path,
    repo: Path,
) -> Path:
    ids = select_ids(ids)
    configuration = {
        "experiment": "04_surface_reconstruction",
        "device": "CPU",
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
        "recovered_run": str(prior.resolve()),
        "reference_enters_backend": False,
    }
    started = perf_counter()
    with Run(runs, repo, configuration) as run:
        provenance = validate_prior(
            prior, dataset, ids, threshold_m, repo, run.path / "metadata/recovered"
        )
        snapshot_metadata(dataset, run.path / "input/dataset")
        reference = run.path / "input/evaluation/living-room.ply"
        copy_checked(dataset / "reference_surface/living-room.ply", reference)
        scorer = SurfaceScorer(read_reference(reference), threshold_m)
        frames: list[dict] = []
        origin: Pose | None = None
        for key in ids:
            record, origin = _frame(
                run,
                dataset,
                key,
                origin,
                scorer,
                prior,
                provenance["prior_artifacts_verified"],
                provenance["verified_artifact_hashes"],
            )
            frames.append(record)
        cloud = np.concatenate(
            [
                np.load(run.path / f"output/{key}/model.npy", allow_pickle=False)
                for key in ids
            ]
        )
        reverse_started = perf_counter()
        LOGGER.info("Scoring full reference against accumulated surface")
        scorer.cover_accumulated(cloud)
        reverse_seconds = perf_counter() - reverse_started
        controls = [
            f for f in frames if f["points"] > 0 and f["negative_controls"] is not None
        ]
        metrics = {
            **scorer.summary(),
            "negative_control_frame_ids": [int(f["frame_id"]) for f in controls],
            "negative_control_clean_accuracy": (
                combine_summaries([f["accuracy"] for f in controls])
                if controls
                else None
            ),
            "negative_controls": (
                {
                    name: combine_summaries(
                        [f["negative_controls"][name] for f in controls]
                    )
                    for name in ("double_depth", "inverse_pose")
                }
                if controls
                else None
            ),
            "recovery": provenance,
            "timings_seconds": {
                "geometry": sum(f["timings_seconds"]["geometry"] for f in frames),
                "reverse_scoring": reverse_seconds,
            },
        }
        preview_started = perf_counter()
        colors = np.concatenate(
            [
                np.load(run.path / f"output/{key}/rgb.npy", allow_pickle=False)
                for key in ids
            ]
        )
        _cloud_preview(run.path / "debug/surface.png", cloud, colors)
        metrics["timings_seconds"]["preview"] = perf_counter() - preview_started
        metrics["timings_seconds"]["before_publication"] = perf_counter() - started
        memory = psutil.Process().memory_info()
        metrics["memory"] = {
            "rss_bytes_at_end": memory.rss,
            "peak_working_set_bytes": getattr(memory, "peak_wset", None),
            "scope": "desktop process, includes joined cloud, reference scoring and full-point preview",
        }
        metrics["representation_bytes"] = sum(
            (run.path / f"output/{key}/surface.ply").stat().st_size for key in ids
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
        if provenance["prior_artifacts_verified"]:
            verify_run(prior)
    verify_run(run.path)
    return run.path


def republish_review(source: Path, runs: Path, repo: Path) -> Path:
    """Preserve verified numerical artifacts while correcting confidence labels."""
    verify_run(source)
    configuration = json.loads((source / "metadata/configuration.json").read_text())
    configuration = {
        **configuration,
        "republication_source": str(source.resolve()),
        "reason": "exclude fault summaries imported before incomplete-run integrity was classified",
    }
    with Run(runs, repo, configuration) as run:
        for name in ("input", "output", "debug"):
            for artifact in (source / name).rglob("*"):
                if artifact.is_file():
                    copy_checked(artifact, run.path / artifact.relative_to(source))
        for artifact in (source / "metadata").rglob("*"):
            if artifact.is_file():
                copy_checked(
                    artifact,
                    run.path
                    / "metadata/previous_publication"
                    / artifact.relative_to(source),
                )
        metrics = json.loads((source / "output/metrics.json").read_text())
        metrics["timing_scope"] = (
            "computation in verified source run; republication copying has separate metadata/timing.json"
        )
        frames = json.loads((source / "metadata/frames.json").read_text())
        recovery = metrics["recovery"]
        trusted = recovery.get("prior_artifacts_verified", False)
        if not trusted:
            metrics = {
                **metrics,
                "negative_controls": None,
                "negative_control_clean_accuracy": None,
                "negative_control_frame_ids": [],
                "recovery": {**recovery, "prior_artifacts_verified": False},
            }
            frames = [
                {
                    **frame,
                    "negative_controls": None,
                    "negative_control_source": "not measured; incomplete prior records are diagnostic only",
                }
                for frame in frames
            ]
        for frame in frames:
            write_json(run.path / f"output/{frame['frame_id']}/stages.json", frame)
        write_json(run.path / "output/metrics.json", metrics)
        surface = json.loads((source / "output/surface.json").read_text())
        write_json(run.path / "output/surface.json", {**surface, "shards": frames})
        write_json(run.path / "metadata/frames.json", frames)
        build_review(run.path, metrics, frames)
        verify_run(source)
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--frame-ids", type=int, nargs="+", required=True)
    parser.add_argument("--threshold-m", type=float, required=True)
    parser.add_argument("--recover-run", type=Path, required=True)
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
            args.recover_run,
            args.runs,
            Path(__file__).resolve().parents[3],
        ),
    )


if __name__ == "__main__":
    main()
