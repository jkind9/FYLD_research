"""Receive phone session v2 from the capture app: store every message, acknowledge it, resume after a dropped connection.

    python experiments/01_camera_capture_delivery/host/capture_receiver.py --out <dir> [--port 8766]

Messages follow phone_session_v2.md and use protocol.py framing. Each session becomes <out>/<session id>/ with
session.json, frames.jsonl, cam0/<seq>.png, frames/<seq>.jpg, depth/<seq>.bin, imu.csv, telemetry.jsonl,
messages.jsonl, and summary.json once the end message arrives. A bad message is answered with an error and
the connection is closed; a resent message is acknowledged and not stored again. Link-speed checks and check
reports arrive on their own connections (reports go to <out>/reports/).
The link has no authentication or encryption: local network only. Allow the port through the Windows
firewall for private networks the first time.
"""

from __future__ import annotations

import argparse
import json
import queue
import socket
import threading
import time
from pathlib import Path

from PIL import Image

import protocol
import session_v2
from session_v1 import _require

PORT = 8766
TIMEOUT_S = 20
CLOCK_BASE_TOLERANCE_NS = 10**9
REFUSED = (ValueError, KeyError, TypeError, AttributeError, IndexError, UnicodeDecodeError)
SESSION_LOGS = ("frames.jsonl", "imu.csv", "telemetry.jsonl")


def _append(path: Path, line: str) -> None:
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def _recover(folder: Path) -> list[dict]:
    path = folder / "messages.jsonl"
    if path.exists():
        data = path.read_bytes()
        with open(path, "r+b") as stream:
            stream.truncate(data.rfind(b"\n") + 1)
    stored = _lines(path)
    sizes = stored[-1]["sizes"] if stored else {}
    for name in SESSION_LOGS:
        path = folder / name
        if path.exists():
            with open(path, "r+b") as stream:
                stream.truncate(sizes.get(name, 0))
    return stored


