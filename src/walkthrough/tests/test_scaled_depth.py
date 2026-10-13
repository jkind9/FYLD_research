"""ZipDepth scaled per frame from a few recorded depth pixels, inside the depth layer."""

import argparse
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from src.walkthrough.steps import depth as depth_step
from src.walkthrough.steps import objects as objects_step
from src.walkthrough.steps.contracts import Calibration, DepthPrediction

SHAPE = (6, 8)
ROWS, COLS = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1]]
TRUE_DEPTH_M = 0.8 + 0.1 * ROWS + 0.05 * COLS


class FakeZipDepth:
    """Stands in for experiment 02's ZipDepth adapter: returns a chosen inverse-depth map."""

    raw = 2.5 / TRUE_DEPTH_M + 0.7  # unknown scale and shift in inverse-depth space
    load_error: Exception | None = None
    created: list = []  # noqa: RUF012  (reset by the fixture before each test)

    def __init__(self, checkpoint, build="gpu", device="cuda", input_size=384):
        FakeZipDepth.created.append({"checkpoint": checkpoint, "build": build, "device": device})

    def load(self):
        if FakeZipDepth.load_error is not None:
            raise FakeZipDepth.load_error

        def predict(frames, *, run):
            for frame in frames:
                raw = np.array(FakeZipDepth.raw, dtype=float)
                valid = np.isfinite(raw)
                yield SimpleNamespace(frame_id=frame.frame_id, depth=raw, valid=valid)

        return predict


class FakeRecorded:
    """Stands in for RecordedSensorDepth: true metres, with one hole."""

    def __init__(self, root):
        self.root = root

    def load(self):
        def read(frames, *, run):
            for frame in frames:
                valid = np.ones(SHAPE, dtype=bool)
                valid[0, 0] = False
                yield DepthPrediction(frame.frame_id, np.where(valid, TRUE_DEPTH_M, np.nan), valid)

        return read


@pytest.fixture
def fakes(monkeypatch):
    FakeZipDepth.raw = 2.5 / TRUE_DEPTH_M + 0.7
    FakeZipDepth.load_error = None
    FakeZipDepth.created = []
    monkeypatch.setattr(depth_step.zipdepth_owner, "ZipDepth", FakeZipDepth)
    monkeypatch.setattr(depth_step, "RecordedSensorDepth", FakeRecorded)
    chosen: list[np.ndarray] = []
    original = depth_step.sparse_points.choose_fit_pixels

    def spy(eligible, count, rng):
        mask = original(eligible, count, rng)
        chosen.append(mask)
        return mask

    monkeypatch.setattr(depth_step.sparse_points, "choose_fit_pixels", spy)
    return chosen


def _run(tmp_path: Path, method, frames: int = 2):
    calibration = Calibration(SHAPE[1], SHAPE[0], 5.0, 5.0, 4.0, 3.0, "x-right_y-down_z-forward")
    rows = []
    for index in range(frames):
        Image.fromarray(np.zeros((*SHAPE, 3), dtype=np.uint8), mode="RGB").save(tmp_path / f"{index}.png")
        rows.append(
            {
                "frame_id": f"frame-{index}",
                "timestamp_s": float(index),
                "image": f"{index}.png",
                "calibration": asdict(calibration),
                "phone_grid": None,
            }
        )
    context = SimpleNamespace(path=tmp_path, measure=lambda *_a, **_k: nullcontext())
    return depth_step.run(context, {"frames": rows}, method)


def _method(**overrides):
    settings = {"checkpoint": Path("phone.pth"), "reference_root": Path("tum"), "points_per_frame": 10}
    return depth_step.ScaledZipDepth(**{**settings, **overrides})


def test_fit_recovers_true_metres_through_the_depth_layer(tmp_path, fakes):
    row, output = _run(tmp_path, _method())

    assert row.status == "complete", row.reason
    assert output["control"] == "reference"
    for frame in output["frames"]:
        with np.load(tmp_path / frame["arrays"]) as saved:
            assert saved["valid"].all()
            np.testing.assert_allclose(saved["depth"], TRUE_DEPTH_M, atol=1e-6)
    assert FakeZipDepth.created[0]["build"] == "npu"


