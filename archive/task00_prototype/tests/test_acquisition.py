import io
import tarfile
from pathlib import Path

import pytest

from fyld_scene_mapping.acquisition import extract_tar


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../escape", "file"),
        ("/absolute", "file"),
        ("C:/escape", "file"),
        ("a\\b", "file"),
        ("link", "symlink"),
    ],
)
def test_unsafe_archives_are_rejected(tmp_path: Path, name: str, kind: str) -> None:
    archive = tmp_path / "bad.tgz"
    with tarfile.open(archive, "w:gz") as stream:
        member = tarfile.TarInfo(name)
        if kind == "symlink":
            member.type, member.linkname = tarfile.SYMTYPE, "outside"
            stream.addfile(member)
        else:
            member.size = 1
            stream.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ValueError):
        extract_tar(archive, tmp_path / "extracted")
    assert not (tmp_path / "extracted").exists()


def test_expanded_budget_and_no_overwrite(tmp_path: Path) -> None:
    archive = tmp_path / "sample.tgz"
    with tarfile.open(archive, "w:gz") as stream:
        member = tarfile.TarInfo("safe/file")
        member.size = 4
        stream.addfile(member, io.BytesIO(b"data"))
    with pytest.raises(ValueError):
        extract_tar(archive, tmp_path / "out", max_expanded_bytes=3)
    extract_tar(archive, tmp_path / "out")
    assert (tmp_path / "out/safe/file").read_bytes() == b"data"
    with pytest.raises(FileExistsError):
        extract_tar(archive, tmp_path / "out")
