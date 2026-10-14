"""Score a phone session v1 walk against tape-measured camera placements."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import session_v1


def _positive(value, name):
    value = float(value)
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive finite metres")
    return value


def _checkpoint(frames, seq):
    frame = frames.get(seq)
    if frame is None or frame.pose is None or frame.tracking != "TRACKING":
        raise ValueError(f"checkpoint {seq} must be received and TRACKING inside the loop interval")
    return np.asarray(frame.pose, dtype=float)


def _tracking(frames):
    lost_events, corrections, path = 0, 0, 0.0
    failures = Counter()
    for i, frame in enumerate(frames):
        corrections += len(frame.anchor_updates)
        previous = frames[i - 1] if i else None
        if frame.pose is None:
            failures[frame.failure] += 1
            lost_events += int(previous is not None and previous.pose is not None)
        elif previous is not None and previous.pose is not None:
            path += float(np.linalg.norm(np.asarray(frame.pose[:3]) - previous.pose[:3]))
    return {"frames": len(frames), "tracked_fraction": sum(f.pose is not None for f in frames) / len(frames),
            "lost_events": lost_events, "failure_frames": dict(failures), "sampled_path_m": path,
            "anchor_corrections": corrections,
            "missing_sequence_numbers": sum(b.seq - a.seq - 1 for a, b in pairwise(frames)),
            "longest_received_gap_s": max((b.t_ns - a.t_ns for a, b in pairwise(frames)), default=0) / 1e9}


def _distance(frames, measured):
    a = _checkpoint(frames, measured["from_seq"])
    b = _checkpoint(frames, measured["to_seq"])
    tape = _positive(measured["tape_m"], "tape_m")
    estimate = float(np.linalg.norm(b[:3] - a[:3]))
    error = estimate - tape
    return measured | {"estimated_m": estimate, "signed_error_mm": error * 1000,
                       "absolute_error_percent": abs(error) / tape * 100}


def score(frames, measured):
    """Live camera poses, in metres, without alignment, scale fitting or anchor correction."""
    # A long walk's JPEGs and depth arrays must be released as each frame is read.
    frames = [SimpleNamespace(seq=f.seq, t_ns=f.t_ns, tracking=f.tracking, failure=f.failure,
                              pose=f.pose, anchor_updates=f.anchor_updates) for f in frames]
    if not frames:
        raise ValueError("session has no frames")
    if any(b.seq <= a.seq or b.t_ns <= a.t_ns for a, b in pairwise(frames)):
        raise ValueError("frame sequences and timestamps must be strictly increasing")
    if any(f.pose is not None and not np.isfinite(f.pose).all() for f in frames):
        raise ValueError("poses must be finite")
    loop = measured["loop"]
    start, end = loop["start_seq"], loop["end_seq"]
    if start >= end:
        raise ValueError("loop start_seq must precede end_seq")
    selected = [f for f in frames if start <= f.seq <= end]
    by_seq = {f.seq: f for f in selected}
    first, last = _checkpoint(by_seq, start), _checkpoint(by_seq, end)
    tape = _positive(loop["tape_length_m"], "tape_length_m")
    closure = float(np.linalg.norm(last[:3] - first[:3]))
    q_first, q_last = first[3:] / np.linalg.norm(first[3:]), last[3:] / np.linalg.norm(last[3:])
    turn = float(np.degrees(2 * np.arccos(np.clip(abs(np.dot(q_first, q_last)), 0, 1))))
    return {"walk": measured["walk"], "environment": measured["environment"],
            "pose_source": "received camera poses; no scale fit or anchor correction",
            "loop": loop | {"closure_mm": closure * 1000,
                            "closure_percent_of_tape_length": closure / tape * 100, "turn_error_deg": turn},
            "tracking": _tracking(selected),
            "distances": [_distance(by_seq, item) for item in measured["distances"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--measurements", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    metadata = session_v1.check_session(json.loads((args.session / "session.json").read_text(encoding="utf-8")))
    measured = json.loads(args.measurements.read_text(encoding="utf-8"))
    result = score(session_v1.read_session(args.session), measured)
    result["session"] = metadata
    result["measurements"] = measured
    result["measurements_file"] = str(args.measurements.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{result['walk']}: closure {result['loop']['closure_mm']:.1f} mm; "
          f"{result['tracking']['lost_events']} tracking losses; scores saved to {args.out}")


if __name__ == "__main__":
    main()
