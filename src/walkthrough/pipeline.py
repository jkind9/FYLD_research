"""Run the six README layers, validate saved outputs, then score and publish."""

from experiments.shared.runs import Run, artifact_inventory, write_json

from . import validation, visualization
from .config import STEP_NAMES, PipelineSpec
from .records import Result, StepResult
from .steps import capture, depth, mapping, objects, surface, tracking

READS = {
    "capture": (),
    "depth": ("capture",),
    "tracking": ("capture", "depth"),
    "surface": ("depth", "tracking"),
    "mapping": ("surface",),
    "objects": ("capture", "depth", "tracking"),
}


def skip_reason(spec: PipelineSpec, status: dict[str, StepResult], name: str) -> str | None:
    """Partial runs wait for inputs; other runs wait for every preceding layer."""
    if name not in spec.requested:
        return "Not requested"
    needs = READS[name] if spec.partial else STEP_NAMES[: STEP_NAMES.index(name)]
    blocking = [f"{need} is {status[need].status}" for need in needs if status[need].status != "complete"]
    return f"Waiting on earlier layers: {', '.join(blocking)}" if blocking else None


def run(spec: PipelineSpec, *, scores: tuple[validation.ScoreRequest, ...] = ()) -> Result:
    """The shared run context owns saved inputs, settings, artifacts and timing."""
    status: dict[str, StepResult] = {}
    captured = measured = tracked = reconstructed = mapped = recognised = None
    with Run(spec.run_root, spec.repo, spec.to_dict()) as run_context:
        # 1. Camera capture: source identity, calibration and original image bytes.
        if reason := skip_reason(spec, status, "capture"):
            status["capture"] = StepResult("capture", "skipped", reason)
        else:
            status["capture"], captured = capture.run(run_context, spec.source)
        if captured is not None:
            capture.validate(captured)
        with run_context.measure("visual_capture"):
            visualization.capture(run_context.path, status["capture"], captured)

        # 2. Depth: metric arrays for exactly the captured frames.
        if reason := skip_reason(spec, status, "depth"):
            status["depth"] = StepResult("depth", "skipped", reason)
        else:
            status["depth"], measured = depth.run(run_context, captured, spec.depth)
        if measured is not None:
            depth.validate(captured, measured)
        with run_context.measure("visual_depth"):
            visualization.depth(run_context.path, status["depth"], captured, measured)

        # 3. Camera position: one valid camera-to-world pose per captured frame.
        if reason := skip_reason(spec, status, "tracking"):
            status["tracking"] = StepResult("tracking", "skipped", reason)
        else:
            status["tracking"], tracked = tracking.run(run_context, captured, measured, spec.tracking)
        with run_context.measure("visual_tracking"):
            visualization.tracking(run_context.path, status["tracking"], tracked)

        # 4. Surface: saved world points retain depth frame IDs and metre units.
        if reason := skip_reason(spec, status, "surface"):
            status["surface"] = StepResult("surface", "skipped", reason)
        else:
            status["surface"], reconstructed = surface.run(run_context, measured, tracked, spec.surface)
        if reconstructed is not None:
            surface.validate(measured, reconstructed)
        with run_context.measure("visual_surface"):
            visualization.surface(run_context.path, status["surface"], captured, measured, reconstructed)

        # 5. Mapping: named measurements must exist before the layer completes.
        if reason := skip_reason(spec, status, "mapping"):
            status["mapping"] = StepResult("mapping", "skipped", reason)
        else:
            status["mapping"], mapped = mapping.run(run_context, reconstructed, spec.mapping)
        with run_context.measure("visual_mapping"):
            visualization.mapping(run_context.path, status["mapping"], mapped)

        # 6. Objects: proposals match capture frames and keep counts per origin.
        if reason := skip_reason(spec, status, "objects"):
            status["objects"] = StepResult("objects", "skipped", reason)
        else:
            status["objects"], recognised = objects.run(run_context, captured, measured, tracked, spec.objects)
        with run_context.measure("visual_objects"):
            visualization.objects(run_context.path, status["objects"], captured, recognised)

        result = Result(run_context.path, tuple(status[name] for name in STEP_NAMES), spec.controls)
        write_json(run_context.path / "output/result.json", result.to_dict())
        # References are opened only after predictions are saved and hashed.
        predictions = run_context.path / "output/predictions"
        prediction_hashes = artifact_inventory(predictions)
        write_json(run_context.path / "metadata/prediction_hashes.json", {"files": prediction_hashes})
        with run_context.measure("scoring"):
            score_results = validation.score(run_context.path, result.steps, scores)
        if artifact_inventory(predictions) != prediction_hashes:
            raise ValueError("Prediction artifacts changed during scoring")
        write_json(run_context.path / "output/scores.json", score_results)
        if not result.complete:
            run_context.stop_incomplete("Six-step predictions are incomplete; inspect output/result.json")
    return result
