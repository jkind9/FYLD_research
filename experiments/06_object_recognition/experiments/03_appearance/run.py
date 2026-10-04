"""Frozen oracle-support appearance comparison; no new models or downloads."""

import argparse
import importlib
import json
import shutil
import time
from pathlib import Path

import numpy as np
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, verify_run, write_json

from . import cache
from .adapter import describe_classical, prepare_crop
from .compare import compare_descriptors
from .evaluator import label_pairs, rank_queries
from .features import FeatureExtractor
from .report import write_report

ROOT = Path(__file__).resolve().parents[4]
source_api = importlib.import_module(
    "experiments.06_object_recognition.experiments.02_segmentation.run"
)
ORIGINAL_SHA256 = "a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920"
PUBLISHED_SHA256 = "27fe047dac254161ea823d6c55aeb28e16bd88cd993f1e4bf8fbdee40d4741d3"
HYPERPARAMETERS = {
    "source": {
        "value": "Task17 six frames/11 oracle supports; 4 enrollment/7 evaluation observations",
        "source": "inherited Task17 desk_smoke_v1",
    },
    "crop": {
        "value": {
            "grid": [128, 128],
            "bounds": "floor/ceil/clamp",
            "rgb": "bilinear",
            "mask": "nearest",
            "outside": 0,
            "aspect": "reshape",
        },
        "source": "confirmed 2026-10-03",
    },
    "zncc": {
        "value": {
            "minimum_joint_pixels": 16,
            "variance": ">0",
            "gray": "COLOR_RGB2GRAY",
        },
        "source": "confirmed 2026-10-03",
    },
    "orb": {
        "value": {
            "nfeatures": 500,
            "scaleFactor": 1.2,
            "nlevels": 8,
            "edgeThreshold": 31,
            "firstLevel": 0,
            "WTA_K": 2,
            "scoreType": "HARRIS",
            "patchSize": 31,
            "fastThreshold": 20,
            "norm": "Hamming",
        },
        "source": "confirmed 2026-10-03",
    },
    "sift": {
        "value": {
            "nfeatures": 500,
            "nOctaveLayers": 3,
            "contrastThreshold": 0.04,
            "edgeThreshold": 10,
            "sigma": 1.6,
            "descriptorType": "CV_32F",
            "enable_precise_upscale": False,
            "norm": "L2",
        },
        "source": "confirmed 2026-10-03",
    },
    "matching": {
        "value": {
            "knn": 2,
            "ratio": 0.75,
            "mutual": True,
            "crossCheck": False,
            "minimum_matches": 4,
            "minimum_inliers": 4,
            "rank_tolerance": 1e-6,
        },
        "source": "confirmed 2026-10-03",
    },
    "homography": {
        "value": {
            "method": "RANSAC",
            "threshold_px": 3,
            "maxIters": 2000,
            "confidence": 0.995,
            "seed": 0,
            "threads": 1,
        },
        "source": "confirmed 2026-10-03",
    },
    "features": {
        "value": {
            "model": "existing YOLO26x",
            "device": "cuda:0",
            "dtype": "float32",
            "imgsz": 640,
            "batch": 1,
            "augment": False,
            "rect": True,
            "half": False,
            "pool": "adaptive_average",
            "layer": "len(layers)-2",
            "input": "RGB128 to contiguous BGR, predictor letterbox640",
            "requested": 11,
            "extra_warmup": "first-call full-model warmup",
        },
        "source": "inherited Task28 model/settings; confirmed 2026-10-04",
    },
    "ranking": {
        "value": {"tie_absolute": 1e-6, "operating_threshold": None},
        "source": "confirmed 2026-10-03 no validation tuning",
    },
    "runtime": {
        "value": {
            "cv2": "5.0.0",
            "numpy": "2.4.2",
            "ultralytics": "8.4.172",
            "torch": "2.11.0+cu128",
        },
        "source": "inherited installed runtime",
    },
    "repeats": {
        "value": 1,
        "source": "confirmed 2026-10-03 reuse each descriptor for all pairs",
    },
}


def output_root(repo: Path, output: Path) -> Path:
    resolved = source_api.output_root(output)
    for protected in (repo / "data", repo / "checkpoints"):
        if resolved.is_relative_to(protected.resolve()):
            raise ValueError(
                "Output must not be inside protected input or checkpoint trees"
            )
    return resolved


