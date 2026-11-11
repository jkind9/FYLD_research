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
