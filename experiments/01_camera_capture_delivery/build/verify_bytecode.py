"""Run with the recovered hostpython 3.14.2 to compare embedded code exactly."""

import argparse
import hashlib
import importlib.util
import io
import json
import marshal
import struct
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


def require_python() -> None:
    if sys.version_info[:3] != (3, 14, 2):
        raise ValueError("Embedded code verification requires recovered Python 3.14.2")


def check_bytecode(payload: bytes, source: Path, expected_filename: str) -> dict:
    require_python()
    source_bytes = Path(source).read_bytes()
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate private archive entries")
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts or "\\" in member.name:
                    raise ValueError("Unsafe private archive entry")
                if not (member.isfile() or member.isdir()):
                    raise ValueError("Links and special private archive entries are unsupported")
            candidates = [member for member in members if member.name == "main.pyc"]
            if len(candidates) != 1 or not candidates[0].isfile():
                raise ValueError("Expected exactly one main.pyc private archive entry")
            if candidates[0].size > 4 * 1024 * 1024:
                raise ValueError("main.pyc exceeds the smoke source verification limit")
            stream = archive.extractfile(candidates[0])
            if stream is None:
                raise ValueError("Cannot read embedded main.pyc")
            with stream:
                code_bytes = stream.read()
    except (tarfile.TarError, EOFError, OSError) as error:
        raise ValueError("Invalid private source archive") from error
    if len(code_bytes) < 16 or code_bytes[:4] != importlib.util.MAGIC_NUMBER:
        raise ValueError("Unsupported or truncated Python bytecode header")
    flags = struct.unpack("<I", code_bytes[4:8])[0]
    if flags not in (0, 1, 3):
        raise ValueError("Unsupported Python bytecode header flags")
    embedded = marshal.loads(code_bytes[16:])
    expected_code = compile(source_bytes, expected_filename, "exec", optimize=2)
    if not isinstance(embedded, type(expected_code)) or embedded != expected_code or \
            embedded.co_filename != expected_filename:
        raise ValueError(
            "Embedded bytecode does not correspond to recovered source and filename "
            f"(embedded filename={embedded.co_filename!r}, expected={expected_filename!r}, "
            f"embedded constants={embedded.co_consts!r}, expected constants={expected_code.co_consts!r})"
        )
    return {"status": "verified", "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "python_version": "3.14.2", "filename": expected_filename,
            "main_pyc_sha256": hashlib.sha256(code_bytes).hexdigest(), "optimize": 2}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("expected_filename")
    args = parser.parse_args()
    with zipfile.ZipFile(args.apk) as archive:
        if archive.namelist().count("assets/private.tar") != 1:
            raise ValueError("Expected exactly one private source archive")
        payload = archive.read("assets/private.tar")
    sys.stdout.write(json.dumps(check_bytecode(payload, args.source, args.expected_filename)) + "\n")


if __name__ == "__main__":
    main()
