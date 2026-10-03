"""Display geometry and artifact identity contracts."""

import json

import numpy as np
import pytest

from experiments.shared.visualization import (
    artifact,
    frustum,
    sample_points,
    write_viewer,
)


def test_roles_and_unknown_role():
    for role in (
        "observed_input",
        "ground_truth",
        "predicted_output",
        "evaluated_output",
    ):
        assert artifact("x", role, "producer", ["source"], "metres")["role"] == role
    with pytest.raises(ValueError):
        artifact("x", "input", "producer", [], "metres")


def test_sampling_pairs_and_finite():
    points = np.arange(30).reshape(10, 3)
    colors = points + 100
    result = sample_points(points, colors, 3)
    assert len(result["points"]) == 3
    assert np.array_equal(np.array(result["colours"]) - 100, result["points"])
    assert result == sample_points(points, colors, 3)
    with pytest.raises(ValueError):
        sample_points(np.array([[np.nan, 0, 0]]), np.zeros((1, 3)), 1)


def test_signed_focal_and_reflected_basis():
    calibration = {"width": 2, "height": 2, "fx": 1, "fy": -1, "cx": 0.5, "cy": 0.5}
    basis = np.diag([-1.0, 1.0, 1.0, 1.0])
    basis[:3, 3] = [2, 3, 4]
    vertices = np.array(frustum(calibration, basis, 1))
    assert np.allclose(vertices[0], [2, 3, 4])
    assert np.allclose(vertices[1], [2.5, 3.5, 5])


def test_viewer_escapes_embedded_json(tmp_path):
    scene = {"title": "</script><script>alert(1)</script>", "frames": [], "note": ""}
    write_viewer(tmp_path, scene)
    page = (tmp_path / "viewer.html").read_text()
    assert "</script><script>alert" not in page
    assert "getContext('2d')" in page
    assert "webgl" not in page.lower()
    assert json.loads((tmp_path / "debug/scene.json").read_text()) == scene


def test_tracking_alignment_rotation_failure_and_first_match():
    from scipy.spatial.transform import Rotation

    from experiments.shared.inspection import aligned_tracking

    first = np.eye(4)
    first[:3, :3] = Rotation.from_euler("z", 30, degrees=True).as_matrix()
    first[:3, 3] = [1, 2, 3]
    second = np.eye(4)
    second[:3, :3] = Rotation.from_euler("x", 20, degrees=True).as_matrix()
    second[:3, 3] = [2, 3, 4]
    reference = np.eye(4)
    reference[:3, :3] = Rotation.from_euler("y", 70, degrees=True).as_matrix()
    reference[:3, 3] = [10, 20, 30]
    records = [
        {
            "timestamp_s": i,
            "pose": (
                None
                if i == 2
                else {
                    "T_world_camera": (first if i < 2 else second).tolist(),
                    "segment_id": "one",
                }
            ),
        }
        for i in range(4)
    ]
    rows = aligned_tracking(records, [(1.0, reference), (3.0, reference)], 0.02)
    assert np.allclose(rows[3][0], reference @ np.linalg.inv(first) @ second)
    assert rows[2] == (None, None, None)
    assert np.allclose(rows[0][0], reference)


def test_depth_role_and_missing_pixels(tmp_path):
    from PIL import Image

    from experiments.shared.visualization import depth_preview

    legend = depth_preview(
        np.array([[0.0, 1.0], [2.0, 3.0]]),
        tmp_path / "depth.png",
        "observed_input",
        "raw.png",
    )
    assert legend["missing_fraction"] == 0.25
    assert legend["role"] == "observed_input"
    assert np.array_equal(np.array(Image.open(tmp_path / "depth.png"))[0, 0], [0, 0, 0])


@pytest.mark.parametrize(
    "points,colours,cap",
    [
        (np.ones((2, 3)), np.ones((1, 3)), 1),
        (np.ones((2, 3)), np.ones((2, 3)), 0),
    ],
)
def test_invalid_samples(points, colours, cap):
    with pytest.raises(ValueError):
        sample_points(points, colours, cap)


def test_empty_cloud():
    assert sample_points(np.empty((0, 3)), np.empty((0, 3)), 2)["display_count"] == 0


def test_nonfinite_calibration_rejected():
    calibration = {"width": 2, "height": 2, "fx": np.nan, "fy": 1, "cx": 0, "cy": 0}
    with pytest.raises(ValueError, match="finite"):
        frustum(calibration, np.eye(4))


