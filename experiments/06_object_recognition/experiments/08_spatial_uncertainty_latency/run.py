"""Paired latency check for frozen and cached Task32 support association."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import platform
import shutil
import statistics
import sys
import time
from pathlib import Path
from types import ModuleType

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[4]
TASK48_RUN = ROOT / (
    "experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/"
    "20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68"
)
TASK48_COMPARATOR = TASK48_RUN / "input/execution_input/evaluator/compare_association.py"
TASK48_ASSOCIATION = TASK48_RUN / (
    "metadata/source/experiments/06_object_recognition/experiments/"
    "07_spatial_uncertainty/association.py"
)
TASK48_INPUT = TASK48_RUN / "input/execution_input/task22_source_input"
TASK48_REFERENCE = TASK48_RUN / "input/execution_input/tum_groundtruth_pose_reference.txt"
TASK48_MEMBER_HASHES = TASK48_RUN / "input/execution_input/tum_member_hashes.json"
ASSOCIATION_SOURCE = ROOT / (
    "experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py"
)
RUNS = Path(__file__).resolve().parent / "runs"

HYPERPARAMETERS = {
    "task48_run": {
        "value": TASK48_RUN.relative_to(ROOT).as_posix(),
        "source": "inherited Task48 pending-review run",
    },
    "selected_frames": {
        "value": 60,
        "source": "inherited Task48 input/execution_input/evaluator/compare_association.py:24",
    },
    "proposals": {
        "value": 457,
        "source": "inherited Task48 input/execution_input/evaluator/timing_result.json",
    },
    "max_distance_m": {
        "value": 0.35,
        "source": "inherited Task48 input/execution_input/evaluator/compare_association.py:51",
    },
    "ambiguity_margin_m": {
        "value": 0.05,
        "source": "inherited Task48 input/execution_input/evaluator/compare_association.py:52",
    },
    "depth_gap_m": {
        "value": 0.08,
        "source": "inherited Task48 input/execution_input/evaluator/compare_association.py:53",
    },
    "support_distance": {
        "value": "symmetric median bidirectional exact nearest-sample distance",
        "source": "inherited Task48 metadata/source/experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:236",
    },
    "nearest_neighbour_workers": {
        "value": 1,
        "source": "inherited Task48 metadata/source/experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:240",
    },
    "support_repeats_per_method": {
        "value": 3,
        "source": "inherited Task48 input/execution_input/evaluator/run_timing.py:13",
    },
    "warmup_repeats": {
        "value": 0,
        "source": "n/a follow the Task48 timing runner's no-warm-up measurement order",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ImportError(f"Cannot load pinned module: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def decision_signature(rows: list[dict]) -> list[dict]:
    """Drop timing-only fields while preserving every association result."""
    return [
        {key: value for key, value in row.items() if key != "processing_time_ms"}
        for row in rows
    ]


def summarize_latency(samples_ms: list[float], proposals: int) -> dict[str, float | int]:
    if any(not math.isfinite(value) for value in samples_ms):
        raise ValueError("Latency samples must be finite")
    if not samples_ms or proposals < 1 or any(value <= 0 for value in samples_ms):
        raise ValueError("Latency samples and proposal count must be positive")
    median_ms = float(statistics.median(samples_ms))
    return {
        "repeats": len(samples_ms),
        "median_total_ms": median_ms,
        "median_ms_per_proposal": median_ms / proposals,
    }


def _run_method(
    module: ModuleType, frames: list[list[object]], ca: ModuleType
) -> tuple[list[dict], list[float], float]:
    tracks: dict = {}
    next_number = 1
    decisions: list[dict] = []
    frame_ms: list[float] = []
    started_all = time.perf_counter()
    for frame_index, observations in enumerate(frames):
        started = time.perf_counter()
        result = module.associate_frame(
            observations,
            tracks,
            next_number,
            ca.MAX_D,
            ca.MARGIN,
            depth_gap_m=ca.GAP,
        )
        frame_ms.append((time.perf_counter() - started) * 1000.0)
        tracks, next_number = result.tracks, result.next_number
        decisions.extend(
            {**row, "frame_index": frame_index} for row in result.decisions
        )
    return decisions, frame_ms, (time.perf_counter() - started_all) * 1000.0


def _baseline_frames(frames: list[list[object]], baseline: ModuleType) -> list[list[object]]:
    from dataclasses import asdict

    return [
        [baseline.BoxObservation(**asdict(observation)) for observation in frame]
        for frame in frames
    ]


def _copy_inputs(run_path: Path) -> tuple[Path, Path, dict[str, str]]:
    frozen_source = run_path / "input/task48_task22_source_inputs"
    shutil.copytree(TASK48_INPUT, frozen_source / "input")
    frozen_tum = run_path / "input/tum_reference"
    frozen_tum.mkdir(parents=True)
    shutil.copy2(TASK48_REFERENCE, frozen_tum / "groundtruth.txt")
    shutil.copy2(TASK48_MEMBER_HASHES, frozen_tum / "member_hashes.json")
    shutil.copy2(TASK48_ASSOCIATION, run_path / "input/task48_association_baseline.py")
    shutil.copy2(TASK48_COMPARATOR, run_path / "input/task48_compare_association.py")
    shutil.copy2(
        TASK48_COMPARATOR.parent / "run_timing.py",
        run_path / "input/task48_run_timing.py",
    )
    files = [
        path
        for base in (frozen_source, frozen_tum)
        for path in sorted(base.rglob("*"))
        if path.is_file()
    ]
    return frozen_source, frozen_tum, {
        path.relative_to(run_path / "input").as_posix(): _sha256(path)
        for path in files
    }


def run(output_root: Path = RUNS) -> Path:
    sys.path.insert(0, str(ROOT))
    from experiments.datasets.acquisition import sha256
    from experiments.shared.runs import Run, verify_run, write_json

    ca = _load_module(TASK48_COMPARATOR, "task48_comparator")
    if verify_run(TASK48_RUN)["status"] != "complete":
        raise ValueError("Task48 source run is not complete")
    source_receipt, ledger, selection = ca.lineage()
    baseline_check, corrected = ca.baseline_check(ledger)
    if baseline_check["per_detection_differences"] != 0:
        raise ValueError("Task46 replay no longer matches Task48 input")

    configuration = {
        "experiment_goal": "reduce one-layer association latency while preserving outputs",
        "layer": "object identity association using spatial support",
        "input": "Task48 fixed 60-frame source replay with 457 proposals and supplied TUM poses",
        "held_fixed": [
            "frame and proposal selection",
            "pose, depth samples, class labels, and source lineage",
            "birth, duplicate, ambiguity, and one-to-one assignment policies",
            "support-distance metric and all thresholds",
        ],
        "reference": "No independent physical identity or position reference; accuracy and physical count are unavailable.",
        "control": "Exact Task48 source snapshot of association.py",
        "variant": "Current Task32 source with exact candidate and track cKDTree indexes reused within each frame",
        "hyperparameters": HYPERPARAMETERS,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    run_path = None
    with Run(output_root, ROOT, configuration) as published:
        run_path = published.path
        frozen_source, frozen_tum, input_hashes = _copy_inputs(published.path)
        task46_copy = published.path / "input/task46_published_observations.json"
        shutil.copy2(ca.TASK46 / "output/observations.json", task46_copy)
        input_hashes[task46_copy.relative_to(published.path / "input").as_posix()] = _sha256(
            task46_copy
        )
        original_source, original_tum = ca.SOURCE, ca.TUM
        try:
            ca.SOURCE, ca.TUM = frozen_source, frozen_tum
            revision = "supplied_tum_mocap:groundtruth_sha256=" + _sha256(
                frozen_tum / "groundtruth.txt"
            )
            frames, rebuilt = ca.rebuild_samples(
                ledger, selection, corrected, revision
            )
        finally:
            ca.SOURCE, ca.TUM = original_source, original_tum

        baseline = _load_module(TASK48_ASSOCIATION, "task48_baseline_association")
        candidate = _load_module(ASSOCIATION_SOURCE, "task49_cached_association")
        baseline_frames = _baseline_frames(frames, baseline)
        expected = None
        measurements = {"task48_baseline": [], "cached_indexes": []}
        for repeat in range(int(HYPERPARAMETERS["support_repeats_per_method"]["value"])):
            order = (
                [("task48_baseline", baseline, baseline_frames), ("cached_indexes", candidate, frames)]
                if repeat % 2 == 0
                else [("cached_indexes", candidate, frames), ("task48_baseline", baseline, baseline_frames)]
            )
            for name, module, variant_frames in order:
                rows, frame_ms, total_ms = _run_method(module, variant_frames, ca)
                signature = decision_signature(rows)
                if expected is None:
                    expected = signature
                if signature != expected:
                    raise ValueError(f"Association outputs changed in {name}, repeat {repeat + 1}")
                measurements[name].append(
                    {"total_ms": total_ms, "frame_ms": frame_ms, "decisions": rows}
                )

        proposal_count = sum(len(frame) for frame in frames)
        if proposal_count != int(HYPERPARAMETERS["proposals"]["value"]):
            raise ValueError(f"Expected 457 proposals, received {proposal_count}")
        baseline_totals = [row["total_ms"] for row in measurements["task48_baseline"]]
        optimized_totals = [row["total_ms"] for row in measurements["cached_indexes"]]
        baseline_stats = summarize_latency(baseline_totals, proposal_count)
        optimized_stats = summarize_latency(optimized_totals, proposal_count)
        baseline_median = float(baseline_stats["median_total_ms"])
        optimized_median = float(optimized_stats["median_total_ms"])
        improvement = (baseline_median - optimized_median) / baseline_median
        result = {
            "goal": configuration["experiment_goal"],
            "layer": configuration["layer"],
            "proposal_count": proposal_count,
            "frame_count": len(frames),
            "output_equal_across_all_repeats": True,
            "decision_count": len(expected or []),
            "accuracy": "unavailable: no independent physical identity or position reference",
            "methods": {
                "task48_baseline": {
                    **baseline_stats,
                    "per_repeat_total_ms": baseline_totals,
                    "frame_median_ms": np.median(
                        [row["frame_ms"] for row in measurements["task48_baseline"]], axis=0
                    ).tolist(),
                },
                "cached_indexes": {
                    **optimized_stats,
                    "per_repeat_total_ms": optimized_totals,
                    "frame_median_ms": np.median(
                        [row["frame_ms"] for row in measurements["cached_indexes"]], axis=0
                    ).tolist(),
                },
            },
            "latency_change": {
                "relative_reduction": improvement,
                "speedup": baseline_median / optimized_median,
                "interpretation": "component-only desktop CPU timing; not end-to-end or phone latency",
            },
            "source_sha256": {
                "task48_association": sha256(TASK48_ASSOCIATION),
                "cached_association": sha256(ASSOCIATION_SOURCE),
                "task48_comparator": sha256(TASK48_COMPARATOR),
            },
            "input_sha256": input_hashes,
            "decision_signature_sha256": hashlib.sha256(
                json.dumps(expected, sort_keys=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest(),
            "task48_lineage": source_receipt,
            "rebuilt_support": rebuilt,
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "platform": platform.platform(),
                "processor": platform.processor(),
                "cpu_count": __import__("os").cpu_count(),
                "note": "single desktop process; other sessions may share this machine",
            },
        }
        write_json(published.path / "input/settings.json", configuration)
        write_json(published.path / "input/HYPERPARAMETERS.json", HYPERPARAMETERS)
        write_json(published.path / "output/association_decisions.json", expected)
        write_json(published.path / "output/results.json", result)
    if run_path is None:
        raise RuntimeError("Run publisher returned without a run path")
    verify_run(run_path)
    print(run_path)
    return run_path


if __name__ == "__main__":
    run()
