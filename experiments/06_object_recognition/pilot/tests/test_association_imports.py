"""The importable counting method keeps the historical replay boundary."""

import importlib
import subprocess
import sys
from copy import deepcopy

import pytest

PACKAGE = "experiments.06_object_recognition.pilot"


def test_method_import_does_not_load_replay_or_detector():
    script = (
        "import importlib, sys; "
        f"importlib.import_module('{PACKAGE}.association'); "
        f"assert '{PACKAGE}.replay' not in sys.modules; "
        f"assert '{PACKAGE}.detector' not in sys.modules"
    )
    subprocess.run([sys.executable, "-B", "-c", script], check=True)


def test_replay_reexports_same_method_and_keeps_settings():
    association = importlib.import_module(f"{PACKAGE}.association")
    replay = importlib.import_module(f"{PACKAGE}.replay")
    assert replay.associate_frame is association.associate_frame
    assert replay.ASSOCIATION_DISTANCE_M == 0.35
    assert replay.AMBIGUITY_MARGIN_M == 0.05
    assert replay.HYPERPARAMETERS["association"]["value"]["max_distance_m"] == 0.35


def test_importable_method_keeps_late_births_and_inputs():
    method = importlib.import_module(f"{PACKAGE}.association").associate_frame
    detection = {"class_id": 41, "label": "cup", "world_position_m": [0, 0, 1]}
    _, tracks, number = method([detection], {}, 1, 0.35, 0.05)
    returned = {**detection, "world_position_m": [1, 0, 1]}
    original = deepcopy((returned, tracks))
    records, updated, number = method([returned], tracks, number, 0.35, 0.05)
    assert records[0]["object_id"] == "object-0002"
    assert records[0]["association"] == "new"
    assert len(updated) == 2 and number == 3
    assert (returned, tracks) == original


@pytest.mark.parametrize("distance, margin", [(0, 0.05), (0.35, -1), (float("nan"), 0)])
def test_importable_method_preserves_invalid_setting_errors(distance, margin):
    method = importlib.import_module(f"{PACKAGE}.association").associate_frame
    with pytest.raises(ValueError, match="Association settings"):
        method([], {}, 1, distance, margin)
