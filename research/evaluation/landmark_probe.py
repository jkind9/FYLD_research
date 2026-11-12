"""Task116: where each frame puts one red object, from ARCore raw depth and from the fused learned depth.

Points use each frame's own pose. Anchor corrections move a whole fragment rigidly, so they cannot separate
copies made inside one fragment.

    python -B -m research.evaluation.landmark_probe --session <v2 session> --first 660 --last 730 --out <probe.json>
"""

import argparse
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from sitescan import scale, session
from sitescan.depth import load_model
from sitescan.depth import predict as predict_depth
from sitescan.pipelines import DEPTH_MODEL
from sitescan.pipelines.room import world_points
from sitescan.scale import fit_grid
from sitescan.session import wire_v1


def red_mask(rgb: np.ndarray) -> np.ndarray:
    """The largest connected blob of saturated red pixels (OpenCV hue below 6 or above 172 of 180)."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    red = (((hsv[..., 0] < 6) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 150) & (hsv[..., 2] > 90)).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(red)
    if count < 2:
        return np.zeros(red.shape, bool)
    return labels == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])


def ray_split(camera: np.ndarray, reference: np.ndarray, other: np.ndarray) -> tuple[float, float]:
    """other - reference as (metres along the camera ray through reference, metres across it)."""
    ray = (reference - camera) / np.linalg.norm(reference - camera)
    offset = other - reference
    along = float(offset @ ray)
    return along, float(np.linalg.norm(offset - along * ray))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--far", type=float, default=4.0, help="furthest fused depth in metres, as the room pipeline")
    args = parser.parse_args(argv)

    model = load_model(DEPTH_MODEL, threads=None)
    keyframe, rows = None, []
    for frame in session.read_wire_session(args.session):
        if frame.anchor_created is not None:
            keyframe = frame.anchor_created[0]
        if not args.first <= frame.seq <= args.last or frame.depth is None or frame.pose is None or keyframe is None:
            continue
        colour = np.asarray(Image.open(io.BytesIO(frame.image_jpeg)).convert("RGB"))
        mask = red_mask(colour)
        world_from_camera = wire_v1.world_from_camera_cv(frame.pose)
        row = {"seq": frame.seq, "fragment": keyframe // 10, "camera": world_from_camera[:3, 3].tolist(),
               "mask_pixels": int(mask.sum()), "depth_age_s": (frame.camera_t_ns - frame.depth.t_ns) / 1e9}
        uv, target = scale.depth_targets(session.arcore_depth(frame.depth), session.camera(frame))
        on = mask[uv[:, 1].astype(int), uv[:, 0].astype(int)]
        row["arcore_pixels"] = int(on.sum())
        if on.any():
            row["arcore"] = np.median(world_points(uv[on], target[on], frame.intrinsics, world_from_camera), 0).tolist()
        depth, valid = predict_depth(model, colour, world_from_camera)
        size = fit_grid(depth, valid, uv, target)
        if size is not None:  # the room pipeline skips the frame otherwise
            rows_, cols = np.nonzero(mask & valid & (depth * size < args.far))
            if len(rows_):
                z = depth[rows_, cols] * size[rows_, cols]
                row["learned"] = np.median(world_points(np.c_[cols, rows_], z, frame.intrinsics, world_from_camera), 0).tolist()
        if "arcore" in row and "learned" in row:
            row["learned_minus_arcore_along_across_m"] = ray_split(
                np.array(row["camera"]), np.array(row["arcore"]), np.array(row["learned"]))
        rows.append(row)
        print(json.dumps(row))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
