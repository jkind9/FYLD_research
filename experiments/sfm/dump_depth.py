"""Save Depth Anything V2 Metric Small depth for every frame of a sequence (CPU, `.venv-yolo`).

    python -m experiments.sfm.dump_depth --recording icl:data/icl_nuim/trajectory2 --every 2 \
        --output experiments/sfm/runs/depth/icl_every2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from experiments.shared.contracts import Calibration
from src.walkthrough.steps.contracts import ColourFrame
from src.walkthrough.steps.depth import DepthAnythingV2Metric

from .src import sequences

CHECKPOINT = Path("data/models/depth_anything_v2_metric_indoor_small")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"{args.output} already exists; depth dumps are never overwritten")
    sequence = sequences.load(args.recording, every=args.every)
    args.output.mkdir(parents=True)
    # Depth Anything ignores calibration; the record only satisfies the frame contract.
    calibration = Calibration(640, 480, 525.0, 525.0, 319.5, 239.5, "x-right_y-down_z-forward")
    frames = (ColourFrame(f, t, calibration, np.asarray(Image.open(sequence.image_root / n).convert("RGB")))
              for f, t, n in zip(sequence.frame_ids, sequence.timestamps_s, sequence.image_names))
    predict = DepthAnythingV2Metric(args.checkpoint, device="cpu").load()
    index, started = {}, time.perf_counter()
    for i, prediction in enumerate(predict(frames, run=None)):
        name = f"{i:06d}.npz"
        np.savez(args.output / name, depth=prediction.depth.astype(np.float32), valid=prediction.valid)
        index[prediction.frame_id] = name
    seconds = time.perf_counter() - started
    record = {"recording": args.recording, "every": args.every, "model": "depth_anything_v2_metric_indoor_small",
              "checkpoint": str(args.checkpoint), "device": "cpu", "frames": index,
              "seconds": seconds, "frames_per_second": len(index) / seconds}
    (args.output / "index.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"{len(index)} frames, {len(index) / seconds:.2f} fps -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
