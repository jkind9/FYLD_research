"""Outputs of today's room build and live processor on a session, saved as the golden reference.

    python -B -m tests.golden.run --session tests/fixtures/tum_desk_20 --out tests/fixtures/tum_desk_20_golden.json

The live processor is fed every frame and updated after each one, without threads or timing, so the result
does not depend on machine load. Objects are off: the detector needs Ultralytics, which the product
environment does not hold yet. Timings are left out because they change from run to run.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import torch

from src.live import room_build
from src.live.processor import LiveProcessor
from src.live.run import DEPTH_CHECKPOINT, depth_anything
from src.live.stream import read_session

THREADS = 16
VOXEL_M = 0.02


def room(session: Path) -> dict:
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch) / "room"
        room_build.main(["--session", str(session), "--out", str(out), "--threads", str(THREADS)])
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    for timing in ("vote_s", "pieces_s"):
        del summary["clean_up"][timing]
    del summary["session"]
    return summary


def live(session: Path) -> dict:
    torch.set_num_threads(THREADS)
    processor = LiveProcessor(depth_anything(DEPTH_CHECKPOINT), None, voxel_m=VOXEL_M)
    updates = []
    for frame in read_session(session):
        processor.add(frame, Path(session) / "frames" / f"{frame.seq:06d}.jpg")
        record = processor.update()
        if record is not None:
            updates.append({key: record.get(key) for key in ("frame_seq", "size", "size_source", "surface_points", "map")})
    return {"updates": updates, "surface_points": len(processor.surface())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    golden = {"room": room(args.session), "live": live(args.session)}
    args.out.write_text(json.dumps(golden, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
