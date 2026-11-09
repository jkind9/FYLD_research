"""Task109: score learned depth on sideways (as recorded) and upright input against ARCore raw depth.

The Redmi camera reports sensor_orientation_deg 90: turning the recorded image 90 degrees clockwise makes it
upright in portrait. The upright prediction is turned back, so pose, intrinsics and raw-depth pixels stay on
the recorded grid.

    python -B -m src.live.orientation_control --session <v2 session> --out <folder>
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from . import sizing
from .stream import read_session, session_v1

PORTRAIT = 0.7  # |camera x . world up| above this: the image's long edge is vertical, so one turn applies


def upright(image: np.ndarray, turns: int = 1) -> np.ndarray:
    """The image turned clockwise by `turns` quarter turns."""
    return np.rot90(image, k=-turns)


def recorded(image: np.ndarray, turns: int = 1) -> np.ndarray:
    return np.rot90(image, k=turns)


def quarter_turns(world_from_camera_cv: np.ndarray) -> int:
    """Clockwise quarter turns (0-3) that bring the image's down axis closest to world down (ARCore y is up)."""
    x, y = world_from_camera_cv[:3, 0], world_from_camera_cv[:3, 1]
    down_after = [y, x, -y, -x]  # each turn makes the old right axis the new down axis
    return int(np.argmax([-axis[1] for axis in down_after]))


_CLOCKWISE = np.array([[0.0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])  # old camera axes from new


def turned_camera(world_from_camera_cv: np.ndarray, intrinsics, size, turns: int):
    """Pose, (fx, fy, cx, cy) and (width, height) of the camera that took upright(image, turns)."""
    T, (fx, fy, cx, cy), (w, h) = np.asarray(world_from_camera_cv, float), intrinsics, size
    for _ in range(turns % 4):
        T, (fx, fy, cx, cy), (w, h) = T @ _CLOCKWISE, (fy, fx, h - 1 - cy, cx), (h, w)
    return T, (fx, fy, cx, cy), (w, h)


def score(model: np.ndarray, valid: np.ndarray, uv: np.ndarray, target: np.ndarray, minimum: int) -> dict | None:
    """One fitted size (Task72 median rule), then AbsRel and the share within 25% at the matched pixels."""
    h, w = model.shape
    cols, rows = np.clip(uv[:, 0].astype(int), 0, w - 1), np.clip(uv[:, 1].astype(int), 0, h - 1)
    keep = valid[rows, cols] & (model[rows, cols] > 0)
    if keep.sum() < minimum:
        return None
    predicted, truth = model[rows, cols][keep], target[keep]
    size = float(np.median(truth / predicted))
    ratio = size * predicted / truth
    return {"size": size, "abs_rel": float(np.mean(np.abs(ratio - 1))),
            "delta_1_25": float(np.mean(np.maximum(ratio, 1 / ratio) < 1.25)), "pixels": int(keep.sum())}


def is_portrait(frame: session_v1.Frame) -> bool:
    return abs(session_v1.world_from_camera(frame.pose)[1, 0]) > PORTRAIT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"{args.out} already exists; runs are never overwritten")
    args.out.mkdir(parents=True)

    eligible, flat = [], 0
    for frame in read_session(args.session):
        if frame.pose is None or frame.depth is None:
            continue
        if len(sizing.depth_targets(frame.depth, frame.intrinsics, frame.image_size)[1]) < sizing.MIN_DEPTH_PIXELS:
            continue
        if is_portrait(frame):
            eligible.append(frame)
        else:
            flat += 1
    chosen = [eligible[i] for i in np.linspace(0, len(eligible) - 1, args.frames).round().astype(int)]
    (args.out / "frames.json").write_text(json.dumps(
        {"eligible": len(eligible), "excluded_not_portrait": flat, "seq": [f.seq for f in chosen]}, indent=1))

    import torch

    from .run import DEPTH_CHECKPOINT, depth_anything
    torch.set_num_threads(args.threads)
    model = depth_anything(DEPTH_CHECKPOINT)
    rows = []
    for i, frame in enumerate(chosen):
        colour = np.asarray(Image.open(io.BytesIO(frame.image_jpeg)).convert("RGB"))
        if i == 0:
            Image.fromarray(colour).save(args.out / f"{frame.seq:06d}_recorded.jpg")
            Image.fromarray(np.ascontiguousarray(upright(colour))).save(args.out / f"{frame.seq:06d}_upright.jpg")
        side_depth, side_valid = model(colour)
        up_depth, up_valid = model(np.ascontiguousarray(upright(colour)))
        up_depth, up_valid = recorded(up_depth), recorded(up_valid)
        assert up_depth.shape == side_depth.shape, (up_depth.shape, side_depth.shape)
        targets = {"arcore_depth": (*sizing.depth_targets(frame.depth, frame.intrinsics, frame.image_size), sizing.MIN_DEPTH_PIXELS),
                   "tracked_points": (*sizing.point_targets(frame), sizing.MIN_POINTS)}
        row = {"seq": frame.seq}
        for name, (uv, target, minimum) in targets.items():
            row[name] = {"sideways": score(side_depth, side_valid, uv, target, minimum),
                         "upright": score(up_depth, up_valid, uv, target, minimum)}
        rows.append(row)
        print(json.dumps(row), flush=True)

    summary = {}
    for name in ("arcore_depth", "tracked_points"):
        for way in ("sideways", "upright"):
            got = [r[name][way] for r in rows if r[name]["sideways"] and r[name]["upright"]]
            if got:
                sizes = [g["size"] for g in got]
                summary[f"{name}/{way}"] = {
                    "frames": len(got), "abs_rel_median": float(np.median([g["abs_rel"] for g in got])),
                    "delta_1_25_median": float(np.median([g["delta_1_25"] for g in got])),
                    "size_min_median_max": [min(sizes), float(np.median(sizes)), max(sizes)]}
    (args.out / "results.json").write_text(json.dumps({"summary": summary, "frames": rows}, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