def test_nested_computation_metadata(tmp_path):
    from experiments.shared.inspection import computation_metadata
    from experiments.shared.runs import write_json

    for suffix in ("metadata", "metadata/computation"):
        write_json(tmp_path / suffix / "configuration.json", {"publication_only": True})
    original = tmp_path / "metadata/computation/computation"
    write_json(original / "configuration.json", {"hyperparameters": {"saved": 1}})
    assert computation_metadata(tmp_path) == original


def test_legacy_surface_computation_metadata(tmp_path):
    from experiments.shared.inspection import computation_metadata
    from experiments.shared.runs import write_json

    write_json(
        tmp_path / "metadata/configuration.json", {"republication_source": "prior"}
    )
    original = tmp_path / "metadata/previous_publication/metadata"
    write_json(original / "configuration.json", {"depth_role": "supplied"})
    assert computation_metadata(tmp_path) == original


def test_publication_preserves_numeric_bytes_and_timing(tmp_path, monkeypatch):
    from experiments.shared import publication, runs
    from experiments.shared.runs import Run, verify_run, write_json

    monkeypatch.setattr(runs, "_git", lambda *_: "fake")
    with Run(tmp_path / "original", tmp_path, {}) as source:
        (source.path / "output/array.npy").write_bytes(b"original-array")
        (source.path / "output/metrics.json").write_bytes(b'{"exact":1}\n')
        (source.path / "review.html").write_text("<html></html>")
    before = (source.path / "metadata/manifest.json").read_bytes()

    def display(root):
        (root / "viewer.html").write_text("viewer")
        write_json(root / "metadata/artifact_roles.json", {})

    monkeypatch.setattr(publication, "tracking_view", display)
    target = publication.publish(source.path, tmp_path / "copies", tmp_path, "03")
    assert (target / "output/array.npy").read_bytes() == b"original-array"
    assert (target / "output/metrics.json").read_bytes() == b'{"exact":1}\n'
    assert (target / "metadata/computation/timing.json").read_bytes() == (
        source.path / "metadata/timing.json"
    ).read_bytes()
    assert (
        json.loads((target / "metadata/timing.json").read_text())["end_to_end_fps"]
        is None
    )
    assert (source.path / "metadata/manifest.json").read_bytes() == before
    verify_run(source.path)
    verify_run(target)


def test_initial_inventory_hash_rejects_changed_source(tmp_path):
    from experiments.shared.publication import copy_inventory

    source = tmp_path / "source"
    source.mkdir()
    (source / "a").write_bytes(b"changed")
    with pytest.raises(ValueError, match="initial inventory"):
        copy_inventory(source, tmp_path / "target", {"files": {"a": {"sha256": "old"}}})


def test_surface_total_cap_and_roles(tmp_path, monkeypatch):
    import importlib

    from experiments.shared.inspection import surface_view
    from experiments.shared.runs import write_json

    reader = importlib.import_module(
        "experiments.04_surface_reconstruction.src.dataset"
    )
    monkeypatch.setattr(reader, "read_reference", lambda _: np.array([[0.0, 0.0, 1.0]]))
    write_json(
        tmp_path / "output/surface.json",
        {"shards": [{"frame_id": str(i)} for i in range(3)]},
    )
    for i in range(3):
        output = tmp_path / f"output/{i}"
        output.mkdir()
        np.save(output / "model.npy", [[0.0, 0.0, 1.0]])
        np.save(output / "rgb.npy", [[255, 0, 0]])
        np.save(output / "depth.npy", [[1.0]])
        write_json(output / "stages.json", {"model_from_world": np.eye(4).tolist()})
        write_json(
            tmp_path / f"input/{i}/observation.json",
            {
                "pose": {"T_world_camera": np.eye(4).tolist()},
                "calibration": {
                    "width": 1,
                    "height": 1,
                    "fx": 1,
                    "fy": -1,
                    "cx": 0,
                    "cy": 0,
                },
            },
        )
    before = (tmp_path / "output/0/model.npy").read_bytes()
    scene = surface_view(tmp_path, cap=2)
    assert scene["display_count"] == 2 and scene["full_count"] == 3
    assert [f["display_count"] for f in scene["frames"]] == [1, 1, 0]
    roles = {r["path"]: r["role"] for r in scene["roles"]}
    assert roles["input/0/depth.png"] == "ground_truth"
    assert roles["output/0/model.npy"] == "evaluated_output"
    assert (tmp_path / "output/0/model.npy").read_bytes() == before
