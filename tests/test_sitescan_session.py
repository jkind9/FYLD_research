"""Recordings become RGB frames with one camera convention; replay preserves their timing."""

import importlib
import json
import shutil
import threading
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from sitescan import session

FIXTURE = Path(__file__).parent / "fixtures" / "tum_desk_20"
WIRE = importlib.import_module("sitescan.session.wire_v1")
REPLAY = importlib.import_module("sitescan.session.replay")
ORIENTATION = importlib.import_module("sitescan.depth.orientation")
TYPES = importlib.import_module("sitescan.types")


def recording(tmp_path, *, version=2, tracking="TRACKING", anchors=True):
    row = json.loads((FIXTURE / "frames.jsonl").read_text().splitlines()[0])
    record = row["arcore"]
    record["anchors"] = [[9, 1, 2, 3, 0, 0, 0, 1]] if anchors else []
    if not anchors:
        record.pop("anchor")
    if tracking != "TRACKING":
        record.update(tracking=tracking, pose=None, device_pose=None, points=[])
    if version == 1:
        row = record | {
            "type": "frame",
            "version": 1,
            "seq": 0,
            "t_ns": row["camera_t_ns"],
            "sent_ms": 0,
            "image": row["colour"],
        }
    for name in ("frames", "cam0", "depth"):
        shutil.copytree(FIXTURE / name, tmp_path / name)
    (tmp_path / "frames.jsonl").write_text(json.dumps(row) + "\n")
    (tmp_path / "session.json").write_text(json.dumps({"version": version}))
    return tmp_path


@pytest.mark.parametrize("version", [1, 2])
def test_reader_returns_rgb_camera_and_metric_depth(tmp_path, version):
    frame = next(session.frames(recording(tmp_path, version=version)))
    assert frame.seq == 0 and frame.t_ns == 1305031453459685120
    assert frame.image.shape == (480, 640, 3) and frame.image.dtype == np.uint8
    np.testing.assert_array_equal(
        frame.image, np.asarray(Image.open(FIXTURE / "frames/000000.jpg"))
    )
    assert (frame.camera.fx, frame.camera.fy, frame.camera.width) == (525, 525, 640)
    assert frame.depth.camera.width == 160 and frame.depth.camera.height == 120
    assert frame.depth.depth_m.dtype == np.float32 and frame.depth.confidence.dtype == np.uint8
    assert frame.depth.t_ns == frame.t_ns
    assert frame.depth.depth_m.max() > 1


def test_camera_pose_projects_world_points_on_the_recorded_grid(tmp_path):
    frame = next(session.frames(recording(tmp_path)))
    camera_from_world = np.linalg.inv(frame.pose)
    points = frame.points_world @ camera_from_world[:3, :3].T + camera_from_world[:3, 3]
    assert (points[:, 2] > 0).all()
    k = frame.camera
    pixels = points[:, :2] / points[:, 2, None] * [k.fx, k.fy] + [k.cx, k.cy]
    np.testing.assert_allclose(pixels, frame.points_pixel)


def test_anchor_creation_and_corrections_use_the_same_matrix_convention(tmp_path):
    frame = next(session.frames(recording(tmp_path)))
    assert frame.anchor_created[0] == 0
    np.testing.assert_array_equal(frame.anchor_created[1], frame.pose)
    expected = np.diag([1.0, -1.0, -1.0, 1.0])
    expected[:3, 3] = [1, 2, 3]
    np.testing.assert_array_equal(frame.anchor_updates[9], expected)


@pytest.mark.parametrize("tracking", ["PAUSED", "STOPPED", "NO_ARCORE"])
def test_missing_pose_and_anchors_stay_absent(tmp_path, tracking):
    folder = recording(tmp_path, tracking="PAUSED", anchors=False)
    if tracking == "NO_ARCORE":
        row = json.loads((folder / "frames.jsonl").read_text())
        row["arcore"] = None
        (folder / "frames.jsonl").write_text(json.dumps(row) + "\n")
    elif tracking == "STOPPED":
        row = json.loads((folder / "frames.jsonl").read_text())
        row["arcore"]["tracking"] = tracking
        (folder / "frames.jsonl").write_text(json.dumps(row) + "\n")
    frame = next(session.frames(folder))
    assert frame.pose is None and frame.tracking == tracking
    assert frame.anchor_created is None and frame.anchor_updates == {}
    assert frame.points_world.shape == (0, 3)
    if tracking == "NO_ARCORE":
        assert frame.depth is None and frame.camera is None and frame.arcore_t_ns is None


