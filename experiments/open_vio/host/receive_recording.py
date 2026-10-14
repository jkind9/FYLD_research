"""Receive recordings that the raw recorder app sends over Wi-Fi, check each file and acknowledge it.

    python experiments/open_vio/host/receive_recording.py --out experiments/open_vio/runs/recordings

Each file arrives as one message (experiment 01's host/protocol.py framing): a header
{type: file, seq, recording, path, size, sha256} and the file's bytes. A file whose size or SHA-256 differs,
or whose path leaves the recording folder, is not saved and the connection is closed, so the phone shows
the error. A final {type: done, files} message marks the recording complete in received.json.
Allow the port through the Windows firewall for private networks the first time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
import time
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "01_camera_capture_delivery" / "host"))
import protocol  # noqa: E402

PORT = 8766


def _safe(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(parts) and not PurePosixPath(path).is_absolute() and ".." not in parts and "\\" not in path


class Receiver:
    def __init__(self, root: Path, *, port: int = PORT, host: str = "0.0.0.0"):
        self.root = Path(root)
        self.listener = socket.create_server((host, port))
        self.port = self.listener.getsockname()[1]
        self.summary: dict = {}

    def serve_one(self) -> Path | None:
        """Handle one upload until the phone closes it or a file fails its check; returns the recording folder."""
        connection, (peer, _) = self.listener.accept()
        folder, files, received, complete, error = None, 0, 0, False, ""
        started = time.perf_counter()
        with connection, connection.makefile("rwb") as stream:
            while (message := protocol.read_message(stream)) is not None:
                header, payload = message
                name = str(header.get("recording", ""))
                if not _safe(name) or len(PurePosixPath(name).parts) != 1:
                    error = f"bad recording name {name!r}"
                    break
                folder = self.root / name
                folder.mkdir(parents=True, exist_ok=True)
                if header.get("type") == "done":
                    complete = header.get("files") == files
                    error = "" if complete else f"phone sent {header.get('files')} files, {files} arrived"
                    break
                path = str(header.get("path", ""))
                if not _safe(path):
                    error = f"path outside the recording: {path!r}"
                    break
                if len(payload) != header.get("size") or hashlib.sha256(payload).hexdigest() != header.get("sha256"):
                    error = f"{path}: size or SHA-256 does not match"
                    break
                target = folder / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                protocol.write_ack(stream, int(header["seq"]))
                stream.flush()
                files += 1
                received += len(payload)
        seconds = time.perf_counter() - started
        self.summary = {"peer": peer, "files": files, "bytes": received, "seconds": seconds,
                        "megabytes_per_second": received / 1e6 / seconds if seconds else 0.0,
                        "complete": complete, "error": error}
        if folder is not None:
            (folder / "received.json").write_text(json.dumps(self.summary, indent=2), encoding="utf-8")
        return folder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    server = Receiver(args.out, port=args.port)
    addresses = sorted({info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
    print(f"Listening on port {server.port}; enter one of these in the recorder app: {', '.join(addresses)}")
    while True:
        folder = server.serve_one()
        print(f"{folder}: {json.dumps(server.summary)}")


if __name__ == "__main__":
    raise SystemExit(main())
