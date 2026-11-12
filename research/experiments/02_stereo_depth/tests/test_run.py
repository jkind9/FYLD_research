"""Mocked contracts for the Task54 local model runner."""

import importlib
import json
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

runner = importlib.import_module("experiments.02_stereo_depth.run")


@pytest.fixture
def tmp_path():
    path = Path.cwd() / f".task54-test-{uuid.uuid4().hex}"
    path.mkdir()
    yield path
    if path.parent == Path.cwd() and path.name.startswith(".task54-test-"):
        shutil.rmtree(path)


def _selection(sequence: str) -> SimpleNamespace:
    frames = tuple(
        SimpleNamespace(
            frame_id=f"{index}.0",
            timestamp_s=float(index),
            colour=np.full((2, 2, 3), index, dtype=np.uint8),
            reference_depth_m=np.full((2, 2), index + 1.0),
            reference_valid=np.ones((2, 2), dtype=bool),
        )
        for index in range(7)
    )
    return SimpleNamespace(
        sequence=sequence,
        source_root=Path(sequence),
        matched_pair_count=70,
        stride=10,
        frames=frames,
    )


def test_frozen_experiment_settings_include_value_provenance():
    assert runner.HYPERPARAMETERS["tum_sample_stride"] == {
        "value": 10,
        "source": "confirmed 2026-10-07",
    }
    assert runner.HYPERPARAMETERS["repeats_per_frame"]["value"] == 3
    assert runner.HYPERPARAMETERS["reference_units_per_metre"]["value"] == 5000.0


def test_sequence_root_resolver_uses_nested_desk_directory(tmp_path):
    tum = tmp_path / "tum"
    nested = tum / "rgbd_dataset_freiburg1_desk" / "rgbd_dataset_freiburg1_desk"
    nested.mkdir(parents=True)
    (nested / "rgb.txt").touch()
    (nested / "depth.txt").touch()

    assert runner._resolve_sequence_root(tum, "rgbd_dataset_freiburg1_desk") == nested


def test_preflight_checks_inputs_without_loading_or_running_model(tmp_path, monkeypatch, capsys):
    tum_root = tmp_path / "tum"
    tum_root.mkdir()
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "weights.pth").touch()
    selections = []

    def select(root, stride):
        selections.append((root, stride))
        return _selection(root.name)

    monkeypatch.setattr(runner, "select_tum_frames", select)
    monkeypatch.setattr(
        runner,
        "_resolve_sequence_root",
        lambda root, name: root / name,
    )
    monkeypatch.setattr(
        runner,
        "_load_method",
        lambda *_args: (_ for _ in ()).throw(AssertionError("model must stay unloaded")),
    )

    status = runner.main(
        [
            "--method",
            "zipdepth",
            "--checkpoint",
            str(checkpoint / "weights.pth"),
            "--tum-root",
            str(tum_root),
            "--output",
            str(tmp_path / "output"),
            "--device",
            "cpu",
            "--preflight",
        ]
    )

    assert status == 0
    assert len(selections) == 2
    assert all(root.parent == tum_root and stride == 10 for root, stride in selections)
    report = json.loads(capsys.readouterr().out)
    assert report["preflight"] is True
    assert report["model_loaded"] is False


def test_existing_run_directory_cannot_replace_shared_run_metadata(tmp_path, monkeypatch):
    checkpoint = tmp_path / "weights.pth"
    checkpoint.touch()
    run_dir = tmp_path / "output" / "zipdepth"
    run_dir.mkdir(parents=True)
    run_json = run_dir / "run.json"
    run_json.write_text('{"checkpoint":"first"}', encoding="utf-8")
    monkeypatch.setattr(runner, "_validate_runtime", lambda *_args: None)
    monkeypatch.setattr(runner, "select_tum_frames", lambda *_args, **_kwargs: _selection("xyz"))
    monkeypatch.setattr(
        runner,
        "_load_method",
        lambda *_args: (_ for _ in ()).throw(AssertionError("existing run must be refused")),
    )

    with pytest.raises(SystemExit):
        runner.main(
            [
                "--method", "zipdepth",
                "--checkpoint", str(checkpoint),
                "--tum-root", str(tmp_path),
                "--output", str(tmp_path / "output"),
                "--device", "cpu",
            ]
        )

    assert run_json.read_text(encoding="utf-8") == '{"checkpoint":"first"}'