class Session:
    """One session folder on the PC: stores messages in order and knows the last one held with no gap."""

    def __init__(self, folder: Path, info: dict):
        self.folder, self.info, self.id = folder, info, folder.name
        self.lock = threading.Lock()
        self.connection: socket.socket | None = None
        self.notified = False
        self._restore()

    def _restore(self) -> None:
        stored = _recover(self.folder)
        path = self.folder / "session.json"
        if path.exists():
            self.info = json.loads(path.read_text(encoding="utf-8"))
        self.through = stored[-1]["n"] if stored else -1
        frames = [m["seq"] for m in stored if m["type"] == "frame"]
        self.last_seq = frames[-1] if frames else -1
        self.ended = any(m["type"] == "end" for m in stored)
        self.last_imu_ns = stored[-1]["imu_last_ns"] if stored else [None, None]
        if self.ended:
            end = stored[-1]["end"]
            self.info = self.info | {"clock": self.info["clock"] | end["clock"], "counts": end["counts"], "end_reason": end["reason"]}

    @classmethod
    def open(cls, root: Path, hello: dict, *, host_ms: float) -> "Session":
        session_v2.check_hello(hello)
        folder = Path(root) / hello["session"]
        info = hello["info"] | {"session": hello["session"], "version": session_v2.VERSION}
        if (folder / "session.json").exists():
            saved = json.loads((folder / "session.json").read_text(encoding="utf-8"))
            _require(saved["clock"]["start"] == info["clock"]["start"], f"another session already uses the id {folder.name}")
            info = saved
        else:
            for sub in ("cam0", "frames", "depth"):
                (folder / sub).mkdir(parents=True, exist_ok=True)
        session = cls(folder, info)
        session.hello(hello, host_ms=host_ms)
        return session

    def _save_info(self) -> None:
        path = self.folder / "session.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.info, indent=2), encoding="utf-8")
        temporary.replace(path)

    def hello(self, hello: dict, *, host_ms: float) -> None:
        session_v2.check_hello(hello)
        _require(hello["info"]["clock"]["start"] == self.info["clock"]["start"], "hello does not match the stored session")
        _append(self.folder / "hellos.jsonl", json.dumps({"host_received_ms": host_ms, "wall_ms": hello["wall_ms"]}))
        self._save_info()
        if self.ended:
            (self.folder / "summary.json").write_text(json.dumps(self.summary(), indent=2), encoding="utf-8")

    def store(self, header: dict, payload: bytes, *, host_ms: float):
        """Stores one message; returns the parsed frame for frame messages, else None. Raises ValueError to refuse."""
        try:
            return self._store_message(header, payload, host_ms=host_ms)
        except OSError:
            self._restore()
            raise

    def _store_message(self, header: dict, payload: bytes, *, host_ms: float):
        n = header.get("n")
        if isinstance(n, int) and 0 <= n <= self.through:
            return None  # a resend after a lost acknowledgement
        _require(header.get("session") == self.id, "message is for another session")
        _require(n == self.through + 1, f"gap: message {n} after {self.through}")
        _require(not self.ended, "session has already ended")
        kind, frame, line = header.get("type"), None, {"n": n, "type": header.get("type"), "bytes": len(payload),
                                                         "host_received_ms": host_ms}
        if kind == "frame":
            frame = session_v2.parse_frame(header, payload)
            _require(frame.seq == self.last_seq + 1, f"frame {frame.seq} after frame {self.last_seq}")
            self._store_frame(frame, header, payload, host_ms)
            self.last_seq = line["seq"] = frame.seq
        elif kind == "imu":
            self._store_imu(session_v2.parse_imu(header, payload))
        elif kind == "telemetry":
            _append(self.folder / "telemetry.jsonl", json.dumps(session_v2.check_telemetry(header) | {"host_received_ms": host_ms}))
        elif kind == "end":
            session_v2.check_end(header)
            line["end"] = header
        else:
            raise ValueError(f"unknown message type {kind!r}")
        line["sizes"] = {name: (self.folder / name).stat().st_size for name in SESSION_LOGS if (self.folder / name).exists()}
        line["imu_last_ns"] = self.last_imu_ns
        _append(self.folder / "messages.jsonl", json.dumps(line))
        self.through = n
        if kind == "end":
            self.ended = True
            self.info = self.info | {"clock": self.info["clock"] | header["clock"], "counts": header["counts"], "end_reason": header["reason"]}
            self._save_info()
            (self.folder / "summary.json").write_text(json.dumps(self.summary(), indent=2), encoding="utf-8")
        return frame

    def _store_frame(self, frame, header: dict, payload: bytes, host_ms: float) -> None:
        name = f"{frame.seq:06d}"
        Image.fromarray(frame.grey).save(self.folder / "cam0" / f"{name}.png", compress_level=1)
        (self.folder / "frames" / f"{name}.jpg").write_bytes(frame.image_jpeg)
        if frame.depth is not None:
            (self.folder / "depth" / f"{name}.bin").write_bytes(payload[header["grey"]["bytes"] + len(frame.image_jpeg):])
        _append(self.folder / "frames.jsonl", json.dumps(header | {"host_received_ms": host_ms}))

    def _store_imu(self, batch: session_v2.ImuBatch) -> None:
        last = self.last_imu_ns.copy()
        for code in (0, 1):
            times = batch.t_ns[batch.sensor == code]
            if len(times):
                _require(self.last_imu_ns[code] is None or times[0] >= self.last_imu_ns[code],
                         f"{session_v2.SENSORS[code]} timestamps go backwards across batches")
                last[code] = int(times[-1])
        path = self.folder / "imu.csv"
        rows = "".join(f"{session_v2.SENSORS[s]},{t}," + ",".join(f"{v:.9g}" for v in (*value, *bias)) + "\n"
                       for t, s, value, bias in zip(batch.t_ns, batch.sensor, batch.values, batch.bias))
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            if f.tell() == 0:
                f.write("sensor,t_ns,x,y,z,bx,by,bz\n")
            f.write(rows)
        self.last_imu_ns = last

    def summary(self) -> dict:
        frames = _lines(self.folder / "frames.jsonl")
        messages = _lines(self.folder / "messages.jsonl")
        hellos = _lines(self.folder / "hellos.jsonl")
        seqs = [f["seq"] for f in frames]
        imu = {name: [] for name in session_v2.SENSORS}
        if (self.folder / "imu.csv").exists():
            with open(self.folder / "imu.csv", encoding="utf-8") as rows:
                next(rows)
                for row in rows:
                    sensor, t, _ = row.split(",", 2)
                    imu[sensor].append(int(t))
        camera_t = [f["camera_t_ns"] for f in frames]
        start = self.info["clock"]["start"]["elapsed_realtime_ns"]
        firsts = {name: int(t[0]) for name, t in (("camera", camera_t), *imu.items()) if t}
        offset_ms = hellos[-1]["host_received_ms"] - hellos[-1]["wall_ms"]
        stop_wall = self.info["clock"].get("end", {}).get("wall_ms")
        span_s = (messages[-1]["host_received_ms"] - messages[0]["host_received_ms"]) / 1000 if len(messages) > 1 else 0.0
        received = sum(m["bytes"] for m in messages)
        return {
            "session": self.id, "kind": self.info["kind"], "end_reason": self.info.get("end_reason"),
            "frames": len(frames), "missing_seq": sorted(set(range(max(seqs) + 1)) - set(seqs)) if seqs else [],
            "repeated_seq": len(seqs) - len(set(seqs)),
            "frames_with_arcore": sum(f["arcore"] is not None for f in frames),
            "frames_tracking": sum(f["arcore"] is not None and f["arcore"]["tracking"] == "TRACKING" for f in frames),
            "frames_with_depth": sum(f["arcore"] is not None and "depth" in f["arcore"] for f in frames),
            "frames_dropped_on_phone": self.info.get("counts", {}).get("frames_dropped"),
            "camera": session_v2.stream_stats(camera_t), "imu": {name: session_v2.stream_stats(t) for name, t in imu.items()},
            "clock_base": {"first_stamp_after_start_ms": {k: (v - start) / 1e6 for k, v in firsts.items()},
                           "same_clock_base": all(abs(v - start) <= CLOCK_BASE_TOLERANCE_NS for v in firsts.values())},
            "messages": len(messages), "megabytes": received / 1e6,
            "megabytes_per_second": received / 1e6 / span_s if span_s else 0.0, "connections": len(hellos),
            "phone_to_pc_clock_offset_ms": offset_ms,
            "sending_after_stop_s": (messages[-1]["host_received_ms"] - (stop_wall + offset_ms)) / 1000 if stop_wall else None,
        }


