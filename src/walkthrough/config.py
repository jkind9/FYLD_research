"""One method choice per layer; scoring references stay outside this record."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .steps.capture import CaptureSource
from .steps.depth import DepthMethod
from .steps.mapping import MappingMethod
from .steps.objects import ObjectSettings
from .steps.surface import MetricPoints, SurfaceMethod
from .steps.tracking import CpuOdometry, TrackingMethod

STEP_NAMES = ("capture", "depth", "tracking", "surface", "mapping", "objects")


@dataclass(frozen=True)
class PipelineSpec:
    run_root: Path
    repo: Path
    source: CaptureSource
    depth: DepthMethod | None = None
    tracking: TrackingMethod = field(default_factory=CpuOdometry)
    surface: SurfaceMethod = field(default_factory=MetricPoints)
    mapping: MappingMethod | None = None
    objects: ObjectSettings = field(default_factory=ObjectSettings)
    requested: tuple[str, ...] = STEP_NAMES
    partial: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.requested, tuple)
            or not all(isinstance(name, str) for name in self.requested)
            or not set(self.requested) <= set(STEP_NAMES)
            or len(set(self.requested)) != len(self.requested)
        ):
            raise ValueError("Requested steps must be a tuple of unique known names")

    @property
    def controls(self) -> dict[str, str]:
        choices = {
            "capture": self.source,
            "depth": self.depth,
            "tracking": self.tracking,
            "surface": self.surface,
            "mapping": self.mapping,
            "objects": self.objects.detector,
            "segmentation": self.objects.segmentation,
            "appearance": self.objects.appearance,
        }
        return {
            name: choice.control
            for name, choice in choices.items()
            if choice is not None and choice.control is not None
        }

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), default=str))
