"""Live processing entry point: a phone session v1 stream in, surface, map and object counts updated in a loop.

    python -m src.live.run --replay <saved session folder> --out <run folder>
    python -m src.live.run --listen 8765 --out <run folder>

--replay feeds a saved session (from the receiver or src.live.stand_in) at its recorded speed, as the phone
would send it. --listen receives one phone connection (saved under <out>/sessions) and processes it while it
streams. Frames that arrive while an update runs are not queued: each update takes the newest frame.
Writes updates.jsonl (one line per update), surface.ply and summary.json. CPU only.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

from experiments.shared.contracts import Calibration

from .processor import LiveProcessor
from .stream import receiver, replay

DEPTH_CHECKPOINT = Path("data/models/depth_anything_v2_metric_indoor_small")
DETECTOR_CHECKPOINT = Path("checkpoints/yolo26x.pt")


def depth_anything(checkpoint: Path):
    """Depth Anything V2 Metric Small on the CPU as depth_model(rgb) -> (depth_m, valid)."""
    from src.walkthrough.steps.contracts import ColourFrame
    from src.walkthrough.steps.depth import DepthAnythingV2Metric

    predict = DepthAnythingV2Metric(checkpoint, device="cpu").load()

    def estimate(colour: np.ndarray):
        h, w = colour.shape[:2]
        # the model ignores calibration; the record only satisfies the frame contract
        frame = ColourFrame("live", None, Calibration(w, h, 1.0, 1.0, w / 2, h / 2, "x-right_y-down_z-forward"), colour)
        prediction = next(iter(predict(iter([frame]), run=None)))
        return prediction.depth, prediction.valid

    return estimate


def yolo26x(checkpoint: Path):
    import importlib

    detector_owner = importlib.import_module("experiments.06_object_recognition.pilot.detector")
    return detector_owner.YoloDetector(checkpoint, "cpu").predict


def wall_ms(record: dict) -> float:
    """An update's own time: the detection that runs alongside is already inside objects_wait."""
    return sum(ms for stage, ms in record["stage_ms"].items() if stage != "objects_alongside")


def run(args: argparse.Namespace) -> dict:
    import torch

    torch.set_num_threads(args.threads)
    args.out.mkdir(parents=True)
    processor = LiveProcessor(depth_anything(args.depth_checkpoint),
                              None if args.no_objects else yolo26x(args.detector_checkpoint), voxel_m=args.voxel)
    done = threading.Event()

    def feed():
        try:
            if args.replay:
                replay(args.replay, processor.add, speed=args.speed)
            else:
                server = receiver.Receiver(args.out / "sessions", port=args.listen, on_frame=processor.add)
                print(f"Listening on port {server.port}", flush=True)
                server.serve_one()
        finally:
            done.set()

    threading.Thread(target=feed, daemon=True).start()
    finished, records = [], []
    with open(args.out / "updates.jsonl", "w", encoding="utf-8") as log:
        while True:
            stream_ended = done.is_set()  # read before update(), so a last frame is never left behind
            record = processor.update()
            if record is None:
                if stream_ended:
                    break
                time.sleep(0.005)
                continue
            finished.append(time.perf_counter())
            records.append(record)
            log.write(json.dumps(record) + "\n")
            log.flush()
            print(f"update {record['update']}: frame {record['frame_seq']}, {record.get('surface_points', 0)} points, "
                  f"counts {record.get('counts', {})}, {wall_ms(record):.0f} ms", flush=True)
    surface = processor.surface()
    if len(surface):
        import open3d as o3d

        o3d.io.write_point_cloud(str(args.out / "surface.ply"), o3d.geometry.PointCloud(o3d.utility.Vector3dVector(surface)))
    gaps = np.diff(finished)
    stages = sorted({name for r in records for name in r["stage_ms"]})
    summary = {
        "input": str(args.replay) if args.replay else f"listen:{args.listen}", "speed": args.speed if args.replay else 1.0,
        "threads": args.threads, "voxel_m": args.voxel, "objects": not args.no_objects,
        "frames_received": processor.frames_received, "updates": len(records),
        "seconds": float(finished[-1] - finished[0]) if len(finished) > 1 else 0.0,
        "updates_per_second": float(len(gaps) / gaps.sum()) if len(gaps) else 0.0,
        "longest_gap_s": float(gaps.max()) if len(gaps) else None,
        "gaps_over_1s": int((gaps > 1.0).sum()),
        "update_ms_median": float(np.median([wall_ms(r) for r in records])) if records else None,
        "stage_ms_median": {s: float(np.median([r["stage_ms"][s] for r in records if s in r["stage_ms"]])) for s in stages},
        "latency_ms_median": float(np.median([r["latency_ms"] for r in records if "latency_ms" in r])) if records else None,
        "size_sources": {s: sum(r["size_source"] == s for r in records) for s in {r["size_source"] for r in records}},
        "corrections": sum(r["corrections"] for r in records),
        "surface_points": len(surface), "final": records[-1] if records else None,
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--replay", type=Path)
    source.add_argument("--listen", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--speed", type=float, default=1.0, help="replay speed; 1.0 is the recorded rate")
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--voxel", type=float, default=0.02, help="fusion voxel in metres (Task72: 0.02 TUM, 0.01 ICL)")
    parser.add_argument("--no-objects", action="store_true")
    parser.add_argument("--depth-checkpoint", type=Path, default=DEPTH_CHECKPOINT)
    parser.add_argument("--detector-checkpoint", type=Path, default=DETECTOR_CHECKPOINT)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"{args.out} already exists; runs are never overwritten")
    summary = run(args)
    print(json.dumps({k: v for k, v in summary.items() if k != "final"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
