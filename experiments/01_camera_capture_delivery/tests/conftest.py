import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

# the host modules import each other by file name; fake_phone is shared with open_vio and src/live tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def publication_time(monkeypatch):
    instant = datetime(2026, 10, 14, 22, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(importlib.import_module("export"), "datetime", SimpleNamespace(now=lambda _: instant))
