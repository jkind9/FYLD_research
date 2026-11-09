"""Write the committed 20-frame fixture, in recording format v2, from the public TUM fr1/desk recording.

    python -B -m tests.fixtures.build

Every 5th frame of the recording goes through today's stand-in writer, and the first 20 are kept. The
stand-in writes format v1, and the room build reads only v2, so each frame is rewritten as v2 here: the
same pose, depth and tracked points, with the grey image taken from the JPEG. The v2 reader checks each
frame on the way out.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from src.live import stand_in
from src.live.stream import session_v2

RECORDING = "tum:data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk"
EVERY = 5
FRAMES = 20
JPEG_QUALITY = 80
FIXTURE = Path(__file__).parent / "tum_desk_20"
ARCORE_FIELDS = ("tracking", "failure", "pose", "intrinsics", "points", "anchors", "depth", "anchor")


def v2_header(v1: dict, jpeg: bytes, w: int, h: int) -> dict:
    arcore = {key: v1[key] for key in ARCORE_FIELDS if key in v1}
    arcore |= {"t_ns": v1["t_ns"], "device_pose": v1["pose"], "texture_intrinsics": v1["intrinsics"]}
    return {"type": "frame", "version": 2, "session": FIXTURE.name, "seq": v1["seq"], "camera_t_ns": v1["t_ns"],
            "wall_ms": 0, "camera": None, "grey": {"width": w, "height": h, "encoding": "raw", "bytes": w * h},
            "colour": {"format": "jpeg", "width": w, "height": h, "quality": JPEG_QUALITY, "bytes": len(jpeg)},
            "arcore": arcore, "n": v1["seq"] + 1}


def build(out: Path = FIXTURE) -> Path:
    with tempfile.TemporaryDirectory() as scratch:
        full = stand_in.write_session(RECORDING, Path(scratch) / "session", every=EVERY)
        for folder in ("frames", "cam0", "depth"):
            (out / folder).mkdir(parents=True)
        session = json.loads((full / "session.json").read_text(encoding="utf-8")) | {"version": 2}
        (out / "session.json").write_text(json.dumps(session, indent=2), encoding="utf-8")
        lines = (full / "frames.jsonl").read_text(encoding="utf-8").splitlines()[:FRAMES]
        with open(out / "frames.jsonl", "w", encoding="utf-8") as log:
            for line in lines:
                v1 = json.loads(line)
                name = f"{v1['seq']:06d}"
                jpeg = (full / "frames" / f"{name}.jpg").read_bytes()
                grey = Image.open(io.BytesIO(jpeg)).convert("L")
                grey.save(out / "cam0" / f"{name}.png")
                (out / "frames" / f"{name}.jpg").write_bytes(jpeg)
                if "depth" in v1:
                    shutil.copy(full / "depth" / f"{name}.bin", out / "depth")
                header = v2_header(v1, jpeg, *grey.size)
                payload = np.asarray(grey).tobytes() + jpeg + ((out / "depth" / f"{name}.bin").read_bytes()
                                                              if "depth" in v1 else b"")
                session_v2.parse_frame(header, payload)
                log.write(json.dumps(header) + "\n")
    return out


if __name__ == "__main__":
    print(build())