def test_recording_preserves_all_frames_and_depth_availability():
    frames = list(session.frames(FIXTURE))
    assert [f.seq for f in frames] == list(range(20))
    assert [f.seq for f in frames if f.depth is not None] == [0, 3, 6, 9, 12, 15, 18]
    assert [f.seq for f in frames if f.anchor_created is not None] == [0, 6, 13]


@pytest.mark.parametrize("speed", [0, 2])
def test_replay_delivers_frames_in_order_and_paces_only_when_requested(monkeypatch, speed):
    waits = []
    delivered = []
    monkeypatch.setattr(REPLAY.time, "perf_counter", lambda: 10.0)
    monkeypatch.setattr(REPLAY.time, "sleep", waits.append)
    count = session.replay(FIXTURE, lambda f, p: delivered.append((f, p)), speed=speed)
    assert count == 20 and [f.seq for f, _ in delivered] == list(range(20))
    assert delivered[0][1] == FIXTURE / "frames/000000.jpg"
    if speed:
        assert len(waits) == 19
        assert waits[-1] == (delivered[-1][0].t_ns - delivered[0][0].t_ns) / 1e9 / speed
    else:
        assert waits == []


def test_replay_does_not_wait_when_processing_is_slower_than_capture(monkeypatch):
    times = iter([0.0] + [100.0] * 20)
    monkeypatch.setattr(REPLAY.time, "perf_counter", lambda: next(times))
    monkeypatch.setattr(REPLAY.time, "sleep", lambda _: pytest.fail("replay is already late"))
    assert session.replay(FIXTURE, lambda *_: None) == 20


def test_replay_stops_between_deliveries():
    stop = threading.Event()
    assert session.replay(FIXTURE, lambda *_: stop.set(), speed=0, stop=stop) == 1
    assert session.replay(FIXTURE, lambda *_: pytest.fail("stopped"), stop=stop) == 0


def test_legacy_reader_keeps_wire_records_for_existing_callers():
    frame = next(session.read_wire_session(FIXTURE))
    assert isinstance(frame.pose, tuple) and frame.image_jpeg[:2] == b"\xff\xd8"
    np.testing.assert_array_equal(
        next(session.frames(FIXTURE)).pose, WIRE.world_from_camera_cv(frame.pose)
    )


def tum_file(path, times, poses):
    """A TUM trajectory file of world_from_camera poses at the given time strings."""
    from scipy.spatial.transform import Rotation

    lines = [f"{t} {' '.join(map(repr, p[:3, 3].tolist()))} "
             f"{' '.join(map(repr, Rotation.from_matrix(p[:3, :3]).as_quat().tolist()))}"
             for t, p in zip(times, poses, strict=True)]
    path.write_text("# time x y z qx qy qz qw\n" + "\n".join(lines) + "\n")
    return path


def turned(angle_deg, axis, position=(0.0, 0.0, 0.0)):
    from scipy.spatial.transform import Rotation

    pose = np.eye(4)
    pose[:3, :3] = Rotation.from_euler(axis, angle_deg, degrees=True).as_matrix()
    pose[:3, 3] = position
    return pose


@pytest.mark.parametrize("up", [(0, 0, 1), (0, 1, 0), (0, -1, 0), (1, 2, 3)])
def test_up_to_y_turns_the_tracker_up_axis_onto_plus_y(up):
    rotation = session.up_to_y(up)
    np.testing.assert_allclose(rotation[:3, :3] @ np.divide(up, np.linalg.norm(up)), [0, 1, 0], atol=1e-12)
    np.testing.assert_allclose(rotation[:3, :3] @ rotation[:3, :3].T, np.eye(3), atol=1e-12)
    assert np.linalg.det(rotation[:3, :3]) == pytest.approx(1.0)


def test_tum_times_are_exact_in_decimal_and_scientific_form(tmp_path):
    path = tum_file(tmp_path / "t.txt", ["1305031453.459685120", "1.305031453627685120e+09"], [np.eye(4)] * 2)
    trajectory = session.read_tum(path, source="basalt", up=(0, 1, 0))
    assert trajectory.t_ns.tolist() == [1305031453459685120, 1305031453627685120]
    assert trajectory.source == "basalt"


def test_tum_poses_become_camera_poses_in_a_y_up_world(tmp_path):
    # A camera looking level along +x in a z-up world: its image-down axis is world -z.
    level = np.eye(4)
    level[:3, :3] = np.array([[0.0, 0, 1], [-1, 0, 0], [0, -1, 0]])
    imu_from_camera = np.eye(4)
    imu_from_camera[:3, 3] = [0.0, 0.0, 0.1]  # the camera sits 10 cm along the IMU's z axis
    path = tum_file(tmp_path / "t.txt", ["1.0"], [level @ np.linalg.inv(imu_from_camera)])
    trajectory = session.read_tum(path, source="basalt", imu_from_camera=imu_from_camera)
    pose = trajectory.world_from_camera[0]
    np.testing.assert_allclose(pose[:3, 1], [0, -1, 0], atol=1e-12)  # image down is world down
    np.testing.assert_allclose(pose[:3, 3], 0, atol=1e-12)
    assert ORIENTATION.quarter_turns(pose) == 0


