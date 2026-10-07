"""The method, status and saved artifact for each layer and the whole run."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class Unavailable(RuntimeError):
    """A required method or compatible input is explicitly absent."""


@dataclass(frozen=True)
class StepResult:
    name: str
    status: str
    reason: str
    method: str | None = None
    frames: int | None = None
    artifact: str | None = None


@dataclass(frozen=True)
class Result:
    path: Path
    steps: tuple[StepResult, ...]
    controls: dict[str, str]

    @property
    def complete(self) -> bool:
        return all(step.status == "complete" for step in self.steps)

    @property
    def is_measurement(self) -> bool:
        return self.complete and not self.controls

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [asdict(step) for step in self.steps],
            "complete": self.complete,
            "controls": self.controls,
            "is_measurement": self.is_measurement,
            "physical_accuracy": "unmeasured",
            "resource_acceptance": "unmeasured",
        }


def failed_step(name: str, error: Exception, method: str | None) -> StepResult:
    """Classify expected method failures; unexpected exceptions propagate."""
    if isinstance(error, Unavailable):
        return StepResult(name, "unavailable", str(error), method)
    return StepResult(name, "failed", f"{type(error).__name__}: {error}", method)
