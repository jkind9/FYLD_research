"""Depth Anything 3 Small depth for every SfM-placed frame (CPU, `.venv-yolo`).

The model code is cloned to third_party/depth-anything-3 (commit 3d835ec) with its extra packages in
third_party/da3-deps; neither is installed into an environment:

    PYTHONPATH="<repo>/third_party/depth-anything-3/src;<repo>/third_party/da3-deps" \
    .venv-yolo/Scripts/python.exe -B -m experiments.sfm.dump_da3_depth --recording icl:data/icl_nuim/trajectory2 --every 2 \
        --sfm-run experiments/sfm/runs/icl_lr2/<run>/output/incremental --size 0.2774 --mode posed --output experiments/sfm/runs/depth/icl_da3_posed

`single` runs each photo alone (relative depth, to be sized per frame like Task72); `posed` gives windows of
photos the sized SfM poses and the camera, and returns depth in metres.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from depth_anything_3.api import DepthAnything3

from .src import posed, prompt, sequences

CHECKPOINT = "depth-anything/da3-small"
IMAGE_HW = (480, 640)
WINDOW = 5


def resized(depth: np.ndarray) -> np.ndarray:
    tensor = torch.from_numpy(depth.astype(np.float32))[None, None]
    return torch.nn.functional.interpolate(tensor, size=IMAGE_HW, mode="bilinear", align_corners=False)[0, 0].numpy()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--sfm-run", type=Path, required=True, help="<sfm run>/output/<mapper>")
    parser.add_argument("--size", type=float, required=True, help="metres per SfM unit")
    parser.add_argument("--mode", choices=("single", "posed"), required=True)
    parser.add_argument("--stride", type=int, default=1, help="posed: frames between window members (1 = consecutive)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"{args.output} already exists; depth dumps are never overwritten")
    sequence = sequences.load(args.recording, every=args.every)
    rows = json.loads((args.sfm_run / "frames.json").read_text(encoding="utf-8"))["frames"]
    largest = prompt.largest_model(rows)
    placed = [k for k, row in enumerate(rows) if row["model_id"] == largest]
    fx, fy, cx, cy = sequence.camera_params[:4]
    intrinsics = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1.0]])
    model = DepthAnything3.from_pretrained(CHECKPOINT).to("cpu").eval()
    args.output.mkdir(parents=True)
    index, metric_flags, model_s, started = {}, set(), 0.0, perf_counter()
    for members, kept in posed.windows(len(placed), WINDOW if args.mode == "posed" else 1, args.stride):
        frames = [placed[i] for i in members]
        paths = [str(sequence.image_root / sequence.image_names[k]) for k in frames]
        t = perf_counter()
        if args.mode == "posed":
            extrinsics = posed.sized_extrinsics([rows[k]["T_world_camera"] for k in frames], args.size)
            prediction = model.inference(paths, extrinsics=extrinsics, intrinsics=np.array([intrinsics] * len(frames)))
        else:
            prediction = model.inference(paths)
        model_s += perf_counter() - t
        metric_flags.add(bool(prediction.is_metric))
        for i in kept:
            result = resized(prediction.depth[members.index(i)])
            name = f"{len(index):06d}.npz"
            np.savez(args.output / name, depth=result, valid=np.isfinite(result) & (result > 0))
            index[sequence.frame_ids[placed[i]]] = name
    seconds = perf_counter() - started
    record = {"recording": args.recording, "every": args.every, "model": CHECKPOINT, "device": "cpu", "mode": args.mode,
              "window": WINDOW if args.mode == "posed" else 1, "stride": args.stride, "size_metres_per_sfm_unit": args.size, "sfm_run": str(args.sfm_run),
              "frames": index, "seconds": seconds, "model_seconds": model_s, "frames_per_second": len(index) / seconds,
              "model_frames_per_second": len(index) / model_s, "is_metric_flags": sorted(metric_flags),
              "torch_threads": torch.get_num_threads()}
    (args.output / "index.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"{len(index)} frames, {len(index) / seconds:.2f} fps end to end -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
