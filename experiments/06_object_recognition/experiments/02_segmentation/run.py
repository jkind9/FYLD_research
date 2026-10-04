"""Publish bounded original-grid classical masks with descriptive depth support."""

import argparse
import importlib
import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.contracts import Calibration
from experiments.shared.runs import Run, verify_run, write_json

from .masks import METHODS, segment
from .report import write_report
from .support import coordinate_difference, summarise

ROOT = Path(__file__).resolve().parents[4]
prepare = importlib.import_module("experiments.06_object_recognition.datasets.prepare")
cache_api = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.cache"
)
score_api = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.scoring"
)
localisation = importlib.import_module(
    "experiments.06_object_recognition.pilot.localisation"
)
PUBLICATION_SHA256 = "eb30954d32b56778d55ac4a1858dd933ddec7550d2aa4da5bfb9e9ae1b5d57e3"
HYPERPARAMETERS = {
    "runtime": {
        "value": {"cv2": "5.0.0", "numpy": "2.4.2"},
        "source": "inherited installed runtime; confirmed 2026-10-03",
    },
    "methods": {
        "value": list(METHODS),
        "source": "confirmed 2026-10-03 delegated bounded trial",
    },
    "source_selection": {
        "value": [0, 9, 27, 37, 42, 59],
        "source": "inherited Task17 frozen references",
    },
    "grid_calibration": {
        "value": [640, 480, 525, 525, 319.5, 239.5],
        "source": "inherited Task17 publication",
    },
    "depth": {
        "value": {"scale": 5000, "missing": 0, "processed_range_m": [0, 4]},
        "source": "inherited stage03 dataset.py:123",
    },
    "rectangle": {
        "value": "floor/ceil/clamped; minimum 2x2; certain background required",
        "source": "confirmed 2026-10-03",
    },
    "grabcut": {
        "value": {"iterations": 5, "mode": "GC_INIT_WITH_RECT"},
        "source": "confirmed 2026-10-03",
    },
    "rng_threads": {
        "value": [0, 1],
        "source": "confirmed 2026-10-03 serial reproducibility",
    },
    "canny": {
        "value": [
            50,
            150,
            3,
            True,
            "RETR_EXTERNAL",
            "CHAIN_APPROX_SIMPLE",
            "largest area filled",
        ],
        "source": "confirmed 2026-10-03",
    },
    "statistics": {
        "value": "component median; q75-q25 linear quantiles; null when empty",
        "source": "confirmed 2026-10-03",
    },
    "predicted_matching_iou": {
        "value": 0.5,
        "source": "inherited Task18 same-category maximum-cardinality/maxsumIoU",
    },
    "synthetic_boundary_tolerance_px": {
        "value": 1,
        "source": "confirmed 2026-10-03 synthetic evaluator control only",
    },
    "repeat_resize_smoothing": {
        "value": [1, False, False],
        "source": "confirmed 2026-10-03",
    },
    "output": {"value": "uint8 0/255 original grid", "source": "confirmed 2026-10-03"},
    "learned_segmentation": {
        "value": None,
        "source": "n/a no acquired mask weights; owner prohibits new models/downloads",
    },
}


def output_root(output: Path) -> Path:
    """Task18 guard semantics, kept local to avoid importing its timed runner."""
    resolved = output.resolve()
    for ancestor in (resolved, *resolved.parents):
        marker = ancestor / "metadata/status.json"
        if marker.exists() or marker.is_symlink():
            raise ValueError("Output must not be inside an existing run")
    return resolved


def preflight(repo: Path) -> dict:
    if cv2.__version__ != "5.0.0" or np.__version__ != "2.4.2":
        raise ValueError("Pinned OpenCV/NumPy runtime mismatch")
    publication = repo / "data/object_revisits/desk_smoke_v1"
    if sha256(publication / "publication.json") != PUBLICATION_SHA256:
        raise ValueError("Task17 publication receipt differs")
    prepare.verify_publication(publication, repo)
    manifest = cache_api.read_json(publication / "annotations.json")
    archived = cache_api.read_json(
        repo / "experiments/datasets/tum_freiburg1_member_hashes.json"
    )["sequences"]["rgbd_dataset_freiburg1_desk"]["members"]
    sources = manifest["source_records"] + [
        f[role] for f in manifest["frames"] for role in ("rgb", "depth")
    ]
    prefix = "data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk/"
    for source in sources:
        if (
            not source["path"].startswith(prefix)
            or archived[source["path"][len(prefix) :]]["sha256"] != source["sha256"]
        ):
            raise ValueError("Original archive member hash differs")
    return manifest


