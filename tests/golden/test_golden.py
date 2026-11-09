"""Today's room build and live processor still give the saved outputs on the TUM fixture."""

import json
from pathlib import Path

import numpy as np
import pytest

from src.live.run import DEPTH_CHECKPOINT
from tests.golden import run

FIXTURES = Path(__file__).parents[1] / "fixtures"
SESSION = FIXTURES / "tum_desk_20"
GOLDEN = json.loads((FIXTURES / "tum_desk_20_golden.json").read_text(encoding="utf-8"))
# Counts may move by 0.1% and lengths by 1 mm when a thread count or library build changes the sums' order.
RELATIVE = 1e-3
ABSOLUTE = 1e-3

pytestmark = [pytest.mark.golden,
              pytest.mark.skipif(not DEPTH_CHECKPOINT.exists(), reason="depth model weights are local only")]


def numbers(value, path=""):
    if isinstance(value, dict):
        return {k: v for key in value for k, v in numbers(value[key], f"{path}/{key}").items()}
    if isinstance(value, list):
        return {k: v for i, item in enumerate(value) for k, v in numbers(item, f"{path}/{i}").items()}
    return {path: value}


def assert_matches(saved, now):
    saved, now = numbers(saved), numbers(now)
    assert saved.keys() == now.keys()
    for path, value in saved.items():
        if isinstance(value, float):
            assert np.isclose(now[path], value, rtol=RELATIVE, atol=ABSOLUTE), path
        elif isinstance(value, int) and not isinstance(value, bool):
            assert abs(now[path] - value) <= RELATIVE * abs(value), path
        else:
            assert now[path] == value, path


def test_numbers_flattens_nested_records():
    assert numbers({"a": [1, {"b": 2.0}], "c": "x"}) == {"/a/0": 1, "/a/1/b": 2.0, "/c": "x"}


def test_room_matches_golden():
    assert_matches(GOLDEN["room"], run.room(SESSION))


def test_live_matches_golden():
    assert_matches(GOLDEN["live"], run.live(SESSION))
