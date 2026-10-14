import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "calibration"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vio"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from synthetic import write_recording  # noqa: E402


@pytest.fixture
def make_recording(tmp_path):
    def make(name="rec", **options):
        return write_recording(tmp_path / name, **options)
    return make
