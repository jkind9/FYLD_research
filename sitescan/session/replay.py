"""Replay a recording at its capture rate or as fast as its consumer allows."""

import threading
import time
from collections.abc import Callable
from pathlib import Path

from .read import frames


def replay(
    folder: Path | str,
    deliver: Callable,
    *,
    speed: float = 1.0,
    stop: threading.Event | None = None,
    reader: Callable = frames,
) -> int:
    """The number of frames delivered, paced by their camera timestamps.

    A speed of zero disables waiting. The reader argument keeps wire-record callers
    working until the orchestrators use the shared Frame record.
    """
    folder = Path(folder)
    started = time.perf_counter()
    first_ns = None
    count = 0
    for frame in reader(folder):
        if stop is not None and stop.is_set():
            break
        if first_ns is None:
            first_ns = frame.t_ns
        if speed > 0:
            delay = (frame.t_ns - first_ns) / 1e9 / speed - (time.perf_counter() - started)
            if delay > 0:
                time.sleep(delay)
        deliver(frame, folder / "frames" / f"{frame.seq:06d}.jpg")
        count += 1
    return count