class Receiver:
    """Accepts phone connections on their own threads; sessions survive dropped connections and PC restarts."""

    def __init__(self, root: Path, *, port: int = PORT, host: str = "0.0.0.0", on_frame=None):
        """on_frame(frame, colour_path), if given, is called after each new frame is saved (live processing hooks in here)."""
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.listener = socket.create_server((host, port))
        self.port = self.listener.getsockname()[1]
        self.on_frame = on_frame
        self.sessions: dict[str, Session] = {}
        self.finished: queue.Queue[Path] = queue.Queue()
        self.reports: queue.Queue[Path] = queue.Queue()
        self._lock = threading.Lock()

    def start(self) -> "Receiver":
        threading.Thread(target=self._accept, daemon=True).start()
        return self

    def wait(self, timeout: float | None = None) -> Path:
        """The folder of the next session whose end message has been stored."""
        return self.finished.get(timeout=timeout)

    def wait_reports(self, count: int, timeout: float | None = None) -> list[Path]:
        return [self.reports.get(timeout=timeout) for _ in range(count)]

    def close(self) -> None:
        self.listener.close()
        for session in self.sessions.values():
            if session.connection is not None:
                _shut(session.connection)

    def _accept(self) -> None:
        while True:
            try:
                connection, (peer, _) = self.listener.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(connection, peer), daemon=True).start()

    def _session(self, hello: dict, connection: socket.socket) -> Session:
        with self._lock:
            session = self.sessions.get(hello.get("session"))
            if session is None:
                session = Session.open(self.root, hello, host_ms=time.time() * 1000)
                self.sessions[session.id] = session
            else:
                with session.lock:
                    session.hello(hello, host_ms=time.time() * 1000)
            if session.connection is not None:
                _shut(session.connection)  # the phone reconnected; the old connection is dead
            session.connection = connection
            return session

    def _handle(self, connection: socket.socket, peer: str) -> None:
        connection.settimeout(TIMEOUT_S)
        try:
            with connection, connection.makefile("rwb") as stream:
                try:
                    self._converse(stream, connection, peer)
                except REFUSED as e:
                    _reply(stream, {"type": "error", "message": f"{type(e).__name__}: {e}"})
        except (OSError, EOFError):
            pass  # dropped connection (closing it can fail too); the phone reconnects and resumes

    def _converse(self, stream, connection: socket.socket, peer: str) -> None:
        message = protocol.read_message(stream)
        if message is None:
            return
        header, payload = message
        if header.get("type") == "speed":
            return self._speed(stream, header, payload)
        if header.get("type") == "report":
            return self._report(payload, peer)
        session = self._session(header, connection)
        _reply(stream, {"type": "ack", "session": session.id, "through": session.through})
        self._finished(session)
        while (message := protocol.read_message(stream)) is not None:
            with session.lock:
                frame = session.store(*message, host_ms=time.time() * 1000)
            if frame is not None and self.on_frame is not None:
                self.on_frame(frame, session.folder / "frames" / f"{frame.seq:06d}.jpg")
            _reply(stream, {"type": "ack", "session": session.id, "through": session.through})
            self._finished(session)

    def _finished(self, session: Session) -> None:
        with session.lock:
            if session.ended and not session.notified:
                session.notified = True
                self.finished.put(session.folder)

    def _speed(self, stream, header: dict, payload: bytes) -> None:
        started, total = time.perf_counter(), len(payload)
        while header.get("chunk", 0) + 1 < header.get("chunks", 1):
            message = protocol.read_message(stream)
            if message is None:
                return
            header, payload = message
            _require(header.get("type") == "speed", "a speed check carries only speed messages")
            total += len(payload)
        _reply(stream, {"type": "speed", "bytes": total, "seconds": time.perf_counter() - started})

    def _report(self, payload: bytes, peer: str) -> None:
        report = json.loads(payload.decode("utf-8"))
        model = "".join(c for c in str(report.get("device", {}).get("model", peer)) if c.isalnum() or c in "-_")
        folder = self.root / "reports"
        folder.mkdir(exist_ok=True)
        path = folder / f"{time.strftime('%Y%m%dT%H%M%S')}_{int(time.time() * 1000) % 1000:03d}_{model}.json"
        path.write_bytes(payload)
        self.reports.put(path)


def _reply(stream, header: dict) -> None:
    protocol.write_message(stream, header)
    stream.flush()


def _shut(connection: socket.socket) -> None:
    try:
        connection.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def addresses() -> list[str]:
    """This PC's IPv4 addresses, the one on the default route first."""
    found = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))  # no packet is sent; this only picks the outgoing interface
            found.append(probe.getsockname()[0])
    except OSError:
        pass
    others = sorted({info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
    return found + [a for a in others if a not in found]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--sessions", type=int, default=0, help="stop after this many sessions have ended (0: run until Ctrl+C)")
    args = parser.parse_args()
    server = Receiver(args.out, port=args.port).start()
    print(f"Listening on port {server.port}. Type this PC's address into the app: {', '.join(addresses())}", flush=True)
    print("Local network only: the link has no authentication or encryption.", flush=True)
    count = 0
    while args.sessions == 0 or count < args.sessions:
        folder = server.wait()
        count += 1
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        print(f"{folder}: {json.dumps(summary)}", flush=True)
    server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
