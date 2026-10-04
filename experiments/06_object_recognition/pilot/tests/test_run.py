"""Fake-detector integration checks keep GPU inference outside routine tests."""

import importlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, verify_run

runner = importlib.import_module("experiments.06_object_recognition.pilot.run")
localisation = importlib.import_module(
    "experiments.06_object_recognition.pilot.localisation"
)
detector_module = importlib.import_module(
    "experiments.06_object_recognition.pilot.detector"
)


class FakeDetector:
    def __init__(self, detections=None, shape=None):
        self.detections = (
            [localisation.Detection((300, 200, 340, 240), "cup", 41, 0.8)]
            if detections is None
            else detections
        )
        self.shape = [480, 640] if shape is None else shape

    def predict(self, image):
        # The adapter receives one original RGB image; neither depth nor poses is an argument.
        assert Path(image).name == "rgb.png"
        assert not (Path(image).parent / "reference_poses.txt").exists()
        return self.detections, {"image_shape_hw": self.shape, "test_double": True}


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    (root / "rgb").mkdir(parents=True)
    (root / "depth").mkdir()
    Image.fromarray(np.full((480, 640, 3), 128, dtype=np.uint8)).save(
        root / "rgb/1.0.png"
    )
    Image.fromarray(np.full((480, 640), 5000, dtype=np.uint16)).save(
        root / "depth/1.001.png"
    )
    (root / "rgb.txt").write_text("1.0 rgb/1.0.png\n")
    (root / "depth.txt").write_text("1.001 depth/1.001.png\n")
    (root / "groundtruth.txt").write_text("1.0 1 2 3 0 0 0 1\n")
    members = {
        p.relative_to(root).as_posix(): {"sha256": sha256(p)}
        for p in root.rglob("*")
        if p.is_file()
    }
    monkeypatch.setattr(runner, "_members", lambda *_: members)
    monkeypatch.setattr(
        runner, "Run", lambda _, repo, config: Run(tmp_path / "runs", repo, config)
    )
    checkpoint = tmp_path / "fixture.pt"
    checkpoint.write_bytes(b"not loaded by fake detector")
    return root, checkpoint, tmp_path


def detection_run(source, fake=None):
    root, checkpoint, _ = source
    return runner.detect(
        runner.ROOT, root, checkpoint, "1.0.png", "cpu", fake or FakeDetector()
    )


def test_named_frame_selection_is_not_first_pair(tmp_path):
    (tmp_path / "rgb.txt").write_text("1 rgb/first.png\n2 rgb/target.png\n")
    (tmp_path / "depth.txt").write_text("1 depth/first.png\n2 depth/target.png\n")
    assert runner.select_row(tmp_path, "target.png")["frame_id"] == "1"
    with pytest.raises(ValueError, match="exactly one"):
        runner.select_row(tmp_path, "missing.png")


def test_published_detection_maps_to_cloud_and_same_measured_marker(source):
    detection = detection_run(source)
    assert verify_run(detection)["status"] == "complete"
    mapped = runner.map_detection(runner.ROOT, detection, True)
    assert verify_run(mapped)["status"] == "complete"
    saved = json.loads((mapped / "output/localisations.json").read_text())
    marker = saved["locations"][0]["centre_sample"]
    cloud = np.load(mapped / "output/cloud.npz")
    index = np.flatnonzero(np.all(cloud["pixel_vu"] == marker["pixel_vu"], axis=1))
    assert len(index) == 1
    np.testing.assert_allclose(
        cloud["world_m"][index[0]], marker["world_m"], atol=1e-10
    )
    np.testing.assert_allclose(
        np.array(marker["camera_m"]) + [1, 2, 3], marker["world_m"], atol=1e-10
    )
    assert "Plotly.newPlot" in (mapped / "review.html").read_text(encoding="utf-8")
    assert (mapped / "review.png").is_file()