def test_pose_at_interpolates_between_neighbours_and_stops_at_gaps():
    poses = np.array([turned(0, "y"), turned(90, "y", (1.0, 0, 0)), turned(90, "y", (2.0, 0, 0))])
    trajectory = TYPES.Trajectory("t", np.array([0, 100_000_000, 400_000_000]), poses)
    np.testing.assert_array_equal(session.pose_at(trajectory, 100_000_000), poses[1])
    middle = session.pose_at(trajectory, 50_000_000)
    np.testing.assert_allclose(middle, turned(45, "y", (0.5, 0, 0)), atol=1e-12)
    assert session.pose_at(trajectory, -10_000) is None and session.pose_at(trajectory, 400_010_000) is None
    assert session.pose_at(trajectory, 200_000_000) is None  # 0.3 s between poses: tracking was lost


def test_a_trajectory_of_the_recorded_poses_gives_the_recorded_poses(tmp_path):
    frames = list(session.frames(FIXTURE))
    times = [f"{f.t_ns // 10**9}.{f.t_ns % 10**9:09d}" for f in frames]
    path = tum_file(tmp_path / "t.txt", times, [f.pose for f in frames])
    trajectory = session.read_tum(path, source="replayed", up=(0, 1, 0))
    tracked = list(session.frames(FIXTURE, trajectory))
    for recorded_frame, tracked_frame in zip(frames, tracked, strict=True):
        np.testing.assert_allclose(tracked_frame.pose, recorded_frame.pose, atol=1e-12)
        assert tracked_frame.pose_source == "replayed" and recorded_frame.pose_source == "arcore"
        assert tracked_frame.points_world.shape == (0, 3) and tracked_frame.anchor_updates == {}
        assert (tracked_frame.depth is None) == (recorded_frame.depth is None)
    created = [f.seq for f in tracked if f.anchor_created is not None]
    assert created == [0, 6, 13]  # one anchor a second: the frames the fixture anchored too
    np.testing.assert_allclose(tracked[6].anchor_created[1], tracked[6].pose, atol=1e-12)


def test_frames_recorded_without_arcore_take_the_tracker_pose_and_calibrated_camera(tmp_path):
    folder = recording(tmp_path)
    row = json.loads((folder / "frames.jsonl").read_text())
    row["arcore"] = None
    (folder / "frames.jsonl").write_text(json.dumps(row) + "\n")
    path = tum_file(tmp_path / "t.txt", ["1305031453.4", "1305031453.5"], [turned(0, "x"), turned(0, "x", (1, 0, 0))])
    calibration = TYPES.Calibration(TYPES.Camera(500.0, 501.0, 320.0, 240.0, 640, 480), (), np.eye(4))
    frame = next(session.frames(folder, session.read_tum(path, source="basalt", up=(0, 1, 0)), calibration))
    np.testing.assert_allclose(frame.pose[:3, 3], [0.59685120, 0, 0], atol=1e-9)
    assert (frame.camera.fx, frame.camera.fy, frame.camera.cx) == (500.0, 501.0, 320.0)
    assert frame.anchor_created[0] == 0 and frame.tracking == "TRACKING"


def test_calibration_file_gives_camera_distortion_and_imu_from_camera(tmp_path):
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps({"camera": {"fx": 500, "fy": 500, "cx": 320, "cy": 240, "width": 640, "height": 480},
                                "distortion": [0.1, -0.2, 0, 0], "imu_from_camera": np.eye(4).tolist()}))
    calibration = session.read_calibration(path)
    assert calibration.camera.width == 640 and calibration.distortion == (0.1, -0.2, 0.0, 0.0)
    np.testing.assert_array_equal(calibration.imu_from_camera, np.eye(4))


def test_a_pose_within_a_microsecond_is_the_frame_own_even_across_a_long_gap():
    poses = np.array([turned(0, "y"), turned(90, "y", (1.0, 0, 0))])
    trajectory = TYPES.Trajectory("t", np.array([1_000, 500_000_000]), poses)
    np.testing.assert_array_equal(session.pose_at(trajectory, 1_400), poses[0])
    np.testing.assert_array_equal(session.pose_at(trajectory, 499_999_200), poses[1])
    assert session.pose_at(trajectory, 3_000) is None  # 0.5 s between poses
