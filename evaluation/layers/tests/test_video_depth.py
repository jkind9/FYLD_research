"""Metric Video Depth Anything Small as a walkthrough depth choice, with its code faked."""

import sys
import types
from pathlib import Path

import numpy as np
import pytest

from src.walkthrough.records import Unavailable
from src.walkthrough.steps import video_depth
from src.walkthrough.steps.contracts import Calibration, ColourFrame

CAMERA = Calibration(8, 6, 5.0, 5.0, 4.0, 3.0, "x-right_y-down_z-forward")


class FakeVideoModel:
    """Stands in for upstream VideoDepthAnything: depth 1.0, 1.5, 2.0 ... metres per frame."""

    created: list = []  # noqa: RUF012  (reset by the fixture)
    calls: list = []  # noqa: RUF012

    def __init__(self, **settings):
        FakeVideoModel.created.append(settings)

    def load_state_dict(self, weights, strict):
        assert strict is True

    def eval(self):
        return self

    def to(self, device):
        return self

    def infer_video_depth(self, frames, target_fps, input_size, device, fp32):
        FakeVideoModel.calls.append({"shape": frames.shape, "input_size": input_size, "device": device, "fp32": fp32})
        depth = np.stack([np.full(frames.shape[1:3], 1.0 + 0.5 * i) for i in range(len(frames))])
        depth[0, 0, 0] = 25.0  # beyond the 20 m cap
        return depth, target_fps


@pytest.fixture
def fake_code(monkeypatch):
    FakeVideoModel.created, FakeVideoModel.calls = [], []
    package = types.ModuleType("video_depth_anything")
    module = types.ModuleType("video_depth_anything.video_depth")
    module.VideoDepthAnything = FakeVideoModel
    monkeypatch.setitem(sys.modules, "video_depth_anything", package)
    monkeypatch.setitem(sys.modules, "video_depth_anything.video_depth", module)
    monkeypatch.setattr(video_depth, "_load_weights", lambda path: {"weights": str(path)})


def _frames(count=3):
    return [ColourFrame(f"f{i}", float(i), CAMERA, np.zeros((6, 8, 3), dtype=np.uint8)) for i in range(count)]


def test_runs_the_small_metric_model_once_over_the_whole_clip_on_the_cpu(fake_code, tmp_path):
    checkpoint = tmp_path / "metric_video_depth_anything_vits.pth"
    checkpoint.write_bytes(b"x")
    method = video_depth.MetricVideoDepthAnything(checkpoint)

    out = list(method.load()(iter(_frames()), run=None))

    assert FakeVideoModel.created == [
        {"encoder": "vits", "features": 64, "out_channels": [48, 96, 192, 384], "metric": True}
    ]
    assert FakeVideoModel.calls == [{"shape": (3, 6, 8, 3), "input_size": 518, "device": "cpu", "fp32": True}]
    assert [p.frame_id for p in out] == ["f0", "f1", "f2"]
    assert out[1].depth[2, 2] == pytest.approx(1.5)
    assert not out[0].valid[0, 0] and np.isnan(out[0].depth[0, 0])  # past 20 m
    assert out[0].valid.sum() == 6 * 8 - 1
    assert method.control is None and method.name == "metric_video_depth_anything_small"


def test_missing_code_names_the_folder_to_put_on_pythonpath(monkeypatch, tmp_path):
    checkpoint = tmp_path / "w.pth"
    checkpoint.write_bytes(b"x")
    monkeypatch.setitem(sys.modules, "video_depth_anything", None)  # import fails

    with pytest.raises(Unavailable, match="PYTHONPATH"):
        video_depth.MetricVideoDepthAnything(checkpoint).load()


def test_missing_checkpoint_is_reported_before_loading(fake_code, tmp_path):
    with pytest.raises(FileNotFoundError, match="checkpoint"):
        video_depth.MetricVideoDepthAnything(tmp_path / "missing.pth").load()


def test_no_frames_gives_no_predictions(fake_code, tmp_path):
    checkpoint = tmp_path / "w.pth"
    checkpoint.write_bytes(b"x")

    assert list(video_depth.MetricVideoDepthAnything(checkpoint).load()(iter([]), run=None)) == []
    assert FakeVideoModel.calls == []


@pytest.mark.parametrize("device", ["gpu", "tpu"])
def test_device_must_be_cpu_or_cuda(device):
    with pytest.raises(ValueError, match="device"):
        video_depth.MetricVideoDepthAnything(Path("w.pth"), device=device)


def test_cli_offers_it_raw_and_with_the_overlap_chain():
    import argparse

    from src.walkthrough.cli import DEFAULT_DEPTH_CHECKPOINTS, depth_choice
    from src.walkthrough.steps.depth_scale import OverlapChainScale, ScaleCorrected

    args = argparse.Namespace(depth="video-depth-anything", depth_checkpoint=None, dataset=Path("tum"),
                              device="cpu", points_per_frame=50, depth_scale=None)
    raw = depth_choice(args)
    chained = depth_choice(argparse.Namespace(**{**vars(args), "depth_scale": "overlap-chain"}))

    assert isinstance(raw, video_depth.MetricVideoDepthAnything) and raw.device == "cpu"
    assert raw.checkpoint == DEFAULT_DEPTH_CHECKPOINTS["video-depth-anything"]
    assert isinstance(chained, ScaleCorrected) and isinstance(chained.scale, OverlapChainScale)
