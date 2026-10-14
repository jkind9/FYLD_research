"""Phone session v1 (phone_session_v1.md): the shared fixture parses to known values; bad frames are refused."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))
import session_v1

FIXTURE = ROOT / "tests" / "fixtures" / "session_v1"


def fixture():
    return json.loads((FIXTURE / "frame_header.json").read_text(encoding="utf-8")), (FIXTURE / "frame_payload.bin").read_bytes()


def test_fixture_parses_to_the_written_values():
    frame = session_v1.parse_frame(*fixture())
    assert (frame.seq, frame.t_ns, frame.tracking, frame.failure) == (7, 123456789000, "TRACKING", "NONE")
    assert frame.image_jpeg == b"\xff\xd8\xff\xd9" and frame.image_size == (640, 480)
    assert frame.intrinsics == (400.0, 400.0, 320.0, 240.0)
    assert frame.point_ids.tolist() == [11, 12]
    assert frame.points_pixel.tolist() == [[370.0, 265.0], [120.0, 140.0]]
    assert frame.points_confidence.tolist() == [0.5, 0.25]
    assert frame.depth.depth_m.shape == (3, 4)
    assert frame.depth.depth_m[0].tolist() == [0.0, 1.0, 1.25, 1.5]
    assert frame.depth.depth_m[2, 3] == 4.0
    assert frame.depth.confidence[0].tolist() == [0, 255, 128, 200]
    assert frame.depth.intrinsics == (2.5, 2.5, 2.0, 1.5) and frame.depth.t_ns == 123456700000
    assert frame.anchor_created[0] == 3
    assert list(frame.anchor_updates) == [1] and frame.anchor_updates[1][2] == 0.0625


def test_fixture_pose_in_opencv_axes_sees_points_in_front_at_their_pixels():
    frame = session_v1.parse_frame(*fixture())
    camera_from_world = np.linalg.inv(session_v1.world_from_camera_cv(frame.pose))
    in_camera = (camera_from_world[:3, :3] @ frame.points_world.T).T + camera_from_world[:3, 3]
    assert (in_camera[:, 2] > 0).all()
    fx, fy, cx, cy = frame.intrinsics
    pixels = np.c_[fx * in_camera[:, 0] / in_camera[:, 2] + cx, fy * in_camera[:, 1] / in_camera[:, 2] + cy]
    assert np.allclose(pixels, frame.points_pixel)


def test_frame_without_depth_or_anchors_needs_only_the_image():
    header, payload = fixture()
    for key in ("depth", "anchor"):
        del header[key]
    header["anchors"] = []
    frame = session_v1.parse_frame(header, payload[:4])
    assert frame.depth is None and frame.anchor_created is None and frame.anchor_updates == {}


def test_lost_tracking_frame_has_no_pose_and_no_points():
    header, payload = fixture()
    header.update(tracking="PAUSED", failure="INSUFFICIENT_FEATURES", pose=None, points=[], anchors=[])
    del header["anchor"]
    frame = session_v1.parse_frame(header, payload)
    assert frame.pose is None and frame.failure == "INSUFFICIENT_FEATURES" and len(frame.point_ids) == 0


def _payload_too_long(h, p):
    return h, p + b"\x00"


def _wrong_version(h, p):
    h["version"] = 2
    return h, p


def _tracking_without_pose(h, p):
    h["pose"] = None
    return h, p


def _pose_while_paused(h, p):
    h.update(tracking="PAUSED", points=[])
    return h, p


def _quaternion_not_unit(h, p):
    h["pose"] = [0, 0, 0, 0, 0, 0, 2]
    return h, p


def _not_jpeg(h, p):
    return h, b"\x00\x00" + p[2:]


def _depth_size_mismatch(h, p):
    h["depth"]["width"] = 5
    return h, p


def _point_pixel_off(h, p):
    h["points"][0][4] += 5.0
    return h, p


def _point_too_short(h, p):
    h["points"][0] = h["points"][0][:6]
    return h, p


@pytest.mark.parametrize("break_frame", [_payload_too_long, _wrong_version, _tracking_without_pose, _pose_while_paused,
                                         _quaternion_not_unit, _not_jpeg, _depth_size_mismatch, _point_pixel_off,
                                         _point_too_short])
def test_bad_frames_are_refused(break_frame):
    header, payload = fixture()
    with pytest.raises(ValueError):
        session_v1.parse_frame(*break_frame(copy.deepcopy(header), payload))


def test_session_start_needs_version_1():
    session_v1.check_session({"type": "session", "version": 1, "device": {"model": "2201116TG"}, "started_ms": 1})
    with pytest.raises(ValueError):
        session_v1.check_session({"type": "session", "version": 2, "device": {}, "started_ms": 1})


def test_anchor_correction_moves_a_frame_with_its_keyframe():
    created = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    moved = [0.0, 0.0, 0.0625, 0.0, 0.0, 0.0, 1.0]
    frame_pose = [1.0, 2.0, 3.0, 0.5, 0.5, 0.5, 0.5]
    corrected = session_v1.corrected_world_from_camera(frame_pose, created, moved)
    assert np.allclose(corrected[:3, 3], [1.0, 2.0, 3.0625])
    assert np.allclose(corrected[:3, :3], session_v1.world_from_camera(frame_pose)[:3, :3])
