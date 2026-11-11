"""Outputs of the room and live pipelines on a recording, saved as the golden reference.

    python -B -m tests.golden.run --session tests/fixtures/tum_desk_20 --out tests/fixtures/tum_desk_20_golden.json

The live processor is fed every frame and updated after each one, without threads or timing, so the result
does not depend on machine load. Objects are off, so the golden lane needs no detector weights. Timings are
left out because they change from run to run.
"""

import argparse
import json
from pathlib import Path

import torch

from sitescan.depth import load_model
from sitescan.pipelines import DEPTH_MODEL, LiveProcessor, LiveSettings, build_room
from sitescan.session import read_wire_session

THREADS = 16
VOXEL_M = 0.02


def room(session: Path) -> dict:
    summary = build_room(session, load_model(DEPTH_MODEL, threads=THREADS)).summary
    del summary["clean_up"]["clean_s"]
    del summary["session"]
    return json.loads(json.dumps(summary))


def live(session: Path) -> dict:
    torch.set_num_threads(THREADS)
    processor = LiveProcessor(load_model(DEPTH_MODEL, threads=None), None, LiveSettings(voxel_m=VOXEL_M))
    updates = []
    for frame in read_wire_session(session):
        processor.add(frame, Path(session) / "frames" / f"{frame.seq:06d}.jpg")
        record = processor.update()
        if record is not None:
            updates.append({key: record.get(key) for key in ("frame_seq", "scale", "scale_source", "surface_points", "map")})
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
