"""Run one local depth model on the frozen Task54 TUM frame sample."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import shutil
import statistics
import sys
import time
import uuid
import warnings
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import datetime, timezone
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from .dataset import TumDepthFrame, TumDepthSelection, select_tum_frames
from .evaluate import evaluate_predictions

METHOD_SETTINGS: dict[str, dict[str, Any]] = {
    "depth-anything": {
        "convention": "metric_depth",
        "input_size_px_short_side": 518,
        "max_depth_m": 20.0,
        "checkpoint_kind": "directory",
    },
    "zipdepth": {
        "convention": "relative_inverse_depth",
        "input_size_px_short_side": 384,
        "max_depth_m": None,
        "checkpoint_kind": "file",
    },
}
HYPERPARAMETERS = {
    "tum_sample_stride": {"value": 10, "source": "confirmed 2026-10-07"},
    "sequence_names": {
        "value": ["rgbd_dataset_freiburg1_xyz", "rgbd_dataset_freiburg1_desk"],
        "source": "confirmed 2026-10-07",
    },
    "depth_anything_short_side_px": {
        "value": 518,
        "source": "confirmed 2026-10-07; official repository default",
    },
    "depth_anything_max_depth_m": {
        "value": 20.0,
        "source": "confirmed 2026-10-07; indoor checkpoint limit",
    },
    "zipdepth_short_side_px": {
        "value": 384,
        "source": "confirmed 2026-10-07; official repository default",
    },
    "zipdepth_gpu_build": {"value": "gpu", "source": "confirmed 2026-10-07"},
    "zipdepth_export_build": {"value": "npu", "source": "confirmed 2026-10-07"},
    "zipdepth_output_convention": {
        "value": "relative_inverse_depth",
        "source": "inherited data/models/ZipDepth/zipdepth/evaluation/evaluator.py:3,51",
    },
    "marigold_resolution_px": {
        "value": [640, 480],
        "source": "confirmed 2026-10-07; native TUM frame size",
    },
    "marigold_steps": {"value": 1, "source": "confirmed 2026-10-07"},
    "marigold_seed": {"value": 0, "source": "confirmed 2026-10-07"},
    "marigold_weight_quantization": {
        "value": "4-bit",
        "source": "confirmed 2026-10-07; official WSL model loader",
    },
    "shape_alignment": {
        "value": "per-frame least-squares scale and shift in native prediction space",
        "source": "confirmed 2026-10-07",
    },
    "distance_bands_m": {
        "value": [[0, 1], [1, 2], [2, 4]],
        "source": "confirmed 2026-10-07",
    },
    "warmup_frames": {"value": 5, "source": "confirmed 2026-10-07"},
    "repeats_per_frame": {"value": 3, "source": "confirmed 2026-10-07"},
    "reference_units_per_metre": {
        "value": 5000.0,
        "source": "inherited src/walkthrough/steps/depth.py:43-45",
    },
    "reference_max_depth_m": {
        "value": 4.0,
        "source": "inherited src/walkthrough/steps/depth.py:43-45",
    },
    "reference_pair_tolerance_s": {
        "value": 0.02,
        "source": "inherited src/walkthrough/steps/depth.py:43-45",
    },
}
SEQUENCE_NAMES = ("rgbd_dataset_freiburg1_xyz", "rgbd_dataset_freiburg1_desk")
SAMPLE_STRIDE = 10
WARMUP_FRAMES = 5
REPEATS_PER_FRAME = 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=tuple(METHOD_SETTINGS), required=True)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Existing local checkpoint path; the runner never downloads weights.",
    )
    parser.add_argument(
        "--tum-root",
        type=Path,
        default=Path("data/tum"),
        help="Directory containing both selected TUM recordings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/task54"),
        help="New output root; existing sequence results are never overwritten.",
    )
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--zip-build", choices=("gpu", "npu"), default="gpu")
    parser.add_argument(
        "--preflight",
        "--dry-run",
        dest="preflight",
        action="store_true",
        help="Check local data and checkpoint paths without loading a model.",
    )
    return parser


def _resolve_sequence_root(tum_root: Path, sequence_name: str) -> Path:
    """Find a TUM sequence, including the extra directory in desk extraction."""
    candidates = (
        tum_root / sequence_name,
        tum_root / sequence_name / sequence_name,
    )
    for candidate in candidates:
        if (candidate / "rgb.txt").is_file() and (candidate / "depth.txt").is_file():
            return candidate
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        f"TUM sequence {sequence_name} is missing rgb.txt/depth.txt; checked {searched}"
    )


def _validate_checkpoint(method: str, checkpoint: Path) -> Path:
    resolved = checkpoint.expanduser().resolve()
    kind = METHOD_SETTINGS[method]["checkpoint_kind"]
    exists = resolved.is_dir() if kind == "directory" else resolved.is_file()
    if not exists:
        expected = "directory" if kind == "directory" else "file"
        raise FileNotFoundError(f"Local {method} checkpoint {expected} not found: {resolved}")
    return resolved


def _load_method(args: argparse.Namespace) -> Callable[..., Iterator[Any]]:
    checkpoint = _validate_checkpoint(args.method, args.checkpoint)
    if args.method == "depth-anything":
        depth_step = importlib.import_module("src.walkthrough.steps.depth")
        method = depth_step.DepthAnythingV2Metric(
            checkpoint=checkpoint,
            device=args.device,
            max_depth_m=20.0,
        )
    else:
        zipdepth = importlib.import_module("experiments.02_stereo_depth.zipdepth")
        method = zipdepth.ZipDepth(
            checkpoint=checkpoint,
            build=args.zip_build,
            device=args.device,
            input_size=384,
        )
    return method.load()


def _checkpoint_manifest(checkpoint: Path) -> list[dict[str, Any]]:
    """Hash every local checkpoint file so the run identifies its exact weights."""
    # Hugging Face's .cache/ folder holds download bookkeeping, not weights, and its
    # timestamps would make the same weights hash differently after a re-download.
    files = [checkpoint] if checkpoint.is_file() else sorted(
        path
        for path in checkpoint.rglob("*")
        if path.is_file() and ".cache" not in path.relative_to(checkpoint).parts
    )
    manifest: list[dict[str, Any]] = []
    for file_path in files:
        digest = hashlib.sha256()
        with file_path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        manifest.append(
            {
                "path": str(file_path.relative_to(checkpoint))
                if checkpoint.is_dir()
                else file_path.name,
                "size_bytes": file_path.stat().st_size,
                "sha256": digest.hexdigest(),
            }
        )
    return manifest


def _runtime_metadata() -> dict[str, str | None]:
    versions: dict[str, str | None] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
    }
    for package in ("torch", "transformers", "pillow"):
        try:
            package_version = version(package)
        except PackageNotFoundError:
            versions[package] = None
        else:
            versions[package] = package_version
    return versions


def _parameter_count(estimator: Any) -> int | None:
    """Read a model's parameter count when its loaded adapter exposes the model."""
    candidates: list[Any] = [estimator]
    if isinstance(estimator, partial):
        candidates.extend((estimator.keywords or {}).values())
    inspected: set[int] = set()
    for candidate in candidates:
        if candidate is None or id(candidate) in inspected:
            continue
        inspected.add(id(candidate))
        for model in (candidate, getattr(candidate, "model", None)):
            if model is None or not callable(getattr(model, "parameters", None)):
                continue
            return sum(int(parameter.numel()) for parameter in model.parameters())
    return None


