"""Bounded ICL acquisition, adapted from the archived prototype's acquisition helpers.

Extraction receipts establish archive integrity only, not geometry/scoring readiness.
"""

import gzip
import hashlib
import io
import json
import logging
import shutil
import tarfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

ASSETS = (
    ("living_room_traj2_frei_png.tar.gz", 429825445, "trajectory2"),
    ("living-room.ply.tar.gz", 89545763, "reference_surface"),
)
BASE_URL = "https://www.doc.ic.ac.uk/~ahanda/"
LICENCE_URL = BASE_URL + "VaFRIC/iclnuim.html"
CHUNK = 1024 * 1024


class CappedTarReader(io.BufferedReader):
    """Bound metadata reads before tarfile allocates a PAX/GNU extension body."""

    def read(self, size: int | None = -1) -> bytes:
        if size is None or size < 0 or size > CHUNK:
            raise ValueError("Tar metadata/read request exceeds 1 MiB")
        return super().read(size)


def sha256(path: Path) -> str:
    """Local fingerprint; does not authenticate the publisher."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(name: str) -> PurePosixPath:
    """Reject portable and Windows-specific extraction hazards."""
    path = PurePosixPath(name)
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved |= {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}
    if (
        path.is_absolute()
        or not path.parts
        or ".." in path.parts
        or "\\" in name
        or ":" in name
        or "\x00" in name
    ):
        raise ValueError(f"Unsafe archive name: {name}")
    for part in path.parts:
        if (
            part.endswith((".", " "))
            or part.split(".")[0].upper() in reserved
            or any(c in part for c in '<>"|?*')
            or any(ord(c) < 32 for c in part)
        ):
            raise ValueError(f"Unsafe Windows name: {name}")
    if path.parts[0].casefold() == "extraction.json":
        raise ValueError("Archive would collide with extraction receipt")
    return path


def checked_members(
    stream: tarfile.TarFile,
    max_expanded_bytes: int,
    max_member_bytes: int,
    max_members: int,
) -> tuple[list[tarfile.TarInfo], int]:
    """Validate every destination before writing any payload."""
    members: list[tarfile.TarInfo] = []
    names: set[str] = set()
    total = 0
    for member in stream:
        path = safe_name(member.name)
        key = str(path).casefold()
        if not (member.isfile() or member.isdir()) or key in names:
            raise ValueError(f"Special/link/duplicate member: {member.name}")
        if any(
            str(parent).casefold() in names
            and any(
                str(safe_name(m.name)).casefold() == str(parent).casefold()
                and m.isfile()
                for m in members
            )
            for parent in path.parents
        ):
            raise ValueError("File used as parent directory")
        names.add(key)
        total += member.size
        if (
            member.size < 0
            or member.size > max_member_bytes
            or total > max_expanded_bytes
            or len(members) >= max_members
        ):
            raise ValueError("Archive extraction budget exceeded")
        members.append(member)
    return members, total


def publish_archive(
    archive: Path,
    destination: Path,
    max_expanded_bytes: int = 8 * 1024**3,
    max_member_bytes: int = 2 * 1024**3,
    max_members: int = 10000,
) -> dict[str, Any]:
    """Stage, verify gzip EOF and publish a new tree with its receipt.

    A failed staging directory is deliberately retained for inspection.
    """
    if destination.exists():
        raise FileExistsError(f"Refusing overwrite: {destination}")
    staging = destination.with_name(destination.name + ".staging-" + uuid4().hex)
    staging.parent.mkdir(parents=True, exist_ok=True)
    spool = staging.with_name(staging.name + ".tar.part")
    # Bound the entire gzip stream and verify its trailer BEFORE tar parsing.
    with gzip.open(archive, "rb") as source, spool.open("xb") as output:
        expanded_stream = 0
        while block := source.read(CHUNK):
            expanded_stream += len(block)
            if expanded_stream > max_expanded_bytes + max_members * 2048 + 10240:
                raise ValueError("Gzip expansion exceeds payload plus header budget")
            output.write(block)
    with CappedTarReader(spool.open("rb", buffering=0)) as raw, tarfile.open(
        fileobj=raw, mode="r:"
    ) as stream:
        members, total = checked_members(
            stream, max_expanded_bytes, max_member_bytes, max_members
        )
        staging.mkdir(parents=True)
        for member in members:
            target = staging.joinpath(*safe_name(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = stream.extractfile(member)
            if payload is None:
                raise ValueError("Missing member payload")
            with payload, target.open("xb") as output:
                shutil.copyfileobj(payload, output, CHUNK)
            if target.stat().st_size != member.size:
                raise ValueError("Truncated extracted member")
    receipt = {
        "archive": archive.name,
        "local_sha256": sha256(archive),
        "compressed_bytes": archive.stat().st_size,
        "expanded_bytes": total,
        "member_count": len(members),
        "gzip_stream_bytes": expanded_stream,
        "validated_utc": datetime.now(UTC).isoformat(),
        "validation": "bounded safe members, exact payload lengths, gzip EOF/CRC",
        "scoring_ready": False,
        "files": [{"path": m.name, "bytes": m.size} for m in members if m.isfile()],
    }
    (staging / "EXTRACTION.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    staging.rename(destination)
    spool.unlink()
    return receipt


def download(url: str, archive: Path, expected_bytes: int) -> dict[str, Any]:
    """Require fresh official length and exact bounded GET; never overwrite."""
    if archive.exists():
        raise FileExistsError(f"Inspect existing archive before reuse: {archive}")
    with urllib.request.urlopen(
        urllib.request.Request(url, method="HEAD"), timeout=60
    ) as head:
        if int(head.headers.get("Content-Length", -1)) != expected_bytes:
            raise ValueError("Publisher length changed; review before download")
    archive.parent.mkdir(parents=True, exist_ok=True)
    partial = archive.with_name(archive.name + "." + uuid4().hex + ".part")
    received = 0
    with urllib.request.urlopen(url, timeout=60) as response, partial.open(
        "xb"
    ) as target:
        resolved = response.url
        if not resolved.startswith("https://www.doc.ic.ac.uk/"):
            raise ValueError("Unexpected download redirect")
        while block := response.read(CHUNK):
            received += len(block)
            if received > expected_bytes:
                raise ValueError("Download exceeds expected size")
            target.write(block)
    if received != expected_bytes:
        raise ValueError("Truncated download; partial retained for inspection")
    metadata = {
        "source_url": url,
        "resolved_url": resolved,
        "bytes": received,
        "local_sha256": sha256(partial),
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "licence": "CC BY 3.0",
        "licence_source": LICENCE_URL,
        "attribution": "Handa, Whelan, McDonald, Davison; ICRA 2014",
        "checksum_status": "local content hash only; no publisher checksum located",
    }
    metadata_path = archive.with_name(archive.name + ".json")
    temporary_metadata = partial.with_name(partial.name + ".json")
    temporary_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    # Publish provenance first: interruption can leave a receipt without a payload,
    # but a final payload is never visible without its provenance.
    temporary_metadata.replace(metadata_path)
    partial.rename(archive)
    return metadata


def main() -> None:
    """Acquire the two predeclared ICL assets; never import estimator code."""
    root = Path(__file__).resolve().parents[2] / "data" / "icl_nuim"
    if shutil.disk_usage(root.parent).free < 18 * 1024**3:
        raise ValueError("Acquisition requires at least 18 GiB free")
    for filename, size, folder in ASSETS:
        archive = root / "archives" / filename
        download(BASE_URL + filename, archive, size)
        receipt = publish_archive(archive, root / folder)
        logging.getLogger(__name__).info(
            "Published %s: %d members, %d expanded bytes",
            folder,
            receipt["member_count"],
            receipt["expanded_bytes"],
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
