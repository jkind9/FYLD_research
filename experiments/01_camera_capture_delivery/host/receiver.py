"""Receive frames and check reports from the Redmi check app, save them, and acknowledge each frame.

    python experiments/01_camera_capture_delivery/host/receiver.py --out experiments/01_camera_capture_delivery/runs/phonecheck

Each connection becomes one session folder: frames/<seq>.jpg, frames.jsonl (each frame's header plus the
host receive time), report.json if the phone sends one, and summary.json (frames, bytes, frames per second).
Allow the port through the Windows firewall for private networks the first time.
"""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

import protocol

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
        frames, payload_bytes, started = 0, 0, time.perf_counter()
        with connection, connection.makefile("rwb") as stream, open(session / "frames.jsonl", "w", encoding="utf-8") as log:
            while (message := protocol.read_message(stream)) is not None:
                header, payload = message
                if header.get("type") == "report":
                    (session / "report.json").write_bytes(payload)
                    continue
                (session / "frames" / f"{int(header['seq']):06d}.jpg").write_bytes(payload)
                log.write(json.dumps(header | {"host_received_ms": time.time() * 1000}) + "\n")
                protocol.write_ack(stream, int(header["seq"]))
                stream.flush()
                frames += 1
                payload_bytes += len(payload)
        seconds = time.perf_counter() - started
        self.summary = {"peer": peer, "frames": frames, "payload_bytes": payload_bytes, "seconds": seconds,
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
