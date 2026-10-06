"""The sole complete walkthrough sequence, with explicit dependency failures."""

from typing import Any

from experiments.shared.runs import Run, artifact_inventory, write_json

from . import validation
from .config import Configuration
from .records import IncompleteRun, Result, StepResult
from .steps import capture, depth, mapping, objects, surface, tracking
from .steps.artifacts import TestProviders


def _check_dependencies(
    config: Configuration,
    states: tuple[StepResult, ...],
    name: str,
    dependencies: tuple[str, ...],
) -> StepResult:
    """Decide whether a step can run; never execute methods or write files."""
    if name not in config.requested:
        return StepResult(name, "skipped", "Not requested")
    completed = {state.name for state in states if state.status == "complete"}
    if not set(dependencies) <= completed:
        return StepResult(name, "skipped", "Required upstream step is incomplete")
    if not config.partial and any(state.status != "complete" for state in states):
        return StepResult(
            name, "skipped", "Required run stopped after an incomplete step"
        )
    return StepResult(name, "pending", "Ready to run")


def run(
    config: Configuration,
    *,
    scores: tuple[validation.ScoreRequest, ...] = (),
    test_providers: TestProviders | None = None,
) -> Result:
    controls: dict[str, Any] = {} if test_providers is None else dict(test_providers)
    if controls and (
        not config.software_control
        or not set(controls) <= {"depth", "mapping", "backend", "detector"}
    ):
        raise ValueError("Explicit test providers require a labelled software control")
    publication = Run(config.run_root, config.repo, config.to_dict())
    result = None
    try:
        with publication:
            states: tuple[StepResult, ...] = ()

            # 1. Validate capture inputs and export originals.
            state = _check_dependencies(config, states, "capture", ())
            state, captured = capture.run(publication, config, state=state)
            states = (*states, state)

            # 2. Estimate depth and export depth arrays.
            state = _check_dependencies(config, states, "depth", ("capture",))
            state, measured = depth.run(
                publication,
                captured,
                config,
                test_provider=controls.get("depth"),
                state=state,
            )
            states = (*states, state)

            # 3. Track the camera and export estimated poses.
            state = _check_dependencies(
                config, states, "tracking", ("capture", "depth")
            )
            state, tracked = tracking.run(
                publication,
                captured,
                measured,
                config,
                test_backend=controls.get("backend"),
                state=state,
            )
            states = (*states, state)

            # 4. Reconstruct and export observed surfaces.
            state = _check_dependencies(
                config, states, "surface", ("depth", "tracking")
            )
            state, reconstructed = surface.run(
                publication, measured, tracked, config, state=state
            )
            states = (*states, state)

            # 5. Calculate and export mapping, dimensions and area.
            state = _check_dependencies(config, states, "mapping", ("surface",))
            state, _ = mapping.run(
                publication,
                reconstructed,
                config,
                test_provider=controls.get("mapping"),
                state=state,
            )
            states = (*states, state)

            # 6. Recognise objects and export distinct counts.
            state = _check_dependencies(
                config, states, "objects", ("capture", "depth", "tracking")
            )
            state, _ = objects.run(
                publication,
                captured,
                measured,
                tracked,
                config,
                test_detector=controls.get("detector"),
                state=state,
            )
            states = (*states, state)

            # Export whole-run results and record prediction hashes before references.
            result = Result(
                publication.path,
                states,
                all(s.status == "complete" for s in states),
                config.software_control,
            )
            write_json(publication.path / "output/result.json", result.to_dict())
            predictions = publication.path / "output/predictions"
            hashes = artifact_inventory(predictions)
            write_json(
                publication.path / "metadata/prediction_hashes.json", {"files": hashes}
            )
            # Load references and validate saved predictions through their owners.
            with publication.measure("scoring"):
                scored = validation.score(publication, config, states, scores)
            if artifact_inventory(predictions) != hashes:
                raise ValueError("Prediction artifacts changed during scoring")
            # Export scoring results only after checking prediction integrity.
            write_json(publication.path / "output/scores.json", scored)
            if not result.complete:
                raise IncompleteRun(
                    "Six-step predictions are incomplete; inspect output/result.json"
                )
            # Publish a complete manifest only when all six steps succeeded.
            publication.finish()
    except IncompleteRun:
        if result is None or result.complete:
            raise
    assert result is not None
    return result