def prompts(frame: dict, predicted: dict | None) -> tuple[list[dict], dict | None]:
    oracle = [
        {
            "prompt_key": f"o{i:03d}",
            "condition": "oracle_box",
            "xyxy": label["bbox_xyxy"],
        }
        for i, label in enumerate(frame["labels"])
    ]
    if predicted is None:
        return oracle, None
    proposals = predicted["proposals"]
    cups = [
        {
            "prompt_key": f"p{i:03d}",
            "condition": "cached_predicted_cup_box",
            "xyxy": proposal["xyxy"],
        }
        for i, proposal in enumerate(proposals)
        if proposal["label"] == "cup"
    ]
    evaluated = score_api.score_category(
        proposals, frame["labels"], "cup", "complete", 0.5
    )
    return oracle + cups, evaluated


def _frame(
    run: Run, repo: Path, frame: dict, calibration: Calibration, predicted: dict | None
) -> dict:
    key = frame["frame_id"]
    for role in ("rgb", "depth"):
        target = run.path / "input" / role / f"{key}.png"
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(repo / frame[role]["path"], target)
        if sha256(target) != frame[role]["sha256"]:
            raise ValueError("Copied source differs")
    # Derive masks only from the exact hash-verified bytes saved in this run.
    with Image.open(run.path / "input/rgb" / f"{key}.png") as image:
        rgb = np.asarray(image.convert("RGB"))
    with Image.open(run.path / "input/depth" / f"{key}.png") as image:
        raw = np.asarray(image)
    Image.fromarray(np.where((raw > 0) & (raw < 20000), 255, 0).astype(np.uint8)).save(
        run.path / "debug" / f"{key}_valid_depth.png"
    )
    selected, matching = prompts(frame, predicted)
    rows = [_prompt(run, rgb, raw, calibration, key, prompt) for prompt in selected]
    return {
        "frame_id": key,
        "timestamp_s": frame["timestamp_s"],
        "prompts": rows,
        "predicted_box_evaluator": matching,
        "formal_mask_accuracy": None,
    }


def _prompt(
    run: Run,
    rgb: np.ndarray,
    raw: np.ndarray,
    calibration: Calibration,
    key: str,
    prompt: dict,
) -> dict:
    rows = []
    for method in METHODS:
        started = time.perf_counter()
        result = segment(rgb, prompt["xyxy"], method)
        method_seconds = time.perf_counter() - started
        mask = result["mask"]
        summary = summarise(mask, raw, calibration)
        filename = f"{key}_{prompt['prompt_key']}_{method}"
        Image.fromarray(mask).save(run.path / "output" / f"{filename}.png")
        overlay = rgb.copy()
        overlay[mask != 0] = (
            rgb[mask != 0].astype(float) * 0.5 + np.array([0, 255, 120]) * 0.5
        ).astype(np.uint8)
        Image.fromarray(overlay).save(run.path / "debug" / f"{filename}.png")
        rows.append(
            {
                "method": method,
                "status": result["status"],
                "error": result["error"],
                "bounds": list(result["bounds"]),
                "method_seconds": method_seconds,
                "support": summary,
                "mask": f"output/{filename}.png",
                "overlay": f"debug/{filename}.png",
            }
        )
    baseline = rows[0]["support"]
    # Rounded bounds align shared pixel-centre localization with our raster rectangle.
    frame = SimpleNamespace(
        calibration=calibration,
        depth=raw.astype(float) / 5000,
        valid=(raw > 0) & (raw < 20000),
    )
    if rows[0]["status"] == "ok":
        detection = localisation.Detection(tuple(rows[0]["bounds"]), "support", 0, 1.0)
        located = localisation.localise_detection(frame, detection, None)
        median = located["box_median"]["camera_m"] if located["box_median"] else None
        if median != baseline["camera_median_m"]:
            raise ValueError("Rectangle localization comparator differs")
    return {
        **prompt,
        "methods": [
            {
                **r,
                "delta_from_rectangle_camera_m": coordinate_difference(
                    r["support"], baseline
                ),
            }
            for r in rows
        ],
    }


