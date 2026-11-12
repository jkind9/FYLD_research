"""Shared steps for every stage wrapper: verify the run, then load owner scorers."""

import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run


def verified_run(path: Path, pinned_sha256: str | None) -> dict:
    """Reject incomplete, damaged or unexpected runs before reading any output."""
    path = Path(path)
    verify_run(path)
    status = read_json(path / "metadata/status.json")
    digest = status["manifest_sha256"]
    if pinned_sha256 is not None and digest != pinned_sha256:
        raise ValueError(
            f"run manifest {digest} differs from pinned {pinned_sha256}: {path.name}"
        )
    return {"id": path.name, "manifest_sha256": digest}


def owner(module: str) -> ModuleType:
    """Digit-prefixed experiment folders cannot use a plain import statement."""
    return importlib.import_module(module)


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return sha256(Path(path))


def scope(items: list[str]) -> dict:
    """Fingerprint of exactly which items were scored, in scoring order."""
    payload = json.dumps([str(item) for item in items]).encode("utf-8")
    return {"items": len(items), "sha256": hashlib.sha256(payload).hexdigest()}


def require_keys(stored: dict, keys: tuple[str, ...], what: str) -> None:
    """Refuse to call a score reproduced when the run never stored it."""
    missing = [key for key in keys if key not in stored]
    if missing:
        raise ValueError(f"{what}: stored metrics lack {', '.join(missing)}")


def require_same(stored: Any, recomputed: Any, what: str) -> None:
    """A wrapper must give exactly the owner's stored numbers, or refuse."""
    if stored != recomputed:
        raise ValueError(f"{what} does not reproduce the run's stored score")
