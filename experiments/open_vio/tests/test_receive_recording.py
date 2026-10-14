"""The Wi-Fi upload receiver: files arrive whole, are checked by SHA-256, and are acknowledged."""

import hashlib
import json
import socket
import threading

import pytest

import receive_recording  # puts experiment 01's host folder, which holds protocol, on the import path
import protocol


def _send_file(stream, seq, path, data, *, digest=None):
    header = {"type": "file", "seq": seq, "recording": "rec_1", "path": path, "size": len(data),
              "sha256": digest or hashlib.sha256(data).hexdigest()}
    protocol.write_message(stream, header, data)
    stream.flush()


def _serve(tmp_path):
    server = receive_recording.Receiver(tmp_path, port=0)
    result = {}
    worker = threading.Thread(target=lambda: result.update(folder=server.serve_one()), daemon=True)
    worker.start()
    return server, worker, result


def test_files_are_saved_checked_and_acknowledged(tmp_path):
    server, worker, result = _serve(tmp_path)
    files = {"meta.json": b'{"schema": 1}', "cam0/123.pgm": b"P5\n1 1\n255\n\x07", "gyro.csv": b"t_ns,x\n1,2\n"}
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as client, client.makefile("rwb") as stream:
        for seq, (path, data) in enumerate(files.items()):
            _send_file(stream, seq, path, data)
            assert protocol.read_ack(stream) == seq
        protocol.write_message(stream, {"type": "done", "recording": "rec_1", "files": 3})
        stream.flush()
    worker.join(5)
    folder = result["folder"]
    assert folder == tmp_path / "rec_1"
    for path, data in files.items():
        assert (folder / path).read_bytes() == data
    summary = json.loads((folder / "received.json").read_text())
    assert summary["files"] == 3 and summary["complete"] is True


def test_corrupted_file_is_refused_and_the_connection_closed(tmp_path):
    server, worker, result = _serve(tmp_path)
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as client, client.makefile("rwb") as stream:
        _send_file(stream, 0, "gyro.csv", b"t_ns,x\n1,2\n", digest="0" * 64)
        with pytest.raises(EOFError):
            protocol.read_ack(stream)
    worker.join(5)
    assert not (tmp_path / "rec_1" / "gyro.csv").exists()
    assert json.loads((tmp_path / "rec_1" / "received.json").read_text())["complete"] is False


@pytest.mark.parametrize("path", ["../escape.csv", "/abs.csv", "cam0/../../x"])
def test_paths_outside_the_recording_are_refused(tmp_path, path):
    server, worker, _ = _serve(tmp_path / "out")
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as client, client.makefile("rwb") as stream:
        _send_file(stream, 0, path, b"x")
        with pytest.raises(EOFError):
            protocol.read_ack(stream)
    worker.join(5)
    assert not any(p.is_file() and p.name != "received.json" for p in tmp_path.rglob("*"))
