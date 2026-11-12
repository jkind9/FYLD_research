"""Explicit synthetic publication and offline-browser controls, not GPU claims."""

import importlib
import json
import subprocess
import sys
import tracemalloc
from pathlib import Path

import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run

runner = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.run"
)
ANNOTATIONS = Path(__file__).parents[3] / "datasets/desk_smoke_v1.json"


@pytest.fixture
def published_control(tmp_path):
    repo = tmp_path / "clean_synthetic_repo"
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
            "synthetic fixture",
        ),
    ]:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    annotations = json.loads(ANNOTATIONS.read_text())
    for frame in annotations["frames"]:
        image = repo / frame["rgb"]["path"]
        image.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (640, 480), "#152536").save(image)
        frame["rgb"]["sha256"] = sha256(image)
    cached = {
        "frames": [{"proposals": []} for _ in annotations["frames"]],
        "manifest_sha256": "synthetic_control_no_GPU_evidence",
        "predecessor_timing": {"synthetic_control": True},
    }
    path = runner._publish(
        repo,
        tmp_path / "synthetic_outputs",
        annotations,
        cached,
        method_name="synthetic_control_empty_cache",
    )
    return path, annotations, cached, repo


def test_publication_all_frames_reference_separation_and_immutable_inventory(
    published_control,
):
    path, annotations, _, _ = published_control
    assert verify_run(path)["status"] == "complete"
    assert len(list((path / "input/rgb").glob("*.png"))) == 6
    assert len(list((path / "debug").glob("*.png"))) == 6
    inputs = json.loads((path / "input/method_inputs.json").read_text())
    assert all(
        set(frame) == {"frame_id", "timestamp_s", "source_selection_index", "rgb"}
        for frame in inputs["frames"]
    )
    scores = json.loads((path / "output/scores.json").read_text())[
        "empty_prediction_software_control"
    ]
    assert scores["frame_count"] == 6
    for result in scores["thresholds"]:
        assert result["summary"]["cup"]["missed"] == 5
        assert result["summary"]["cup"]["precision"] is None
        assert result["summary"]["cup"]["recall"] == 0
        assert result["summary"]["tv"]["missed"] == 6
        assert result["summary"]["tv"]["recall"] is None
        assert len(result["frames"]) == len(annotations["frames"])
    receipt = json.loads((path / "output/receipt.json").read_text())
    assert receipt["method"].startswith("synthetic_control")
    (path / "debug/23.png").write_bytes(b"tamper")
    with pytest.raises(ValueError, match="inventory"):
        verify_run(path)


def test_failed_copy_leaves_failed_fresh_run(published_control, tmp_path):
    _, annotations, cached, repo = published_control
    annotations["frames"][0]["rgb"]["sha256"] = "0" * 64
    output = tmp_path / "failed_runs"
    with pytest.raises(ValueError, match="Copied RGB"):
        runner._publish(
            repo, output, annotations, cached, method_name="synthetic_control_bad_copy"
        )
    path = next(output.iterdir())
    assert json.loads((path / "metadata/status.json").read_text())["status"] == "failed"
    with pytest.raises(ValueError, match="complete"):
        verify_run(path)


def test_production_rejects_changed_annotations(tmp_path):
    path = tmp_path / runner.ANNOTATIONS
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    with pytest.raises(ValueError, match="manifest changed"):
        runner.run_evaluation(repo=tmp_path)
    assert not tracemalloc.is_tracing()
    tracemalloc.start()
    try:
        with pytest.raises(ValueError, match="manifest changed"):
            runner.run_evaluation(repo=tmp_path)
        assert tracemalloc.is_tracing()
    finally:
        tracemalloc.stop()


def test_output_cannot_contaminate_accepted_cache(tmp_path):
    with pytest.raises(ValueError, match="modify the accepted cache"):
        runner.run_evaluation(cache=tmp_path, output=tmp_path / "outputs")


@pytest.mark.parametrize("suffix", ["", "runs", "debug/nested/runs"])
def test_output_cannot_modify_previous_completed_run(published_control, suffix):
    path, annotations, cached, repo = published_control
    before = sha256(path / "metadata/manifest.json")
    output = path / suffix
    with pytest.raises(ValueError, match="inside an existing run"):
        runner.run_evaluation(repo=repo, output=output)
    with pytest.raises(ValueError, match="inside an existing run"):
        runner._publish(
            repo, output, annotations, cached, method_name="synthetic_control_nested"
        )
    assert sha256(path / "metadata/manifest.json") == before
    assert verify_run(path)["status"] == "complete"


def test_output_alias_cannot_modify_previous_completed_run(published_control, tmp_path):
    path, annotations, cached, repo = published_control
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
    with pytest.raises(ValueError, match="inside an existing run"):
        runner.run_evaluation(repo=repo, output=alias / "runs")
    with pytest.raises(ValueError, match="inside an existing run"):
        runner._publish(
            repo,
            alias / "runs",
            annotations,
            cached,
            method_name="synthetic_control_alias",
        )
    assert not (path / "runs").exists()
    assert verify_run(path)["status"] == "complete"


def test_actual_accepted_cache_and_all_threshold_accounting():
    accepted_path = runner.ROOT / runner.ACCEPTED_RELATIVE
    if not accepted_path.is_dir():
        pytest.skip(
            "Optional recorded-data check requires the transferred accepted Task28 run"
        )
    annotations = json.loads(ANNOTATIONS.read_text())
    captures = [
        {
            key: frame[key]
            for key in ("frame_id", "rgb", "timestamp_s", "source_selection_index")
        }
        for frame in annotations["frames"]
    ]
    cached = runner.load_accepted_cache(accepted_path, captures)
    results = runner.evaluate(annotations["frames"], cached["frames"], (0.3, 0.5, 0.7))
    assert len(cached["frames"]) == 6
    assert sum(len(f["proposals"]) for f in cached["frames"]) > 5
    assert results["thresholds"][1]["summary"]["cup"]["reference_count"] == 5
    assert results["thresholds"][1]["summary"]["tv"]["reference_count"] == 6


def test_offline_report_browser(published_control):
    sync = pytest.importorskip("playwright.sync_api")
    path, _, _, _ = published_control
    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("Local Edge not installed")
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
        assert page.locator("section").count() == 6
        assert page.locator("img").count() == 6
        assert page.locator("img").evaluate_all(
            "imgs => imgs.every(i => i.complete && i.naturalWidth === 640)"
        )
        page.locator("section details summary").first.click()
        assert "diagnostics" in page.locator("section pre").first.inner_text()
        assert errors == [] and external == []
        browser.close()
