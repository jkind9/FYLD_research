"""Length-prefixed JSON headers and binary payloads for phone messages."""

import json
import struct
from typing import BinaryIO

_LENGTH = struct.Struct(">I")


def _read_exact(stream: BinaryIO, count: int) -> bytes:
    """Exactly count bytes, or EOFError when a message is truncated."""
    received = stream.read(count)
    if len(received) != count:
        raise EOFError(f"connection ended after {len(received)} of {count} bytes")
    return received


def write_message(stream: BinaryIO, header: dict, payload: bytes = b"") -> None:
    """Write a header and payload with their big-endian byte lengths."""
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    stream.write(
        _LENGTH.pack(len(header_bytes)) + header_bytes + _LENGTH.pack(len(payload)) + payload
    )


def read_message(stream: BinaryIO) -> tuple[dict, bytes] | None:
    """The next message, or None when the sender closed the connection between messages."""
    prefix = stream.read(_LENGTH.size)
    if not prefix:
        return None
    if len(prefix) != _LENGTH.size:
        raise EOFError("connection ended inside a message length")
    header = json.loads(_read_exact(stream, _LENGTH.unpack(prefix)[0]).decode("utf-8"))
    payload = _read_exact(stream, _LENGTH.unpack(_read_exact(stream, _LENGTH.size))[0])
    return header, payload


def write_ack(stream: BinaryIO, seq: int) -> None:
    """Write the sequence number acknowledged by a v1 receiver."""
    stream.write(_LENGTH.pack(seq))


def read_ack(stream: BinaryIO) -> int:
    """The sequence number acknowledged by a v1 receiver."""
    return _LENGTH.unpack(_read_exact(stream, _LENGTH.size))[0]
