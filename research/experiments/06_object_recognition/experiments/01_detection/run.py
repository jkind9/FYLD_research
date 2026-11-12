"""Score the fixed Task17 frames from the exact accepted Task28 GPU cache."""

import argparse
import importlib
import json
import shutil
import time
import tracemalloc
from pathlib import Path

import psutil  # type: ignore[import-untyped]

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, verify_run, write_json

from .cache import (
    ACCEPTED_ANNOTATIONS_SHA256,
    ACCEPTED_MANIFEST_SHA256,
    ACCEPTED_RELATIVE,
    SELECTION_INDEXES,
    load_accepted_cache,
    read_json,
)
from .report import write_report
from .scoring import evaluate

manifest_api = importlib.import_module(
    "experiments.06_object_recognition.shared.manifest"
)
ROOT = Path(__file__).resolve().parents[4]
ANNOTATIONS = "experiments/06_object_recognition/datasets/desk_smoke_v1.json"
HYPERPARAMETERS = {
    "iou_thresholds": {
        "value": [0.3, 0.5, 0.7],
        "source": "confirmed 2026-10-03 delegated overnight protocol; all reported",
    },
    "primary_iou": {
        "value": 0.5,
        "source": "confirmed 2026-10-03 delegated diagnostic choice",
    },
    "source_selection_indexes": {
        "value": list(SELECTION_INDEXES),
        "source": "inherited Task17 frozen desk_smoke_v1.json",
    },
    "assignment": {
        "value": "maximum cardinality then maximum summed IoU, same category, one-to-one",
        "source": "confirmed 2026-10-03 delegated protocol",
    },
    "new_inference_repeats": {
        "value": 0,
        "source": "confirmed 2026-10-03 efficiency: cached inference only",
    },
    "evaluation_repeats": {
        "value": 1,
        "source": "confirmed 2026-10-03 bounded diagnostic",
    },
    "control": {
        "value": "empty_prediction_software_control",
        "source": "confirmed 2026-10-03 delegated accounting check",
    },
    "predecessor_manifest_sha256": {
        "value": ACCEPTED_MANIFEST_SHA256,
        "source": "inherited accepted Task28 completion receipt",
    },
    "annotation_manifest_sha256": {
        "value": ACCEPTED_ANNOTATIONS_SHA256,
        "source": "inherited Task17 frozen coarse RGB references",
    },
}


def _output_root(output: Path) -> Path:
    """Resolve aliases and reject any destination owned by an existing run."""
    resolved = output.resolve()
    for ancestor in (resolved, *resolved.parents):
        marker = ancestor / "metadata/status.json"
        if marker.exists() or marker.is_symlink():
            raise ValueError("Output must not be inside an existing run")
    return resolved


def _publish(
    repo: Path, output: Path, annotations: dict, cached: dict, *, method_name: str
) -> Path:
    """Internal publication; fixtures explicitly use synthetic_control method names."""
    output = _output_root(output)
    if method_name == "cached_yolo26x_accepted_task28":
        if cached["manifest_sha256"] != ACCEPTED_MANIFEST_SHA256:
            raise ValueError("Production publication requires accepted cache")
        parameters = HYPERPARAMETERS
    elif method_name.startswith("synthetic_control"):
        parameters = {
            "synthetic_control": {
                "value": True,
                "source": "synthetic fixture; no GPU evidence",
            }
        }
    else:
        raise ValueError("Unknown publication method")
    config = {
        "phase": "detection_smoke_diagnostics",
        "hyperparameters": parameters,
        "method": method_name,
        "predecessor_manifest_sha256": cached["manifest_sha256"],
        "claim": "within_session_smoke",
        "no_new_inference": True,
    }
    with Run(output, repo, config) as run:
        frames, proposals = annotations["frames"], cached["frames"]
        with run.measure("input_copy", frames=len(frames)):
            write_json(run.path / "input/annotations.json", annotations)
            inputs = [
                {
                    k: f[k]
                    for k in (
                        "frame_id",
                        "timestamp_s",
                        "source_selection_index",
                        "rgb",
                    )
                }
                for f in frames
            ]
            write_json(run.path / "input/method_inputs.json", {"frames": inputs})
            for frame in frames:
                copied = run.path / "input/rgb" / f'{frame["frame_id"]}.png'
                copied.parent.mkdir(exist_ok=True)
                shutil.copyfile(repo / frame["rgb"]["path"], copied)
                if sha256(copied) != frame["rgb"]["sha256"]:
                    raise ValueError("Copied RGB differs from frozen source")
            write_json(run.path / "output/cached_proposals.json", cached)
        with run.measure("scoring", frames=len(frames)):
            results = {
                method_name: evaluate(frames, proposals, (0.3, 0.5, 0.7)),
                "empty_prediction_software_control": evaluate(
                    frames, [{"proposals": []} for _ in frames], (0.3, 0.5, 0.7)
                ),
            }
            write_json(run.path / "output/scores.json", results)
        with run.measure("report", frames=len(frames)):
            write_report(run.path, frames, proposals, results)
        run.set_processed_frames(len(frames))
        write_json(
            run.path / "output/receipt.json",
            {
                "method": method_name,
                "claims": "coarse within-session diagnostics; not formal held-out accuracy",
                "frame_count": len(frames),
                "new_inference_count": 0,
                "predecessor": {
                    "manifest_sha256": cached["manifest_sha256"],
                    "timing": cached["predecessor_timing"],
                    "cost_scope": "original 60-frame predecessor; not charged as six-frame evaluation cost",
                },
                "thresholds": [0.3, 0.5, 0.7],
                "hyperparameters": parameters,
                "failures": [],
                "deferred": [
                    "other detectors: no local shortlisted weights; no downloads authorised",
                    "formal blind accuracy and mask-boundary accuracy: coarse already inspected references",
                ],
            },
        )
    verify_run(run.path)
    return run.path