def _peak_process_memory_mib() -> float:
    """Lifetime peak resident memory of this runner process, in MiB.

    It covers model loading and any earlier sequence in the same run, so it is an
    upper bound for one sequence. Windows reports the peak working set; Linux reports
    max RSS in KiB.
    """
    if sys.platform == "win32":
        psutil = importlib.import_module("psutil")
        return float(psutil.Process().memory_info().peak_wset / (1024**2))
    resource = importlib.import_module("resource")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024**2 if sys.platform == "darwin" else 1024
    return float(peak / divisor)


def _sync_device(device: str) -> None:
    if device == "cuda":
        torch = importlib.import_module("torch")
        torch.cuda.synchronize()


def _validate_runtime(device: str) -> None:
    try:
        torch = importlib.import_module("torch")
    except ModuleNotFoundError as error:
        raise RuntimeError("PyTorch is required to run a Task54 model") from error
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was selected, but PyTorch cannot access a CUDA device")


def _model_frame(frame: TumDepthFrame) -> SimpleNamespace:
    """Drop sensor reference fields before the frame crosses the model boundary."""
    return SimpleNamespace(frame_id=frame.frame_id, colour=frame.colour)


def _infer_one(
    estimator: Callable[..., Iterable[Any]], frame: TumDepthFrame, device: str
) -> tuple[np.ndarray, np.ndarray]:
    model_frame = _model_frame(frame)
    prediction_iterator = iter(estimator(iter((model_frame,)), run=None))
    prediction = next(prediction_iterator, None)
    if prediction is None:
        raise ValueError(f"Model returned no prediction for {frame.frame_id}")
    if prediction.frame_id != frame.frame_id:
        raise ValueError(
            f"Model returned {prediction.frame_id} for input frame {frame.frame_id}"
        )
    depth = np.asarray(prediction.depth, dtype=np.float32)
    valid = np.asarray(prediction.valid)
    if depth.ndim != 2 or depth.shape != frame.colour.shape[:2]:
        raise ValueError(f"{frame.frame_id}: model output grid differs from the RGB grid")
    if valid.shape != depth.shape or valid.dtype != np.bool_:
        raise ValueError(f"{frame.frame_id}: model validity mask is not a matching boolean map")
    valid = valid & np.isfinite(depth)
    return np.where(valid, depth, np.nan), valid


