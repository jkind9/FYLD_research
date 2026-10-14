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


def test_receiver_saves_frames_and_acknowledges_in_order(tmp_path):
    server = receiver.Receiver(tmp_path, port=0)
    worker = threading.Thread(target=server.serve_one, daemon=True)
    worker.start()
    acks = []
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as client, client.makefile("rwb") as stream:
        for seq in range(5):
            protocol.write_message(stream, {"type": "frame", "seq": seq, "pose": [0, 0, 0, 0, 0, 0, 1]}, b"\xff\xd8" + bytes([seq]))
            stream.flush()
            acks.append(protocol.read_ack(stream))
        protocol.write_message(stream, {"type": "report", "schema": 1}, json.dumps({"checks": []}).encode())
        stream.flush()
    worker.join(timeout=5)
    session = next(tmp_path.iterdir())
    assert acks == [0, 1, 2, 3, 4]
    assert len(list((session / "frames").glob("*.jpg"))) == 5
    assert len((session / "frames.jsonl").read_text().splitlines()) == 5
    assert (session / "report.json").is_file()
    assert server.summary["frames"] == 5


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