def run_evaluation(
    repo: Path = ROOT, output: Path | None = None, cache: Path | None = None
) -> Path:
    """Production entry pins both manifests; no prediction/provider injection API."""
    cache_path = cache or repo / ACCEPTED_RELATIVE
    output_path = output or Path(__file__).parent / "runs"
    if output_path.resolve().is_relative_to(cache_path.resolve()):
        raise ValueError("Output must not modify the accepted cache")
    output_path = _output_root(output_path)
    started = time.perf_counter()
    owns_tracing = not tracemalloc.is_tracing()
    if owns_tracing:
        tracemalloc.start()
    try:
        return _execute(repo, output_path, cache_path, started)
    finally:
        if owns_tracing:
            tracemalloc.stop()


def _execute(repo: Path, output: Path, cache: Path, started: float) -> Path:
    """Execute only after immutable-output and tracer ownership checks."""
    annotations_path = repo / ANNOTATIONS
    if sha256(annotations_path) != ACCEPTED_ANNOTATIONS_SHA256:
        raise ValueError("Task17 annotation manifest changed")
    annotations = read_json(annotations_path)
    manifest_api.validate_manifest(annotations, repo)
    captures = [
        {k: f[k] for k in ("frame_id", "timestamp_s", "source_selection_index", "rgb")}
        for f in annotations["frames"]
    ]
    preflight_started = time.perf_counter()
    cached = load_accepted_cache(cache, captures)
    preflight_seconds = time.perf_counter() - preflight_started
    path = _publish(
        repo,
        output,
        annotations,
        cached,
        method_name="cached_yolo26x_accepted_task28",
    )
    # This external timing companion is deliberately outside the immutable run.
    # It includes final hash verification, which Run's internal timing excludes.
    _, peak = tracemalloc.get_traced_memory()
    process = psutil.Process()
    peak_host = getattr(process.memory_info(), "peak_wset", None)
    write_json(
        path.parent / f"{path.name}_execution.json",
        {
            "run_manifest_sha256": sha256(path / "metadata/manifest.json"),
            "evaluation_entry_to_verified_seconds": time.perf_counter() - started,
            "process_creation_to_verified_seconds": time.time() - process.create_time(),
            "process_timing_scope": "OS process creation through verified result; includes imports for the dedicated CLI process; wall clock",
            "preflight_seconds": preflight_seconds,
            "peak_traced_python_bytes": peak,
            "peak_process_working_set_bytes": peak_host,
            "process_memory_scope": "Windows OS peak working set for dedicated CLI; null if OS lacks peak_wset",
            "memory_scope": "Python allocation tracer; not total RSS or device memory",
            "new_device_allocations": 0,
            "new_inference_count": 0,
            "inference_cost_scope": "preserved predecessor timings, no inference re-executed",
        },
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache", type=Path, help="Offline copy of exact accepted Task28 run"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(
        json.dumps({"run": str(run_evaluation(output=args.output, cache=args.cache))})
    )


if __name__ == "__main__":
    main()
