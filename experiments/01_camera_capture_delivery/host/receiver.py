"""Receive frames and check reports from the Redmi check app, save them, and acknowledge each frame.

    python experiments/01_camera_capture_delivery/host/receiver.py --out experiments/01_camera_capture_delivery/runs/phonecheck

Messages follow phone_session_v1.md: a stream connection starts with a session message, and session_v1.parse_frame
checks every frame; a bad frame closes the connection. Each connection becomes one session folder: session.json,
frames/<seq>.jpg, depth/<seq>.bin (raw depth then confidence, for frames with new depth), frames.jsonl (each
frame's header plus the host receive time), report.json if the phone sends one, and summary.json (frames,
depth frames, bytes, frames per second).
Allow the port through the Windows firewall for private networks the first time.
"""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

import protocol
import session_v1

PORT = 8765


class Receiver:
    def __init__(self, root: Path, *, port: int = PORT, host: str = "0.0.0.0"):
        self.root = Path(root)
        self.listener = socket.create_server((host, port))
        self.port = self.listener.getsockname()[1]
        self.summary: dict = {}

    def serve_one(self) -> Path:
        """Handle one phone connection until it closes; returns its session folder."""
        connection, (peer, _) = self.listener.accept()
        session = self.root / f"{time.strftime('%Y%m%dT%H%M%S')}_{peer.replace(':', '-')}"
        (session / "frames").mkdir(parents=True)
        (session / "depth").mkdir()
        frames, depth_frames, payload_bytes, started, session_started = 0, 0, 0, time.perf_counter(), False
        with connection, connection.makefile("rwb") as stream, open(session / "frames.jsonl", "w", encoding="utf-8") as log:
            while (message := protocol.read_message(stream)) is not None:
                header, payload = message
                if header.get("type") == "report":
                    (session / "report.json").write_bytes(payload)
                    continue
                if header.get("type") == "session":
                    (session / "session.json").write_text(json.dumps(session_v1.check_session(header), indent=2), encoding="utf-8")
                    session_started = True
                    continue
                if not session_started:
                    raise ValueError("a frame arrived before the session start message")
                frame = session_v1.parse_frame(header, payload)
                name = f"{frame.seq:06d}"
                (session / "frames" / f"{name}.jpg").write_bytes(frame.image_jpeg)
                if frame.depth is not None:
                    (session / "depth" / f"{name}.bin").write_bytes(payload[len(frame.image_jpeg):])
                    depth_frames += 1
                log.write(json.dumps(header | {"host_received_ms": time.time() * 1000}) + "\n")
                protocol.write_ack(stream, frame.seq)
                stream.flush()
                frames += 1
                payload_bytes += len(payload)
        seconds = time.perf_counter() - started
        self.summary = {"peer": peer, "frames": frames, "depth_frames": depth_frames, "payload_bytes": payload_bytes, "seconds": seconds,
                        "frames_per_second": frames / seconds if seconds else 0.0,
                        "megabytes_per_second": payload_bytes / 1e6 / seconds if seconds else 0.0}
        (session / "summary.json").write_text(json.dumps(self.summary, indent=2), encoding="utf-8")
        return session


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--sessions", type=int, default=0, help="stop after this many connections (0: run until Ctrl+C)")
    args = parser.parse_args()
    server = Receiver(args.out, port=args.port)
    addresses = sorted({info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
    print(f"Listening on port {server.port}; enter one of these in the app: {', '.join(addresses)}")
    count = 0
    while args.sessions == 0 or count < args.sessions:
        session = server.serve_one()
        count += 1
        print(f"{session}: {json.dumps(server.summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
