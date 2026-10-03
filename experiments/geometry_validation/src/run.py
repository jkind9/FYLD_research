"""Export every control stage for explicit ICL IDs; CPU only."""

import argparse
import shutil
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np

from experiments.datasets.acquisition import sha256
from experiments.shared.exporting import export_frame
from experiments.shared.runs import Run, verify_run, write_json

from .control import GeometryBackend, compute
from .icl import load_frame, select_ids
from .review import build_review

# Frame selection is a required CLI argument, not a default scientific choice.
HYPERPARAMETERS = {
    "depth_units_per_metre": {
        "value": 5000,
        "source": "inherited data/icl_nuim/conventions.json:15",
    },
    "depth_validity": {
        "value": "positive finite; all pixels; no clipping",
        "source": "n/a projection domain",
    },
    "backend": {
        "value": "numpy_cpu_control",
        "source": "n/a analytic control; GPU permission required",
    },
}


def _copy_inputs(root: Path, destination: Path, frame_id: int) -> None:
    destination.mkdir(parents=True)
    for kind in ("rgb", "depth"):
        source = root / f"trajectory2/{kind}/{frame_id}.png"
        target = destination / f"{kind}.png"
        shutil.copyfile(source, target)
        if sha256(source) != sha256(target):
            raise ValueError("Input changed while copying")


def _frame(run: Run, dataset: Path, frame_id: int, backend: GeometryBackend) -> dict:
    key = str(frame_id)
    started = perf_counter()
    _copy_inputs(dataset, run.path / "input" / key, frame_id)
    # Decode COPIED bytes and metadata: downstream work uses the run's input snapshot.
    snapshot = run.path / "input/dataset"
    staged = snapshot / "trajectory2"
    for kind in ("rgb", "depth"):
        (staged / kind).mkdir(exist_ok=True)
        shutil.copyfile(
            run.path / f"input/{key}/{kind}.png", staged / f"{kind}/{key}.png"
        )
    frame = load_frame(snapshot, frame_id)
    loaded = perf_counter()
    write_json(run.path / f"input/{key}/observation.json", frame.observation.to_dict())
    result = backend(frame)
    computed = perf_counter()
    output, debug = run.path / "output" / key, run.path / "debug" / key
    artifacts = export_frame(
        output,
        debug,
        result.depth,
        result.mask,
        result.pixels,
        result.camera,
        result.world,
        result.model,
        frame.rgb,
        result.projection_error,
    )
    exported = perf_counter()
    metadata = {
        "frame_id": key,
        "input": f"input/{key}",
        "output": f"output/{key}",
        "debug": f"debug/{key}",
        "pose_source": "supplied_control",
        "valid_pixels": int(result.mask.sum()),
        "max_projection_error_pixels": (
            float(np.abs(result.projection_error).max()) if result.pixels.size else None
        ),
        "calibration": asdict(frame.observation.calibration),
        "model_from_world": (
            frame.model_from_first @ np.linalg.inv(frame.world_from_first)
        ).tolist(),
        "coordinate_frames": {
            "camera": frame.observation.calibration.axes,
            "world": frame.observation.pose.world_id,
            "model": "publisher_reference_surface",
        },
        "timings_seconds": {
            "copy_decode": loaded - started,
            "geometry": computed - loaded,
            "export": exported - computed,
        },
        "stage_sequence": [
            "raw_colour_depth",
            "metric_axial_depth_and_mask",
            "camera_points",
            "world_points",
            "reference_basis_points",
            "projection_roundtrip",
        ],
        "artifacts": artifacts,
    }
    write_json(output / "stages.json", metadata)
    return metadata


def execute(
    dataset: Path,
    ids: list[int],
    runs: Path,
    repo: Path,
    *,
    backend: GeometryBackend = compute,
) -> Path:
    ids = select_ids(ids)
    if backend is not compute:
        raise ValueError("This entry point permits only the CPU geometry control")
    configuration = {
        "experiment": "geometry_validation",
        "frame_ids": ids,
        "dataset_source": str(dataset.resolve()),
        "hyperparameters": HYPERPARAMETERS,
        "pose_role": "supplied control; never tracker inference",
        "surface_scoring_ready": False,
        "reference_surface_used": False,
    }
    with Run(runs, repo, configuration) as run:
        snapshot = run.path / "input/dataset"
        (snapshot / "trajectory2").mkdir(parents=True)
        shutil.copyfile(dataset / "conventions.json", snapshot / "conventions.json")
        shutil.copyfile(
            dataset / "trajectory2/livingRoom2.gt.freiburg",
            snapshot / "trajectory2/livingRoom2.gt.freiburg",
        )
        frames = [_frame(run, dataset, frame_id, backend) for frame_id in ids]
        write_json(run.path / "metadata/frames.json", frames)
        build_review(run.path, frames)
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--frame-ids", type=int, nargs="+", required=True)
    parser.add_argument(
        "--runs", type=Path, default=Path(__file__).resolve().parents[1] / "runs"
    )
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    print(execute(args.dataset, args.frame_ids, args.runs, repo))


if __name__ == "__main__":
    main()
