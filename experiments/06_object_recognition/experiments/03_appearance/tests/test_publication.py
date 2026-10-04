"""Small clean repositories exercise source separation, failure and publication."""

import importlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

runner = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.run"
)
cache = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.cache"
)


@pytest.fixture
def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "fixture",
        ],
        check=True,
        capture_output=True,
    )
    Image.fromarray(
        np.random.default_rng(0).integers(0, 256, (64, 64, 3), dtype=np.uint8)
    ).save(repo / "rgb.png")
    labels = [
        {
            "instance_id": "hidden_identity_a",
            "category": "tv",
            "bbox_xyxy": [0, 0, 64, 64],
        },
        {
            "instance_id": "hidden_identity_b",
            "category": "tv",
            "bbox_xyxy": [0, 0, 64, 64],
        },
    ]
    manifest = {
        "frames": [
            {
                "frame_id": str(i),
                "partition": "enrollment" if i == 0 else "evaluation",
                "rgb": {"path": "rgb.png", "sha256": sha256(repo / "rgb.png")},
                "labels": labels,
            }
            for i in range(2)
        ]
    }
    return repo, manifest


def test_publish_all_pairs_ties_identity_separation_and_tamper(fixture_repo, tmp_path):
    repo, manifest = fixture_repo
    path = runner._publish(repo, tmp_path / "outputs", manifest, synthetic=True)
    assert verify_run(path)["status"] == "complete"
    result = json.loads((path / "output/results.json").read_text())
    assert result["counts"] == {
        "observations": 4,
        "same_category_pairs": 6,
        "same_identity_pairs": 2,
        "different_identity_pairs": 4,
        "gallery_observations": 2,
        "query_observations": 2,
    }
    method = (path / "input/method_inputs.json").read_text()
    descriptors = (path / "output/descriptors.json").read_text()
    assert "hidden_identity" not in method and "hidden_identity" not in descriptors
    assert result["new_requested_gpu_embeddings"] == 0
    assert len(result["queries"]) == 8
    assert all(
        r["status"] == "ambiguous" for r in result["queries"] if r["method"] != "yolo"
    )
    assert all(
        r["status"] == "unavailable" for r in result["queries"] if r["method"] == "yolo"
    )
    assert len(list((path / "debug").glob("*.png"))) == 4
    (path / "output/results.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        verify_run(path)


@pytest.mark.parametrize("suffix", ["", "runs", "debug/deeper"])
def test_nested_output_rejected_before_effects(fixture_repo, tmp_path, suffix):
    repo, manifest = fixture_repo
    path = runner._publish(repo, tmp_path / "outputs", manifest, synthetic=True)
    pinned = sha256(path / "metadata/manifest.json")
    with pytest.raises(ValueError, match="existing run"):
        runner._publish(repo, path / suffix, manifest, synthetic=True)
    assert sha256(path / "metadata/manifest.json") == pinned
    assert verify_run(path)["status"] == "complete"


@pytest.mark.parametrize(
    "relative",
    [
        "data",
        "data/object_revisits/desk_smoke_v1",
        "data/object_revisits/desk_smoke_v1/deeper",
        "checkpoints",
        "checkpoints/deeper",
    ],
)
def test_protected_source_destination_rejected_before_publication(
    fixture_repo, relative, monkeypatch
):
    repo, manifest = fixture_repo
    destination = repo / relative
    calls = []
    monkeypatch.setattr(runner, "_extract", lambda *args: calls.append(args))
    with pytest.raises(ValueError, match="protected input"):
        runner._publish(repo, destination, manifest, synthetic=True)
    assert not destination.exists() and calls == []


def test_resolved_alias_cannot_enter_protected_source(fixture_repo, monkeypatch):
    repo, manifest = fixture_repo
    alias = repo / "alias"
    target = repo / "data/object_revisits/desk_smoke_v1"
    original = Path.resolve

    def resolve(path, *args, **kwargs):
        return target if path == alias else original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="protected input"):
        runner._publish(repo, alias, manifest, synthetic=True)
    assert not alias.exists() and not target.exists()


