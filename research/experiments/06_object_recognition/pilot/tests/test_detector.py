"""Adapter boundary controls use synthetic results without loading a model."""

import hashlib
import importlib
import sys
from types import SimpleNamespace

import pytest

module = importlib.import_module("experiments.06_object_recognition.pilot.detector")


class Array:
    def __init__(self, values):
        self.values = values

    def cpu(self):
        return self

    def tolist(self):
        return self.values


def result(boxes=True):
    return SimpleNamespace(
        boxes=SimpleNamespace(
            xyxy=Array([[0, 0, 4, 3]]), cls=Array([41]), conf=Array([0.8])
        )
        if boxes
        else None,
        names={41: "cup"},
        orig_shape=(3, 4),
        speed={"inference": 1.0},
    )


def adapter(tmp_path, monkeypatch, outputs):
    checkpoint = tmp_path / "yolo26x.pt"
    checkpoint.write_bytes(b"not a real checkpoint")
    monkeypatch.setattr(
        module, "CHECKPOINT_SHA256", hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    )

    class Model:
        predictor = SimpleNamespace(
            args=SimpleNamespace(imgsz=640),
            model=SimpleNamespace(device="cpu", fp16=False),
        )

        def predict(self, image, **settings):
            assert image == "frame.png"
            assert settings["device"] == "cpu"
            assert settings["save"] is False
            return outputs

    monkeypatch.setitem(
        sys.modules,
        "ultralytics",
        SimpleNamespace(YOLO=lambda *_args, **_kwargs: Model()),
    )
    return module.YoloDetector(checkpoint, "cpu")


def test_adapter_retains_original_pixel_boxes_and_records_actual_device(
    tmp_path, monkeypatch
):
    detector = adapter(tmp_path, monkeypatch, [result()])
    boxes, metadata = detector.predict("frame.png")
    assert boxes[0].xyxy == (0, 0, 4, 3)
    assert boxes[0].class_id == 41
    assert boxes[0].confidence == 0.8
    assert metadata["image_shape_hw"] == [3, 4]
    assert metadata["actual_device"] == "cpu"
    assert metadata["actual_fp16"] is False


@pytest.mark.parametrize("outputs", [[], [result(), result()], [result(False)]])
def test_malformed_detector_result_is_rejected(tmp_path, monkeypatch, outputs):
    detector = adapter(tmp_path, monkeypatch, outputs)
    with pytest.raises(ValueError):
        detector.predict("frame.png")


def test_alternate_checkpoint_is_rejected_before_model_loading(tmp_path, monkeypatch):
    checkpoint = tmp_path / "yolo26x.pt"
    checkpoint.write_bytes(b"different model with class 41 meaning something else")
    monkeypatch.setitem(sys.modules, "ultralytics", None)
    with pytest.raises(ValueError, match="verified YOLO26x"):
        module.YoloDetector(checkpoint, "cpu")


def test_legacy_filename_is_rejected_even_when_bytes_match(tmp_path, monkeypatch):
    checkpoint = tmp_path / "yolov5s.pt"
    checkpoint.write_bytes(b"pinned bytes under a substitutable filename")
    monkeypatch.setattr(
        module, "CHECKPOINT_SHA256", hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    )
    monkeypatch.setitem(sys.modules, "ultralytics", None)
    with pytest.raises(ValueError, match="verified YOLO26x"):
        module.YoloDetector(checkpoint, "cpu")


def test_wrong_target_class_label_is_rejected(tmp_path, monkeypatch):
    output = result()
    output.names = {41: "chair"}
    detector = adapter(tmp_path, monkeypatch, [output])
    with pytest.raises(ValueError, match="class 41 must mean cup"):
        detector.predict("frame.png")


@pytest.mark.parametrize(
    "directory", ["owner's-checkpoints", "yolov5s.pt", "yolov3.pt"]
)
def test_path_normalisation_cannot_substitute_other_weights(
    tmp_path, monkeypatch, directory
):
    folder = tmp_path / directory
    folder.mkdir()
    checkpoint = folder / "yolo26x.pt"
    checkpoint.write_bytes(b"pinned bytes under a normalised path")
    monkeypatch.setattr(
        module, "CHECKPOINT_SHA256", hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    )
    monkeypatch.setitem(sys.modules, "ultralytics", None)
    with pytest.raises(ValueError, match="verified YOLO26x"):
        module.YoloDetector(checkpoint, "cpu")