def test_exactly_the_requested_points_are_used_and_repeat_for_a_seed(tmp_path, fakes):
    FakeZipDepth.raw = FakeZipDepth.raw.copy()
    FakeZipDepth.raw[2, 3] = np.nan  # ZipDepth has no answer here

    (tmp_path / "a").mkdir()
    _run(tmp_path / "a", _method(), frames=2)
    first = [mask.copy() for mask in fakes]
    fakes.clear()
    (tmp_path / "b").mkdir()
    _run(tmp_path / "b", _method(), frames=2)

    assert [int(mask.sum()) for mask in first] == [10, 10]
    assert not any(mask[0, 0] or mask[2, 3] for mask in first)  # sensor hole, ZipDepth hole
    assert not np.array_equal(first[0], first[1])  # each frame draws its own points
    for again, before in zip(fakes, first, strict=True):
        np.testing.assert_array_equal(again, before)


def test_too_few_eligible_pixels_fails_the_frame_by_name(tmp_path, fakes):
    row, output = _run(tmp_path, _method(points_per_frame=100))

    assert row.status == "failed"
    assert "frame-0" in row.reason and "100" in row.reason
    assert output is None


def test_a_non_positive_scale_fails_instead_of_flipping_near_and_far(tmp_path, fakes):
    FakeZipDepth.raw = -2.5 / TRUE_DEPTH_M + 5.0

    row, _ = _run(tmp_path, _method())

    assert row.status == "failed"
    assert "scale" in row.reason


def test_fitted_depth_beyond_the_cap_is_invalid(tmp_path, fakes):
    FakeZipDepth.raw = FakeZipDepth.raw.copy()
    FakeZipDepth.raw[5, 7] = 2.5 / 25.0 + 0.7  # this pixel fits to 25 m

    row, output = _run(tmp_path, _method())

    assert row.status == "complete", row.reason
    with np.load(tmp_path / output["frames"][0]["arrays"]) as saved:
        assert not saved["valid"][5, 7]
        assert saved["valid"].sum() == SHAPE[0] * SHAPE[1] - 1


@pytest.mark.parametrize(
    "missing,expected",
    [("zipdepth.inference", "PYTHONPATH"), ("cv2", "'cv2'")],
)
def test_missing_code_makes_the_layer_unavailable_with_the_right_fix(tmp_path, fakes, missing, expected):
    FakeZipDepth.load_error = ModuleNotFoundError(f"No module named {missing!r}", name=missing)

    row, output = _run(tmp_path, _method())

    assert row.status == "unavailable"
    assert expected in row.reason
    assert output is None


@pytest.mark.parametrize("points", [1, 0, 2.5, True])
def test_points_per_frame_must_be_an_integer_of_at_least_two(points):
    with pytest.raises(ValueError, match="points_per_frame"):
        _method(points_per_frame=points)


def test_cli_scaled_choice_uses_the_phone_checkpoint_by_default():
    from src.walkthrough.cli import DEFAULT_DEPTH_CHECKPOINTS, depth_choice

    args = argparse.Namespace(
        depth="zipdepth-scaled", depth_checkpoint=None, dataset=Path("tum"), device="cpu", points_per_frame=50
    )
    method = depth_choice(args)

    assert isinstance(method, depth_step.ScaledZipDepth)
    assert method.checkpoint == DEFAULT_DEPTH_CHECKPOINTS["zipdepth-scaled"]
    assert method.checkpoint.name == "zipdepth_base_npu.pth"
    assert method.reference_root == Path("tum")
    other = depth_choice(argparse.Namespace(**{**vars(args), "depth": "depth-anything"}))
    assert other.checkpoint == DEFAULT_DEPTH_CHECKPOINTS["depth-anything"]


def test_detector_device_reaches_the_detector(monkeypatch):
    seen = []
    monkeypatch.setattr(
        objects_step.detector_owner, "YoloDetector", lambda checkpoint, device: seen.append(device)
    )

    objects_step.Yolo26x(Path("checkpoints/yolo26x.pt"), device="0").load()

    assert seen == ["0"]
    with pytest.raises(ValueError, match="device"):
        objects_step.Yolo26x(Path("checkpoints/yolo26x.pt"), device="1")
