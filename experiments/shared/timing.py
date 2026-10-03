"""Monotonic stage measurements with explicit throughput denominators."""

import math
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from time import perf_counter


def _count(value: int | None) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("Frame count must be a nonnegative integer or None")


def _seconds(value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError("Elapsed seconds must be finite and nonnegative")


def _fps(frames: int | None, seconds: float) -> float | None:
    if frames is None or seconds <= 0:
        return None
    try:
        result = frames / seconds
    except OverflowError:
        # Unrepresentable throughput is explicitly unavailable in metadata.
        return None
    return result if math.isfinite(result) else None


@dataclass(frozen=True)
class TimingSample:
    stage: str
    frames: int | None
    elapsed_seconds: float
    status: str

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "fps": (
                _fps(self.frames, self.elapsed_seconds)
                if self.status == "complete"
                else None
            ),
        }


class TimingLedger:
    """Own one run's timing scopes; replace immutable sample tuples on append."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self.clock = perf_counter if clock is None else clock
        self.samples: tuple[TimingSample, ...] = ()
        self.processed_frames: int | None = None
        self.active = 0

    def set_processed_frames(self, frames: int) -> None:
        _count(frames)
        self.processed_frames = frames

    @contextmanager
    def measure(self, stage: str, *, frames: int | None = None) -> Iterator[None]:
        if not isinstance(stage, str) or not stage.strip() or stage != stage.strip():
            raise ValueError("Timing stage must be a nonblank, trimmed string")
        _count(frames)
        started = self.clock()
        if not math.isfinite(started):
            raise ValueError("Clock reading must be finite")
        self.active += 1
        status = "failed"
        try:
            yield
            status = "complete"
        finally:
            self.active -= 1
            elapsed = self.clock() - started
            _seconds(elapsed)
            self.samples = (*self.samples, TimingSample(stage, frames, elapsed, status))

    def summary(self, elapsed_seconds: float, *, completed: bool) -> dict:
        _seconds(elapsed_seconds)
        if self.active:
            raise ValueError("Cannot publish timing while scopes are active")
        stages = {}
        for name in sorted({sample.stage for sample in self.samples}):
            rows = [sample for sample in self.samples if sample.stage == name]
            successful = [sample for sample in rows if sample.status == "complete"]
            seconds = math.fsum(sample.elapsed_seconds for sample in successful)
            frames = (
                sum(sample.frames for sample in successful if sample.frames is not None)
                if successful
                and all(sample.frames is not None for sample in successful)
                else None
            )
            stages[name] = {
                "successful_samples": len(successful),
                "failed_samples": len(rows) - len(successful),
                "frames": frames,
                "elapsed_seconds": seconds,
                "fps": _fps(frames, seconds),
            }
        return {
            "timing_schema_version": 2,
            "clock": "monotonic_perf_counter",
            "processed_frames": self.processed_frames,
            "end_to_end_fps": (
                _fps(self.processed_frames, elapsed_seconds) if completed else None
            ),
            "end_to_end_scope": (
                "Run construction through timing publication; includes input/source "
                "snapshots, computation, evaluation and reporting; excludes final "
                "manifest hashing and completion publication"
            ),
            "stage_fps_definition": (
                "sum successful sample frames / sum successful sample seconds; "
                "counts describe each named stage, not unique run observations"
            ),
            "stages": stages,
            "samples": [sample.to_dict() for sample in self.samples],
        }
