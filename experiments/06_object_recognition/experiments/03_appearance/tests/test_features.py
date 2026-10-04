"""Synthetic adapter tests cannot publish a GPU provenance claim."""

import importlib
import sys
from types import SimpleNamespace

import numpy as np
import pytest

features = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.features"
)
adapter = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.adapter"
)


@pytest.fixture
def synthetic_backend(monkeypatch):
    seen = []

    class Tensor:
        ndim = 1
        device = "cuda:0"
        dtype = "float32"
        values = np.array([1, 2, 3], np.float32)

        def detach(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self.values

    tensor = Tensor()
    cuda = SimpleNamespace(
        is_available=lambda: True,
        synchronize=lambda device: None,
        max_memory_allocated=lambda device: 100,
        max_memory_reserved=lambda device: 200,
    )
    torch = SimpleNamespace(__version__="2.11.0+cu128", cuda=cuda, float32="float32")
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setattr(features.importlib.metadata, "version", lambda name: "8.4.172")

    def embed(bgr, **kwargs):
        seen.append((bgr, kwargs))
        return [tensor]

    predictor = SimpleNamespace(
        model=SimpleNamespace(device="cuda:0", fp16=False),
        args=SimpleNamespace(imgsz=640, embed=[0]),
    )
    model = SimpleNamespace(
        model=SimpleNamespace(model=[object(), object()]),
        embed=embed,
        predictor=predictor,
    )
    monkeypatch.setattr(
        features.detector_api,
        "YoloDetector",
        lambda checkpoint, device: SimpleNamespace(model=model),
    )
    monkeypatch.setattr(
        features, "sha256", lambda path: features.detector_api.CHECKPOINT_SHA256
    )
    return tensor, torch, predictor, seen


def crop(empty=False):
    rgb = np.full((128, 128, 3), [200, 30, 5], np.uint8)
    mask = (
        np.zeros((128, 128), np.uint8) if empty else np.full((128, 128), 255, np.uint8)
    )
    return adapter.prepare_crop(rgb, mask, [0, 0, 128, 128])


def test_backend_channel_conversion_runtime_and_receipt(synthetic_backend, tmp_path):
    _tensor, _torch, _predictor, seen = synthetic_backend
    extractor = features.FeatureExtractor(tmp_path / "checkpoint.pt")
    assert extractor.extract(crop()) == [1, 2, 3]
    assert seen[0][0][64, 64].tolist() == [5, 30, 200]
    assert seen[0][0].flags.c_contiguous
    assert seen[0][1]["embed"] == [0] and seen[0][1]["half"] is False
    assert extractor.extract(crop()) == [1, 2, 3]
    receipt = extractor.receipt()
    assert receipt["requested_embedding_count"] == 2
    assert receipt["actual_device"] == "cuda:0" and receipt["actual_fp16"] is False
    assert receipt["vector_length"] == 3
    assert receipt["costs"][0]["first_call_includes_full_model_warmup"] is True
    assert receipt["costs"][1]["first_call_includes_full_model_warmup"] is False
    assert extractor.extract(crop(empty=True)) == [] and len(seen) == 2


@pytest.mark.parametrize("mode", ["package", "torch", "gpu"])
def test_runtime_rejects_before_model(synthetic_backend, tmp_path, monkeypatch, mode):
    _tensor, torch, _predictor, seen = synthetic_backend
    if mode == "package":
        monkeypatch.setattr(
            features.importlib.metadata, "version", lambda name: "wrong"
        )
    elif mode == "torch":
        torch.__version__ = "wrong"
    else:
        torch.cuda.is_available = lambda: False
    with pytest.raises(ValueError):
        features.FeatureExtractor(tmp_path / "checkpoint.pt")
    assert seen == []


@pytest.mark.parametrize(
    "mode", ["length", "device", "half", "tensor_device", "dtype", "nan", "zero"]
)
def test_invalid_gpu_outputs_never_receipted(synthetic_backend, tmp_path, mode):
    tensor, _torch, predictor, _seen = synthetic_backend
    extractor = features.FeatureExtractor(tmp_path / "checkpoint.pt")
    if mode == "length":
        tensor.ndim = 2
    elif mode == "device":
        predictor.model.device = "cpu"
    elif mode == "half":
        predictor.model.fp16 = True
    elif mode == "tensor_device":
        tensor.device = "cpu"
    elif mode == "dtype":
        tensor.dtype = "float16"
    elif mode == "nan":
        tensor.values = np.array([np.nan])
    else:
        tensor.values = np.zeros(3)
    with pytest.raises(ValueError):
        extractor.extract(crop())
    assert extractor.calls == 0


def test_checkpoint_changed_fails_receipt(synthetic_backend, tmp_path, monkeypatch):
    extractor = features.FeatureExtractor(tmp_path / "checkpoint.pt")
    extractor.extract(crop())
    monkeypatch.setattr(features, "sha256", lambda path: "changed")
    with pytest.raises(ValueError, match="Checkpoint changed"):
        extractor.receipt()


def test_invalid_crop_shape(synthetic_backend, tmp_path):
    extractor = features.FeatureExtractor(tmp_path / "checkpoint.pt")
    with pytest.raises(ValueError, match="128-grid"):
        extractor.extract(
            adapter.CropEvidence(
                np.zeros((1, 1, 3), np.uint8), np.ones((1, 1), np.uint8), (0, 0, 1, 1)
            )
        )
