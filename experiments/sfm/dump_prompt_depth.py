"""Prompt Depth Anything depth for every SfM-placed frame, prompted with that frame's SfM points (CPU, `.venv-yolo`).

    python -m experiments.sfm.dump_prompt_depth --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2 \
        --sfm-run experiments/sfm/runs/tum_xyz/<run>/output/incremental --size 0.0459 --fill linear \
        --output experiments/sfm/runs/depth/xyz_prompt_linear
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

from .src import prompt, sequences

CHECKPOINT = "depth-anything/prompt-depth-anything-vits-hf"
IMAGE_HW = (480, 640)
GRID_HW = (192, 256)
MIN_POINTS = 20


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--sfm-run", type=Path, required=True, help="<sfm run>/output/<mapper>")
    parser.add_argument("--size", type=float, required=True, help="metres per SfM unit")
    parser.add_argument("--fill", choices=("linear", "nearest"), default="linear")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"{args.output} already exists; depth dumps are never overwritten")
    sequence = sequences.load(args.recording, every=args.every)
    rows = json.loads((args.sfm_run / "frames.json").read_text(encoding="utf-8"))["frames"]
    largest = prompt.largest_model(rows)
    points = np.load(args.sfm_run / "points.npz")
    observations = dict(np.load(args.sfm_run / "observations.npz"))
    keep = (points["track_length"] >= 3) & (points["error_px"] <= 2.0)
    processor = AutoImageProcessor.from_pretrained(CHECKPOINT)
    model = AutoModelForDepthEstimation.from_pretrained(CHECKPOINT).eval()
    args.output.mkdir(parents=True)
    index, skipped, prompt_s, model_s, started = {}, 0, 0.0, 0.0, perf_counter()
    for k, row in enumerate(rows):
        if row["model_id"] != largest:
            continue
        t = perf_counter()
        uv, depth = prompt.frame_points(rows, points["xyz"], observations, keep, k, size=args.size,
                                        width=IMAGE_HW[1], height=IMAGE_HW[0])
        grid = prompt.prompt_map(uv, depth, IMAGE_HW, GRID_HW, args.fill) if len(depth) >= MIN_POINTS else None
        prompt_s += perf_counter() - t
        if grid is None:
            skipped += 1
            continue
        t = perf_counter()
        image = Image.open(sequence.image_root / sequence.image_names[k]).convert("RGB")
        pixels = processor(images=image, return_tensors="pt")["pixel_values"]
        with torch.no_grad():
            predicted = model(pixel_values=pixels, prompt_depth=torch.from_numpy(grid)[None, None]).predicted_depth
            resized = torch.nn.functional.interpolate(predicted[None], size=IMAGE_HW, mode="bilinear", align_corners=False)[0, 0]
        model_s += perf_counter() - t
        result = resized.numpy().astype(np.float32)
        name = f"{len(index):06d}.npz"
        np.savez(args.output / name, depth=result, valid=np.isfinite(result) & (result > 0))
        index[sequence.frame_ids[k]] = name
    seconds = perf_counter() - started
    record = {"recording": args.recording, "every": args.every, "model": CHECKPOINT, "device": "cpu", "fill": args.fill,
              "size_metres_per_sfm_unit": args.size, "sfm_run": str(args.sfm_run), "frames": index,
              "frames_skipped_few_points": skipped, "seconds": seconds, "prompt_seconds": prompt_s, "model_seconds": model_s,
              "frames_per_second": len(index) / seconds, "model_frames_per_second": len(index) / model_s,
              "torch_threads": torch.get_num_threads()}
    (args.output / "index.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"{len(index)} frames ({skipped} skipped), {len(index) / seconds:.2f} fps end to end -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