def _publish(
    repo: Path,
    output: Path,
    manifest: dict,
    cached: dict | None,
    *,
    synthetic: bool = False,
    cache_source: Path | None = None,
) -> Path:
    """Trusted prevalidated inputs; synthetic fixtures must explicitly opt in.

    Public production callers use run_evaluation, which pins sources and cache.
    """
    output = output_root(output)
    if not synthetic:
        verified = preflight(repo)
        if manifest != verified:
            raise ValueError("Production publication requires frozen Task17 inputs")
        source = cache_source or repo / cache_api.ACCEPTED_RELATIVE
        captures = [
            {
                k: f[k]
                for k in ("frame_id", "timestamp_s", "source_selection_index", "rgb")
            }
            for f in verified["frames"]
        ]
        expected = (
            cache_api.load_accepted_cache(source, captures) if source.is_dir() else None
        )
        if cached != expected:
            raise ValueError("Production publication requires verified accepted cache")
    configuration = {
        "phase": "classical_mask_depth_controls",
        "synthetic_control": synthetic,
        "hyperparameters": HYPERPARAMETERS,
        "learned_available": False,
        "formal_mask_accuracy": None,
    }
    with Run(output, repo, configuration) as run:
        calibration = Calibration(**manifest["calibration"])
        write_json(run.path / "input/evaluator_annotations.json", manifest)
        method_inputs = [
            {
                "frame_id": f["frame_id"],
                "rgb": f["rgb"],
                "depth": f["depth"],
                "timestamp_s": f["timestamp_s"],
            }
            for f in manifest["frames"]
        ]
        write_json(
            run.path / "input/method_inputs.json",
            {
                "frames": method_inputs,
                "calibration": manifest["calibration"],
                "oracle_prompt_exception": "bbox only; named oracle_box condition",
            },
        )
        with run.measure("masks_depth_artifacts", frames=len(method_inputs)):
            rows = [
                _frame(
                    run,
                    repo,
                    frame,
                    calibration,
                    cached["frames"][i] if cached else None,
                )
                for i, frame in enumerate(manifest["frames"])
            ]
        receipt = {
            "frames": rows,
            "hyperparameters": HYPERPARAMETERS,
            "synthetic_control": synthetic,
            "formal_mask_accuracy": None,
            "source_publication_sha256": PUBLICATION_SHA256 if not synthetic else None,
            "cached_detector_manifest_sha256": (
                cached["manifest_sha256"] if cached else None
            ),
            "predicted_prompt_condition": {
                "status": "available" if cached else "unavailable",
                "reason": (
                    "verified cached boxes"
                    if cached
                    else "optional default accepted cache absent; oracle-box condition only"
                ),
            },
            "learned_branches": {
                "status": "unavailable",
                "reason": "No acquired segmentation weights; existing YOLO26x checkpoint is detection-only; no new models/downloads",
            },
            "claim": "camera coordinate differences and depth support; not mask accuracy or location error",
            "new_inference_count": 0,
        }
        write_json(run.path / "output/results.json", receipt)
        with run.measure("report", frames=len(rows)):
            write_report(run.path, receipt)
        run.set_processed_frames(len(rows))
    verify_run(run.path)
    return run.path


def run_evaluation(
    repo: Path = ROOT, output: Path | None = None, cache: Path | None = None
) -> Path:
    destination = output_root(output or Path(__file__).parent / "runs")
    manifest = preflight(repo)
    cache_path = cache or repo / cache_api.ACCEPTED_RELATIVE
    if cache is not None and not cache_path.is_dir():
        raise ValueError(
            "Explicit cache path unavailable; provide the verified offline cache"
        )
    captures = [
        {k: f[k] for k in ("frame_id", "timestamp_s", "source_selection_index", "rgb")}
        for f in manifest["frames"]
    ]
    cached = (
        cache_api.load_accepted_cache(cache_path, captures)
        if cache_path.is_dir()
        else None
    )
    return _publish(repo, destination, manifest, cached, cache_source=cache_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    print(
        json.dumps({"run": str(run_evaluation(output=args.output, cache=args.cache))})
    )


if __name__ == "__main__":
    main()
