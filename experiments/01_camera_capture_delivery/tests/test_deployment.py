"""APK handoffs use one destination and retain their exact bytes."""

import hashlib
import importlib
import sys
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))
export = importlib.import_module("export")
deployment = importlib.import_module("deployment")
pytestmark = pytest.mark.usefixtures("publication_time")


def test_capture_publication_has_named_folder_and_email_copy(tmp_path):
    apk = tmp_path / "app-debug.apk"
    apk.write_bytes(b"synthetic APK bytes")
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    output = tmp_path / "mobile_deployments"
    published = export.publish_capture(apk, output, "1.2")
    assert published.name == f"capture_v1.2_20261014T220000Z_{digest[:8]}"
    filename = "fyld-capture_v1.2_20261014T220000Z.apk"
    assert (published / filename).read_bytes() == apk.read_bytes()
    assert (published / f"{filename}.bin").read_bytes() == apk.read_bytes()
    assert digest in (published / "README.md").read_text()
    with pytest.raises(FileExistsError):
        export.publish_capture(apk, output, "1.2")


def test_capture_rejects_non_apk(tmp_path):
    source = tmp_path / "wrong.txt"
    source.write_bytes(b"wrong file")
    with pytest.raises(ValueError, match="APK"):
        export.publish_capture(source, tmp_path / "mobile_deployments", "1.2")


def test_capture_rejects_corrupted_copy(tmp_path, monkeypatch):
    apk = tmp_path / "debug.apk"
    apk.write_bytes(b"APK")
    monkeypatch.setattr(export.shutil, "copyfile", lambda _, dst: Path(dst).write_bytes(b"bad"))
    output = tmp_path / "mobile_deployments"
    with pytest.raises(ValueError, match="hash"):
        export.publish_capture(apk, output, "1.2")
    assert not list(output.glob("capture_*"))


@pytest.mark.parametrize("version", ["", "../escape", "1/2"])
def test_publication_rejects_unsafe_version(version):
    with pytest.raises(ValueError, match="version"):
        export.bundle_name("capture", "a" * 64, version)


@pytest.mark.parametrize("badging, expected", [("package: name='org.fyld.capture' versionName='1.2'", "1.2"),
                                               ("package: name='org.fyld.capture'", None)])
def test_version_comes_from_built_apk(monkeypatch, badging, expected):
    calls = []
    monkeypatch.setattr(deployment.subprocess, "check_output", lambda args, **_: calls.append(args) or badging)
    if expected is None:
        with pytest.raises(ValueError, match="versionName"):
            deployment.apk_version(Path("debug.apk"), Path("aapt"))
    else:
        assert deployment.apk_version(Path("debug.apk"), Path("aapt")) == expected
    assert calls == [["aapt", "dump", "badging", "debug.apk"]]
