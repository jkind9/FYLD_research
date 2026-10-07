"""Swappable named site measurements; Task55 owns the predictive method."""

import math
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .contracts import MappingOutput, MethodChoice, SurfaceOutput, method_label

MappingEstimator = Callable[[SurfaceOutput, Path], dict[str, Any]]


class MappingMethod(MethodChoice, Protocol):
    """Load a method receiving the saved surface and returning named measurements."""

    def load(self) -> MappingEstimator: ...


def run(
    run_context: Run, surface: SurfaceOutput, method: MappingMethod | None
) -> tuple[StepResult, MappingOutput | None]:
    artifact = "output/predictions/mapping.json"
    name = method.name if method is not None else None
    try:
        with run_context.measure("load_mapping"):
            if method is None:
                raise Unavailable("Task55 mapping, dimensions and area implementation is unavailable")
            measure_site = method.load()
        with run_context.measure("prediction_mapping"):
            output: MappingOutput = {
                "methods": {"mapping": method_label(method)},
                "control": method.control,
                "measurements": measure_site(surface, run_context.path),
            }
            validate(output)
            write_json(run_context.path / artifact, output)
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("mapping", error, name), None
    return (
        StepResult("mapping", "complete", "Method outputs saved", name, None, artifact),
        output,
    )


def validate(output: MappingOutput) -> None:
    """Completed mapping must state at least one named measurement."""
    if not isinstance(output["measurements"], dict) or not output["measurements"]:
        raise ValueError("Completed mapping output must contain measurements")
    if output["control"] is None:
        for name, measurement in output["measurements"].items():
            if (
                not isinstance(measurement, dict)
                or type(measurement.get("value")) not in (int, float)
                or not math.isfinite(measurement["value"])
                or not isinstance(measurement.get("units"), str)
                or not measurement["units"].strip()
            ):
                raise ValueError(f"Measurement {name} needs a finite value and explicit units")