def test_mapping_requires_review_and_rejects_changed_parent(source):
    detection = detection_run(source)
    with pytest.raises(ValueError, match="Visually inspect"):
        runner.map_detection(runner.ROOT, detection, False)
    (detection / "output/detections.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        runner.map_detection(runner.ROOT, detection, True)


def test_mapping_rejects_changed_source_depth_and_marks_run_failed(source):
    detection = detection_run(source)
    (source[0] / "depth/1.001.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="archive member"):
        runner.map_detection(runner.ROOT, detection, True)
    assert any(
        json.loads(p.read_text())["status"] == "failed"
        for p in (source[2] / "runs").glob("*/metadata/status.json")
    )


def test_empty_detections_publish_no_object_locations(source):
    detection = detection_run(source, FakeDetector([]))
    mapped = runner.map_detection(runner.ROOT, detection, True)
    assert (
        json.loads((mapped / "output/localisations.json").read_text())["locations"]
        == []
    )


@pytest.mark.parametrize(
    "fake",
    [
        FakeDetector(shape=[240, 320]),
        FakeDetector([localisation.Detection((600, 200, 650, 240), "cup", 41, 0.8)]),
    ],
)
def test_invalid_detector_grid_cannot_publish_complete(source, fake):
    with pytest.raises(ValueError):
        detection_run(source, fake)
    statuses = list((source[2] / "runs").glob("*/metadata/status.json"))
    assert statuses and all(
        json.loads(p.read_text())["status"] == "failed" for p in statuses
    )


def test_missing_checkpoint_never_triggers_a_download(tmp_path):
    with pytest.raises(ValueError, match="already exist"):
        runner.detect(runner.ROOT, tmp_path, tmp_path / "missing.pt", "1.0.png", "0")
    with pytest.raises(ValueError, match="already acquired"):
        detector_module.YoloDetector(tmp_path / "missing.pt", "0")


def test_invalid_device_rejected_before_model_loading(tmp_path):
    path = tmp_path / "fixture.pt"
    path.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="Explicit device"):
        detector_module.YoloDetector(path, "automatic")


def test_no_supplied_pose_leaves_failed_mapping_receipt(source, monkeypatch):
    detection = detection_run(source)
    monkeypatch.setattr(
        runner.evaluation, "read_references", lambda _: [(100.0, np.eye(4))]
    )
    with pytest.raises(ValueError, match="No supplied pose"):
        runner.map_detection(runner.ROOT, detection, True)


def test_copied_parent_tampering_fails_even_when_parent_is_unchanged(
    source, monkeypatch
):
    detection = detection_run(source)
    copy = runner.shutil.copyfile

    def corrupt_copy(src, dst):
        value = copy(src, dst)
        if Path(src) == detection / "output/detections.json":
            Path(dst).write_text('{"proposals":[]}')
        return value

    monkeypatch.setattr(runner.shutil, "copyfile", corrupt_copy)
    with pytest.raises(ValueError, match="Copied parent artifact hash"):
        runner.map_detection(runner.ROOT, detection, True)
    assert verify_run(detection)["status"] == "complete"


def test_all_invalid_depth_publishes_empty_cloud_and_no_marker(source, monkeypatch):
    root, _, _ = source
    depth_path = root / "depth/1.001.png"
    Image.fromarray(np.zeros((480, 640), dtype=np.uint16)).save(depth_path)
    members = {
        **runner._members(runner.ROOT, root),
        "depth/1.001.png": {"sha256": sha256(depth_path)},
    }
    monkeypatch.setattr(runner, "_members", lambda *_: members)
    detection = detection_run(source)
    mapped = runner.map_detection(runner.ROOT, detection, True)
    saved = json.loads((mapped / "output/localisations.json").read_text())
    assert saved["locations"][0]["status"] == "no_valid_depth"
    assert np.load(mapped / "output/cloud.npz")["world_m"].shape == (0, 3)
    assert verify_run(mapped)["status"] == "complete"
