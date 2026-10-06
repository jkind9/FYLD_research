"""CPU-only provenance snapshots and fail-closed artifact publication."""

import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Literal, Self
from uuid import uuid4

from experiments.datasets.acquisition import sha256
from experiments.shared.timing import TimingLedger

EXCLUDED = {"metadata/status.json", "metadata/manifest.json"}


def write_json(path: Path, data: object) -> None:
    """Serialize strictly before publishing via same-directory atomic replace."""
    payload = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".part")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _inventory(path: Path) -> dict:
    files = {}
    for artifact in sorted(path.rglob("*")):
        relative = artifact.relative_to(path).as_posix()
        if artifact.is_symlink():
            raise ValueError(f"Run contains symbolic link: {relative}")
        if artifact.is_file() and relative not in EXCLUDED:
            files[relative] = {
                "sha256": sha256(artifact),
                "bytes": artifact.stat().st_size,
            }
    return files


def _validate_inventory(path: Path, manifest: dict) -> None:
    if manifest.get("schema_version") != 1 or manifest.get("files") != _inventory(path):
        raise ValueError("Run artifact inventory does not match manifest")


def artifact_inventory(path: Path) -> dict:
    """Hash artifacts with the publication manifest's exclusions and link checks."""
    return _inventory(path)


def verify_run(path: Path) -> dict:
    """Reject incomplete runs and any changed, missing or additional artifact."""
    status = json.loads((path / "metadata/status.json").read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        raise ValueError("Run is not complete")
    manifest_path = path / "metadata/manifest.json"
    if status.get("manifest_sha256") != sha256(manifest_path):
        raise ValueError("Run manifest hash differs from completion receipt")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _validate_inventory(path, manifest)
    return {"status": "complete", "file_count": len(manifest["files"])}


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments], check=True, capture_output=True
    )
    return result.stdout.decode("utf-8", errors="replace")


def _snapshot(repo: Path, destination: Path, run_root: Path) -> dict:
    files = {}
    sources: list[Path] = []
    for root in (repo, repo / "experiments", repo / "src", repo / "src/walkthrough"):
        if root.is_symlink():
            raise ValueError(f"Source snapshot refuses symbolic link: {root}")
    for root in (repo / "experiments", repo / "src/walkthrough"):
        for directory, children, names in os.walk(root):
            for name in children:
                child = Path(directory) / name
                if child.is_symlink():
                    raise ValueError(f"Source snapshot refuses symbolic link: {child}")
            # os.walk requires modifying this list to prune generated trees.
            children[:] = [
                name
                for name in children
                if name not in {"runs", "__pycache__", ".venv", "node_modules"}
                and not (
                    (Path(directory) / name)
                    .resolve()
                    .is_relative_to(run_root.resolve())
                    and (Path(directory) / name / "metadata/status.json").is_file()
                )
            ]
            sources.extend(Path(directory) / name for name in names)
    for source in sorted(sources):
        relative = source.relative_to(repo)
        if any(
            part in {"runs", "__pycache__", ".venv", "node_modules"}
            for part in relative.parts
        ):
            continue
        if source.is_symlink():
            raise ValueError(f"Source snapshot refuses symbolic link: {relative}")
        if not source.is_file() or not (
            source.suffix == ".py" or source.name == "requirements.txt"
        ):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256(source) != sha256(target):
            raise ValueError(f"Source changed during snapshot: {relative}")
        files[relative.as_posix()] = sha256(target)
    return files


def _environment() -> dict:
    packages = sorted(
        (d.metadata["Name"], d.version)
        for d in importlib.metadata.distributions()
        if d.metadata.get("Name")
    )
    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "packages": [{"name": name, "version": version} for name, version in packages],
        "invocation": sys.argv,
        "cwd": str(Path.cwd()),
        "gpu_probe": "not performed; GPU runs require explicit user approval",
    }


