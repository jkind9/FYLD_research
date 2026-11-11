"""Depth predicts arrays on the recorded grid, with upright input chosen by its caller."""

from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest

from sitescan import depth
from sitescan.depth import orientation
from sitescan.depth.model import infer, metres


@pytest.mark.parametrize("turns", range(4))
def test_prediction_turns_upright_and_returns_to_the_recorded_grid(turns):
    image = np.arange(18, dtype=np.uint8).reshape(2, 3, 3)
    upright_pose = np.diag([1.0, -1.0, -1.0, 1.0])
    pose, _, _ = orientation.turned_camera(upright_pose, (1, 1, 0, 0), (3, 2), turns)
    received = []

    def model(rgb):
        received.append(rgb)
        return rgb[:, :, 0].astype(float), np.ones(rgb.shape[:2], bool)

    predicted, valid = depth.predict(model, image, pose)
    np.testing.assert_array_equal(predicted, image[:, :, 0])
    assert valid.shape == (2, 3) and valid.all()
    assert received[0].flags.c_contiguous
    expected = orientation.upright(image, orientation.quarter_turns(pose))
    np.testing.assert_array_equal(received[0], expected)


def test_prediction_without_pose_preserves_live_recorded_input():
    image = np.arange(18, dtype=np.uint8).reshape(2, 3, 3)
    received = []

    def model(rgb):
        received.append(rgb)
        return np.ones((2, 3)), np.ones((2, 3), bool)

    predicted, valid = depth.predict(model, image)
    np.testing.assert_array_equal(received[0], image)
    assert predicted.shape == valid.shape == image.shape[:2]


def test_metres_preserves_the_existing_positive_finite_mask():
    encoded = np.array([[0, -1, np.nan, np.inf, 1000, 20000.0]])
    predicted, valid = metres(encoded, units_per_metre=1000)
    np.testing.assert_array_equal(valid, [[False, False, False, False, True, True]])
    np.testing.assert_array_equal(predicted[valid], [1.0, 20.0])
    assert np.isnan(predicted[~valid]).all()
    assert predicted.dtype == np.float64


def test_inference_resizes_and_masks_depth_on_the_original_grid():
    import torch as tensor_runtime

    image = np.arange(12, dtype=np.uint8).reshape(2, 2, 3)
    calls = []

    def processor(*, images, return_tensors):
        np.testing.assert_array_equal(np.asarray(images), image)
        assert return_tensors == "pt"
        return {"pixels": tensor_runtime.tensor(image)}

    def interpolate(tensor, *, size, mode, align_corners):
        calls.append((size, mode, align_corners))
        return tensor

    torch = SimpleNamespace(
        inference_mode=nullcontext,
        nn=SimpleNamespace(functional=SimpleNamespace(interpolate=interpolate)),
    )
    model = lambda **_: SimpleNamespace(
        predicted_depth=tensor_runtime.tensor(
            [[[0.0, 0.05], [20.0, 21.0]]], dtype=tensor_runtime.float64
        )
    )
    predicted, valid = infer(image, processor=processor, model=model, torch=torch, device="cpu")
    assert calls == [((2, 2), "bicubic", False)]
    np.testing.assert_array_equal(valid, [[False, True], [True, False]])
    np.testing.assert_array_equal(predicted[valid], [0.05, 20.0])
    assert np.isnan(predicted[~valid]).all()


def test_loader_loads_local_weights_once_and_reuses_them(monkeypatch, tmp_path):
    import sys

    calls = []

    class Model:
        def to(self, device):
            calls.append(("device", device))
            return self

        def eval(self):
            return self

    class Loader:
        @classmethod
        def from_pretrained(cls, path, *, local_files_only):
            calls.append((path, local_files_only))
            return Model()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoImageProcessor=Loader, AutoModelForDepthEstimation=Loader),
    )
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(set_num_threads=lambda n: calls.append(n))
    )
    model = depth.load_model(tmp_path, threads=3)
    assert callable(model)
    assert calls == [3, (tmp_path, True), (tmp_path, True), ("device", "cpu")]
