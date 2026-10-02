"""Independent failure cases for bounded publication of downloaded archives."""

import importlib.util
import io
import tarfile
from pathlib import Path

import pytest

MODULE = Path(__file__).parents[1] / "acquisition.py"
spec = importlib.util.spec_from_file_location("acquisition", MODULE)
acquisition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquisition)


def make_archive(path: Path, names: tuple[str, ...], link: bool = False) -> None:
    with tarfile.open(path, "w:gz") as stream:
        for name in names:
            member = tarfile.TarInfo(name)
            if link:
                member.type, member.linkname = tarfile.SYMTYPE, "outside"
                stream.addfile(member)
            else:
                member.size = 4
                stream.addfile(member, io.BytesIO(b"data"))


@pytest.mark.parametrize(
    "names,link",
    [
        (("../escape",), False),
        (("/absolute",), False),
        (("C:/escape",), False),
        (("a\\b",), False),
        (("link",), True),
        (("same", "same"), False),
        (("Same", "same"), False),
        (("NUL",), False),
        (("a.",), False),
        (("EXTRACTION.json",), False),
    ],
)
def test_unsafe_archive_never_publishes(tmp_path, names, link):
    archive, destination = tmp_path / "bad.tgz", tmp_path / "out"
    make_archive(archive, names, link)
    with pytest.raises(ValueError):
        acquisition.publish_archive(archive, destination)
    assert not destination.exists()


@pytest.mark.parametrize(
    "limits",
    [
        {"max_expanded_bytes": 3},
        {"max_member_bytes": 3},
        {"max_members": 0},
    ],
)
def test_bounds_never_publish(tmp_path, limits):
    archive = tmp_path / "bounded.tgz"
    make_archive(archive, ("safe",))
    with pytest.raises(ValueError):
        acquisition.publish_archive(archive, tmp_path / "out", **limits)
    assert not (tmp_path / "out").exists()


def test_truncated_gzip_never_publishes(tmp_path):
    archive = tmp_path / "truncated.tgz"
    make_archive(archive, ("safe",))
    archive.write_bytes(archive.read_bytes()[:-8])
    with pytest.raises((EOFError, OSError, tarfile.TarError)):
        acquisition.publish_archive(archive, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_valid_archive_and_no_overwrite(tmp_path):
    archive, destination = tmp_path / "good.tgz", tmp_path / "out"
    make_archive(archive, ("safe/file",))
    receipt = acquisition.publish_archive(archive, destination)
    assert (destination / "safe/file").read_bytes() == b"data"
    assert receipt["expanded_bytes"] == 4
    assert receipt["member_count"] == 1
    assert (destination / "EXTRACTION.json").is_file()
    with pytest.raises(FileExistsError):
        acquisition.publish_archive(archive, destination)


def test_oversized_pax_metadata_never_publishes(tmp_path):
    archive = tmp_path / "pax.tgz"
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as stream:
        member = tarfile.TarInfo("safe")
        member.size = 1
        member.pax_headers = {"comment": "x" * (2 * 1024**2)}
        stream.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="metadata/read"):
        acquisition.publish_archive(archive, tmp_path / "out")
    assert not (tmp_path / "out").exists()


class Response(io.BytesIO):
    def __init__(self, payload=b"", length=4, url="https://www.doc.ic.ac.uk/asset"):
        super().__init__(payload)
        self.headers = {"Content-Length": str(length)}
        self.url = url


@pytest.mark.parametrize(
    "length,payload,url,valid",
    [
        (4, b"data", "https://www.doc.ic.ac.uk/asset", True),
        (3, b"data", "https://www.doc.ic.ac.uk/asset", False),
        (4, b"dat", "https://www.doc.ic.ac.uk/asset", False),
        (4, b"extra", "https://www.doc.ic.ac.uk/asset", False),
        (4, b"data", "https://unexpected.invalid/asset", False),
    ],
)
def test_download_receipt_or_no_complete_archive(
    tmp_path, monkeypatch, length, payload, url, valid
):
    def response(request, timeout):
        return (
            Response(length=length)
            if hasattr(request, "get_method")
            else Response(payload, url=url)
        )

    monkeypatch.setattr(acquisition.urllib.request, "urlopen", response)
    archive = tmp_path / "download.tgz"
    if valid:
        metadata = acquisition.download("https://www.doc.ic.ac.uk/asset", archive, 4)
        assert archive.read_bytes() == b"data"
        assert metadata["bytes"] == 4 and metadata["licence"] == "CC BY 3.0"
        assert archive.with_name(archive.name + ".json").is_file()
        with pytest.raises(FileExistsError):
            acquisition.download("https://www.doc.ic.ac.uk/asset", archive, 4)
    else:
        with pytest.raises(ValueError):
            acquisition.download("https://www.doc.ic.ac.uk/asset", archive, 4)
        assert not archive.exists()


def test_gzip_budget_precedes_tar_parser(tmp_path):
    archive = tmp_path / "huge-metadata.tgz"
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as stream:
        member = tarfile.TarInfo("safe")
        member.size = 1
        member.pax_headers = {"comment": "x" * (1024**2)}
        stream.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="Gzip expansion"):
        acquisition.publish_archive(
            archive, tmp_path / "out", max_expanded_bytes=1, max_members=1
        )
    assert not (tmp_path / "out").exists()


def test_metadata_write_failure_never_publishes_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(
        acquisition.urllib.request,
        "urlopen",
        lambda request, timeout: Response(b"data"),
    )
    original = Path.write_text

    def fail_metadata(path, text, **kwargs):
        if path.name.endswith(".json"):
            raise OSError("injected receipt failure")
        return original(path, text, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_metadata)
    archive = tmp_path / "download.tgz"
    with pytest.raises(OSError, match="injected"):
        acquisition.download("https://www.doc.ic.ac.uk/asset", archive, 4)
    assert not archive.exists()
    monkeypatch.setattr(Path, "write_text", original)
    acquisition.download("https://www.doc.ic.ac.uk/asset", archive, 4)
    assert archive.read_bytes() == b"data"
