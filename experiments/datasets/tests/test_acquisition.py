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


def test_tum_download_verifies_publisher_length_and_records_local_hash(
    tmp_path, monkeypatch
):
    calls = []

    def response(request, timeout):
        calls.append(request.get_method())
        return (
            Response(length=4, url="https://cvg.cit.tum.de/archive")
            if request.get_method() == "HEAD"
            else Response(b"data", url="https://webshare.cvg.cit.tum.de/archive")
        )

    monkeypatch.setattr(acquisition.urllib.request, "urlopen", response)
    archive = tmp_path / "fresh" / "desk.tgz"

    receipt = acquisition.download_tum_desk(archive)

    assert calls == ["HEAD", "GET"]
    assert archive.read_bytes() == b"data"
    assert receipt["bytes"] == 4
    assert receipt["local_sha256"] == acquisition.sha256(archive)
    assert receipt["checksum_status"] == "local content hash only; publisher checksum not listed"
    assert receipt["licence"] == "CC BY 4.0 unless otherwise specified"
    assert archive.parent.is_dir()
    assert archive.with_name("desk.tgz.json").is_file()


@pytest.mark.parametrize(
    "length,url",
    [
        (acquisition.TUM_MAX_COMPRESSED_BYTES + 1, "https://cvg.cit.tum.de/archive"),
        (4, "https://unexpected.invalid/archive"),
    ],
)
def test_tum_download_rejects_oversize_or_untrusted_publisher(
    tmp_path, monkeypatch, length, url
):
    def response(request, timeout):
        return (
            Response(length=length, url="https://cvg.cit.tum.de/archive")
            if request.get_method() == "HEAD"
            else Response(b"data", url=url)
        )

    monkeypatch.setattr(acquisition.urllib.request, "urlopen", response)
    archive = tmp_path / "desk.tgz"

    with pytest.raises(ValueError):
        acquisition.download_tum_desk(archive)

    assert not archive.exists()


def test_tum_download_rejects_an_existing_acquisition_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(
        acquisition.urllib.request,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("network must not start while another writer holds the lock"),
    )
    archive = tmp_path / "desk.tgz"
    archive.with_name("desk.tgz.lock").write_text("active writer", encoding="utf-8")

    with pytest.raises(FileExistsError):
        acquisition.download_tum_desk(archive)


def test_tum_download_does_not_replace_a_destination_created_mid_publish(
    tmp_path, monkeypatch
):
    def response(request, timeout):
        return (
            Response(length=4, url="https://cvg.cit.tum.de/archive")
            if request.get_method() == "HEAD"
            else Response(b"data", url="https://webshare.cvg.cit.tum.de/archive")
        )

    monkeypatch.setattr(acquisition.urllib.request, "urlopen", response)
    archive = tmp_path / "desk.tgz"
    link = acquisition.os.link

    def create_destination_then_link(source, destination):
        if Path(destination) == archive:
            archive.write_bytes(b"external writer")
        return link(source, destination)

    monkeypatch.setattr(acquisition.os, "link", create_destination_then_link)
    with pytest.raises(FileExistsError):
        acquisition.download_tum_desk(archive)

    assert archive.read_bytes() == b"external writer"
    assert not archive.with_name("desk.tgz.json").exists()


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
