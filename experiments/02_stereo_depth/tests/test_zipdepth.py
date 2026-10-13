"""Contracts for the local-only ZipDepth experiment adapter."""

import importlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

zipdepth = importlib.import_module("experiments.02_stereo_depth.zipdepth")


def test_zipdepth_declares_relative_inverse_depth_convention():
    method = zipdepth.ZipDepth(Path("checkpoint.pth"))

    assert method.output_convention == "relative_inverse_depth"
    assert method.name == "zipdepth_base_gpu"


def test_zipdepth_requires_a_local_checkpoint_before_loading_runtime(monkeypatch):
    imported = []
    monkeypatch.setattr(zipdepth.importlib, "import_module", lambda name: imported.append(name))
    monkeypatch.setattr(Path, "is_file", lambda _path: False)
    method = zipdepth.ZipDepth(Path("missing.pth"))

    with pytest.raises(FileNotFoundError, match="checkpoint"):
        method.load()

    assert imported == []


@pytest.mark.parametrize(
    "build,device,expected_unfold",
    [("gpu", "cuda", True), ("npu", "cpu", False)],
)
def test_zipdepth_loads_offline_with_selected_checkpoint_variant(
    monkeypatch, build, device, expected_unfold
):
    checkpoint = Path(f"zipdepth_{build}.pth")
    monkeypatch.setattr(Path, "is_file", lambda path: path == checkpoint)
    constructor_calls = []

    class FakeDepthInference:
        def __init__(self, **kwargs):
            constructor_calls.append(kwargs)

    fake_module = SimpleNamespace(DepthInference=FakeDepthInference)
    monkeypatch.setattr(zipdepth.importlib, "import_module", lambda name: fake_module)
    method = zipdepth.ZipDepth(checkpoint, build=build, device=device)

    method.load()

    assert constructor_calls == [
        {
            "checkpoint_path": str(checkpoint),
            "variant": "base",
            "device": device,
            "input_size": 384,
            "upsample_unfold": expected_unfold,
            "use_compile": False,
        }
    ]


def test_zipdepth_predicts_from_rgb_only_and_returns_typed_native_map(monkeypatch):
    checkpoint = Path("zipdepth_base.pth")
    monkeypatch.setattr(Path, "is_file", lambda path: path == checkpoint)
    captured = []

    class FakeDepthInference:
        def __init__(self, **_kwargs):
            pass

        def infer_image(self, image_bgr):
            captured.append(image_bgr.copy())
            return np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)

    fake_module = SimpleNamespace(DepthInference=FakeDepthInference)
    monkeypatch.setattr(zipdepth.importlib, "import_module", lambda _name: fake_module)
    method = zipdepth.ZipDepth(checkpoint, device="cpu")
    predict = method.load()
    rgb = np.array(
        [
            [[255, 0, 0], [0, 255, 0]],
            [[0, 0, 255], [5, 10, 15]],
        ],
        dtype=np.uint8,
    )
    frame = SimpleNamespace(frame_id="frame-7", colour=rgb)

    result = next(predict(iter([frame]), run=None))

    np.testing.assert_array_equal(captured[0], rgb[..., ::-1])
    assert isinstance(result, zipdepth.ZipDepthPrediction)
    assert result.frame_id == "frame-7"
    assert result.convention == "relative_inverse_depth"
    np.testing.assert_array_equal(result.valid, [[True, False], [True, True]])
    assert np.isnan(result.depth[0, 1])


def test_zipdepth_rejects_output_with_a_different_image_grid(monkeypatch):
    checkpoint = Path("zipdepth_base.pth")
    monkeypatch.setattr(Path, "is_file", lambda path: path == checkpoint)

    class FakeDepthInference:
        def __init__(self, **_kwargs):
            pass

        def infer_image(self, _image_bgr):
            return np.ones((1, 2), dtype=np.float32)

    fake_module = SimpleNamespace(DepthInference=FakeDepthInference)
    monkeypatch.setattr(zipdepth.importlib, "import_module", lambda _name: fake_module)
    prediction = zipdepth.ZipDepth(checkpoint, device="cpu").load()
    frame = SimpleNamespace(
        frame_id="frame-8",
        colour=np.zeros((2, 2, 3), dtype=np.uint8),
    )

    with pytest.raises(ValueError, match="grid|shape"):
        next(prediction(iter([frame]), run=None))
