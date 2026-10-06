from pathlib import Path

import pytest

from tools import check
from tools.check import _find_task_list_leaks

TaskPathEntry = tuple[Path, bool, bool, bool]


def _entry(
    path: str, *, file: bool = False, directory: bool = False, symlink: bool = False
) -> TaskPathEntry:
    return Path(path), file, directory, symlink


def test_task_board_metadata_and_task_records_are_allowed() -> None:
    entries = (
        _entry("README.md", file=True),
        _entry("CONSTITUTION.md", file=True),
        _entry(".journal.log", file=True),
        _entry("open", directory=True),
        _entry("open/01_example.md", file=True),
    )

    assert _find_task_list_leaks(entries) == ()


@pytest.mark.parametrize(
    "entry",
    [
        _entry("open/test_probe.py", file=True),
        _entry("closed/__pycache__/probe.pyc", file=True),
        _entry("open/.pytest_cache", directory=True),
        _entry("open/job_alloc_probe_123", directory=True),
        _entry("open/nested/01_example.md", file=True),
    ],
)
def test_pytest_and_unexpected_task_board_paths_are_reported(entry: TaskPathEntry) -> None:
    assert _find_task_list_leaks((entry,)) == (entry[0].as_posix(),)


def test_task_board_symlinks_are_reported() -> None:
    entry = _entry("open/linked_task.md", file=True, symlink=True)

    assert _find_task_list_leaks((entry,)) == (entry[0].as_posix(),)


def test_check_stops_before_pytest_when_task_board_has_a_leak(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check, "find_task_list_leaks", lambda _: ("open/test_probe.py",))
    monkeypatch.setattr(check.subprocess, "run", pytest.fail)

    assert check.main() == 2
    assert "open/test_probe.py" in capsys.readouterr().err
