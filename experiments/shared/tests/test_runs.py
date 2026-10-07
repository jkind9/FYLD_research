"""CPU-only run lifecycle and review artifact contracts."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.shared.exporting import export_frame
from experiments.shared.runs import Run, verify_run, write_json


def test_stop_incomplete_keeps_files_and_refuses_verify(tmp_path):
    with Run(tmp_path / "runs", Path.cwd(), {}) as run:
        write_json(run.path / "output/partial.json", {"saved": True})
        run.stop_incomplete("Depth unavailable")
        with pytest.raises(ValueError, match="Only running runs"):
            run.finish()
    status = json.loads((run.path / "metadata/status.json").read_text())
    assert status["status"] == "failed"
    assert status["error_type"] == "IncompleteRun"
    assert status["error"] == "Depth unavailable"
    assert (run.path / "output/partial.json").is_file()
    assert (run.path / "metadata/timing.json").is_file()
    assert not (run.path / "metadata/manifest.json").exists()
    with pytest.raises(ValueError, match="not complete"):
        verify_run(run.path)


def test_snapshot_includes_dirty_untracked_walkthrough_and_hash_changes(tmp_path):
    from experiments.shared.runs import _snapshot

    source = tmp_path / "src/walkthrough/pipeline.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    experiment = tmp_path / "experiments/method.py"
    experiment.parent.mkdir()
    experiment.write_text("value = 2\n")
    unrelated = tmp_path / "src/other.py"
    unrelated.write_text("value = 3\n")
    first = _snapshot(tmp_path, tmp_path / "snapshot-1", tmp_path / "runs")
    assert set(first) == {"experiments/method.py", "src/walkthrough/pipeline.py"}
    assert (
        tmp_path / "snapshot-1/src/walkthrough/pipeline.py"
    ).read_text() == "value = 1\n"
    source.write_text("value = 4\n")
    second = _snapshot(tmp_path, tmp_path / "snapshot-2", tmp_path / "runs")
    assert first["src/walkthrough/pipeline.py"] != second["src/walkthrough/pipeline.py"]


@pytest.mark.parametrize(
    "linked",
    [
        ".",
        "experiments",
        "src",
        "src/walkthrough",
        "src/walkthrough/steps",
        "src/walkthrough/pipeline.py",
    ],
)
def test_source_snapshot_rejects_linked_roots_directories_and_files(
    tmp_path, monkeypatch, linked
):
    from experiments.shared.runs import _snapshot

    source = tmp_path / "src/walkthrough/pipeline.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    (source.parent / "steps").mkdir()
    (tmp_path / "experiments").mkdir()
    original = Path.is_symlink
    link = tmp_path / linked
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == link or original(path))
    with pytest.raises(ValueError, match="symbolic link"):
        _snapshot(tmp_path, tmp_path / "snapshot", tmp_path / "runs")


def test_run_refuses_repo_symlink_before_resolving_it(tmp_path, monkeypatch):
    original = Path.is_symlink
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path == tmp_path or original(path)
    )
    with pytest.raises(ValueError, match="symbolic link"):
        Run(tmp_path / "runs", tmp_path, {})


def test_walkthrough_custom_run_root_excludes_prior_source_copies(
    tmp_path, monkeypatch
):
    from experiments.shared import runs

    source = tmp_path / "src/walkthrough/pipeline.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    monkeypatch.setattr(runs, "_git", lambda *_: "fake-test-repository")
    for _ in range(2):
        with Run(source.parent / "custom-output", tmp_path, {}) as run:
            pass
        snapshot = json.loads((run.path / "metadata/source_snapshot.json").read_text())
        assert list(snapshot["files"]) == ["src/walkthrough/pipeline.py"]


def test_public_artifact_inventory_reuses_manifest_contract(tmp_path):
    from experiments.shared import runs

    (tmp_path / "prediction.bin").write_bytes(b"prediction")
    assert runs.artifact_inventory(tmp_path) == runs._inventory(tmp_path)


def test_custom_run_root_excluded_from_source_snapshot(tmp_path, monkeypatch):
    from experiments.shared import runs

    source = tmp_path / "experiments/example.py"
    source.parent.mkdir()
    source.write_text("value = 1\n")
    monkeypatch.setattr(runs, "_git", lambda *_: "fake-test-repository")
    root = tmp_path / "experiments/custom-output"
    for _ in range(2):
        with Run(root, tmp_path, {}) as run:
            pass
        snapshot = json.loads((run.path / "metadata/source_snapshot.json").read_text())
        assert list(snapshot["files"]) == ["experiments/example.py"]


def test_atomic_json_rejects_nonfinite_without_overwriting(tmp_path):
    path = tmp_path / "data.json"
    write_json(path, {"value": 1})
    with pytest.raises(ValueError):
        write_json(path, {"value": float("nan")})
    assert json.loads(path.read_text()) == {"value": 1}


def test_atomic_replace_failure_retains_previous_receipt(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    write_json(path, {"value": 1})

    def refuse_replace(self, target):
        raise OSError("injected replace failure")

    monkeypatch.setattr(Path, "replace", refuse_replace)
    with pytest.raises(OSError, match="replace failure"):
        write_json(path, {"value": 2})
    assert json.loads(path.read_text()) == {"value": 1}
    assert list(tmp_path.glob("*.part")) == []


def test_run_completion_snapshot_and_unique_directory(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    with Run(tmp_path, repo, {"seed": 0}) as run:
        (run.path / "input" / "example.bin").write_bytes(b"example")
    assert verify_run(run.path)["file_count"] > 0
    assert (run.path / "metadata/source/experiments/datasets/acquisition.py").exists()
    with Run(tmp_path, repo, {}) as other:
        assert other.path != run.path
    assert (
        json.loads((run.path / "metadata/status.json").read_text())["status"]
        == "complete"
    )


@pytest.mark.parametrize("damage", ["changed", "missing", "extra"])
def test_verify_detects_damage(tmp_path, damage):
    repo = Path(__file__).resolve().parents[3]
    with Run(tmp_path, repo, {}) as run:
        artifact = run.path / "output/a.bin"
        artifact.write_bytes(b"original")
    if damage == "changed":
        artifact.write_bytes(b"different")
    elif damage == "missing":
        artifact.unlink()
    else:
        (run.path / "output/extra.bin").write_bytes(b"extra")
    with pytest.raises(ValueError):
        verify_run(run.path)


def test_manifest_tamper_and_interrupted_state_are_rejected(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    with Run(tmp_path, repo, {}) as run:
        pass
    write_json(run.path / "metadata/manifest.json", {"schema_version": 1, "files": {}})
    with pytest.raises(ValueError, match="manifest hash"):
        verify_run(run.path)
    interrupted = Run(tmp_path, repo, {})
    interrupted.__enter__()
    with pytest.raises(ValueError, match="complete"):
        verify_run(interrupted.path)


def test_snapshot_failure_records_failed_state(tmp_path, monkeypatch):
    run = Run(tmp_path, Path(__file__).resolve().parents[3], {})
    monkeypatch.setattr(
        run, "_capture", lambda: (_ for _ in ()).throw(OSError("snapshot"))
    )
    with pytest.raises(OSError, match="snapshot"):
        run.__enter__()
    assert (
        json.loads((run.path / "metadata/status.json").read_text())["status"]
        == "failed"
    )


def test_duplicate_directory_is_never_reused(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    with Run(tmp_path, repo, {}) as run:
        pass
    duplicate = Run(tmp_path, repo, {})
    duplicate.path = run.path
    with pytest.raises(FileExistsError):
        duplicate.__enter__()
    assert verify_run(run.path)["status"] == "complete"


def test_explicit_finish_can_leave_context_successfully(tmp_path):
    with Run(tmp_path, Path(__file__).resolve().parents[3], {}) as run:
        run.finish()
    assert verify_run(run.path)["status"] == "complete"


def test_failure_and_failed_publication_are_not_complete(tmp_path, monkeypatch):
    repo = Path(__file__).resolve().parents[3]
    with pytest.raises(RuntimeError, match="injected"), Run(tmp_path, repo, {}) as run:
        raise RuntimeError("injected")
    assert (
        json.loads((run.path / "metadata/status.json").read_text())["status"]
        == "failed"
    )
    with pytest.raises(ValueError, match="complete"):
        verify_run(run.path)
    with (
        pytest.raises(OSError, match="publication"),
        Run(tmp_path, repo, {}) as publication,
    ):
        monkeypatch.setattr(
            publication,
            "finish",
            lambda: (_ for _ in ()).throw(OSError("publication")),
        )
    assert (
        json.loads((publication.path / "metadata/status.json").read_text())["status"]
        == "failed"
    )


def test_export_preserves_correspondence_and_full_resolution(tmp_path):
    depth = np.array([[1.0, 2.0], [np.nan, 3.0]])
    mask = np.isfinite(depth)
    pixels = np.array([[0, 0], [0, 1], [1, 1]])
    points = np.array([[0.0, 0.0, 1.0], [2.0, 0.0, 2.0], [3.0, 3.0, 3.0]])
    export_frame(
        tmp_path / "output",
        tmp_path / "debug",
        depth,
        mask,
        pixels,
        points,
        points,
        points,
        np.zeros((2, 2, 3), dtype=np.uint8),
        np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]),
    )
    assert np.array_equal(np.load(tmp_path / "output/pixels.npy"), pixels)
    assert np.array_equal(np.load(tmp_path / "output/camera.npy"), points)
    assert Image.open(tmp_path / "debug/depth.png").size == (2, 2)
    assert (tmp_path / "output/world.ply").exists()
    assert (tmp_path / "debug/model_z.png").exists()
    assert (tmp_path / "debug/legends.json").exists()
    assert (tmp_path / "debug/camera_cloud.png").exists()
    assert (tmp_path / "debug/world_cloud.png").exists()
    assert (tmp_path / "debug/model_cloud.png").exists()


def test_export_empty_cloud(tmp_path):
    export_frame(
        tmp_path / "output",
        tmp_path / "debug",
        np.full((2, 2), np.nan),
        np.zeros((2, 2), dtype=bool),
        np.empty((0, 2), dtype=int),
        np.empty((0, 3)),
        np.empty((0, 3)),
        np.empty((0, 3)),
        np.zeros((2, 2, 3), dtype=np.uint8),
        np.empty((0, 2)),
    )
    assert (tmp_path / "debug/camera_cloud.png").exists()
