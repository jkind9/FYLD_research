"""APK handoffs use one destination and retain their exact bytes."""

import hashlib
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))
export = importlib.import_module("export")


def test_capture_publication_has_named_folder_and_email_copy(tmp_path):
    apk = tmp_path / "app-debug.apk"
    apk.write_bytes(b"synthetic APK bytes")
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    output = tmp_path / "mobile_deployments"
    published = export.publish_capture(apk, output)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    assert published.name == f"capture_{day}_{digest[:8]}"
    assert (published / "fyld-capture.apk").read_bytes() == apk.read_bytes()
    assert (published / "fyld-capture.apk.bin").read_bytes() == apk.read_bytes()
    assert digest in (published / "README.md").read_text()
    with pytest.raises(FileExistsError):
        export.publish_capture(apk, output)


def test_capture_rejects_non_apk(tmp_path):
    source = tmp_path / "wrong.txt"
    source.write_bytes(b"wrong file")
    with pytest.raises(ValueError, match="APK"):
        export.publish_capture(source, tmp_path / "mobile_deployments")


def test_capture_rejects_corrupted_copy(tmp_path, monkeypatch):
    apk = tmp_path / "debug.apk"
    apk.write_bytes(b"APK")
    monkeypatch.setattr(export.shutil, "copyfile", lambda _, dst: Path(dst).write_bytes(b"bad"))
    output = tmp_path / "mobile_deployments"
    with pytest.raises(ValueError, match="hash"):
        export.publish_capture(apk, output)
    assert not list(output.glob("capture_*"))
