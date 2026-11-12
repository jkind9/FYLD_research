"""Bridge TUM RGB samples to and from the official WSL Marigold V2 runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .dataset import SAMPLE_STRIDE, select_tum_frames
from .evaluate import evaluate_predictions
from .run import HYPERPARAMETERS as _runner_settings
from .run import SEQUENCE_NAMES, _resolve_sequence_root

MARIGOLD_CONVENTION = "affine_invariant_log_depth"
# Every tunable value this bridge runs with; values and provenance are the runner's frozen
# Task54 entries (run.py HYPERPARAMETERS), copied into each results.json.
HYPERPARAMETERS = {
    name: setting
    for name, setting in _runner_settings.items()
    if name.startswith(("marigold_", "tum_", "sequence_", "reference_"))
    or name in ("shape_alignment", "distance_bands_m")
}


def export_rgb_inputs(tum_root: Path, output_root: Path) -> list[dict[str, Any]]:
    """Write only sampled color frames for Marigold's separate WSL process."""
    written: list[dict[str, Any]] = []
    for sequence_name in SEQUENCE_NAMES:
        sequence_root = _resolve_sequence_root(tum_root, sequence_name)
        selection = select_tum_frames(sequence_root, stride=SAMPLE_STRIDE)
        input_dir = output_root / sequence_name
        input_dir.mkdir(parents=True, exist_ok=True)
        sequence_rows: list[dict[str, Any]] = []
        for frame in selection.frames:
            Image.fromarray(frame.colour, mode="RGB").save(
                input_dir / f"{frame.frame_id}.png"
            )
            sequence_rows.append(
                {"frame_id": frame.frame_id, "timestamp_s": frame.timestamp_s}
            )
        manifest = {
            "sequence": sequence_name,
            "matched_pair_count": selection.matched_pair_count,
            "sample_stride": selection.stride,
            "frame_count": len(selection.frames),
            "frames": sequence_rows,
        }
        (input_dir / "frames.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        written.append(manifest)
    return written


def marigold_prediction_dir(prediction_root: Path, sequence_name: str) -> Path:
    """Where the official infer.py writes one sequence's native log-depth maps.

    infer.py mirrors its input folder under <output_dir>/images/, so a run whose
    output_dir is <prediction_root>/<sequence> saves maps in images/predictions_npy/.
    """
    return prediction_root / sequence_name / "images" / "predictions_npy"


def marigold_cost(sequence_dir: Path, prediction_dir: Path) -> dict[str, Any] | None:
    """Summarise the WSL wrapper's records (marigold_wsl_run.sh); None when it did not run.

    Per-frame time is the median gap between consecutive saved maps, so it includes
    writing each map and its preview image. The first map's delay includes loading and
    4-bit quantising the model. GPU memory is whole-device use sampled once per second.
    """
    status_path = sequence_dir / "run_status.json"
    if not status_path.is_file():
        return None
    status = json.loads(status_path.read_text(encoding="utf-8"))
    saved_at = sorted(path.stat().st_mtime for path in prediction_dir.glob("*.npy"))
    gaps = np.diff(saved_at)
    gpu_used = [
        float(line.split(",")[1])
        for line in (sequence_dir / "gpu_memory.csv").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    max_rss_kib = None
    for line in (sequence_dir / "time.txt").read_text(encoding="utf-8").splitlines():
        if "Maximum resident set size" in line:
            max_rss_kib = float(line.rsplit(":", 1)[1])
    return {
        "exit_status": status["exit_status"],
        "wall_time_s": status["finished_unix_s"] - status["started_unix_s"],
        "first_map_after_start_s": saved_at[0] - status["started_unix_s"] if saved_at else None,
        "median_frame_interval_s": float(np.median(gaps)) if gaps.size else None,
        "gpu_memory_idle_mib": gpu_used[0] if gpu_used else None,
        "gpu_memory_peak_mib": max(gpu_used) if gpu_used else None,
        "gpu_memory_peak_minus_idle_mib": max(gpu_used) - gpu_used[0] if gpu_used else None,
        "peak_process_memory_mib": max_rss_kib / 1024 if max_rss_kib is not None else None,
    }


def score_predictions(
    tum_root: Path, prediction_root: Path, sequences: tuple[str, ...] | None = None
) -> list[dict[str, Any]]:
    """Score official Marigold native log-depth maps against TUM references.

    `sequences` names the recordings to score (default: all); each must have every
    selected frame.
    """
    sequences = SEQUENCE_NAMES if sequences is None else sequences
    unknown = set(sequences) - set(SEQUENCE_NAMES)
    if unknown or not sequences:
        raise ValueError(f"Choose from {SEQUENCE_NAMES}; got {sorted(sequences)}")
    results: list[dict[str, Any]] = []
    for sequence_name in sequences:
        sequence_root = _resolve_sequence_root(tum_root, sequence_name)
        selection = select_tum_frames(sequence_root, stride=SAMPLE_STRIDE)
        prediction_dir = marigold_prediction_dir(prediction_root, sequence_name)
        predictions: dict[str, np.ndarray] = {}
        for frame in selection.frames:
            path = prediction_dir / f"{frame.frame_id}.npy"
            if not path.is_file():
                raise FileNotFoundError(f"Missing Marigold prediction: {path}")
            depth = np.load(path, allow_pickle=False)
            if depth.ndim != 2:
                raise ValueError(
                    f"{frame.frame_id}: expected a 2D log-depth map, got {depth.shape}"
                )
            predictions[frame.frame_id] = depth
        scores = evaluate_predictions(selection, predictions, MARIGOLD_CONVENTION)
        result = {
            "method": "marigold-v2-depth-log-stage2",
            "sequence": sequence_name,
            "convention": MARIGOLD_CONVENTION,
            "prediction_root": str(prediction_dir),
            "frames": [
                {
                    "frame_id": frame.frame_id,
                    "prediction_file": f"images/predictions_npy/{frame.frame_id}.npy",
                }
                for frame in selection.frames
            ],
            "timing": marigold_cost(prediction_root / sequence_name, prediction_dir),
            "hyperparameters": HYPERPARAMETERS,
            "scores": scores,
        }
        result_path = prediction_root / sequence_name / "results.json"
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        results.append(result)
    return results


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser("export-rgb")
    export_parser.add_argument("--tum-root", type=Path, default=Path("data/tum"))
    export_parser.add_argument("--output", type=Path, required=True)
    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("--tum-root", type=Path, default=Path("data/tum"))
    score_parser.add_argument("--predictions", type=Path, required=True)
    score_parser.add_argument("--sequences", nargs="+", default=list(SEQUENCE_NAMES))
    args = parser.parse_args()
    if args.command == "export-rgb":
        result = export_rgb_inputs(args.tum_root, args.output)
    else:
        result = score_predictions(args.tum_root, args.predictions, tuple(args.sequences))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
