"""Run LingBot-Map on a phone session's frames and save a camera pose and a depth map for every frame.

Runs in research/experiments/lingbot_map/.venv (Python 3.10, torch 2.8.0 cu128) and reuses LingBot-Map's own demo.py for loading,
the model and post-processing. Frames are turned 90 degrees clockwise first, because the Redmi records
portrait walks on their side (Task109). Only what compare.py needs is kept, as memory-mappable .npy files:
depth.npy and depth_conf.npy (float16, N x 518 x 518), extrinsic.npy (world-to-camera, N x 3 x 4),
intrinsic.npy (N x 3 x 3), and run.json with timings and memory peaks.

    experiments\\lingbot_map\\.venv\\python -B research/experiments/lingbot_map/run.py --frames <session>/frames --model <ckpt.pt> --out <folder>
"""

import argparse
import json
import os
import shutil
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import psutil
import torch

REPO = Path(__file__).resolve().parents[3] / "third_party" / "lingbot-map"
sys.path.insert(0, str(REPO))
import demo

SCALE_FRAMES = 8  # demo.py default: the first frames fix the scene's scale


def stop_above(limit_gb: float) -> None:
    """End the process if its RAM passes the limit, so a long CPU run cannot starve other work on this PC."""
    process = psutil.Process()

    def watch():
        while process.memory_info().rss < limit_gb * 1e9:
            time.sleep(0.5)
        print(f"RAM passed {limit_gb} GB; stopping", flush=True)
        os._exit(3)

    threading.Thread(target=watch, daemon=True).start()


def keyframe_interval(frames: int) -> int:
    """demo.py's automatic rule: keep at most 320 frames in the streaming cache (1 for 320 frames or fewer)."""
    return (frames + 319) // 320


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--first", type=int, default=None, help="only the first N frames (smoke tests)")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-ram-gb", type=float, default=18.0)
    parser.add_argument("--window", type=int, default=64, help="recent frames kept in full; RAM grows with it")
    parser.add_argument("--anchors", type=int, default=SCALE_FRAMES, help="first frames processed together to fix scale")
    args = parser.parse_args(argv)
    stop_above(args.max_ram_gb)
    device = torch.device(args.device)
    start = time.time()

    # ".jpg" only: demo.py's default also globs ".JPG", which on Windows matches every file a second time
    images, paths, rotated = demo.load_images(image_folder=str(args.frames), image_ext=".jpg", first_k=args.first,
                                              stride=args.stride, rotate_clockwise_90=True)
    shutil.rmtree(rotated, ignore_errors=True)  # demo.py leaves its turned copies in a temp folder
    settings = SimpleNamespace(mode="streaming", image_size=518, patch_size=14, enable_3d_rope=True,
                               max_frame_num=1024, kv_cache_sliding_window=args.window, num_scale_frames=args.anchors,
                               use_sdpa=True, camera_num_iterations=4,  # SDPA: FlashInfer is not installed
                               model_path=str(args.model))
    # Load and cast on the CPU: loading straight to the GPU puts the fp32 checkpoint and an fp32 model copy there
    # (8.9 GB), and on Windows that freed memory fragments and later spills into system RAM
    model = demo.load_model(settings, torch.device("cpu"))
    gpu = device.type == "cuda"
    dtype = torch.bfloat16  # the authors' inference type; halves weight and attention memory, and Zen 5 has bf16 maths
    model.aggregator = model.aggregator.to(dtype=dtype)  # demo.py does this on the GPU; the heads stay fp32
    model = model.to(device)
    if gpu:  # Windows has no expandable CUDA segments: the growing cache fragments the pool unless freed blocks go back
        forward = model.forward

        def forward_then_release(*a, **k):
            out = forward(*a, **k)
            torch.cuda.empty_cache()
            return out

        model.forward = forward_then_release
    shape_probe = images[:1]  # postprocess needs only the image size, so the full stack can leave the CPU
    frames = len(images)
    # Frames stay in system RAM: inference_streaming moves one frame at a time, saving ~0.9 GB of GPU memory
    loaded_s = time.time() - start

    interval = keyframe_interval(frames)
    start = time.time()
    with torch.no_grad(), torch.autocast(device.type, dtype=dtype):
        predictions = model.inference_streaming(images, num_scale_frames=args.anchors, keyframe_interval=interval,
                                                output_device=torch.device("cpu"))
    inference_s = time.time() - start
    del images, model
    if gpu:
        peak_gpu_gb = torch.cuda.max_memory_allocated() / 1e9
        torch.cuda.empty_cache()
    predictions.pop("world_points", None)  # 3 floats per pixel; compare.py rebuilds points from depth
    predictions.pop("world_points_conf", None)
    predictions, _ = demo.postprocess(predictions, shape_probe)

    args.out.mkdir(parents=True, exist_ok=True)
    # On the CPU the heads also run in bfloat16: LingBot-Map turns autocast off for them on CUDA only
    np.save(args.out / "depth.npy", predictions.pop("depth")[..., 0].float().numpy().astype(np.float16))
    np.save(args.out / "depth_conf.npy", predictions.pop("depth_conf").float().numpy().astype(np.float16))
    np.save(args.out / "extrinsic.npy", predictions["extrinsic"].float().numpy())
    np.save(args.out / "intrinsic.npy", predictions["intrinsic"].float().numpy())
    record = {
        "frames": frames, "stride": args.stride, "keyframe_interval": interval, "window": args.window, "anchors": args.anchors, "device": torch.cuda.get_device_name(0) if gpu else "cpu",
        "names": [Path(p).name for p in paths], "processed_hw": list(shape_probe.shape[-2:]),
        "model": args.model.name, "load_s": round(loaded_s, 1), "inference_s": round(inference_s, 1),
        "frames_per_s": round(frames / inference_s, 2),
        "peak_ram_gb": round(psutil.Process().memory_info().peak_wset / 1e9, 2),
        "peak_gpu_gb": round(peak_gpu_gb, 2) if gpu else None,
    }
    (args.out / "run.json").write_text(json.dumps(record, indent=1))
    print(json.dumps({k: v for k, v in record.items() if k != "names"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
