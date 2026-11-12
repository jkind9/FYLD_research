"""Small clean repository publication, recovery and offline browser controls."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

runner = importlib.import_module(
    "experiments.06_object_recognition.experiments.02_segmentation.run"
)


@pytest.fixture
def inputs(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    for args in [
        ("init",),
        (
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "fixture",
        ),
    ]:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    rgb = np.full((32, 32, 3), 10, np.uint8)
    rgb[8:24, 8:24] = [220, 100, 40]
    Image.fromarray(rgb).save(repo / "rgb.png")
    Image.fromarray(np.full((32, 32), 5000, np.uint16)).save(repo / "depth.png")
    frame = {
        "frame_id": "1",
        "timestamp_s": 1.0,
        "rgb": {"path": "rgb.png", "sha256": sha256(repo / "rgb.png")},
        "depth": {"path": "depth.png", "sha256": sha256(repo / "depth.png")},
        "labels": [
            {
                "instance_id": "reference",
                "category": "cup",
                "bbox_xyxy": [5.1, 5.1, 26.1, 26.1],
            }
        ],
    }
    manifest = {
        "calibration": {
            "width": 32,
            "height": 32,
            "fx": 20,
            "fy": 20,
            "cx": 15.5,
            "cy": 15.5,
            "axes": "x-right_y-down_z-forward",
        },
        "frames": [frame],
    }
    predicted = {
        "frames": [
            {
                "proposals": [
                    {
                        "xyxy": [5.0, 5.0, 27.0, 27.0],
                        "label": "cup",
                        "class_id": 41,
                        "confidence": 0.8,
                    }
                ]
            }
        ],
        "manifest_sha256": "synthetic_no_gpu",
    }
    return repo, manifest, predicted


def test_publication_reference_separation_masks_comparator_and_tamper(inputs, tmp_path):
    repo, manifest, predicted = inputs
    path = runner._publish(
        repo, tmp_path / "outputs", manifest, predicted, synthetic=True
    )
    assert verify_run(path)["status"] == "complete"
    result = json.loads((path / "output/results.json").read_text())
    assert (
        result["synthetic_control"] is True
        and result["source_publication_sha256"] is None
    )
    assert result["formal_mask_accuracy"] is None
    assert len(result["frames"][0]["prompts"]) == 2
    assert result["frames"][0]["predicted_box_evaluator"]["matched"] == 1
    assert len(list((path / "output").glob("*.png"))) == 6
    method_inputs = json.loads((path / "input/method_inputs.json").read_text())
    assert all(
        "labels" not in frame and "instance_id" not in frame
        for frame in method_inputs["frames"]
    )
    for prompt in result["frames"][0]["prompts"]:
        assert "instance_id" not in prompt
        assert prompt["methods"][0]["delta_from_rectangle_camera_m"] == [0, 0, 0]
    (path / "output/results.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        verify_run(path)


@pytest.mark.parametrize("suffix", ["", "runs", "debug/nested/runs"])
def test_nested_output_cannot_modify_completed_inventory(inputs, tmp_path, suffix):
    repo, manifest, predicted = inputs
    path = runner._publish(
        repo, tmp_path / "outputs", manifest, predicted, synthetic=True
    )
    pinned = sha256(path / "metadata/manifest.json")
    with pytest.raises(ValueError, match="existing run"):
        runner._publish(repo, path / suffix, manifest, predicted, synthetic=True)
    assert sha256(path / "metadata/manifest.json") == pinned
    assert verify_run(path)["status"] == "complete"


def test_failed_copy_never_complete(inputs, tmp_path):
    repo, manifest, _ = inputs
    manifest["frames"][0]["rgb"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Copied source"):
        runner._publish(repo, tmp_path / "failed", manifest, None, synthetic=True)
    path = next((tmp_path / "failed").iterdir())
    assert json.loads((path / "metadata/status.json").read_text())["status"] == "failed"
    with pytest.raises(ValueError, match="complete"):
        verify_run(path)


def test_only_hash_verified_saved_inputs_are_decoded(inputs, tmp_path, monkeypatch):
    repo, manifest, _ = inputs
    original_open = runner.Image.open
    original_sources = {(repo / "rgb.png").resolve(), (repo / "depth.png").resolve()}
    decoded_originals = []

    def replaced_source_open(path, *args, **kwargs):
        if Path(path).resolve() in original_sources:
            decoded_originals.append(Path(path))
            # Simulate different decoded pixels while copy/hash sees correct bytes.
            return Image.new("RGB", (32, 32), "black")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(runner.Image, "open", replaced_source_open)
    path = runner._publish(repo, tmp_path / "outputs", manifest, None, synthetic=True)
    assert decoded_originals == []
    rows = json.loads((path / "output/results.json").read_text())["frames"][0][
        "prompts"
    ][0]["methods"]
    assert rows[2]["status"] == "ok"
    assert sha256(path / "input/rgb/1.png") == manifest["frames"][0]["rgb"]["sha256"]


def test_resolved_output_alias_rejects_before_mutation(inputs, tmp_path):
    repo, manifest, predicted = inputs
    path = runner._publish(
        repo, tmp_path / "outputs", manifest, predicted, synthetic=True
    )
    alias = tmp_path / "run_alias"
    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(path)],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
    else:
        alias.symlink_to(path, target_is_directory=True)
    assert alias.resolve() == path.resolve()
    with pytest.raises(ValueError, match="existing run"):
        runner.run_evaluation(repo=repo, output=alias / "runs")
    assert not (path / "runs").exists()
    assert verify_run(path)["status"] == "complete"


def test_preflight_runtime_and_publication_pins(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.cv2, "__version__", "invalid")
    with pytest.raises(ValueError, match="runtime"):
        runner.preflight(tmp_path)
    monkeypatch.setattr(runner.cv2, "__version__", "5.0.0")
    receipt = tmp_path / "data/object_revisits/desk_smoke_v1/publication.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}")
    with pytest.raises(ValueError, match="receipt"):
        runner.preflight(tmp_path)


def test_explicit_unavailable_cache_fails_without_publication(
    inputs, tmp_path, monkeypatch
):
    _, manifest, _ = inputs
    monkeypatch.setattr(runner, "preflight", lambda repo: manifest)
    output = tmp_path / "unused_output"
    with pytest.raises(ValueError, match="Explicit cache"):
        runner.run_evaluation(
            repo=tmp_path, output=output, cache=tmp_path / "missing_cache"
        )
    assert not output.exists()


def test_generic_fixture_cannot_stamp_real_task17_provenance(inputs, tmp_path):
    repo, manifest, predicted = inputs
    receipt = repo / "data/object_revisits/desk_smoke_v1/publication.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}")
    with pytest.raises(ValueError, match="receipt"):
        runner._publish(repo, tmp_path / "unused", manifest, predicted)
    assert not (tmp_path / "unused").exists()


def test_production_helper_rejects_changed_inputs_or_cache(
    inputs, tmp_path, monkeypatch
):
    repo, manifest, predicted = inputs
    monkeypatch.setattr(runner, "preflight", lambda repo: {"frames": []})
    with pytest.raises(ValueError, match="frozen Task17"):
        runner._publish(repo, tmp_path / "unused", manifest, predicted)
    monkeypatch.setattr(runner, "preflight", lambda repo: manifest)
    manifest["frames"][0]["source_selection_index"] = 0
    with pytest.raises(ValueError, match="verified accepted cache"):
        runner._publish(repo, tmp_path / "unused", manifest, predicted)
    assert not (tmp_path / "unused").exists()


def test_unusable_no_depth_and_no_predicted_condition(inputs, tmp_path):
    repo, manifest, _ = inputs
    manifest["frames"][0]["labels"][0]["bbox_xyxy"] = [0, 0, 32, 32]
    Image.fromarray(np.zeros((32, 32), np.uint16)).save(repo / "depth.png")
    manifest["frames"][0]["depth"]["sha256"] = sha256(repo / "depth.png")
    path = runner._publish(repo, tmp_path / "outputs", manifest, None, synthetic=True)
    prompt = json.loads((path / "output/results.json").read_text())["frames"][0][
        "prompts"
    ][0]
    assert all(
        row["status"] == "unusable_prompt"
        and row["delta_from_rectangle_camera_m"] is None
        for row in prompt["methods"]
    )


def test_offline_browser(inputs, tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("Local Edge unavailable")
    repo, manifest, predicted = inputs
    path = runner._publish(
        repo, tmp_path / "outputs", manifest, predicted, synthetic=True
    )
    with sync.sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(edge), headless=True)
        page = browser.new_page()
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                external.append(request.url)
                if request.url.startswith(("http:", "https:"))
                else None
            ),
        )
        page.goto((path / "review.html").as_uri())
        assert page.locator("section").count() == 1
        assert page.locator("img").count() == 8
        page.locator("details summary").first.click()
        assert page.locator("img").evaluate_all(
            "imgs => imgs.every(i => i.complete && i.naturalWidth === 32)"
        )
        assert errors == [] and external == []
        browser.close()
