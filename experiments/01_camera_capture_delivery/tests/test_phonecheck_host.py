"""Host side of the Redmi check app: message framing, the frame receiver and the report check."""

import io
import json
import socket
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
import protocol
import receiver
import report
import session_v1

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "session_v1"


def test_message_round_trip():
    stream = io.BytesIO()
    protocol.write_message(stream, {"type": "frame", "seq": 3}, b"\xff\xd8jpeg")
    stream.seek(0)
    header, payload = protocol.read_message(stream)
    assert header == {"type": "frame", "seq": 3} and payload == b"\xff\xd8jpeg"


def test_truncated_message_raises():
    stream = io.BytesIO()
    protocol.write_message(stream, {"type": "frame", "seq": 1}, b"0123456789")
    cut = io.BytesIO(stream.getvalue()[:-4])
    with pytest.raises(EOFError):
        protocol.read_message(cut)


def stream_to_receiver(server, messages):
    """Sends (header, payload) messages over loopback; returns the acknowledgements for frames."""
    worker = threading.Thread(target=server.serve_one, daemon=True)
    worker.start()
    acks = []
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as client, client.makefile("rwb") as stream:
        for header, payload in messages:
            protocol.write_message(stream, header, payload)
            stream.flush()
            if header["type"] == "frame":
                acks.append(protocol.read_ack(stream))
    worker.join(timeout=5)
    return acks


def v1_frames(count):
    header, payload = json.loads((FIXTURE / "frame_header.json").read_text()), (FIXTURE / "frame_payload.bin").read_bytes()
    frames = []
    for seq in range(count):
        h = json.loads(json.dumps(header)) | {"seq": seq}
        if seq % 2:  # odd frames carry no new depth
            del h["depth"]
            frames.append((h, payload[:4]))
        else:
            frames.append((h, payload))
    return frames


SESSION = {"type": "session", "version": 1, "device": {"model": "2201116TG"}, "started_ms": 1}


def test_receiver_saves_v1_frames_and_acknowledges_in_order(tmp_path):
    server = receiver.Receiver(tmp_path, port=0)
    frames = v1_frames(5)
    acks = stream_to_receiver(server, [(SESSION, b"")] + frames)
    session = next(tmp_path.iterdir())
    assert acks == [0, 1, 2, 3, 4]
    assert len(list((session / "frames").glob("*.jpg"))) == 5
    assert len(list((session / "depth").glob("*.bin"))) == 3
    assert json.loads((session / "session.json").read_text())["version"] == 1
    assert server.summary["frames"] == 5 and server.summary["depth_frames"] == 3
    saved = list(session_v1.read_session(session))
    assert [f.seq for f in saved] == [0, 1, 2, 3, 4]
    assert saved[0].depth.depth_m[0, 1] == 1.0 and saved[1].depth is None


def test_receiver_hands_each_saved_frame_to_the_callback(tmp_path):
    seen = []
    server = receiver.Receiver(tmp_path, port=0, on_frame=lambda frame, image: seen.append((frame.seq, image.is_file())))
    stream_to_receiver(server, [(SESSION, b"")] + v1_frames(3))
    assert seen == [(0, True), (1, True), (2, True)]


def test_receiver_saves_a_report_sent_alone(tmp_path):
    server = receiver.Receiver(tmp_path, port=0)
    stream_to_receiver(server, [({"type": "report", "schema": 1}, json.dumps({"checks": []}).encode())])
    assert (next(tmp_path.iterdir()) / "report.json").is_file()


def test_receiver_refuses_frames_before_the_session_start(tmp_path):
    server = receiver.Receiver(tmp_path, port=0)
    with pytest.raises(ValueError):
        with socket.create_connection(("127.0.0.1", server.port), timeout=5) as client, client.makefile("rwb") as stream:
            protocol.write_message(stream, *v1_frames(1)[0])
            stream.flush()
            server.serve_one()


def valid_report():
    return {"schema": 1, "device": {"model": "2201116TG"},
            "checks": [{"name": "arcore_available", "status": "PASS", "reason": "", "detail": {}},
                       {"name": "raw_depth", "status": "SKIPPED", "reason": "not supported", "detail": {}}]}


def test_report_check_accepts_a_valid_report_and_summarises_it():
    assert report.summarise(report.validate(valid_report())) == {"PASS": 1, "FAIL": 0, "SKIPPED": 1}


@pytest.mark.parametrize("change", [
    lambda r: r["checks"][0].update(status="MAYBE"),
    lambda r: r["checks"][1].update(reason=""),
    lambda r: r.update(schema=2),
])
def test_report_check_rejects_bad_reports(change):
    bad = valid_report()
    change(bad)
    with pytest.raises(ValueError):
        report.validate(bad)
