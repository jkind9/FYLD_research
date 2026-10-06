"""Whole-run state; metric calibration and poses remain shared records."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class Unavailable(RuntimeError):
    """A required method or compatible input is explicitly absent."""


class IncompleteRun(RuntimeError):
    """Prevents the shared Run context from publishing incomplete predictions."""


@dataclass(frozen=True)
class StepResult:
    name: str
    status: str
    reason: str
    artifact: str | None = None


@dataclass(frozen=True)
class Result:
    path: Path
    steps: tuple[StepResult, ...]
    complete: bool
    software_control: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [asdict(step) for step in self.steps],
            "complete": self.complete,
            "software_control": self.software_control,
            "physical_accuracy": "unmeasured",
            "resource_acceptance": "unmeasured",
        }


def failed_step(name: str, error: Exception) -> StepResult:
    """Classify expected method failures consistently; unexpected errors propagate."""
    if isinstance(error, Unavailable):
        return StepResult(name, "unavailable", str(error))
    return StepResult(name, "failed", f"{type(error).__name__}: {error}")
