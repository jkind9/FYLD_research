"""Phone session input: experiment 01's readers and the v2 capture receiver, and a replay of a saved session.

A v2 folder (the capture app, through host/capture_receiver.py) and a v1 folder (the old live stream, or
src.live.stand_in) replay the same way; a v2 frame is a v1 frame with more fields.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

HOST = Path(__file__).resolve().parents[2] / "experiments" / "01_camera_capture_delivery" / "host"
sys.path.insert(0, str(HOST))  # the host modules import each other by file name
import capture_receiver  # noqa: E402
import session_v1  # noqa: E402
import session_v2  # noqa: E402

__all__ = ["capture_receiver", "replay", "session_v1", "session_v2"]


def read_session(folder: Path):
    """Frames of a saved session, v1 or v2 by its session.json."""
    version = json.loads((Path(folder) / "session.json").read_text(encoding="utf-8")).get("version")
    return (session_v2 if version == session_v2.VERSION else session_v1).read_session(folder)


def replay(folder: Path, deliver: Callable, *, speed: float = 1.0, stop: threading.Event | None = None) -> int:
    """Calls deliver(frame, image_path) for each saved frame, paced by its camera timestamps; returns the count.

    speed 1.0 plays at the recorded rate, as the phone would send it; 0 sends as fast as possible.
    """
    folder = Path(folder)
    started, first_ns, count = time.perf_counter(), None, 0
    for frame in read_session(folder):
        if stop is not None and stop.is_set():
            break
        first_ns = frame.t_ns if first_ns is None else first_ns
        if speed > 0:
            wait = (frame.t_ns - first_ns) / 1e9 / speed - (time.perf_counter() - started)
            if wait > 0:
                time.sleep(wait)
        deliver(frame, folder / "frames" / f"{frame.seq:06d}.jpg")
        count += 1
    return count
