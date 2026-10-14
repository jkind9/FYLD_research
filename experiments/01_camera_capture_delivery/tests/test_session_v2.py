"""Phone session v2: the shared fixture parses to its written values, and bad messages are refused."""

import copy
import struct
import zlib

import numpy as np
import pytest

import fake_phone
import session_v2
from fake_phone import fixture


def frame_fixture():
    return copy.deepcopy(fixture("frame.json")), fixture("frame.bin")


def test_fixture_frame_parses_to_its_values():
    frame = session_v2.parse_frame(*frame_fixture())
    assert (frame.n, frame.seq, frame.camera_t_ns, frame.wall_ms) == (12, 7, 5000123456789, 1760450000000)
    assert frame.t_ns == frame.camera_t_ns and frame.arcore_t_ns == 123456789000
    assert frame.camera == fake_phone.CAMERA
    assert frame.grey.shape == (3, 4) and frame.grey[1, 0] == 80 and frame.grey.dtype == np.uint8
    assert frame.image_jpeg == b"\xff\xd8\xff\xd9" and frame.image_size == (4, 3)
    assert frame.tracking == "TRACKING" and frame.pose == (0.5, 1.25, -2.0, 0.5, 0.5, 0.5, 0.5)
    assert frame.device_pose == (0.5, 1.25, -2.0, 0.0, 0.0, 0.0, 1.0)
    assert frame.texture_intrinsics == (500.0, 500.0, 960.0, 540.0)
    assert list(frame.point_ids) == [11, 12] and np.allclose(frame.points_pixel[0], [370, 265])
    assert frame.depth.depth_m.shape == (3, 4) and frame.depth.depth_m[0, 1] == 1.0 and frame.depth.confidence[0, 2] == 128
    assert frame.anchor_created == (3, (0.5, 1.25, -2.0, 0.5, 0.5, 0.5, 0.5))
    assert frame.anchor_updates == {1: (0.0, 0.0, 0.0625, 0.0, 0.0, 0.0, 1.0)}


def test_fixture_imu_telemetry_end_and_hello_parse():
    batch = session_v2.parse_imu(fixture("imu.json"), fixture("imu.bin"))
    assert list(batch.t_ns) == [5000120000000, 5000121250000, 5000122500000] and list(batch.sensor) == [0, 1, 0]
    assert np.allclose(batch.values[1], [0.0, 9.75, -0.5]) and np.allclose(batch.bias[0], [0.0078125, 0.0, -0.0078125])
    assert session_v2.check_telemetry(fixture("telemetry.json"))["queue_frames"] == 42
    assert session_v2.check_end(fixture("end.json"))["counts"]["frames"] == 214
    assert session_v2.check_hello(fixture("hello.json"))["info"]["kind"] == "walk"


def test_deflated_grey_reads_back_exactly():
    grey = (np.arange(48 * 8) % 251).astype(np.uint8).reshape(8, 48)
    header, payload = fake_phone.frame(0, 1, grey, encoding="deflate")
    assert header["grey"]["bytes"] < grey.size
    assert np.array_equal(session_v2.parse_frame(header | {"n": 0}, payload).grey, grey)


def test_frame_without_arcore_record_has_no_pose():
    header, payload = fake_phone.frame(0, 99, np.zeros((3, 4), np.uint8), camera=None)
    frame = session_v2.parse_frame(header | {"n": 0}, payload)
    assert frame.pose is None and frame.arcore_t_ns is None and frame.camera is None and frame.t_ns == 99


def _broken(change):
    header, payload = frame_fixture()
    payload = change(header, payload) or payload
    return header, payload


BAD_FRAMES = {
    "version": lambda h, p: h.update(version=1),
    "grey size": lambda h, p: h["grey"].update(width=5),
    "grey encoding": lambda h, p: h["grey"].update(encoding="png"),
    "deflate size": lambda h, p: (h["grey"].update(encoding="deflate", bytes=len(zlib.compress(p[:11]))),
                                  zlib.compress(p[:11]) + p[12:])[1],
    "colour not jpeg": lambda h, p: p[:12] + b"\x00\x00" + p[14:],
    "colour size": lambda h, p: h["colour"].update(height=4),
    "payload length": lambda h, p: p + b"\x00",
    "pose while lost": lambda h, p: h["arcore"].update(tracking="PAUSED"),
    "device pose while lost": lambda h, p: h["arcore"].update(tracking="PAUSED", pose=None, points=[], anchor=None),
    "point off projection": lambda h, p: h["arcore"]["points"][0].__setitem__(4, 372.0),
    "depth size": lambda h, p: h["arcore"]["depth"].update(width=5),
    "camera field": lambda h, p: h["camera"].pop("iso"),
    "seq": lambda h, p: h.update(seq=-1),
}


@pytest.mark.parametrize("name", BAD_FRAMES)
def test_bad_frames_are_refused(name):
    header, payload = _broken(BAD_FRAMES[name])
    if header["arcore"].get("anchor", 0) is None:
        del header["arcore"]["anchor"]
    with pytest.raises(ValueError):
        session_v2.parse_frame(header, payload)


@pytest.mark.parametrize("change", [
    lambda h, p: (h, p + b"\x00"),
    lambda h, p: (h, struct.pack("<qi6f", 1, 2, 0, 0, 0, 0, 0, 0) + p[36:]),
    lambda h, p: (h, p[:72] + struct.pack("<qi6f", 5000110000000, 0, 0, 0, 0, 0, 0, 0)),
])
def test_bad_imu_batches_are_refused(change):
    header, payload = change(dict(fixture("imu.json")), fixture("imu.bin"))
    with pytest.raises(ValueError):
        session_v2.parse_imu(header, payload)


def test_missing_fields_and_bad_session_ids_are_refused():
    telemetry = dict(fixture("telemetry.json"))
    del telemetry["free_bytes"]
    end = dict(fixture("end.json"))
    del end["counts"]
    hello = copy.deepcopy(fixture("hello.json"))
    hello["session"] = "../escape"
    no_clock = copy.deepcopy(fixture("hello.json"))
    del no_clock["info"]["clock"]
    for check, header in ((session_v2.check_telemetry, telemetry), (session_v2.check_end, end),
                          (session_v2.check_hello, hello), (session_v2.check_hello, no_clock)):
        with pytest.raises(ValueError):
            check(header)


def test_read_session_reads_a_saved_folder(tmp_path):
    folder = fake_phone.write_session(tmp_path, fake_phone.walk(6))
    frames = list(session_v2.read_session(folder))
    assert [f.seq for f in frames] == list(range(6))
    assert frames[2].grey[0, 0] == 2 and frames[2].pose[0] == pytest.approx(0.02)
    assert frames[0].image_jpeg == fake_phone.JPEG
