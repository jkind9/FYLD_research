"""Score saved depth predictions when each frame's scale comes from a few known points.

A phone has no dense depth sensor. It can know the true distance at a few points, for
example from ARCore depth or tracked features. This script fits each frame's scale (and
shift) from N reference pixels chosen at random, then scores every valid reference pixel.
The chosen points are exact Kinect values, so the result is still optimistic: real phone
points carry their own error.

Usage, from the repository root:
    python -m experiments.02_stereo_depth.sparse_scale \
        --set "Depth Anything V2=experiments/02_stereo_depth/runs/task54/depth-anything" \
        --set "ZipDepth phone=experiments/02_stereo_depth/runs/task62/zipdepth" \
        --output experiments/02_stereo_depth/runs/task62/sparse_scale.json
Each --set path holds one folder per sequence with a results.json that lists the saved
prediction files and their output convention (runner and Marigold scorer outputs both do).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .dataset import SAMPLE_STRIDE, TumDepthSelection, select_tum_frames
from .evaluate import aggregate_scores, evaluate_predictions
from .geometry import alignment_fit_pixels
from .run import SEQUENCE_NAMES, _resolve_sequence_root
from .scoring import score_sparse_fit

HYPERPARAMETERS = {
    "point_counts_per_frame": {
        "value": [10, 50, 200, 1000],
        "source": "confirmed 2026-10-07 (owner delegated: 'Fix it all')",
    },
    "seeds": {
        "value": [0, 1, 2, 3, 4],
        "source": "confirmed 2026-10-07 (owner delegated: 'Fix it all')",
    },
    "point_sampling": {
        "value": "uniform without replacement over valid reference and prediction pixels; "
        "numpy default_rng([seed, frame_index])",
        "source": "confirmed 2026-10-07 (owner delegated: 'Fix it all')",
    },
    "fit": {
        "value": "native-space least-squares scale and shift; metric depth also scale-only",
        "source": "confirmed 2026-10-07 (owner delegated: 'Fix it all')",
    },
    "point_noise": {
        "value": "none; Kinect values used as given",
        "source": "confirmed 2026-10-07 (owner delegated: 'Fix it all')",
    },
    "frames_and_reference": {
        "value": "every tenth TUM pair, Kinect depth valid 0-4 m",
        "source": "inherited experiments/02_stereo_depth/run.py:43-102",
    },
}
POINT_COUNTS = tuple(HYPERPARAMETERS["point_counts_per_frame"]["value"])
SEEDS = tuple(HYPERPARAMETERS["seeds"]["value"])


def choose_fit_pixels(
    eligible: NDArray[np.bool_], count: int, rng: np.random.Generator
) -> NDArray[np.bool_]:
    """Pick `count` distinct eligible pixels uniformly; refuse if there are too few."""
    candidates = np.flatnonzero(eligible)
    if candidates.size < count:
        raise ValueError(
            f"Requested {count} fit points but only {candidates.size} pixels are eligible"
        )
    chosen = rng.choice(candidates, size=count, replace=False)
    mask = np.zeros(eligible.size, dtype=np.bool_)
    mask[chosen] = True
    return mask.reshape(eligible.shape)


def load_prediction_set(
    method_dir: Path, selection: TumDepthSelection
) -> tuple[str, dict[str, np.ndarray]]:
    """Read one sequence's saved native predictions and their declared convention."""
    sequence_dir = method_dir / selection.sequence
    report = json.loads((sequence_dir / "results.json").read_text(encoding="utf-8"))
    files = {row["frame_id"]: sequence_dir / row["prediction_file"] for row in report["frames"]}
    expected = [frame.frame_id for frame in selection.frames]
    if sorted(files) != sorted(expected):
        raise ValueError(f"{sequence_dir}: saved frames differ from the TUM selection")
    predictions = {frame_id: np.load(files[frame_id], allow_pickle=False) for frame_id in expected}
    return report["convention"], predictions


def score_sequence(
    selection: TumDepthSelection,
    convention: str,
    predictions: dict[str, np.ndarray],
    *,
    scale_only: bool,
) -> dict[str, Any]:
    """Pooled scores for every point count and seed, plus the summary over seeds."""
    by_count: dict[str, Any] = {}
    for count in POINT_COUNTS:
        seed_rows = []
        for seed in SEEDS:
            frame_rows = []
            for frame_index, frame in enumerate(selection.frames):
                raw = predictions[frame.frame_id]
                eligible = alignment_fit_pixels(
                    raw, convention, frame.reference_depth_m, frame.reference_valid
                )
                fit_mask = choose_fit_pixels(
                    eligible, count, np.random.default_rng([seed, frame_index])
                )
                frame_rows.append(
                    score_sparse_fit(
                        raw,
                        convention,
                        frame.reference_depth_m,
                        frame.reference_valid,
                        fit_mask,
                        scale_only=scale_only,
                    )
                )
            seed_rows.append({"seed": seed, **aggregate_scores(frame_rows)})
        by_count[str(count)] = {"seeds": seed_rows, "summary": _summary(seed_rows)}
    return by_count


def _summary(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for metric in ("abs_rel", "rmse_m", "delta1", "valid_coverage"):
        values = [row["overall"][metric] for row in seed_rows]
        summary[metric] = {
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }
    return summary


def _parse_sets(entries: list[str]) -> list[tuple[str, Path]]:
    parsed = []
    for entry in entries:
        label, separator, path = entry.partition("=")
        if not separator or not label or not path:
            raise ValueError(f"--set must look like LABEL=PATH, got {entry!r}")
        parsed.append((label, Path(path)))
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", dest="sets", action="append", required=True)
    parser.add_argument("--tum-root", type=Path, default=Path("data/tum"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"Refusing to overwrite {args.output}")

    selections = [
        select_tum_frames(_resolve_sequence_root(args.tum_root, name), stride=SAMPLE_STRIDE)
        for name in SEQUENCE_NAMES
    ]
    results: list[dict[str, Any]] = []
    for label, method_dir in _parse_sets(args.sets):
        for selection in selections:
            if not (method_dir / selection.sequence / "results.json").is_file():
                # For example Marigold V2, dropped part-way through desk for being too slow.
                results.append(
                    {
                        "label": label,
                        "method_dir": str(method_dir),
                        "sequence": selection.sequence,
                        "not_run": "no results.json for this recording",
                    }
                )
                continue
            convention, predictions = load_prediction_set(method_dir, selection)
            full_frame = evaluate_predictions(selection, predictions, convention)
            fits = [False, True] if convention == "metric_depth" else [False]
            for scale_only in fits:
                results.append(
                    {
                        "label": label,
                        "method_dir": str(method_dir),
                        "sequence": selection.sequence,
                        "convention": convention,
                        "fit": "scale_only" if scale_only else "scale_and_shift",
                        "frame_count": len(selection.frames),
                        "every_valid_pixel_fit": full_frame["reference_aligned_shape"][
                            "aggregate"
                        ]["overall"],
                        "raw_metric": full_frame["metric"]["aggregate"]["overall"]
                        if full_frame["metric"]["available"]
                        else None,
                        "point_counts": score_sequence(
                            selection, convention, predictions, scale_only=scale_only
                        ),
                    }
                )
            print(f"scored {label} {selection.sequence}", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"hyperparameters": HYPERPARAMETERS, "results": results},
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
