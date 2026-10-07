"""Recorded input entrypoint; software fixtures stay outside the command line."""

import argparse
import importlib
import json
from functools import partial
from pathlib import Path

from .config import STEP_NAMES, PipelineSpec
from .pipeline import run
from .steps.capture import PhoneExport, TumSequence
from .steps.objects import (
    ClassicalAppearance,
    ClassicalSegmentation,
    ObjectSettings,
    Yolo26x,
)
from .validation import ScoreRequest

pose_evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Six walkthrough layers; missing methods stay unavailable")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--report", type=Path)
    source.add_argument("--dataset", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--steps", nargs="+", choices=STEP_NAMES)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--max-distance-m", type=float)
    parser.add_argument("--ambiguity-margin-m", type=float)
    parser.add_argument("--segmentation", choices=("rectangle", "grabcut", "canny"))
    parser.add_argument("--appearance", action="store_true")
    args = parser.parse_args(argv)
    if (args.report is None) != (args.bundle is None):
        parser.error("Phone input requires both --report and --bundle")
    spec = PipelineSpec(
        args.run_root,
        Path(__file__).resolve().parents[2],
        (TumSequence(args.dataset) if args.dataset is not None else PhoneExport(args.report, args.bundle)),
        partial=args.partial,
        requested=tuple(args.steps) if args.steps else STEP_NAMES,
        objects=ObjectSettings(
            detector=Yolo26x(args.checkpoint) if args.checkpoint is not None else None,
            max_distance_m=args.max_distance_m,
            ambiguity_margin_m=args.ambiguity_margin_m,
            segmentation=ClassicalSegmentation(args.segmentation) if args.segmentation else None,
            appearance=ClassicalAppearance() if args.appearance else None,
        ),
    )
    scores: tuple[ScoreRequest, ...] = ()
    if args.dataset is not None:
        reference_file = args.dataset / "groundtruth.txt"
        scores = (
            ScoreRequest(
                "tracking",
                partial(pose_evaluation.read_references, reference_file),
                reference_file=reference_file,
            ),
        )
    result = run(spec, scores=scores)
    print(json.dumps({"path": str(result.path), **result.to_dict()}, indent=2))
    return 0 if result.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
