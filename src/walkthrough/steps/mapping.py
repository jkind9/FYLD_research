"""Task55 owns site dimensions and defined area; no invented measurements."""

from experiments.shared.runs import Run, write_json

from ..config import Configuration
from ..records import StepResult, Unavailable, failed_step
from .artifacts import MappingOutput, MappingProvider, SurfaceOutput


def run(
    publication: Run,
    surface: SurfaceOutput | None,
    config: Configuration,
    *,
    state: StepResult,
    test_provider: MappingProvider | None = None
) -> tuple[StepResult, MappingOutput | None]:
    if state.status != "pending":
        return state, None
    artifact = "output/predictions/mapping.json"
    try:
        with publication.measure("prediction_mapping"):
            if surface is None:
                raise ValueError("Required upstream predictions are missing")
            if test_provider is None:
                raise Unavailable(
                    "Task55 mapping, dimensions and area implementation is unavailable"
                )
            if not config.software_control:
                raise ValueError("Test mapping providers require software_control=True")
            output: MappingOutput = {
                "software_control": True,
                "measurements": test_provider(surface),
            }
            # Export this layer's predictions before returning downstream data.
            write_json(publication.path / artifact, output)
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        return failed_step(state.name, error), None
    return StepResult(state.name, "complete", "Method outputs saved", artifact), output
