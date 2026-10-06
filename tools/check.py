"""Run CPU checks with all generated files under the operating system temp folder."""

import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = ROOT / "task_list"
TASK_ROOT_FILES = {".journal.log", "CONSTITUTION.md", "README.md"}
TASK_GROUPS = {"archive", "closed", "open", "pending_review", "stale"}


def _find_task_list_leaks(
    entries: Iterable[tuple[Path, bool, bool, bool]],
) -> tuple[str, ...]:
    """Return paths outside the task board's allowed files and folders."""
    leaks: list[str] = []
    for relative, is_file, is_directory, is_symlink in sorted(
        entries, key=lambda entry: entry[0].as_posix()
    ):
        parts = relative.parts
        if is_symlink:
            allowed = False
        elif len(parts) == 1:
            allowed = (is_file and relative.name in TASK_ROOT_FILES) or (
                is_directory and relative.name in TASK_GROUPS
            )
        elif len(parts) == 2:
            allowed = parts[0] in TASK_GROUPS and is_file and relative.suffix.lower() == ".md"
        else:
            allowed = False

        if not allowed:
            leaks.append(relative.as_posix())
    return tuple(leaks)


def find_task_list_leaks(task_root: Path) -> tuple[str, ...]:
    """Return task-board paths that are not task records or board metadata."""
    if not task_root.is_dir():
        raise FileNotFoundError(f"Task board directory does not exist: {task_root}")

    entries = (
        (path.relative_to(task_root), path.is_file(), path.is_dir(), path.is_symlink())
        for path in task_root.rglob("*")
    )
    return _find_task_list_leaks(entries)


def main() -> int:
    leaks = find_task_list_leaks(TASK_ROOT)
    if leaks:
        print("Task board contains non-task files or folders:", file=sys.stderr)
        for leak in leaks:
            print(f"  {leak}", file=sys.stderr)
        return 2

    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    args = sys.argv[1:] or [
        "src/walkthrough/tests",
        "experiments/geometry_validation/tests",
        "experiments/shared/tests",
        "experiments/evaluation/tests",
        "experiments/datasets/tests",
        "experiments/04_surface_reconstruction/tests",
        "experiments/03_camera_pose_estimation/tests",
        "experiments/06_object_recognition/tests",
        "experiments/06_object_recognition/shared/tests",
        "experiments/06_object_recognition/datasets/tests",
        "experiments/06_object_recognition/experiments/01_detection/tests",
        "experiments/06_object_recognition/experiments/02_segmentation/tests",
        "experiments/06_object_recognition/experiments/03_appearance/tests",
        "experiments/06_object_recognition/experiments/04_geometry_identity/tests",
        "experiments/06_object_recognition/experiments/05_replay/tests",
        "tools/demos/tests",
        "tools/tests",
    ]
    with tempfile.TemporaryDirectory(prefix="fyld-scene-mapping-checks-") as scratch:
        cache = Path(scratch)
        environment.update(
            {
                "COVERAGE_FILE": str(cache / "coverage"),
                "MYPY_CACHE_DIR": str(cache / "mypy"),
                "RUFF_CACHE_DIR": str(cache / "ruff"),
            }
        )
        command = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(cache / "pytest"),
            *args,
        ]
        return subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