def _measure_prediction(
    estimator: Callable[..., Iterable[Any]], frame: TumDepthFrame, device: str
) -> tuple[np.ndarray, float]:
    _sync_device(device)
    started = time.perf_counter()
    depth, _ = _infer_one(estimator, frame, device)
    _sync_device(device)
    return depth, time.perf_counter() - started


def _run_sequence(
    args: argparse.Namespace,
    selection: TumDepthSelection,
    estimator: Callable[..., Iterable[Any]],
    load_times: list[float],
    run_metadata: Mapping[str, Any],
) -> None:
    sequence_dir = args.output / args.method / selection.sequence
    if sequence_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run output: {sequence_dir}")
    incomplete_root = sequence_dir.parent / ".incomplete"
    incomplete_root.mkdir(parents=True, exist_ok=True)
    staging_dir = incomplete_root / f"{selection.sequence}-{uuid.uuid4().hex}"
    prediction_dir = staging_dir / "predictions"
    prediction_dir.mkdir(parents=True)
    if args.device == "cuda":
        torch = importlib.import_module("torch")
        torch.cuda.reset_peak_memory_stats()

    warmup_frames = tuple(
        selection.frames[index % len(selection.frames)]
        for index in range(WARMUP_FRAMES)
    )
    for warmup in warmup_frames:
        _measure_prediction(estimator, warmup, args.device)

    predictions: dict[str, np.ndarray] = {}
    frame_times: dict[str, list[float]] = {}
    frame_index: list[dict[str, Any]] = []
    for index, frame in enumerate(selection.frames):
        repeat_maps: list[np.ndarray] = []
        repeat_times: list[float] = []
        for _ in range(REPEATS_PER_FRAME):
            depth, elapsed_s = _measure_prediction(estimator, frame, args.device)
            repeat_maps.append(depth)
            repeat_times.append(elapsed_s)
        # The scored native map is the pixelwise median of three independent calls.
        combined = np.nanmedian(np.stack(repeat_maps), axis=0).astype(np.float32)
        predictions[frame.frame_id] = combined
        frame_times[frame.frame_id] = repeat_times
        filename = f"{index:05d}.npy"
        np.save(prediction_dir / filename, combined, allow_pickle=False)
        frame_index.append(
            {
                "frame_id": frame.frame_id,
                "timestamp_s": frame.timestamp_s,
                "prediction_file": f"predictions/{filename}",
            }
        )

    convention = METHOD_SETTINGS[args.method]["convention"]
    scores = evaluate_predictions(selection, predictions, convention)
    median_by_frame = [statistics.median(values) for values in frame_times.values()]
    peak_memory_mib = None
    if args.device == "cuda":
        torch = importlib.import_module("torch")
        peak_memory_mib = float(torch.cuda.max_memory_allocated() / (1024**2))

    result = {
        "method": args.method,
        "sequence": selection.sequence,
        "source_root": str(selection.source_root),
        "matched_pair_count": selection.matched_pair_count,
        "sample_stride": SAMPLE_STRIDE,
        "evaluated_frame_count": len(selection.frames),
        "convention": convention,
        "settings": {
            **METHOD_SETTINGS[args.method],
            "device": args.device,
            "zip_build": args.zip_build if args.method == "zipdepth" else None,
            "warmup_frames_discarded": WARMUP_FRAMES,
            "repeats_per_frame": REPEATS_PER_FRAME,
            "scored_repeat_map": "pixelwise median of the three repeated predictions",
        },
        "model_load_time_s": load_times[0],
        "timing": {
            "warmup_frames_discarded": WARMUP_FRAMES,
            "warmup_frame_ids": [frame.frame_id for frame in warmup_frames],
            "repeats_per_frame": REPEATS_PER_FRAME,
            "per_frame_repeat_seconds": frame_times,
            "median_frame_time_s": statistics.median(median_by_frame),
            "peak_cuda_allocated_mib": peak_memory_mib,
            "peak_process_memory_mib": _peak_process_memory_mib(),
            "peak_process_memory_definition": (
                "lifetime peak resident memory of the runner process, including model load"
            ),
        },
        "parameters": run_metadata.get("parameters"),
        "checkpoint_files": run_metadata["checkpoint_files"],
        "runtime": run_metadata["runtime"],
        "frames": frame_index,
        "scores": scores,
    }
    (staging_dir / "results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    try:
        staging_dir.rename(sequence_dir)
    except PermissionError:
        if sys.platform != "win32":
            raise
        warnings.warn(
            "Windows denied run-directory rename; publishing a verified file copy",
            RuntimeWarning,
            stacklevel=2,
        )
        # mkdir reserves this destination atomically. Never clear a folder that
        # another run may have published after the failed rename.
        sequence_dir.mkdir()
        try:
            shutil.copytree(staging_dir, sequence_dir, dirs_exist_ok=True)
        except BaseException:
            shutil.rmtree(sequence_dir)
            raise
        source_files = sorted(
            path.relative_to(staging_dir) for path in staging_dir.rglob("*") if path.is_file()
        )
        published_files = sorted(
            path.relative_to(sequence_dir) for path in sequence_dir.rglob("*") if path.is_file()
        )
        if source_files != published_files:
            shutil.rmtree(sequence_dir)
            raise OSError(f"Incomplete Windows publish copy for {selection.sequence}")
        same_file_sizes = all(
            (staging_dir / relative_path).stat().st_size
            == (sequence_dir / relative_path).stat().st_size
            for relative_path in source_files
        )
        if not same_file_sizes:
            shutil.rmtree(sequence_dir)
            raise OSError(f"Incomplete Windows publish copy for {selection.sequence}")
        shutil.rmtree(staging_dir)


def _preflight(args: argparse.Namespace) -> dict[str, Any]:
    checkpoint = _validate_checkpoint(args.method, args.checkpoint)
    selections: list[TumDepthSelection] = []
    for sequence_name in SEQUENCE_NAMES:
        root = _resolve_sequence_root(args.tum_root, sequence_name)
        selections.append(select_tum_frames(root, stride=SAMPLE_STRIDE))
    _validate_runtime(args.device)
    return {
        "preflight": True,
        "model_loaded": False,
        "method": args.method,
        "checkpoint": str(checkpoint),
        "device": args.device,
        "sample_stride": SAMPLE_STRIDE,
        "sequences": [
            {
                "name": selection.sequence,
                "source_root": str(selection.source_root),
                "matched_pair_count": selection.matched_pair_count,
                "selected_frame_count": len(selection.frames),
            }
            for selection in selections
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.preflight:
            print(json.dumps(_preflight(args), indent=2, sort_keys=True))
            return 0

        checkpoint = _validate_checkpoint(args.method, args.checkpoint)
        _validate_runtime(args.device)
        selections = [
            select_tum_frames(
                _resolve_sequence_root(args.tum_root, sequence_name),
                stride=SAMPLE_STRIDE,
            )
            for sequence_name in SEQUENCE_NAMES
        ]
        run_dir = args.output / args.method
        if run_dir.exists():
            raise FileExistsError(f"Refusing to reuse existing method run directory: {run_dir}")
        for selection in selections:
            existing = args.output / args.method / selection.sequence
            if existing.exists():
                raise FileExistsError(
                    f"Refusing to overwrite existing run output: {existing}"
                )

        args.checkpoint = checkpoint
        checkpoint_files = _checkpoint_manifest(checkpoint)
        started = time.perf_counter()
        estimator = _load_method(args)
        load_times = [time.perf_counter() - started]
        metadata = {
            "runtime": _runtime_metadata(),
            "parameters": _parameter_count(estimator),
            "checkpoint_files": checkpoint_files,
        }
        args.output.mkdir(parents=True, exist_ok=True)
        # This exclusive mkdir arbitrates two runs that started from the same
        # precheck. Only its winner may publish run.json or sequence results.
        run_dir.mkdir()
        (run_dir / "run.json").write_text(
            json.dumps(
                {
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "method": args.method,
                    "checkpoint": str(checkpoint),
                    "device": args.device,
                    "settings": METHOD_SETTINGS[args.method],
                    "runtime": metadata["runtime"],
                    "parameters": metadata["parameters"],
                    "checkpoint_files": checkpoint_files,
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
        for selection in selections:
            _run_sequence(args, selection, estimator, load_times, metadata)
        print(json.dumps({"output": str(run_dir), "sequences_completed": len(selections)}))
        return 0
    except (FileNotFoundError, FileExistsError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    sys.exit(main())
