"""Method inputs only: references belong to validation requests."""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STEP_NAMES: tuple[str, ...] = (
    "capture",
    "depth",
    "tracking",
    "surface",
    "mapping",
    "objects",
)


@dataclass(frozen=True)
class Configuration:
    run_root: Path
    repo: Path
    report: Path
    bundle: Path
    partial: bool = False
    requested: tuple[str, ...] = STEP_NAMES
    checkpoint: Path | None = None
    max_distance_m: float | None = None
    ambiguity_margin_m: float | None = None
    segmentation: str | None = None
    appearance: bool = False
    software_control: bool = False

    def __post_init__(self) -> None:
        names = set(STEP_NAMES)
        if (
            not isinstance(self.requested, tuple)
            or not all(isinstance(name, str) for name in self.requested)
            or not set(self.requested) <= names
            or len(set(self.requested)) != len(self.requested)
        ):
            raise ValueError("Requested steps must be a tuple of unique known names")
        if any(
            type(getattr(self, name)) is not bool
            for name in ("partial", "appearance", "software_control")
        ):
            raise ValueError("Run and optional-component switches must be booleans")
        for name in ("run_root", "repo", "report", "bundle", "checkpoint"):
            value = getattr(self, name)
            if value is None and name != "checkpoint":
                raise ValueError(
                    "Run, repository, report and bundle paths are required"
                )
            if value is not None:
                object.__setattr__(self, name, Path(value))
        if self.segmentation not in {None, "rectangle", "grabcut", "canny"}:
            raise ValueError("Choose an existing segmentation method explicitly")
        for name in ("max_distance_m", "ambiguity_margin_m"):
            value = getattr(self, name)
            if value is not None and (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value < 0
                or (name == "max_distance_m" and value == 0)
            ):
                raise ValueError(
                    "Explicit counting settings must be finite valid metres"
                )

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in asdict(self).items()
        }
