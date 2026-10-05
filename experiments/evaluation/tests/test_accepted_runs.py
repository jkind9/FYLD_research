"""Reproduce the owners' stored numbers from the four pinned accepted runs.

Run folders are gitignored. Point EVAL_RUNS_ROOT at the checkout that holds
them; without it these tests skip with that reason.
"""

import json
import os
from pathlib import Path

import pytest

from experiments.evaluation import run as runner
from experiments.evaluation import schema

ROOT = os.environ.get("EVAL_RUNS_ROOT")
pytestmark = pytest.mark.skipif(
    not ROOT, reason="EVAL_RUNS_ROOT not set; pinned run folders are gitignored"
)


def _section(stage: str) -> dict:
    pin = runner.PINNED[stage]
    return pin["wrapper"](
        Path(ROOT) / pin["path"],
        dataset=pin["dataset"],
        pinned_sha256=pin["sha256"],
        reference_kind=pin["reference_kind"],
    )


def _value(section: dict, method: str, name: str):
    return next(
        m["value"]
        for m in section["measures"]
        if m["method"] == method and m["name"] == name
    )


def test_camera_reproduces_task05_exactly():
    section = _section("camera_path")
    assert _value(section, "layer3_tracker", "position_rmse") == 0.006925680114771647


def test_detection_reproduces_task18_cup_counts_at_every_threshold():
    section = _section("detection")
    method = "cached_yolo26x_accepted_task28"
    for threshold in (0.3, 0.5, 0.7):
        assert _value(section, method, f"cup.matched@iou{threshold}") == 4
        assert _value(section, method, f"cup.missed@iou{threshold}") == 1
        assert _value(section, method, f"cup.false_detections@iou{threshold}") == 0
        assert _value(section, method, f"cup.precision@iou{threshold}") == 1.0
        assert _value(section, method, f"cup.recall@iou{threshold}") == 0.8
        assert _value(section, method, f"tv.precision@iou{threshold}") is None
    assert section["reference"]["kind"] == "provisional"


def test_surface_reproduces_task04_bit_for_bit():
    section = _section("surface")
    stored = json.loads(
        (
            Path(ROOT) / runner.PINNED["surface"]["path"] / "output/metrics.json"
        ).read_text()
    )
    method = "layer4_point_surface"
    assert _value(section, method, "accuracy_mean") == stored["accuracy"]["mean_m"]
    assert (
        _value(section, method, "reference_coverage_fraction")
        == stored["reference_coverage_fraction"]
    )


def test_identity_reproduces_task21_for_all_five_conditions():
    section = _section("identity")
    assert len({m["method"] for m in section["measures"]}) == 5
    assert _value(section, "combined-viewmedian", "matched") == 11
    assert _value(section, "appearance-viewmedian", "unresolved") == 4


def test_composite_report_has_all_stages():
    report = runner.build(Path(ROOT))
    statuses = {s["stage"]: s["status"] for s in report["sections"]}
    assert list(statuses) == list(schema.STAGES)
    assert sum(v == "scored" for v in statuses.values()) == 4
