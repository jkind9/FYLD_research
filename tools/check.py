"""Run CPU checks with all generated files under the operating system temp folder."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cache = Path(tempfile.gettempdir()) / "fyld-scene-mapping-checks" / uuid4().hex
    cache.mkdir(parents=True)
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "COVERAGE_FILE": str(cache / "coverage"),
        "MYPY_CACHE_DIR": str(cache / "mypy"),
        "RUFF_CACHE_DIR": str(cache / "ruff"),
    }
    args = sys.argv[1:] or [
        "experiments/geometry_validation/tests",
        "experiments/shared/tests",
        "experiments/datasets/tests",
        "experiments/04_surface_reconstruction/tests",
        "experiments/03_camera_pose_estimation/tests",
    ]
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
    result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    print(f"Check artifacts: {cache}")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
