"""Recorded input entrypoint; software providers are never CLI methods."""

import argparse
import json
from pathlib import Path

from .config import STEP_NAMES, Configuration
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Six sequential walkthrough steps; missing methods stay unavailable"
    )
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=STEP_NAMES,
    )
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--max-distance-m", type=float)
    parser.add_argument("--ambiguity-margin-m", type=float)
    parser.add_argument("--segmentation", choices=("rectangle", "grabcut", "canny"))
    parser.add_argument("--appearance", action="store_true")
    args = parser.parse_args(argv)
    config = Configuration(
        args.run_root,
        Path(__file__).resolve().parents[2],
        args.report,
        args.bundle,
        partial=args.partial,
        requested=tuple(args.steps) if args.steps else STEP_NAMES,
        checkpoint=args.checkpoint,
        max_distance_m=args.max_distance_m,
        ambiguity_margin_m=args.ambiguity_margin_m,
        segmentation=args.segmentation,
        appearance=args.appearance,
    )
    result = run(config)
    print(json.dumps({"path": str(result.path), **result.to_dict()}, indent=2))
    return 0 if result.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
