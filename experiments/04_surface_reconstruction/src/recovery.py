"""Reject reuse when any fault-scoring dependency differs from saved provenance."""

import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

from .dataset import copy_checked
from .run import HYPERPARAMETERS

SAME_SOURCE = (
    "experiments/04_surface_reconstruction/src/validation/controls.py",
    "experiments/04_surface_reconstruction/src/backend.py",
    "experiments/04_surface_reconstruction/src/run.py",
    "experiments/geometry_validation/src/control.py",
    "experiments/shared/geometry.py",
    "experiments/shared/contracts.py",
)
EVALUATION = "experiments/04_surface_reconstruction/src/evaluation.py"


def _query_signature(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    signature = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "QUERY_BATCH" for t in node.targets
        ):
            signature.append(ast.dump(node))
        if isinstance(node, ast.FunctionDef) and node.name in {
            "nearest",
            "validate_points",
            "distance_summary",
        }:
            signature.append(ast.dump(node))
        if isinstance(node, ast.ClassDef):
            selected = (
                {"__init__", "add", "summary"}
                if node.name == "DistanceTotals"
                else {"__init__", "distances"}
            )
            if node.name in {"DistanceTotals", "SurfaceScorer"}:
                signature.extend(
                    node.name + ast.dump(method)
                    for method in node.body
                    if isinstance(method, ast.FunctionDef) and method.name in selected
                )
    return signature


def validate_prior(
    prior: Path,
    dataset: Path,
    ids: list[int],
    threshold: float,
    repo: Path,
    evidence: Path,
) -> dict:
    config = json.loads((prior / "metadata/configuration.json").read_text())
    status = json.loads((prior / "metadata/status.json").read_text())
    verified = status.get("status") == "complete"
    artifact_hashes = None
    if verified:
        verify_run(prior)
        manifest_payload = (prior / "metadata/manifest.json").read_bytes()
        if hashlib.sha256(manifest_payload).hexdigest() != status["manifest_sha256"]:
            raise ValueError("Prior manifest integrity changed during verification")
        artifact_hashes = {
            name: record["sha256"]
            for name, record in json.loads(manifest_payload)["files"].items()
        }
    if (
        config["frame_ids"] != ids
        or config["hyperparameters"]["threshold_m"]["value"] != threshold
    ):
        raise ValueError("Recovery selection or threshold differs")
    if any(
        config["hyperparameters"].get(key) != value
        for key, value in HYPERPARAMETERS.items()
    ):
        raise ValueError("Recovery fixed settings differ")
    inputs = ("conventions.json", "trajectory2/livingRoom2.gt.freiburg")
    for name in inputs:
        if sha256(prior / "input/dataset" / name) != sha256(dataset / name):
            raise ValueError("Recovery decoder metadata differs")
    if sha256(prior / "input/evaluation/living-room.ply") != sha256(
        dataset / "reference_surface/living-room.ply"
    ):
        raise ValueError("Recovery reference differs")
    source = prior / "metadata/source"
    for name in SAME_SOURCE:
        if not (source / name).is_file():
            raise ValueError(f"Recovery source dependency missing: {name}")
        if sha256(source / name) != sha256(repo / name):
            raise ValueError(f"Recovery source differs: {name}")
    if _query_signature(source / EVALUATION) != _query_signature(repo / EVALUATION):
        raise ValueError("Recovery query implementation differs")
    environment = json.loads((prior / "metadata/environment.json").read_text())
    packages = {p["name"].lower(): p["version"] for p in environment["packages"]}
    for name in ("numpy", "scipy"):
        if packages.get(name) != importlib.metadata.version(name):
            raise ValueError("Recovery numerical dependency differs")
    for name in (
        "configuration.json",
        "status.json",
        "environment.json",
        "source_snapshot.json",
    ):
        copy_checked(prior / "metadata" / name, evidence / name)
    for name in (*SAME_SOURCE, EVALUATION):
        copy_checked(source / name, evidence / "source" / name)
    return {
        "source_run": str(prior.resolve()),
        "eligibility": "matching inputs, reference, settings, versions and relevant code",
        "original_status": status,
        "prior_artifacts_verified": verified,
        "verified_artifact_hashes": artifact_hashes,
        "source_manifest_available": (prior / "metadata/manifest.json").exists(),
        "reference_sha256": sha256(prior / "input/evaluation/living-room.ply"),
    }


def recover_frame(
    prior: Path,
    key: str,
    dataset: Path,
    model: np.ndarray,
    accuracy: dict | None,
    evidence: Path,
    verified_hashes: dict[str, str] | None = None,
) -> dict | None:
    record = prior / f"output/{key}/stages.json"
    if not record.exists():
        return None
    for kind in ("rgb", "depth"):
        if sha256(prior / f"input/{key}/{kind}.png") != sha256(
            dataset / f"trajectory2/{kind}/{key}.png"
        ):
            raise ValueError("Recovered input differs")
    if not np.array_equal(
        np.load(prior / f"output/{key}/model.npy", allow_pickle=False), model
    ):
        raise ValueError("Recovered geometry differs")
    payload = record.read_bytes()
    if verified_hashes is not None and hashlib.sha256(
        payload
    ).hexdigest() != verified_hashes.get(f"output/{key}/stages.json"):
        raise ValueError("Recovered stage integrity differs from verified manifest")
    saved = json.loads(payload)
    if (
        saved["frame_id"] != key
        or saved["points"] != len(model)
        or saved["accuracy"] != accuracy
    ):
        raise ValueError("Recovered clean score differs")
    controls = saved["negative_controls"]
    if controls is not None and not isinstance(controls, dict):
        raise ValueError("Invalid recovered fault summary record")
    for name in ("double_depth", "inverse_pose"):
        if controls is None:
            break
        summary = controls.get(name)
        if not len(model):
            if summary is not None:
                raise ValueError("Invalid recovered empty fault summary")
            continue
        if not isinstance(summary, dict) or summary.get("points") != len(model):
            raise ValueError("Recovered fault summary point count differs")
        values = [summary.get(k) for k in ("mean_m", "rmse_m", "max_m")]
        if any(not isinstance(v, (int, float)) for v in values):
            raise ValueError("Invalid recovered fault summary values")
        numeric = np.array(
            [summary[k] for k in ("mean_m", "rmse_m", "max_m")], dtype=float
        )
        mean, rmse, maximum = numeric
        if (
            not np.isfinite(numeric).all()
            or mean < 0
            or rmse < mean - 1e-12
            or maximum < rmse - 1e-12
        ):
            raise ValueError("Invalid recovered fault summary distances")
    target = evidence / f"{key}/stages.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return saved


def combine_summaries(records: list[dict]) -> dict:
    count = sum(r["points"] for r in records)
    if not count:
        raise ValueError("No measured controls available for recovery")
    for record in records:
        if (
            record["points"] < 1
            or not np.isfinite([record[k] for k in ("mean_m", "rmse_m", "max_m")]).all()
        ):
            raise ValueError("Invalid recovered score summary")
    return {
        "points": count,
        "mean_m": sum(r["points"] * r["mean_m"] for r in records) / count,
        "rmse_m": float(
            np.sqrt(sum(r["points"] * r["rmse_m"] ** 2 for r in records) / count)
        ),
        "max_m": max(r["max_m"] for r in records),
    }
