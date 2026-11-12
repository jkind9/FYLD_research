"""The live and room orchestrators on small synthetic frames, with a fake depth model and a fake detector."""

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image
from scipy.spatial.transform import Rotation

from apps import cli
from sitescan import session
from sitescan.objects import Detection
from sitescan.pipelines import (
    LiveProcessor,
    LiveSettings,
    RoomSettings,
    build_room,
    run_live,
)
from sitescan.pipelines.live import frame_scale
from sitescan.pipelines.room import fresh_depth, scale_jumps, vote_views
from sitescan.session import wire_v1
from sitescan.triangulate import SparseDepth

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


@pytest.mark.parametrize(("history", "new", "limit", "jumps"), [
    ([0.6] * 20, 1.6, 1.25, True),  # a frame sized 2.6 times too large, as at seq 565-572 of the 15 October walk
    ([0.6] * 20, 0.4, 1.25, True),
    ([0.6] * 20, 0.7, 1.25, False),
    ([0.6] * 4, 1.6, 1.25, False),  # too few fused frames to compare with
    ([0.6] * 20, 1.6, None, False),  # check off
    ([3.0] * 5 + [0.6] * 15, 1.6, 1.25, True),  # only the most recent frames count
])
def test_room_skips_a_frame_whose_scale_jumps_from_recent_frames(history, new, limit, jumps):
    assert scale_jumps(history, new, limit) is jumps


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


def test_the_command_refuses_a_label_that_breaks_the_naming_rule(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["room", "--session", str(tmp_path), "--label", "My Run", "--root", str(tmp_path)])


def test_room_options_make_a_run_folder_named_after_the_recording(tmp_path):
    args = cli.parse_room_args(cli.room_parser("trial"), ["--session", "tum-desk-20", "--label", "far-3",
                                                          "--root", str(tmp_path), "--far", "3"], "trial")
    assert args.session == FIXTURE and args.out.parent == tmp_path / "tum-desk-20" / "trial"
    assert args.out.name.endswith("_far-3")
    assert json.loads((args.out / "run.json").read_text(encoding="utf-8"))["typed"] == {"far": 3.0}


FIXTURE = Path(__file__).parent / "fixtures" / "tum_desk_20"


def flat_model(colour):
    return np.full(colour.shape[:2], 3.0), np.ones(colour.shape[:2], bool)


def fixture_trajectory(tmp_path, frames=20):
    """The fixture's motion-capture poses as a tracker file, in their own z-up world."""
    folder = tmp_path / "recording"
    for name in ("frames", "cam0", "depth"):
        shutil.copytree(FIXTURE / name, folder / name)
    lines = (FIXTURE / "frames.jsonl").read_text(encoding="utf-8").splitlines()[:frames]
    (folder / "frames.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copy(FIXTURE / "session.json", folder / "session.json")
    rows = []
    for frame in session.frames(folder):
        quaternion = Rotation.from_matrix(frame.pose[:3, :3]).as_quat()
        rows.append(f"{frame.t_ns / 1e9:.9f} " + " ".join(f"{v:.12f}" for v in (*frame.pose[:3, 3], *quaternion)))
    path = tmp_path / "trajectory.txt"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return folder, session.read_tum(path, source="mocap", up=(0.0, 0.0, 1.0))


def test_sparse_points_scale_a_frame_and_count_by_their_depth_error():
    learned = np.full((48, 64), 4.0)
    uv = np.c_[np.arange(30), np.zeros(30)].astype(float)
    depth = np.r_[np.full(20, 2.0), np.full(10, 3.0)]
    sigma = np.r_[np.full(20, 0.5), np.full(10, 0.01)]  # the 3 m points are far more precise
    sparse = SparseDepth(uv, depth, sigma, np.arange(30))
    fitted, source = frame_scale(learned, np.ones_like(learned, bool), wire_frame(1, depth_m=None), None,
                                 ("sparse",), sparse)
    assert source == "sparse" and fitted == pytest.approx(0.75)


@pytest.mark.parametrize("sources,frames", [(("sparse",), 20), (("dense", "sparse"), 7)])
def test_a_room_builds_from_tracker_poses_sized_only_by_triangulated_depth(tmp_path, sources, frames):
    folder, trajectory = fixture_trajectory(tmp_path, frames)
    room = build_room(folder, flat_model, RoomSettings(scale_sources=sources), trajectory)
    summary = room.summary
    assert summary["pose_source"] == "mocap" and summary["scale"]["sources"] == list(sources)
    used = summary["scale"]["frames_per_source"]
    assert summary["frames"]["fused"] == sum(used.values()) >= frames // 2
    assert used.get(sources[0], 0) >= 1
    # The desk is 1-1.3 m away and the model reads 3 m everywhere, so the scale is about 0.4.
    assert 0.3 < summary["scale_min_median_max"][1] < 0.45
    assert summary["surface_points"] > 1000


def test_live_updates_take_their_scale_from_sparse_points_on_tracker_poses(tmp_path):
    folder, trajectory = fixture_trajectory(tmp_path)
    processor = LiveProcessor(flat_model, None, LiveSettings(scale_sources=("sparse",)))
    sources = []
    for frame in session.read_wire_session(folder, trajectory):
        processor.add(frame, folder / "frames" / f"{frame.seq:06d}.jpg")
        sources.append(processor.update()["scale_source"])
    assert sources[0] == "none" and sources.count("sparse") >= 15
