"""The live processor on a synthetic session, with a fake depth model and a fake detector."""

import importlib

import numpy as np
import pytest
from PIL import Image

from src.live.processor import LiveProcessor
from src.live.stream import session_v1

localisation = importlib.import_module("experiments.06_object_recognition.pilot.localisation")

K = (50.0, 50.0, 32.0, 24.0)
POSE = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
SHIFTED = (0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)


def model_depth(colour):
    return np.full(colour.shape[:2], 3.0), np.ones(colour.shape[:2], bool)  # reads 1.5 times too far


def one_cup(image_path):
    return [localisation.Detection((24.0, 16.0, 40.0, 32.0), "cup", 41, 0.9)], {"image_shape_hw": [48, 64]}


def make_frame(seq, pose, *, anchor=None, updates=None):
    depth = session_v1.Depth(seq, np.full((12, 16), 2.0, np.float32), np.full((12, 16), 200, np.uint8),
                             tuple(v / 4 for v in K))
    return session_v1.Frame(seq, seq * 33_000_000, 0, "TRACKING", "NONE", pose, K, b"", (64, 48), np.zeros(0, np.int64),
                            np.zeros((0, 3)), np.zeros((0, 2)), np.zeros(0), depth, anchor, updates or {})


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "frame.jpg"
    Image.fromarray(np.full((48, 64, 3), 120, np.uint8)).save(path)
    return path


def test_update_uses_the_newest_frame_and_reports_surface_map_and_counts(image):
    processor = LiveProcessor(model_depth, one_cup, voxel_m=0.02)
    assert processor.update() is None
    processor.add(make_frame(0, POSE, anchor=(0, POSE)), image)
    for seq in range(1, 5):
        processor.add(make_frame(seq, POSE), image)
    record = processor.update()
    assert record["frame_seq"] == 4 and record["size_source"] == "arcore_depth"
    assert record["size"] == pytest.approx(2.0 / 3.0)
    assert record["surface_points"] > 0 and "map" in record
    assert record["counts"] == {"cup": 1}
    assert record["detections"] == [{"label": "cup", "confidence": 0.9, "outcome": "new", "object_id": "object-0001",
                                     "nearest_same_class_m": None}]
    assert processor.update() is None  # nothing new since


def test_a_pose_correction_moves_the_surface_and_the_objects(image):
    processor = LiveProcessor(model_depth, one_cup, voxel_m=0.02)
    processor.add(make_frame(0, POSE, anchor=(0, POSE)), image)
    processor.update()
    before = np.median(processor.surface(), 0)
    # ARCore moves keyframe 0 by 0.5 m; its later poses are in the corrected world
    processor.add(make_frame(1, SHIFTED, updates={0: SHIFTED}), image)
    record = processor.update()
    assert np.allclose(np.median(processor.surface(), 0) - before, [0.5, 0.0, 0.0], atol=0.02)
    assert record["counts"] == {"cup": 1} and record["corrections"] == 1
    [seen] = record["detections"]
    assert seen["outcome"] == "matched" and seen["nearest_same_class_m"] == pytest.approx(0.0, abs=0.02)


def test_run_replays_a_session_and_writes_updates_surface_and_summary(tmp_path, monkeypatch):
    from argparse import Namespace

    from src.live import run, stand_in
    from src.live.tests.test_stand_in import tum_folder

    session = stand_in.write_session(f"tum:{tum_folder(tmp_path / 'clip')}", tmp_path / "session", depth_size=(16, 12))
    monkeypatch.setattr(run, "depth_anything", lambda checkpoint: model_depth)
    monkeypatch.setattr(run, "yolo26x", lambda checkpoint: one_cup)
    args = Namespace(replay=session, listen=None, out=tmp_path / "run", speed=0.0, threads=1, voxel=0.05,
                     no_objects=False, depth_checkpoint=None, detector_checkpoint=None)
    summary = run.run(args)
    lines = (tmp_path / "run" / "updates.jsonl").read_text().splitlines()
    assert summary["frames_received"] == 9 and summary["updates"] == len(lines) >= 1
    assert (tmp_path / "run" / "surface.ply").is_file() and summary["final"]["counts"] == {"cup": 1}
