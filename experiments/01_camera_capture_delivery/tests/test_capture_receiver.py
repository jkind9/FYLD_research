"""The PC capture receiver: windowed, acknowledged, resumable delivery into one session folder."""

import json
import queue
import socket
import threading

import numpy as np
import pytest
from PIL import Image

import capture_receiver
import fake_phone
import protocol


@pytest.fixture
def receiver(tmp_path):
    frames = []
    server = capture_receiver.Receiver(tmp_path / "out", port=0, on_frame=lambda f, path: frames.append((f.seq, path)))
    server.start()
    server.delivered = frames
    yield server
    server.close()


def _lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_dropped_connection_resumes_with_no_missing_or_repeated_frames(receiver):
    messages = fake_phone.walk(40)
    phone = fake_phone.FakePhone(messages, window=8)
    phone.send(receiver.port, cut_after=25)
    assert phone.send(receiver.port) == messages[-1][0]["n"]
    folder = receiver.wait(timeout=10)
    frames = _lines(folder / "frames.jsonl")
    assert [f["seq"] for f in frames] == list(range(40))
    assert sorted(p.name for p in (folder / "cam0").iterdir()) == [f"{s:06d}.png" for s in range(40)]
    assert len(list((folder / "frames").glob("*.jpg"))) == 40
    grey = np.asarray(Image.open(folder / "cam0" / "000005.png"))
    assert grey.shape == (3, 4) and grey[0, 0] == 5
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["frames"] == 40 and summary["missing_seq"] == [] and summary["connections"] == 2
    assert [seq for seq, _ in receiver.delivered] == list(range(40))
    assert receiver.delivered[3][1] == folder / "frames" / "000003.jpg"


def test_resent_messages_are_acknowledged_but_not_stored_twice(receiver):
    messages = fake_phone.walk(10)
    phone = fake_phone.FakePhone(messages)
    phone.send(receiver.port, cut_after=8)
    phone.send(receiver.port, start=0)  # resends everything, ignoring the PC's resume point
    folder = receiver.wait(timeout=10)
    assert [f["seq"] for f in _lines(folder / "frames.jsonl")] == list(range(10))
    assert [m["n"] for m in _lines(folder / "messages.jsonl")] == list(range(len(messages)))


def _refusal(port, messages):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as c, c.makefile("rwb") as stream:
        protocol.write_message(stream, fake_phone.hello())
        stream.flush()
        assert protocol.read_message(stream)[0] == {"type": "ack", "session": fake_phone.SESSION, "through": -1}
        for header, payload in messages:
            protocol.write_message(stream, header, payload)
            stream.flush()
        replies = []
        while (message := protocol.read_message(stream)) is not None:
            replies.append(message[0])
        return replies


def test_a_gap_in_message_numbers_is_refused(receiver):
    messages = fake_phone.walk(4)
    replies = _refusal(receiver.port, [messages[0], messages[2]])
    assert replies[0]["through"] == 0 and replies[-1]["type"] == "error" and "gap" in replies[-1]["message"]


def test_a_bad_frame_is_refused_and_not_stored(receiver):
    header, payload = fake_phone.walk(1)[0]
    replies = _refusal(receiver.port, [(header, payload + b"\x00")])
    assert [r["type"] for r in replies] == ["error"]
    folder = receiver.root / fake_phone.SESSION
    assert not (folder / "frames.jsonl").exists() and not list((folder / "cam0").glob("*.png"))


def test_speed_check_and_report_connections(receiver):
    with socket.create_connection(("127.0.0.1", receiver.port), timeout=5) as c, c.makefile("rwb") as stream:
        for chunk in range(3):
            protocol.write_message(stream, {"type": "speed", "chunk": chunk, "chunks": 3}, b"\x00" * 1000)
        stream.flush()
        answer = protocol.read_message(stream)[0]
    assert answer["type"] == "speed" and answer["bytes"] == 3000 and answer["seconds"] >= 0
    with socket.create_connection(("127.0.0.1", receiver.port), timeout=5) as c, c.makefile("rwb") as stream:
        protocol.write_message(stream, {"type": "report", "schema": 1}, b'{"schema": 1, "device": {"model": "2201116TG"}}')
        stream.flush()
    receiver.wait_reports(1, timeout=5)
    assert json.loads(next((receiver.root / "reports").iterdir()).read_text())["schema"] == 1


def test_summary_reports_imu_rates_clock_base_rate_and_sending_after_stop(tmp_path):
    rows = [(5_000_100_000_000 + k * 2_500_000, 0, 0.1, 0, 0, 0, 0, 0) for k in range(400)]
    rows += [(5_000_100_000_000 + k * 5_000_000, 1, 0, 9.8, 0, 0, 0, 0) for k in range(200)]
    rows.sort()
    messages = fake_phone.numbered([fake_phone.imu(rows), fake_phone.end(wall_ms=1_760_450_000_000)])
    store = capture_receiver.Session.open(tmp_path, fake_phone.hello(wall_ms=1_760_449_990_000), host_ms=1_760_449_990_250)
    store.store(*messages[0], host_ms=1_760_449_991_000)
    store.store(*messages[1], host_ms=1_760_450_003_250)  # 3 s after Stop on the PC clock (offset +250 ms)
    summary = json.loads((store.folder / "summary.json").read_text())
    assert summary["imu"]["gyro"]["rate_hz"] == pytest.approx(400) and summary["imu"]["accel"]["rate_hz"] == pytest.approx(200)
    assert summary["imu"]["gyro"]["gaps_over_1_5x"] == 0
    assert summary["clock_base"]["same_clock_base"] is True
    assert summary["sending_after_stop_s"] == pytest.approx(3.0)
    assert summary["phone_to_pc_clock_offset_ms"] == pytest.approx(250)
    assert summary["megabytes_per_second"] > 0
    lines = (store.folder / "imu.csv").read_text().splitlines()
    assert lines[0] == "sensor,t_ns,x,y,z,bx,by,bz" and len(lines) == 601 and lines[1].startswith("gyro,5000100000000,")


