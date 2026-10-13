import importlib
import os
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

marigold = importlib.import_module("experiments.02_stereo_depth.marigold")
TumDepthFrame = importlib.import_module("experiments.02_stereo_depth.dataset").TumDepthFrame
TumDepthSelection = importlib.import_module("experiments.02_stereo_depth.dataset").TumDepthSelection


@pytest.fixture
def work_dir():
    path = Path.cwd() / f".task54-marigold-test-{uuid.uuid4().hex}"
    path.mkdir()
    yield path
    if path.parent == Path.cwd() and path.name.startswith(".task54-marigold-test-"):
        shutil.rmtree(path)


def _selection(root: Path) -> TumDepthSelection:
    rgb = np.full((2, 3, 3), 127, dtype=np.uint8)
    reference = np.full((2, 3), 2.0, dtype=np.float64)
    valid = np.ones((2, 3), dtype=np.bool_)
    frame = TumDepthFrame("frame-01", 1.0, rgb, reference, valid)
    return TumDepthSelection("sequence", root, 1, 10, (frame,))


def test_export_writes_only_selected_rgb_as_png(work_dir, monkeypatch):
    selection = _selection(work_dir)
    monkeypatch.setattr(marigold, "SEQUENCE_NAMES", ("sequence",))
    monkeypatch.setattr(marigold, "_resolve_sequence_root", lambda *_args: work_dir)
    monkeypatch.setattr(marigold, "select_tum_frames", lambda *_args, **_kwargs: selection)

    written = marigold.export_rgb_inputs(work_dir, work_dir / "input")

    image_path = work_dir / "input" / "sequence" / "frame-01.png"
    with Image.open(image_path) as image:
        assert np.array_equal(np.asarray(image), selection.frames[0].colour)
    assert written[0]["frames"][0]["frame_id"] == "frame-01"
    assert len(list(image_path.parent.glob("*.png"))) == 1


def test_score_loads_native_log_depth_predictions(work_dir, monkeypatch):
    selection = _selection(work_dir)
    monkeypatch.setattr(marigold, "SEQUENCE_NAMES", ("sequence",))
    monkeypatch.setattr(marigold, "_resolve_sequence_root", lambda *_args: work_dir)
    monkeypatch.setattr(marigold, "select_tum_frames", lambda *_args, **_kwargs: selection)
    # The official infer.py writes under <output_dir>/images/predictions_npy/.
    output_dir = work_dir / "output" / "sequence"
    prediction_dir = output_dir / "images" / "predictions_npy"
    prediction_dir.mkdir(parents=True)
    np.save(prediction_dir / "frame-01.npy", np.log(np.full((2, 3), 2.0)))

    result = marigold.score_predictions(work_dir, work_dir / "output")

    assert result[0]["sequence"] == "sequence"
    assert result[0]["scores"]["metric"]["available"] is False
    assert result[0]["scores"]["reference_aligned_shape"]["aggregate"]["overall"]["abs_rel"] < 1e-6


def test_cost_summary_reads_wrapper_records(work_dir):
    sequence_dir = work_dir / "sequence"
    prediction_dir = sequence_dir / "images" / "predictions_npy"
    prediction_dir.mkdir(parents=True)
    (sequence_dir / "run_status.json").write_text(
        '{"sequence": "sequence", "exit_status": 0, "started_unix_s": 1000.0, '
        '"finished_unix_s": 1100.0}'
    )
    (sequence_dir / "gpu_memory.csv").write_text(
        "2026/10/07 21:52:52.798, 3000\n2026/10/07 21:52:53.798, 15000\n"
        "2026/10/07 21:52:54.798, 9000\n"
    )
    (sequence_dir / "time.txt").write_text("\tMaximum resident set size (kbytes): 2097152\n")
    for index, saved_at in enumerate((1040.0, 1055.0, 1069.0)):
        path = prediction_dir / f"{index}.npy"
        np.save(path, np.zeros((1, 1)))
        os.utime(path, (saved_at, saved_at))

    cost = marigold.marigold_cost(sequence_dir, prediction_dir)

    assert cost["wall_time_s"] == 100.0
    assert cost["first_map_after_start_s"] == 40.0
    assert cost["median_frame_interval_s"] == 14.5
    assert cost["gpu_memory_peak_minus_idle_mib"] == 12000.0
    assert cost["peak_process_memory_mib"] == 2048.0


def test_cost_summary_is_absent_without_wrapper_records(work_dir):
    assert marigold.marigold_cost(work_dir, work_dir) is None


def test_score_only_the_requested_sequences(work_dir, monkeypatch):
    selection = _selection(work_dir)
    monkeypatch.setattr(marigold, "SEQUENCE_NAMES", ("sequence", "unfinished"))
    monkeypatch.setattr(marigold, "_resolve_sequence_root", lambda *_args: work_dir)
    monkeypatch.setattr(marigold, "select_tum_frames", lambda *_args, **_kwargs: selection)
    prediction_dir = work_dir / "output" / "sequence" / "images" / "predictions_npy"
    prediction_dir.mkdir(parents=True)
    np.save(prediction_dir / "frame-01.npy", np.log(np.full((2, 3), 2.0)))

    result = marigold.score_predictions(work_dir, work_dir / "output", ("sequence",))

    assert [row["sequence"] for row in result] == ["sequence"]
    with pytest.raises(ValueError, match="Choose from"):
        marigold.score_predictions(work_dir, work_dir / "output", ("elsewhere",))