def test_failed_copy_not_complete(fixture_repo, tmp_path):
    repo, manifest = fixture_repo
    manifest["frames"][0]["rgb"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Copied RGB"):
        runner._publish(repo, tmp_path / "bad", manifest, synthetic=True)
    path = next((tmp_path / "bad").iterdir())
    assert json.loads((path / "metadata/status.json").read_text())["status"] == "failed"
    with pytest.raises(ValueError, match="complete"):
        verify_run(path)


def test_decode_only_saved_sources(fixture_repo, tmp_path, monkeypatch):
    repo, manifest = fixture_repo
    original = runner.Image.open
    seen = []

    def checked(path, *args, **kwargs):
        seen.append(Path(path))
        assert Path(path).resolve() != (repo / "rgb.png").resolve()
        return original(path, *args, **kwargs)

    monkeypatch.setattr(runner.Image, "open", checked)
    runner._publish(repo, tmp_path / "outputs", manifest, synthetic=True)
    assert seen and all("input" in p.parts for p in seen)


def test_synthetic_payload_never_production(fixture_repo, tmp_path, monkeypatch):
    repo, manifest = fixture_repo
    monkeypatch.setattr(runner, "preflight", lambda repo: {"frames": []})
    with pytest.raises(ValueError, match="frozen"):
        runner._publish(repo, tmp_path / "outputs", manifest)
    assert not (tmp_path / "outputs").exists()


def test_cache_unpinned_and_changed_signature(fixture_repo, tmp_path, monkeypatch):
    repo, manifest = fixture_repo
    path = runner._publish(repo, tmp_path / "outputs", manifest, synthetic=True)
    monkeypatch.setattr(cache, "ACCEPTED_MANIFEST_SHA256", None)
    with pytest.raises(ValueError, match="pinned"):
        cache.read_verified(path, {})
    monkeypatch.setattr(cache, "ACCEPTED_MANIFEST_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="completion"):
        cache.read_verified(path, {})
    monkeypatch.setattr(
        cache, "ACCEPTED_MANIFEST_SHA256", sha256(path / "metadata/manifest.json")
    )
    with pytest.raises(ValueError, match="provenance"):
        cache.read_verified(path, {})
    payload = json.loads((path / "output/descriptors.json").read_text())
    with pytest.raises(ValueError, match="provenance"):
        cache.read_verified(path, payload["signature"])


def test_signature_changes_for_configuration_or_feature_source(monkeypatch):
    first = runner._signature([])
    monkeypatch.setattr(cache, "feature_code", lambda: {"features.py": "changed"})
    assert runner._signature([]) != first
    assert cache.fingerprint({"b": 2, "a": 1}) == cache.fingerprint({"a": 1, "b": 2})


def test_transitive_detector_and_predict_settings_are_pinned(monkeypatch):
    source = cache.feature_code()
    assert source["pilot/detector.py"] == sha256(Path(cache.detector.__file__))
    first = runner._signature([])
    monkeypatch.setattr(
        cache.detector,
        "PREDICT_SETTINGS",
        {**cache.detector.PREDICT_SETTINGS, "imgsz": 320},
    )
    assert runner._signature([]) != first
    assert runner._signature([])["effective_requested_predict_settings"]["imgsz"] == 320


def test_main_passes_output_cache(monkeypatch, tmp_path, capsys):
    import sys

    monkeypatch.setattr(
        sys,
        "argv",
        ["run", "--output", str(tmp_path), "--cache", str(tmp_path / "cache")],
    )
    seen = {}

    def run(**kwargs):
        seen.update(kwargs)
        return tmp_path / "result"

    monkeypatch.setattr(runner, "run_evaluation", run)
    runner.main()
    assert seen == {"output": tmp_path, "cache_path": tmp_path / "cache"}
    assert json.loads(capsys.readouterr().out)["run"].endswith("result")