@pytest.mark.parametrize("kind", ["frame", "imu", "telemetry"])
@pytest.mark.parametrize("partial_commit", [False, True])
@pytest.mark.parametrize("prefix", [False, True])
def test_restart_discards_uncommitted_rows_before_resending(tmp_path, monkeypatch, kind, partial_commit, prefix):
    messages = fake_phone.walk(3)
    header, payload = next(m for m in messages if m[0]["type"] == kind)
    header = header | {"n": int(prefix), **({"seq": int(prefix)} if kind == "frame" else {})}
    store = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=1)
    if prefix:
        store.store(*messages[0], host_ms=1)
    append = capture_receiver._append

    def interrupted(path, line):
        if path.name == "messages.jsonl":
            if partial_commit:
                with open(path, "ab") as stream:
                    stream.write(line[:10].encode("utf-8"))
            raise OSError("interrupted commit")
        append(path, line)

    with monkeypatch.context() as patch:
        patch.setattr(capture_receiver, "_append", interrupted)
        with pytest.raises(OSError, match="interrupted commit"):
            store.store(header, payload, host_ms=2)
    reopened = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=3)
    assert reopened.through == int(prefix) - 1
    reopened.store(header, payload, host_ms=4)
    filename = {"frame": "frames.jsonl", "imu": "imu.csv", "telemetry": "telemetry.jsonl"}[kind]
    lines = (reopened.folder / filename).read_text().splitlines()
    assert len(lines) == (header["samples"] + 1 if kind == "imu" else 1 + int(prefix and kind == "frame"))
    assert len(_lines(reopened.folder / "messages.jsonl")) == 1 + int(prefix)


def test_restart_preserves_committed_rows_and_imu_order(tmp_path):
    rows = [(5_000_100_000_000, 0, 1, 0, 0, 0, 0, 0)]
    first = fake_phone.numbered([fake_phone.imu(rows)])[0]
    store = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=1)
    store.store(*first, host_ms=2)
    reopened = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=3)
    earlier = [(rows[0][0] - 1, *rows[0][1:])]
    header, payload = fake_phone.imu(earlier)
    with pytest.raises(ValueError, match="backwards"):
        reopened.store(header | {"n": 1}, payload, host_ms=4)
    assert len((reopened.folder / "imu.csv").read_text().splitlines()) == 2


def test_completion_is_published_after_end_ack_is_flushed(receiver, monkeypatch):
    replies, completed = [], []
    reply, put = capture_receiver._reply, receiver.finished.put

    def replied(stream, header):
        reply(stream, header)
        replies.append(header)

    def finished(folder):
        completed.append(replies[-1]["through"])
        put(folder)

    monkeypatch.setattr(capture_receiver, "_reply", replied)
    monkeypatch.setattr(receiver.finished, "put", finished)
    messages = fake_phone.walk(1)
    fake_phone.FakePhone(messages).send(receiver.port)
    receiver.wait(timeout=5)
    assert completed == [messages[-1][0]["n"]]


def test_restart_recovers_committed_end_before_metadata_was_saved(tmp_path, monkeypatch):
    store = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=1)
    header, payload = fake_phone.numbered([fake_phone.end(frames=0)])[0]

    def interrupted():
        raise OSError("interrupted metadata save")

    monkeypatch.setattr(store, "_save_info", interrupted)
    with pytest.raises(OSError, match="interrupted metadata save"):
        store.store(header, payload, host_ms=2)
    reopened = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=3)
    assert reopened.ended and reopened.through == 0
    info = json.loads((reopened.folder / "session.json").read_text())
    assert info["clock"]["end"] == header["clock"]["end"] and info["counts"] == {"frames": 0}
    assert json.loads((reopened.folder / "summary.json").read_text())["end_reason"] == "stop"
    telemetry, payload = fake_phone.telemetry()
    with pytest.raises(ValueError, match="already ended"):
        reopened.store(telemetry | {"n": 1}, payload, host_ms=4)


def test_reconnecting_completed_session_reports_completion_once(receiver):
    messages = fake_phone.walk(1)
    folder = fake_phone.write_session(receiver.root, messages)
    phone = fake_phone.FakePhone(messages)
    assert phone.send(receiver.port) == messages[-1][0]["n"]
    assert receiver.wait(timeout=2) == folder
    phone.send(receiver.port)
    with pytest.raises(queue.Empty):
        receiver.wait(timeout=0.1)


def test_transient_commit_error_allows_resend_without_receiver_restart(tmp_path, monkeypatch):
    store = capture_receiver.Session.open(tmp_path, fake_phone.hello(), host_ms=1)
    message = fake_phone.walk(1)[0]
    append = capture_receiver._append

    def interrupted(path, line):
        if path.name == "messages.jsonl":
            raise OSError("temporary storage error")
        append(path, line)

    with monkeypatch.context() as patch:
        patch.setattr(capture_receiver, "_append", interrupted)
        with pytest.raises(OSError, match="temporary storage error"):
            store.store(*message, host_ms=2)
    store.store(*message, host_ms=3)
    assert [row["seq"] for row in _lines(store.folder / "frames.jsonl")] == [0]
