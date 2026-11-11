"""Surface stage: replay layer 4's published accumulation from saved distances."""

from pathlib import Path

import numpy as np

from experiments.evaluation import schema
from experiments.evaluation.stages.common import (
    file_sha256,
    owner,
    read_json,
    require_keys,
    require_same,
    scope,
    verified_run,
)

EVALUATION = "experiments.04_surface_reconstruction.src.evaluation"
METHOD = "layer4_point_surface"
REPORTED = (
    "threshold_m",
    "accuracy",
    "reconstruction_within_threshold_fraction",
    "reference_coverage_fraction",
)


def _reference_sha256(run_path: Path, stored: dict) -> str:
    """Hash the reference copied into the run; recovery runs must agree with it."""
    copies = sorted((run_path / "input/evaluation").glob("*.ply"))
    if len(copies) != 1:
        raise ValueError(f"expected one copied reference surface, found {len(copies)}")
    digest = file_sha256(copies[0])
    recorded = (stored.get("recovery") or {}).get("reference_sha256")
    if recorded is not None and recorded != digest:
        raise ValueError("copied reference differs from the run's recorded reference")
    return digest


def score(run_path: Path, threshold_m: float) -> dict:
    """Same order and arithmetic as `SurfaceScorer`: per-frame totals, then reference."""
    evaluation = owner(EVALUATION)
    frame_ids = read_json(run_path / "metadata/configuration.json")["frame_ids"]
    totals, within = evaluation.DistanceTotals(), 0
    for frame in frame_ids:
        distances = np.load(run_path / "output" / str(frame) / "reference_distance.npy")
        totals.add(distances)
        within += int(np.count_nonzero(distances <= threshold_m))
    accuracy = totals.summary()
    reference = np.load(run_path / "output/reference_distance.npy")
    covered = int(np.count_nonzero(reference <= threshold_m))
    return {
        "accuracy": accuracy,
        "reconstruction_within_threshold_fraction": within / accuracy["points"],
        "reference_covered_points": covered,
        "reference_coverage_fraction": covered / len(reference),
        "reference_distance": evaluation.distance_summary(reference),
        "reference_points": len(reference),
    }


def surface_section(
    run_path: Path,
    *,
    dataset: str,
    pinned_sha256: str | None = None,
    input_mode: str = "isolated",
    reference_kind: str = "independent",
) -> dict:
    run_path = Path(run_path)
    run = verified_run(run_path, pinned_sha256)
    stored = read_json(run_path / "output/metrics.json")
    require_keys(stored, REPORTED, "surface")
    metrics = score(run_path, stored["threshold_m"])
    reference_sha256 = _reference_sha256(run_path, stored)
    frame_ids = read_json(run_path / "metadata/configuration.json")["frame_ids"]
    for key in stored.keys() & metrics.keys():
        require_same(stored[key], metrics[key], f"surface {key}")
    accuracy, points = metrics["accuracy"], metrics["accuracy"]["points"]
    reference_points = metrics["reference_points"]

    def item(name: str, value: float, unit: str, better: str, samples: int) -> dict:
        return schema.measure(
            METHOD,
            name,
            value,
            unit,
            samples=samples,
            coverage="complete",
            better=better,
        )

    return schema.section(
        "surface",
        run=run,
        dataset=dataset,
        reference={
            "id": "published reference surface",
            "version": "as recorded by the run",
            "sha256": reference_sha256,
            "kind": reference_kind,
        },
        input_mode=input_mode,
        scope=scope([str(frame) for frame in frame_ids]),
        measures=[
            item("accuracy_mean", accuracy["mean_m"], "m", "lower", points),
            item("accuracy_rmse", accuracy["rmse_m"], "m", "lower", points),
            item("accuracy_max", accuracy["max_m"], "m", "lower", points),
            item(
                "within_threshold_fraction",
                metrics["reconstruction_within_threshold_fraction"],
                "fraction",
                "higher",
                points,
            ),
            item(
                "reference_coverage_fraction",
                metrics["reference_coverage_fraction"],
                "fraction",
                "higher",
                reference_points,
            ),
        ],
        rows=[
            {"threshold_m": stored["threshold_m"], "reference_points": reference_points}
        ],
    )