def test_run_discards_warmups_scores_rgb_only_and_saves_native_predictions(
    tmp_path, monkeypatch
):
    selection = _selection("xyz")
    model_inputs = []
    evaluation_calls = []

    class FakePrediction:
        def __init__(self, frame_id, depth):
            self.frame_id = frame_id
            self.depth = depth
            self.valid = np.isfinite(depth)

    class FakeEstimator:
        def __call__(self, frames, *, run):
            assert run is None
            for frame in frames:
                assert not hasattr(frame, "reference_depth_m")
                assert not hasattr(frame, "reference_valid")
                model_inputs.append(frame.colour.copy())
                yield FakePrediction(
                    frame.frame_id,
                    np.full(frame.colour.shape[:2], 2.0, dtype=np.float32),
                )

    monkeypatch.setattr(runner, "select_tum_frames", lambda *_args: selection)
    monkeypatch.setattr(runner, "_resolve_sequence_root", lambda *_args: Path("xyz"))
    monkeypatch.setattr(runner, "_load_method", lambda *_args: FakeEstimator())
    monkeypatch.setattr(runner, "_runtime_metadata", lambda *_args: {"runtime": "fake"})
    monkeypatch.setattr(runner, "_checkpoint_manifest", lambda *_args: [])
    monkeypatch.setattr(runner, "_parameter_count", lambda *_args: 12)
    monkeypatch.setattr(runner, "_sync_device", lambda *_args: None)
    monkeypatch.setattr(runner.time, "perf_counter", iter(range(100)).__next__)

    def evaluate(actual_selection, predictions, convention):
        evaluation_calls.append((actual_selection, predictions, convention))
        return {"evaluated_frame_count": len(predictions), "convention": convention}

    monkeypatch.setattr(runner, "evaluate_predictions", evaluate)
    output = tmp_path / "run"
    run_spec = SimpleNamespace(
        method="zipdepth",
        checkpoint=Path("checkpoint.pth"),
        device="cpu",
        zip_build="gpu",
        output=output,
        tum_root=tmp_path,
        preflight=False,
    )

    original_rename = Path.rename

    def deny_staging_rename(source, target):
        if source.parent.name == ".incomplete":
            raise PermissionError("simulated Windows rename denial")
        return original_rename(source, target)

    monkeypatch.setattr(Path, "rename", deny_staging_rename)
    with pytest.warns(RuntimeWarning, match="publishing a verified file copy"):
        runner._run_sequence(
            run_spec,
            selection,
            FakeEstimator(),
            [0.25],
            {"parameters": 12, "checkpoint_files": [], "runtime": {"runtime": "fake"}},
        )

    expected_inputs = 5 + len(selection.frames) * 3
    assert len(model_inputs) == expected_inputs
    assert len(evaluation_calls) == 1
    scored_predictions = evaluation_calls[0][1]
    assert set(scored_predictions) == {frame.frame_id for frame in selection.frames}
    assert np.all(scored_predictions[selection.frames[0].frame_id] == 2.0)
    assert len(list((output / "zipdepth" / "xyz" / "predictions").glob("*.npy"))) == 7
    report = json.loads((output / "zipdepth" / "xyz" / "results.json").read_text())
    assert report["timing"]["warmup_frames_discarded"] == 5
    assert report["timing"]["repeats_per_frame"] == 3
    assert report["parameters"] == 12
    # CPU runs must record memory too; GPU allocation stays empty on CPU.
    assert report["timing"]["peak_cuda_allocated_mib"] is None
    assert report["timing"]["peak_process_memory_mib"] > 0


def test_peak_process_memory_is_a_positive_mebibyte_count():
    peak = runner._peak_process_memory_mib()
    assert isinstance(peak, float)
    assert 1.0 < peak < 1024 * 1024


def test_checkpoint_manifest_skips_download_cache_metadata(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    (checkpoint / ".cache" / "huggingface").mkdir(parents=True)
    (checkpoint / ".cache" / "huggingface" / "model.safetensors.metadata").write_text("t")
    (checkpoint / "model.safetensors").write_bytes(b"weights")

    manifest = runner._checkpoint_manifest(checkpoint)

    assert [row["path"] for row in manifest] == ["model.safetensors"]

