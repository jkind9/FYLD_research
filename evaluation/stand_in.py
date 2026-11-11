"""Turn a recorded clip into a phone session v1 folder, as a stand-in until ARCore recordings exist.

    python -m src.live.stand_in --recording tum:data/tum/rgbd_dataset_freiburg1_xyz --out <session folder>

This is a reference control, never a measurement of ARCore: the poses are the recording's ground truth and
the "raw depth" is its depth sensor, subsampled to ARCore's size. session.json says so (control: reference).
Images are re-encoded as JPEG quality 80 like the phone; every 3rd frame carries new depth (ARCore makes about
10 per second at 30 frames per second); 20 tracked points per frame (the Redmi's median was 19) come from the
sensor depth; one anchor per second; no pose corrections.
"""

from __future__ import annotations

import argparse
import importlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

from .stream import session_v1

sequences = importlib.import_module("experiments.sfm.src.sequences")

DEPTH_UNITS_PER_METRE = 5000.0  # TUM and ICL depth PNGs
DEPTH_EVERY = 3
POINTS_PER_FRAME = 20
ANCHOR_INTERVAL_NS = 1_000_000_000
ICL_FPS = 30.0  # ICL's time column is the frame number
POSE_TOLERANCE_S = 0.02  # inherited reference matching tolerance (src/walkthrough README)


def _arcore_pose(world_from_camera_cv: np.ndarray) -> list[float]:
    matrix = world_from_camera_cv @ np.diag([1.0, -1.0, -1.0, 1.0])
    return [*matrix[:3, 3].tolist(), *Rotation.from_matrix(matrix[:3, :3]).as_quat().tolist()]


def _jpeg(path: Path) -> bytes:
    out = io.BytesIO()
    Image.open(path).convert("RGB").save(out, "JPEG", quality=80)
    return out.getvalue()


def write_session(recording: str, out: Path, *, every: int = 1, depth_size=(160, 120), seed: int = 0) -> Path:
    sequence = sequences.load(recording, every=every)
    is_icl = recording.startswith("icl:")
    truth = sequence.references()
    truth_times = np.array([t for t, _ in truth])
    fx, fy, cx, cy = sequence.camera_params[:4]
    out = Path(out)
    (out / "frames").mkdir(parents=True)
    (out / "depth").mkdir()
    (out / "session.json").write_text(json.dumps({
        "type": "session", "version": 1, "device": {"model": "stand-in"}, "started_ms": 0, "control": "reference",
        "source": recording, "every": every,
        "note": "ground-truth poses and sensor depth in the phone session format; not ARCore"}, indent=2), encoding="utf-8")
    rng = np.random.default_rng(seed)
    seq, anchors, last_anchor_ns = 0, 0, None
    with open(out / "frames.jsonl", "w", encoding="utf-8") as log:
        for k, (time_s, image_name) in enumerate(zip(sequence.timestamps_s, sequence.image_names)):
            nearest = int(np.argmin(np.abs(truth_times - time_s)))
            if abs(truth_times[nearest] - time_s) > POSE_TOLERANCE_S or sequence.depth_names[k] is None:
                continue
            world_from_camera = truth[nearest][1]
            pose = _arcore_pose(world_from_camera)
            sensor = np.asarray(Image.open(sequence.image_root / sequence.depth_names[k]), dtype=np.float64) / DEPTH_UNITS_PER_METRE
            h, w = sensor.shape
            jpeg = _jpeg(sequence.image_root / image_name)
            t_ns = round((time_s / ICL_FPS if is_icl else time_s) * 1e9)
            header = {"type": "frame", "version": 1, "seq": seq, "t_ns": t_ns, "sent_ms": 0, "tracking": "TRACKING",
                      "failure": "NONE", "pose": pose, "intrinsics": [fx, fy, cx, cy],
                      "image": {"format": "jpeg", "width": w, "height": h, "bytes": len(jpeg)}, "anchors": []}
            v, u = np.nonzero(sensor > 0)
            pick = rng.choice(len(u), size=min(POINTS_PER_FRAME, len(u)), replace=False)
            camera = np.c_[(u[pick] - cx) / fx, (v[pick] - cy) / fy, np.ones(len(pick))] * sensor[v[pick], u[pick]][:, None]
            world = camera @ world_from_camera[:3, :3].T + world_from_camera[:3, 3]
            pixels = session_v1.project(pose, (fx, fy, cx, cy), world)
            header["points"] = [[seq * 100 + i, *world[i], *pixels[i], 1.0] for i in range(len(pick))]
            payload = jpeg
            if seq % DEPTH_EVERY == 0:
                dw, dh = depth_size
                sx, sy = dw / w, dh / h
                rows = np.clip(np.round(np.arange(dh) / sy).astype(int), 0, h - 1)
                cols = np.clip(np.round(np.arange(dw) / sx).astype(int), 0, w - 1)
                millimetres = np.clip(np.round(sensor[np.ix_(rows, cols)] * 1000), 0, 65535).astype("<u2")
                confidence = np.where(millimetres > 0, 255, 0).astype(np.uint8)
                header["depth"] = {"t_ns": t_ns, "width": dw, "height": dh, "intrinsics": [fx * sx, fy * sy, cx * sx, cy * sy],
                                   "bytes": millimetres.nbytes, "confidence_bytes": confidence.nbytes}
                (out / "depth" / f"{seq:06d}.bin").write_bytes(millimetres.tobytes() + confidence.tobytes())
                payload = jpeg + millimetres.tobytes() + confidence.tobytes()
            if last_anchor_ns is None or t_ns - last_anchor_ns >= ANCHOR_INTERVAL_NS:
                header["anchor"] = {"id": anchors, "pose": pose}
                anchors, last_anchor_ns = anchors + 1, t_ns
            session_v1.parse_frame(header, payload)  # refuse to write anything the receiver would refuse
            (out / "frames" / f"{seq:06d}.jpg").write_bytes(jpeg)
            log.write(json.dumps(header) + "\n")
            seq += 1
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True, help="tum:<folder> or icl:<folder>")
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"{args.out} already exists")
    print(write_session(args.recording, args.out, every=args.every))
    return 0


if __name__ == "__main__":
    sys.exit(main())
