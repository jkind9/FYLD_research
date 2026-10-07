"""Pin the swappable layer choices and their control labels."""

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from experiments.shared.contracts import Pose
from experiments.shared.runs import write_json
from src.walkthrough import validation
from src.walkthrough.records import StepResult
from src.walkthrough.steps import depth, mapping, tracking
from src.walkthrough.steps.capture import TumSequence, pose_dataset


def test_reference_choices_are_distinct_from_measurements(tmp_path: Path) -> None:
    from src.walkthrough.config import PipelineSpec
    from src.walkthrough.steps.capture import TumSequence
    from src.walkthrough.steps.depth import RecordedSensorDepth
    from src.walkthrough.steps.tracking import ReferencePoses

    spec = PipelineSpec(
        tmp_path / "runs",
        Path.cwd(),
        TumSequence(tmp_path),
        depth=RecordedSensorDepth(tmp_path),
        tracking=ReferencePoses(tmp_path / "groundtruth.txt"),
    )
    assert spec.controls == {"depth": "reference", "tracking": "reference"}


@dataclass(frozen=True)
class LoadSpy:
    name: str = "spy"
    control: None = None

    def load(self):
        raise AssertionError("Method loaded before its input was validated")


def test_missing_depth_calibration_prevents_method_loading(tmp_path):
    capture = {"frames": [{"calibration": None, "phone_grid": None}]}
    row, output = depth.run(SimpleNamespace(path=tmp_path), capture, LoadSpy())
    assert row.status == "unavailable"
    assert "calibration" in row.reason
    assert output is None


def test_missing_tracking_clock_prevents_method_loading(tmp_path):
    capture = {"frames": [{"timestamp_s": None, "timestamp_source": None}]}
    row, output = tracking.run(SimpleNamespace(path=tmp_path), capture, {}, LoadSpy())
    assert row.status == "unavailable"
    assert "timestamp" in row.reason
    assert output is None


@pytest.mark.parametrize(
    "measurement",
    [
        None,
        {},
        {"value": 7},
        {"units": "metres"},
        {"value": None, "units": "metres"},
        {"value": True, "units": "metres"},
        {"value": 7, "units": ""},
        {"value": float("nan"), "units": "metres"},
        {"value": 7, "units": None},
    ],
)
def test_predictive_mapping_refuses_values_without_numeric_measurement_and_units(
    measurement,
):
    with pytest.raises(ValueError, match="finite value and explicit units"):
        mapping.validate(
            {
                "methods": {"mapping": "test"},
                "control": None,
                "measurements": {"length": measurement},
            }
        )


def test_predictive_mapping_accepts_finite_measurement_with_units():
    mapping.validate(
        {
            "methods": {"mapping": "test"},
            "control": None,
            "measurements": {"length": {"value": 7, "units": "metres"}},
        }
    )


def test_missing_reference_file_is_visible_when_tracking_is_skipped(tmp_path):
    request = validation.ScoreRequest(
        "tracking",
        lambda: pytest.fail("Truth loaded"),
        reference_file=tmp_path / "missing.txt",
    )
    rows = (StepResult("tracking", "skipped", "depth is unavailable"),)
    scores = validation.score(tmp_path, rows, (request,))
    assert scores["tracking"]["status"] == "unavailable"
    assert "depth is unavailable" in scores["tracking"]["reason"]
    assert scores["tracking"]["reference_sha256"] is None
    assert "FileNotFoundError" in scores["tracking"]["reference_unavailable_reason"]


def test_unsupported_scorer_does_not_open_missing_reference_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        validation, "sha256", lambda path: pytest.fail("Reference opened")
    )
    request = validation.ScoreRequest(
        "detection",
        lambda: pytest.fail("Truth loaded"),
        reference_file=tmp_path / "missing.txt",
    )
    scores = validation.score(tmp_path, (), (request,))
    assert scores["detection"]["status"] == "unavailable"
    assert "Task56" in scores["detection"]["reason"]
    assert scores["detection"]["reference_sha256"] is None


def test_tracking_scoring_keeps_worlds_separate_with_same_segment_id(tmp_path):
    records = []
    references = []
    for index, (world, position, reference_position) in enumerate(
        [("a", 0, 0), ("a", 1, 1), ("b", 0, 10), ("b", 1, 11)]
    ):
        matrix = np.eye(4)
        matrix[0, 3] = position
        reference = np.eye(4)
        reference[0, 3] = reference_position
        timestamp = float(index + 1)
        records.append(
            {
                "frame_id": str(index),
                "timestamp_s": timestamp,
                "status": "tracked",
                "reason": "test",
                "pose": Pose(matrix, world, "0", "estimated").to_dict(),
            }
        )
        references.append((timestamp, reference))
    artifact = "output/predictions/tracking.json"
    write_json(
        tmp_path / artifact, {"methods": {}, "control": None, "records": records}
    )
    saved_before = (tmp_path / artifact).read_bytes()
    request = validation.ScoreRequest(
        "tracking", lambda: references, {"tolerance": 0.0}
    )
    step = StepResult("tracking", "complete", "test", artifact=artifact)
    scores = validation.score(tmp_path, (step,), (request,))["tracking"]["result"]
    assert scores["position_rmse_m"] == 0
    assert len(scores["segments"]) == 2
    assert (tmp_path / artifact).read_bytes() == saved_before
    assert all(
        row["pose"]["segment_id"] == "0" for row in json.loads(saved_before)["records"]
    )


def test_tum_capture_detaches_calibration_from_other_frames_and_runs(tmp_path):
    (tmp_path / "rgb").mkdir()
    for index in range(2):
        Image.new("RGB", (640, 480)).save(tmp_path / f"rgb/{index}.png")
    (tmp_path / "rgb.txt").write_text("1.7 rgb/0.png\n1.72 rgb/1.png\n")
    frames = TumSequence(tmp_path).read(SimpleNamespace(path=tmp_path / "run"))
    original_fx = pose_dataset.CALIBRATION.fx
    frames[0]["calibration"]["fx"] = 1.0
    assert frames[1]["calibration"]["fx"] == original_fx
    assert pose_dataset.CALIBRATION.fx == original_fx
