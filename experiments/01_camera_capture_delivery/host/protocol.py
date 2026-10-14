"""Messages between the Redmi check app and the host: a JSON header and a binary payload, each length-prefixed.

Message: 4-byte big-endian header length, UTF-8 JSON header, 4-byte big-endian payload length, payload.
Acknowledgement (host to phone, one per frame): the frame's 4-byte big-endian sequence number.
The Java side is phonecheck/app/src/main/java/org/fyld/phonecheck/HostStream.java.
"""

from __future__ import annotations

import json
import struct
from typing import BinaryIO

_LENGTH = struct.Struct(">I")


def _read_exact(stream: BinaryIO, count: int) -> bytes:
    data = stream.read(count)
    if len(data) != count:
        raise EOFError(f"connection ended after {len(data)} of {count} bytes")
    return data


def write_message(stream: BinaryIO, header: dict, payload: bytes = b"") -> None:
    encoded = json.dumps(header, separators=(",", ":")).encode("utf-8")
    stream.write(_LENGTH.pack(len(encoded)) + encoded + _LENGTH.pack(len(payload)) + payload)


def read_message(stream: BinaryIO) -> tuple[dict, bytes] | None:
    """The next message, or None when the sender closed the connection between messages."""
    first = stream.read(_LENGTH.size)
    if not first:
        return None
    if len(first) != _LENGTH.size:
        raise EOFError("connection ended inside a message length")
    header = json.loads(_read_exact(stream, _LENGTH.unpack(first)[0]).decode("utf-8"))
    payload = _read_exact(stream, _LENGTH.unpack(_read_exact(stream, _LENGTH.size))[0])
    return header, payload


def write_ack(stream: BinaryIO, seq: int) -> None:
    stream.write(_LENGTH.pack(seq))


def read_ack(stream: BinaryIO) -> int:
    return _LENGTH.unpack(_read_exact(stream, _LENGTH.size))[0]
