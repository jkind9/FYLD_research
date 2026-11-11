"""The live and room orchestrators on small synthetic frames, with a fake depth model and a fake detector."""

import json
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from apps import cli
from sitescan.objects import Detection
from sitescan.pipelines import LiveProcessor, LiveSettings, run_live
from sitescan.pipelines.live import frame_scale
from sitescan.pipelines.room import fresh_depth, vote_views
from sitescan.session import wire_v1

K = (50.0, 50.0, 32.0, 24.0)
POSE = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)  # ARCore camera at the origin, looking along -z
SHIFTED = (0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
SETTINGS = LiveSettings(voxel_m=0.02)
NO_POINTS = np.zeros((0, 3))


def model_depth(colour):
    return np.full(colour.shape[:2], 3.0), np.ones(colour.shape[:2], bool)  # reads 1.5 times too far


def one_cup(colour):
    return [Detection((24.0, 16.0, 40.0, 32.0), "cup", 41, 0.9)]


def wire_frame(seq, pose=POSE, *, depth_m=2.0, anchor=None, updates=None, points_world=NO_POINTS):
    depth = None if depth_m is None else wire_v1.Depth(
        seq, np.full((12, 16), depth_m, np.float32), np.full((12, 16), 200, np.uint8), tuple(v / 4 for v in K))
    pixels = wire_v1.project(pose, K, points_world) if len(points_world) else np.zeros((0, 2))
    return wire_v1.Frame(seq, seq * 33_000_000, 0, "TRACKING", "NONE", pose, K, b"", (64, 48),
                         np.arange(len(points_world)), points_world, pixels, np.ones(len(points_world)), depth,
                         anchor, updates or {})


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "frame.jpg"
    Image.fromarray(np.full((48, 64, 3), 120, np.uint8)).save(path)
    return path


def test_update_uses_the_newest_frame_and_reports_surface_map_and_counts(image):
    processor = LiveProcessor(model_depth, one_cup, SETTINGS)
    assert processor.update() is None
    processor.add(wire_frame(0, anchor=(0, POSE)), image)
    for seq in range(1, 5):
        processor.add(wire_frame(seq), image)
    record = processor.update()
    assert record["frame_seq"] == 4 and record["scale_source"] == "arcore_depth"
    assert record["scale"] == pytest.approx(2.0 / 3.0)
    assert record["surface_points"] > 0 and "map" in record
    assert record["counts"] == {"cup": 1}
    assert record["detections"] == [{"label": "cup", "confidence": 0.9, "outcome": "new", "object_id": "object-0001",
                                     "nearest_same_class_m": None}]
    assert processor.update() is None  # nothing new since


def test_a_pose_correction_moves_the_surface_and_the_objects(image):
    processor = LiveProcessor(model_depth, one_cup, SETTINGS)
    processor.add(wire_frame(0, anchor=(0, POSE)), image)
    processor.update()
    before = np.median(processor.surface(), 0)
    # ARCore moves keyframe 0 by 0.5 m; its later poses are in the corrected world
    processor.add(wire_frame(1, SHIFTED, updates={0: SHIFTED}), image)
    record = processor.update()
    assert np.allclose(np.median(processor.surface(), 0) - before, [0.5, 0.0, 0.0], atol=0.02)
    assert record["counts"] == {"cup": 1} and record["corrections"] == 1
    [seen] = record["detections"]
    assert seen["outcome"] == "matched" and seen["nearest_same_class_m"] == pytest.approx(0.0, abs=0.02)


def test_run_live_logs_every_update_and_writes_the_surface_and_summary(tmp_path, image):
    processor = LiveProcessor(model_depth, one_cup, SETTINGS)

    def feed():
        processor.add(wire_frame(0, anchor=(0, POSE)), image)
        for seq in range(1, 9):
            processor.add(wire_frame(seq), image)

    summary = run_live(processor, feed, tmp_path, {"input": "synthetic"})
    lines = (tmp_path / "updates.jsonl").read_text(encoding="utf-8").splitlines()
    assert summary["input"] == "synthetic" and summary["frames_received"] == 9
    assert summary["updates"] == len(lines) >= 1
    assert (tmp_path / "surface.ply").is_file() and summary["final"]["counts"] == {"cup": 1}
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["updates"] == summary["updates"]


def test_scale_comes_from_arcore_depth_first():
    learned = np.full((48, 64), 3.0)
    assert frame_scale(learned, np.ones_like(learned, bool), wire_frame(1), None) == (pytest.approx(2.0 / 3.0), "arcore_depth")


def test_scale_falls_back_to_tracked_points_then_to_the_previous_scale():
    learned = np.full((48, 64), 4.0)
    valid = np.ones_like(learned, bool)
    rng = np.random.default_rng(0)
    points = np.c_[rng.uniform(-0.5, 0.5, (25, 2)), np.full(25, -2.0)]
    assert frame_scale(learned, valid, wire_frame(1, depth_m=None, points_world=points), None) == (
        pytest.approx(0.5), "tracked_points")
    assert frame_scale(learned, valid, wire_frame(1, depth_m=None, points_world=points[:5]), 0.7) == (0.7, "previous")
    assert frame_scale(learned, valid, wire_frame(1, depth_m=None), None) == (None, "none")


@pytest.mark.parametrize(("age_s", "fresh"), [(0.008, True), (0.1, True), (4.4, False)])
def test_room_frames_need_depth_measured_within_one_depth_period(age_s, fresh):
    frame = SimpleNamespace(camera_t_ns=10_000_000_000, depth=SimpleNamespace(t_ns=10_000_000_000 - round(age_s * 1e9)))
    assert fresh_depth(frame) is fresh


def test_vote_views_move_each_camera_by_its_anchor_correction_since_fusion():
    moved = np.eye(4)
    moved[0, 3] = 1.0  # the anchor placing keyframe 3 has moved 1 m along x since the frame was fused
    fragments = SimpleNamespace(placing_anchor=lambda keyframe: moved if keyframe == 3 else np.eye(4))
    evidence = np.ones((2, 2))
    placed = [(np.eye(4), (1.0, 1.0, 0.0, 0.0), 3, np.eye(4), evidence),
              (np.eye(4), (1.0, 1.0, 0.0, 0.0), 0, np.eye(4), evidence)]
    (first, k, depth), (second, _, _) = vote_views(fragments, placed)
    assert first[0, 3] == -1.0 and second[0, 3] == 0.0  # camera_from_world of a camera now at x = 1 m, and at 0
    assert k == (1.0, 1.0, 0.0, 0.0) and depth is evidence


def test_the_command_refuses_to_overwrite_a_run(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["room", "--session", str(tmp_path), "--out", str(tmp_path)])
