"""Bounded downloads and fail-closed archive extraction; never executes fetched code."""

import hashlib
import json
import shutil
import tarfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4


def sha256(path: Path) -> str:
    """Stream a local content hash; this is not publisher authentication."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_tar(
    archive: Path,
    destination: Path,
    max_expanded_bytes: int = 2_000_000_000,
    max_members: int = 100_000,
) -> None:
    """Reject traversal, links, devices, duplicate files and excessive expanded size."""
    root = destination.resolve()
    with tarfile.open(archive, "r:gz") as stream:
        members: list[tarfile.TarInfo] = []
        total, names = 0, set()
        for member in stream:
            if len(members) >= max_members:
                raise ValueError("Archive member-count budget exceeded")
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.name
                or ":" in member.name
                or not (member.isfile() or member.isdir())
            ):
                raise ValueError(f"Unsafe archive entry: {member.name}")
            path = (root / member.name).resolve()
            if not path.is_relative_to(root) or (member.isfile() and path in names):
                raise ValueError("Archive escape/duplicate detected")
            names.add(path)
            total += member.size
            if total > max_expanded_bytes:
                raise ValueError("Expanded archive exceeds budget")
            members.append(member)
        root.mkdir(parents=True, exist_ok=True)
        for member in members:
            path = root / member.name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                if path.exists():
                    raise FileExistsError(
                        f"Refusing to overwrite extraction target: {path}"
                    )
                path.parent.mkdir(parents=True, exist_ok=True)
                source = stream.extractfile(member)
                if source is None:
                    raise ValueError("Missing archive file stream")
                with source, path.open("xb") as target:
                    shutil.copyfileobj(source, target)


def download(
    url: str,
    archive: Path,
    budget_bytes: int,
    expected_bytes: int,
    publisher_sha256: str | None = None,
) -> dict:
    """Cache only hash-checked completed files; HEAD and streaming enforce size budget."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = archive.with_suffix(archive.suffix + ".json")
    existing_size = sum(
        p.stat().st_size for p in archive.parent.glob("*.tgz") if p != archive
    )
    allowance = budget_bytes - existing_size
    if expected_bytes > allowance or expected_bytes <= 0:
        raise ValueError("Total archive budget exceeded before download")
    if archive.exists() and not metadata_path.exists():
        if archive.stat().st_size != expected_bytes:
            raise ValueError("Orphaned archive has unexpected size; inspect cache")
        digest = sha256(archive)
        if publisher_sha256 and digest != publisher_sha256:
            raise ValueError("Publisher checksum mismatch")
        # A process can die after archive rename but before provenance write.
        # Recovery must disclose that original HTTP receipt metadata was lost.
        metadata = download_metadata(
            url, None, expected_bytes, digest, publisher_sha256
        )
        metadata["recovery"] = (
            "orphaned cache; local size/hash checked, original network receipt unavailable"
        )
        write_metadata(metadata_path, metadata)
        print(
            "Recovered orphaned local archive metadata; no publisher verification implied",
            flush=True,
        )
    if archive.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata["source_url"] != url
            or archive.stat().st_size != expected_bytes
            or sha256(archive) != metadata["local_sha256"]
        ):
            raise ValueError(
                "Cache provenance/hash mismatch; inspect before removing cache"
            )
        if publisher_sha256 and metadata["local_sha256"] != publisher_sha256:
            raise ValueError("Publisher checksum mismatch")
        print(f"Verified cached local hash: {archive.name}", flush=True)
        return metadata
    with urllib.request.urlopen(
        urllib.request.Request(url, method="HEAD"), timeout=60
    ) as head:
        declared = head.headers.get("Content-Length")
        if (
            declared is None
            or int(declared) != expected_bytes
            or int(declared) > allowance
        ):
            raise ValueError(
                f"Unexpected archive size {declared}; verified size is {expected_bytes}"
            )
    partial = archive.with_suffix(archive.suffix + ".part")
    received, next_progress = 0, 0
    try:
        with urllib.request.urlopen(url, timeout=60) as response, partial.open(
            "wb"
        ) as target:
            resolved = response.url
            while block := response.read(1024 * 1024):
                received += len(block)
                if received > allowance or received > expected_bytes:
                    raise ValueError("Streaming download exceeds size budget")
                target.write(block)
                if received >= next_progress:
                    print(
                        f"{archive.name}: {received / 1e6:.1f}/{expected_bytes / 1e6:.1f} MB",
                        flush=True,
                    )
                    next_progress = received + 25_000_000
        if received != expected_bytes:
            raise ValueError("Truncated archive")
        digest = sha256(partial)
        if publisher_sha256 and digest != publisher_sha256:
            raise ValueError("Publisher checksum mismatch")
        partial.replace(archive)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    metadata = download_metadata(url, resolved, received, digest, publisher_sha256)
    write_metadata(metadata_path, metadata)
    return metadata


def write_metadata(path: Path, metadata: dict) -> None:
    """Atomically publish provenance without importing the rendering stack."""
    temporary = path.with_name(path.name + f".{uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8"
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def download_metadata(
    url: str,
    resolved: str | None,
    received: int,
    digest: str,
    publisher_sha256: str | None,
) -> dict:
    """TUM provenance; local checksum is distinct from publisher authentication."""
    return {
        "source_url": url,
        "resolved_url": resolved,
        "size_bytes": received,
        "local_sha256": digest,
        "publisher_sha256": publisher_sha256,
        "checksum_status": (
            "publisher verified"
            if publisher_sha256
            else "local content hash only; no publisher checksum located"
        ),
        "download_utc": datetime.now(UTC).isoformat(),
        "licence": "CC BY 4.0",
        "licence_source": "https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license",
        "attribution": "Sturm, Engelhard, Endres, Burgard, Cremers (IROS 2012), A Benchmark for the Evaluation of RGB-D SLAM Systems",
    }