class Run:
    """A fresh directory stays running until all artifact hashes validate."""

    def __init__(self, root: Path, repo: Path, configuration: dict) -> None:
        self.root = Path(root)
        if Path(repo).is_symlink():
            raise ValueError(f"Source snapshot refuses symbolic link: {repo}")
        self.repo = Path(repo).resolve()
        self.configuration = json.loads(json.dumps(configuration, allow_nan=False))
        self.path = self.root / (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid4().hex
        )
        self.started = datetime.now(UTC).isoformat()
        self.clock = time.perf_counter()
        self.timing = TimingLedger()

    def _require_running(self) -> None:
        status = json.loads((self.path / "metadata/status.json").read_text())
        if status.get("status") != "running":
            raise ValueError("Timing can only change while a run is running")

    @contextmanager
    def measure(self, stage: str, *, frames: int | None = None) -> Iterator[None]:
        """Time a named operation; counts belong to that stage's work unit."""
        self._require_running()
        with self.timing.measure(stage, frames=frames):
            yield

    def set_processed_frames(self, frames: int) -> None:
        """Set unique image count for whole-run throughput, independent of stages."""
        self._require_running()
        self.timing.set_processed_frames(frames)

    def _write_timing(self, *, completed: bool) -> None:
        elapsed = time.perf_counter() - self.clock
        write_json(
            self.path / "metadata/timing.json",
            {
                "started_utc": self.started,
                "ended_utc": datetime.now(UTC).isoformat(),
                "elapsed_seconds": elapsed,
                **self.timing.summary(elapsed, completed=completed),
            },
        )

    def __enter__(self) -> Self:
        self.path.mkdir(parents=True, exist_ok=False)
        for name in ("input", "output", "debug", "metadata"):
            (self.path / name).mkdir()
        write_json(
            self.path / "metadata/status.json",
            {"status": "running", "started_utc": self.started},
        )
        try:
            self._capture()
        except BaseException as error:
            self._failed(error)
            raise
        return self

    def _capture(self) -> None:
        metadata = self.path / "metadata"
        git = {
            "commit": _git(self.repo, "rev-parse", "HEAD").strip(),
            "status": _git(
                self.repo, "status", "--porcelain=v1", "--untracked-files=all"
            ),
            "working_diff": _git(self.repo, "diff", "--binary"),
            "staged_diff": _git(self.repo, "diff", "--cached", "--binary"),
        }
        write_json(metadata / "git.json", git)
        write_json(metadata / "configuration.json", self.configuration)
        write_json(metadata / "environment.json", _environment())
        sources = _snapshot(self.repo, metadata / "source", self.root)
        write_json(metadata / "source_snapshot.json", {"files": sources})

    def _failed(self, error: BaseException) -> None:
        write_json(
            self.path / "metadata/status.json",
            {
                "status": "failed",
                "started_utc": self.started,
                "ended_utc": datetime.now(UTC).isoformat(),
                "elapsed_seconds": time.perf_counter() - self.clock,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
        try:
            self._write_timing(completed=False)
        except (OSError, ValueError) as timing_error:
            # Failure status must survive an independently unwritable timing file.
            raise error from timing_error

    def finish(self) -> None:
        metadata = self.path / "metadata"
        status = json.loads((metadata / "status.json").read_text(encoding="utf-8"))
        if status["status"] != "running":
            raise ValueError("Only running runs can finish")
        self._write_timing(completed=True)
        manifest = {"schema_version": 1, "files": _inventory(self.path)}
        write_json(metadata / "manifest.json", manifest)
        _validate_inventory(self.path, manifest)
        write_json(
            metadata / "status.json",
            {
                "status": "complete",
                "manifest_sha256": sha256(metadata / "manifest.json"),
            },
        )

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        if error is not None:
            self._failed(error)
            return False
        try:
            status = json.loads(
                (self.path / "metadata/status.json").read_text(encoding="utf-8")
            )
            if status["status"] == "complete":
                verify_run(self.path)
            else:
                self.finish()
        except BaseException as failure:
            self._failed(failure)
            raise
        return False
