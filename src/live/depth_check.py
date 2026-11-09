"""Task117: fused learned depth against ARCore's tracked points, by distance and by ARCore depth support.

A tracked point comes from ARCore's tracking, not its depth maps, so it checks both kinds of grid cell: cells sized
by their own ARCore depth ("supported") and cells that took the frame-median fallback. One physical point is
counted once per frame that sees it.

    python -B -m src.live.depth_check --session <v2 session> --out <check.json>
"""

import argparse
import io
import json
from itertools import pairwise
from pathlib import Path

import numpy as np
from PIL import Image

from . import sizing
from .room_build import fresh_depth, grid_size, supported_pixels, upright_depth
from .stream import read_session, session_v1

BINS = (0.0, 1.0, 2.0, 3.0, 4.0)  # metres along the camera axis; 4.0 is room_build's far limit


def summarise(learned: np.ndarray, tracked: np.ndarray, supported: np.ndarray, bins=BINS) -> list[dict]:
    """learned / tracked depth per (supported, distance bin), skipping empty groups."""
    rows = []
    for flag in (True, False):
        for low, high in pairwise(bins):
            mine = (supported == flag) & (tracked >= low) & (tracked < high)
            if mine.any():
                ratio = learned[mine] / tracked[mine]
                rows.append({"supported": flag, "from_m": low, "to_m": high, "count": int(mine.sum()),
                             "median_ratio": float(np.median(ratio)), "p25": float(np.percentile(ratio, 25)),
                             "p75": float(np.percentile(ratio, 75))})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    from .run import DEPTH_CHECKPOINT, depth_anything
    model = depth_anything(DEPTH_CHECKPOINT)
    keyframe, learned, tracked, supported, frames = None, [], [], [], 0
    for frame in read_session(args.session):
        if frame.anchor_created is not None:
            keyframe = frame.anchor_created[0]
        if frame.depth is None or frame.pose is None or keyframe is None or not fresh_depth(frame):
            continue
        colour = np.asarray(Image.open(io.BytesIO(frame.image_jpeg)).convert("RGB"))
        depth, valid, _ = upright_depth(model, colour, session_v1.world_from_camera_cv(frame.pose))
        uv, target = sizing.depth_targets(frame.depth, frame.intrinsics, frame.image_size)
        size = grid_size(depth, valid, uv, target)
        if size is None:
            continue
        frames += 1
        pixels, z = sizing.point_targets(frame)
        h, w = depth.shape
        inside = (pixels[:, 0] >= 0) & (pixels[:, 0] < w) & (pixels[:, 1] >= 0) & (pixels[:, 1] < h)
        cols, rows = pixels[inside, 0].astype(int), pixels[inside, 1].astype(int)
        keep = valid[rows, cols]
        learned.append((depth * size)[rows, cols][keep])
        tracked.append(z[inside][keep])
        supported.append(supported_pixels(uv, depth.shape)[rows, cols][keep])
    learned, tracked, supported = map(np.concatenate, (learned, tracked, supported))
    rows = summarise(learned, tracked, supported)
    for row in rows:
        print(json.dumps(row))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"frames": frames, "points": len(tracked), "rows": rows}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