def preflight(repo: Path) -> dict:
    manifest = source_api.preflight(repo)
    if (
        sha256(repo / "experiments/06_object_recognition/datasets/desk_smoke_v1.json")
        != ORIGINAL_SHA256
    ):
        raise ValueError("Original annotation pin differs")
    if (
        sha256(repo / "data/object_revisits/desk_smoke_v1/annotations.json")
        != PUBLISHED_SHA256
    ):
        raise ValueError("Published annotation pin differs")
    return manifest


def _inputs(
    run: Run, repo: Path, manifest: dict, *, synthetic: bool
) -> tuple[list[dict], list[dict]]:
    method: list[dict] = []
    truth: list[dict] = []
    publication = repo / "data/object_revisits/desk_smoke_v1"
    pinned_masks = (
        {
            r["path"]: r["sha256"]
            for r in json.loads((publication / "publication.json").read_text())["files"]
        }
        if not synthetic
        else {}
    )
    for frame in manifest["frames"]:
        target = run.path / "input/rgb" / f"{frame['frame_id']}.png"
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(repo / frame["rgb"]["path"], target)
        if sha256(target) != frame["rgb"]["sha256"]:
            raise ValueError("Copied RGB source differs")
        for label in frame["labels"]:
            key = f"o{len(method):03d}"
            support = (
                publication
                / "masks"
                / frame["frame_id"]
                / f"{label['instance_id']}.png"
            )
            mask_target = run.path / "input/masks" / f"{key}.png"
            mask_target.parent.mkdir(exist_ok=True)
            if synthetic:
                with Image.open(target) as im:
                    mask = np.full((im.height, im.width), 255, np.uint8)
                Image.fromarray(mask).save(mask_target)
            else:
                expected = pinned_masks[support.relative_to(publication).as_posix()]
                shutil.copyfile(support, mask_target)
                if sha256(mask_target) != expected:
                    raise ValueError("Copied support source differs")
            method.append(
                {
                    "key": key,
                    "frame_id": frame["frame_id"],
                    "rgb": f"input/rgb/{frame['frame_id']}.png",
                    "rgb_sha256": frame["rgb"]["sha256"],
                    "mask": f"input/masks/{key}.png",
                    "mask_sha256": sha256(mask_target),
                    "bbox": label["bbox_xyxy"],
                }
            )
            truth.append(
                {
                    "key": key,
                    "frame_id": frame["frame_id"],
                    "category": label["category"],
                    "partition": frame["partition"],
                    "identity": label["instance_id"],
                }
            )
    write_json(run.path / "input/method_inputs.json", method)
    write_json(run.path / "input/evaluator_truth.json", truth)
    return method, truth


def _signature(method: list[dict]) -> dict:
    return {
        "inputs": method,
        "hyperparameters": HYPERPARAMETERS,
        "feature_code": cache.feature_code(),
        "checkpoint_sha256": cache.detector.CHECKPOINT_SHA256,
        "effective_requested_predict_settings": dict(cache.detector.PREDICT_SETTINGS),
        "original_annotations_sha256": ORIGINAL_SHA256,
        "published_annotations_sha256": PUBLISHED_SHA256,
    }


def _extract(
    run: Run, method: list[dict], checkpoint: Path | None
) -> tuple[list[dict], dict]:
    extractor = FeatureExtractor(checkpoint) if checkpoint is not None else None
    rows = []
    for record in method:
        started = time.perf_counter()
        with Image.open(run.path / record["rgb"]) as image:
            rgb = np.asarray(image.convert("RGB"))
        with Image.open(run.path / record["mask"]) as image:
            support = np.asarray(image.convert("L"))
        crop = prepare_crop(rgb, support, record["bbox"])
        preparation_seconds = time.perf_counter() - started
        Image.fromarray(crop.rgb).save(run.path / "debug" / f"{record['key']}.png")
        started = time.perf_counter()
        classical = describe_classical(crop)
        classical_seconds = time.perf_counter() - started
        vector = extractor.extract(crop) if extractor is not None else []
        rows.append(
            {
                "key": record["key"],
                "rgb": crop.rgb.tolist(),
                "mask": crop.mask.tolist(),
                **classical,
                "yolo": vector,
                "bounds": list(crop.bounds),
                "preparation_seconds": preparation_seconds,
                "classical_seconds": classical_seconds,
            }
        )
    return rows, (
        extractor.receipt()
        if extractor is not None
        else {"synthetic_control": True, "requested_embedding_count": 0}
    )


