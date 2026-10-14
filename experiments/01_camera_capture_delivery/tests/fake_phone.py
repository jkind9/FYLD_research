"""A stand-in for the capture app in tests: builds phone session v2 messages and sends them as Uploader.java does.

Also used by experiments/open_vio/tests and src/live/tests to write synthetic v2 session folders.
"""

from __future__ import annotations

import json
import socket
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

HOST = Path(__file__).resolve().parents[1] / "host"
sys.path.insert(0, str(HOST))
import capture_receiver  # noqa: E402
import protocol  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[1] / "capture" / "app" / "src" / "test" / "resources" / "session_v2"
SESSION = "20261014_201500_walk"
JPEG = b"\xff\xd8\xff\xd9"
CAMERA = {"exposure_ns": 8_000_000, "frame_duration_ns": 33_333_333, "rolling_shutter_skew_ns": 20_000_000,
          "focus_distance_dpt": 0.5, "iso": 400, "ois_mode": 0}
K = [400.0, 400.0, 320.0, 240.0]


def fixture(name: str):
    path = FIXTURE / name
    return json.loads(path.read_text(encoding="utf-8")) if name.endswith(".json") else path.read_bytes()


def info(kind: str = "walk", start_ns: int = 5_000_100_000_000) -> dict:
    out = json.loads(json.dumps(fixture("hello.json")["info"]))
    out["kind"] = kind
    out["clock"]["start"]["elapsed_realtime_ns"] = start_ns
    if kind == "imu_only":
        out["camera"] = out["arcore"] = None
    return out


def hello(session: str = SESSION, session_info: dict | None = None, wall_ms: int = 1_760_449_990_000) -> dict:
    return {"type": "hello", "version": 2, "session": session, "wall_ms": wall_ms, "info": session_info or info()}


def _queued(kind: str, session: str, **fields) -> dict:
    return {"type": kind, "version": 2, "session": session, "n": -1, **fields}


def arcore(t_ns: int, pose=None, *, tracking: str = "TRACKING", **extra) -> dict:
    pose = list(pose) if pose is not None else ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0] if tracking == "TRACKING" else None)
    return {"t_ns": t_ns, "tracking": tracking, "failure": "NONE" if tracking == "TRACKING" else "INSUFFICIENT_FEATURES",
            "pose": pose, "device_pose": pose, "intrinsics": K, "texture_intrinsics": [500.0, 500.0, 960.0, 540.0],
            "points": [], "anchors": [], **extra}


def frame(seq: int, camera_t_ns: int, grey: np.ndarray, *, record: dict | None = None, camera: dict | None = CAMERA,
          colour: bytes = JPEG, encoding: str = "raw", depth: bytes = b"", session: str = SESSION) -> tuple[dict, bytes]:
    h, w = grey.shape
    packed = grey.tobytes() if encoding == "raw" else zlib.compress(grey.tobytes(), 1)
    header = _queued("frame", session, seq=seq, camera_t_ns=camera_t_ns, wall_ms=1_760_450_000_000 + seq * 33,
                     camera=camera, grey={"width": w, "height": h, "encoding": encoding, "bytes": len(packed)},
                     colour={"format": "jpeg", "width": w, "height": h, "quality": 90, "bytes": len(colour)}, arcore=record)
    return header, packed + colour + depth


def imu(rows, session: str = SESSION) -> tuple[dict, bytes]:
    """rows: (t_ns, sensor 0 gyro / 1 accel, x, y, z, bx, by, bz)."""
    return _queued("imu", session, samples=len(rows)), b"".join(struct.pack("<qi6f", *row) for row in rows)


def telemetry(session: str = SESSION, **fields) -> tuple[dict, bytes]:
    values = {k: v for k, v in fixture("telemetry.json").items() if k not in ("type", "version", "session", "n")}
    return _queued("telemetry", session, **(values | fields)), b""


def end(session: str = SESSION, *, end_ns: int = 5_000_300_000_000, wall_ms: int = 1_760_450_100_000, **counts) -> tuple[dict, bytes]:
    clock = {"end": {"elapsed_realtime_ns": end_ns, "nano_time_ns": 0, "wall_ms": wall_ms}}
    return _queued("end", session, reason="stop", clock=clock, counts=counts or {"frames": 0}), b""


def numbered(messages) -> list[tuple[dict, bytes]]:
    """Gives queued messages their message numbers in order, as DiskQueue.add does."""
    return [(header | {"n": n}, payload) for n, (header, payload) in enumerate(messages)]


def walk(frames: int = 12, *, size=(4, 3), start_ns: int = 5_000_100_000_000) -> list[tuple[dict, bytes]]:
    """A short numbered walk: frames at 30 fps with ARCore records, an IMU batch every 3 frames, telemetry, end."""
    w, h = size
    out = []
    for seq in range(frames):
        t = start_ns + 10_000_000 + seq * 33_333_333
        grey = (np.arange(w * h, dtype=np.int64).reshape(h, w) + seq).astype(np.uint8)
        out.append(frame(seq, t, grey, record=arcore(t + 7, [0.01 * seq, 0, 0, 0, 0, 0, 1])))
        if seq % 3 == 2:
            out.append(imu([(t + k * 2_500_000, k % 2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0) for k in range(8)]))
        if seq == frames // 2:
            out.append(telemetry())
    out.append(end(frames=frames))
    return numbered(out)


class FakePhone:
    """Sends numbered messages over TCP with a window and cumulative acknowledgements, resuming where the PC says."""

    def __init__(self, messages, session: str = SESSION, session_info: dict | None = None, window: int = 64):
        self.messages = messages
        self.hello = hello(session, session_info)
        self.window = window

    def send(self, port: int, *, cut_after: int | None = None, start: int | None = None) -> int:
        """One connection. cut_after: close abruptly once message n is sent. start: ignore the PC's resume point
        (a phone that lost track of its acknowledgements). Returns the PC's last acknowledgement."""
        with socket.create_connection(("127.0.0.1", port), timeout=10) as connection, connection.makefile("rwb") as stream:
            protocol.write_message(stream, self.hello)
            stream.flush()
            reply, _ = protocol.read_message(stream)
            if reply["type"] == "error":
                raise ConnectionRefusedError(reply["message"])
            through = reply["through"]
            following = through + 1 if start is None else start
            for header, payload in self.messages[following:]:
                protocol.write_message(stream, header, payload)
                stream.flush()
                if header["n"] == cut_after:
                    connection.shutdown(socket.SHUT_RDWR)
                    return through
                while header["n"] - through >= self.window:
                    through = self._ack(stream)
            while through < self.messages[-1][0]["n"]:
                through = self._ack(stream)
            return through

    @staticmethod
    def _ack(stream) -> int:
        reply, _ = protocol.read_message(stream)
        if reply["type"] == "error":
            raise ConnectionRefusedError(reply["message"])
        return reply["through"]


def write_session(root: Path, messages, *, session: str = SESSION, session_info: dict | None = None) -> Path:
    """Stores numbered messages under one session id through the receiver's session store, without a network."""
    store = capture_receiver.Session.open(Path(root), hello(session, session_info), host_ms=1_760_449_990_005)
    for header, payload in messages:
        store.store(header | {"session": session}, payload, host_ms=1_760_450_000_000 + header["n"])
    return store.folder