def _evaluate(rows: list[dict], truth: list[dict]) -> dict:
    pairs = []
    for i, left in enumerate(rows):
        for j in range(i + 1, len(rows)):
            if truth[i]["category"] == truth[j]["category"]:
                right = rows[j]
                pairs.append(
                    {
                        "left": left["key"],
                        "right": right["key"],
                        "scores": compare_descriptors(left, right),
                    }
                )
    return {
        "pairs": label_pairs(truth, pairs),
        "queries": rank_queries(truth, pairs),
        "counts": {
            "observations": len(rows),
            "same_category_pairs": len(pairs),
            "same_identity_pairs": sum(
                p["same_identity"] for p in label_pairs(truth, pairs)
            ),
            "different_identity_pairs": sum(
                not p["same_identity"] for p in label_pairs(truth, pairs)
            ),
            "gallery_observations": sum(r["partition"] == "enrollment" for r in truth),
            "query_observations": sum(r["partition"] == "evaluation" for r in truth),
        },
    }


def _publish(
    repo: Path,
    output: Path,
    manifest: dict,
    *,
    synthetic: bool = False,
    cache_path: Path | None = None,
) -> Path:
    output = output_root(repo, output)
    if not synthetic and manifest != preflight(repo):
        raise ValueError("Production requires the frozen verified sources")
    checkpoint = repo / "checkpoints/yolo26x.pt"
    with Run(
        output,
        repo,
        {
            "hyperparameters": HYPERPARAMETERS,
            "synthetic_control": synthetic,
            "condition": "oracle_provisional_support",
        },
    ) as run:
        with run.measure("verified_input_copy", frames=len(manifest["frames"])):
            method, truth = _inputs(run, repo, manifest, synthetic=synthetic)
        signature = _signature(method)
        if cache_path is not None:
            payload = cache.read_verified(cache_path, signature)
            rows = payload["rows"]
            feature_receipt = json.loads(
                (cache_path / "output/feature_receipt.json").read_text()
            )
            for record in method:
                shutil.copyfile(
                    cache_path / "debug" / f"{record['key']}.png",
                    run.path / "debug" / f"{record['key']}.png",
                )
        else:
            with run.measure(
                "descriptors_including_model_load_warmup_transfer", frames=len(method)
            ):
                rows, feature_receipt = _extract(
                    run, method, None if synthetic else checkpoint
                )
        if not synthetic:
            preflight(repo)
            if cache.feature_code() != signature["feature_code"]:
                raise ValueError("Feature-producing source changed during extraction")
        write_json(
            run.path / "output/descriptors.json",
            {"signature": signature, "rows": rows, "synthetic_control": synthetic},
        )
        write_json(run.path / "output/feature_receipt.json", feature_receipt)
        with run.measure("pair_and_gallery_scoring", frames=len(method)):
            result = _evaluate(rows, truth)
        result = {
            **result,
            "hyperparameters": HYPERPARAMETERS,
            "synthetic_control": synthetic,
            "claim": "Previously inspected oracle provisional supports; descriptive within-session comparisons, no operating threshold, probability, blind accuracy or identity guarantee",
            "new_requested_gpu_embeddings": (
                0
                if synthetic or cache_path
                else feature_receipt["requested_embedding_count"]
            ),
            "feature_cache_manifest_sha256": (
                sha256(cache_path / "metadata/manifest.json") if cache_path else None
            ),
            "feature_receipt": feature_receipt,
            "observations": truth,
        }
        write_json(run.path / "output/results.json", result)
        with run.measure("report", frames=len(method)):
            write_report(run.path, result)
        run.set_processed_frames(len(manifest["frames"]))
    verify_run(run.path)
    return run.path


def run_evaluation(
    repo: Path = ROOT, output: Path | None = None, cache_path: Path | None = None
) -> Path:
    destination = output_root(repo, output or Path(__file__).parent / "runs")
    return _publish(repo, destination, preflight(repo), cache_path=cache_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            {"run": str(run_evaluation(output=args.output, cache_path=args.cache))}
        )
    )


if __name__ == "__main__":
    main()
