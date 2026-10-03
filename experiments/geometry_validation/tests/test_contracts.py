"""Independent analytic geometry, identity and dataset controls."""

import importlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.shared.contracts import (
    Calibration,
    Observation,
    Pose,
    require_same_origin,
)
from experiments.shared.geometry import (
    associate_times,
    backproject,
    depth_metres,
    pose_matrix,
    project,
    transform_points,
    validate_transform,
)

icl = importlib.import_module("experiments.geometry_validation.src.icl")
control = importlib.import_module("experiments.geometry_validation.src.control")


def test_known_geometry_and_direction():
    k = Calibration(2, 1, 2.0, -2.0, 0.0, 0.0, "x-right_y-up_z-forward")
    depth, valid = depth_metres(np.array([[0, 10000]]), 5000)
    points, pixels = backproject(depth, valid, k)
    np.testing.assert_allclose(points, [[1, 0, 2]], atol=1e-10)
    pose = pose_matrix([1, 2, 3], [0, 0, np.sqrt(0.5), np.sqrt(0.5)])
    np.testing.assert_allclose(transform_points(points, pose), [[1, 3, 5]], atol=1e-10)
    np.testing.assert_allclose(project(points, k), pixels[:, ::-1], atol=1e-10)
    np.testing.assert_allclose(
        transform_points([[1, 3, 5]], np.linalg.inv(pose)), points
    )


@pytest.mark.parametrize("values", [[[0, -1, np.nan, np.inf]], [[0, 0, 0, 0]]])
def test_invalid_depth(values):
    depth, valid = depth_metres(np.array(values), 1)
    assert not valid.any()
    assert np.isnan(depth).all()
    k = Calibration(4, 1, 2, 2, 0, 0, "x-right_y-down_z-forward")
    assert backproject(depth, valid, k)[0].shape == (0, 3)


def test_reflection_and_rounded_basis():
    reflected = np.diag([1.0, 1.0, -1.0, 1.0])
    with pytest.raises(ValueError, match="proper"):
        validate_transform(reflected)
    np.testing.assert_equal(
        transform_points([[1, 2, 3]], reflected, basis=True), [[1, 2, -3]]
    )
    reflected[0, 0] = 2
    with pytest.raises(ValueError):
        validate_transform(reflected, basis=True)


@pytest.mark.parametrize("bad", [np.eye(3), np.full((4, 4), np.nan), np.zeros((4, 4))])
def test_bad_transform(bad):
    with pytest.raises(ValueError):
        validate_transform(bad)


def test_calibration_validation_and_mask_consistency():
    with pytest.raises(ValueError):
        Calibration(0, 1, 1, 1, 0, 0, "x-right_y-down_z-forward")
    with pytest.raises(ValueError):
        Calibration(1, 1, 1, -1, 0, 0, "x-right_y-down_z-forward")
    with pytest.raises(ValueError):
        depth_metres(np.ones((1, 1)), 0)
    k = Calibration(1, 1, 1, 1, 0, 0, "x-right_y-down_z-forward")
    with pytest.raises(ValueError):
        backproject(np.array([[np.nan]]), np.array([[True]]), k)
    with pytest.raises(ValueError):
        project([[0, 0, 0]], k)


def test_pose_and_observation_immutable_and_segment():
    source = np.eye(4)
    a = Pose(source, "world", "segment", "supplied")
    source[0, 3] = 7
    assert a.matrix[0, 3] == 0
    with pytest.raises(ValueError):
        a.matrix[0, 3] = 2
    require_same_origin(a, a)
    with pytest.raises(ValueError):
        require_same_origin(a, Pose(np.eye(4), "world", "reset", "supplied"))
    k = Calibration(1, 1, 1, 1, 0, 0, "x-right_y-down_z-forward")
    obs = Observation("1", "camera", None, "frame_index_only", k, a)
    assert obs.to_dict()["timestamp_s"] is None
    with pytest.raises(ValueError):
        Observation("1", "camera", np.nan, "capture", k, a)
    with pytest.raises(ValueError):
        pose_matrix([0, 0, 0], [0, 0, 0, 0])


def test_timestamp_boundary_and_order():
    assert associate_times([0.0, 2.0], [0.125, 2.126], 0.125) == [(0, 0)]
    assert associate_times([], [], 0) == []
    for a, b, t in [([1, 1], [1], 0), ([1], [np.nan], 0), ([1], [1], -1)]:
        with pytest.raises(ValueError):
            associate_times(a, b, t)


@pytest.fixture
def dataset(tmp_path):
    for kind in ("rgb", "depth"):
        (tmp_path / "trajectory2" / kind).mkdir(parents=True)
    Image.fromarray(np.array([[5000, 0]], dtype=np.uint16)).save(
        tmp_path / "trajectory2/depth/1.png"
    )
    Image.new("RGB", (2, 1), "red").save(tmp_path / "trajectory2/rgb/1.png")
    (tmp_path / "trajectory2/livingRoom2.gt.freiburg").write_text(
        "1 0 0 -2.25 0 0 0 1\n"
    )
    conventions = {
        "calibration": {
            "width": 2,
            "height": 1,
            "fx": 2,
            "fy": -2,
            "cx": 0,
            "cy": 0,
            "source": "publisher provenance must not enter numeric constructor",
        },
        "alignment": {
            "S_model_first_camera": [
                [1, 0, 0, 1],
                [0, 1, 0, 2],
                [0, 0, -1, 3],
                [0, 0, 0, 1],
            ]
        },
    }
    (tmp_path / "conventions.json").write_text(json.dumps(conventions))
    return tmp_path


def test_exact_id_adapter_and_control(dataset):
    frame = icl.load_frame(dataset, 1)
    result = control.compute(frame)
    np.testing.assert_equal(result.camera, [[0, 0, 1]])
    np.testing.assert_equal(result.world, [[0, 0, -1.25]])
    np.testing.assert_equal(result.model, [[1, 2, 2]])
    assert result.projection_error.max() == 0
    with pytest.raises(ValueError, match="pose"):
        icl.load_frame(dataset, 0)
    with pytest.raises(ValueError):
        icl.select_ids([1, 1])
    with pytest.raises(ValueError):
        icl.select_ids([])
    with pytest.raises(ValueError):
        icl.select_ids([-1])


def test_bad_images_and_pose_rows(dataset):
    Image.new("RGB", (3, 1)).save(dataset / "trajectory2/rgb/1.png")
    with pytest.raises(ValueError, match="resolution"):
        icl.load_frame(dataset, 1)
    (dataset / "trajectory2/livingRoom2.gt.freiburg").write_text(
        "1 0 0 -2.25 0 0 0 1\n1 0 0 0 0 0 0 1\n"
    )
    with pytest.raises(ValueError, match="duplicate"):
        icl.read_poses(dataset / "trajectory2/livingRoom2.gt.freiburg")


def test_publisher_surface_origin():
    # Expected constants transcribed from publisher SurfReg trajectory-2 mapping.
    repo = Path(__file__).resolve().parents[3]
    conventions = json.loads((repo / "data/icl_nuim/conventions.json").read_text())
    basis = np.asarray(conventions["alignment"]["S_model_first_camera"])
    np.testing.assert_allclose(
        transform_points([[0, 0, 0]], basis, basis=True),
        [[-0.786316, 1.28433, 1.45583]],
        atol=1e-10,
    )
    with pytest.raises(ValueError):
        validate_transform(basis)
    first = pose_matrix([0, 0, -2.25], [0, 0, 0, 1])
    derived = basis @ np.linalg.inv(first)
    np.testing.assert_allclose(
        derived,
        conventions["alignment"]["derived_model_from_compatible_world"],
        atol=1e-10,
    )


def test_complete_pipeline_and_failure(dataset, tmp_path):
    runner = importlib.import_module("experiments.geometry_validation.src.run")
    from experiments.shared.runs import verify_run

    repo = Path(__file__).resolve().parents[3]
    path = runner.execute(dataset, [1], tmp_path / "runs", repo)
    assert verify_run(path)["status"] == "complete"
    assert (
        json.loads((path / "metadata/configuration.json").read_text())["experiment"]
        == "geometry_validation"
    )
    assert (path / "review.html").is_file()
    assert (path / "debug/1/model_cloud.png").is_file()
    np.testing.assert_equal(np.load(path / "output/1/model.npy"), [[1, 2, 2]])
    assert (path / "input/1/rgb.png").read_bytes() == (
        dataset / "trajectory2/rgb/1.png"
    ).read_bytes()
    assert json.loads((path / "metadata/frames.json").read_text())[0]["frame_id"] == "1"
    for kind in ("rgb", "depth"):
        (dataset / f"trajectory2/{kind}/2.png").write_bytes(
            (dataset / f"trajectory2/{kind}/1.png").read_bytes()
        )
    with pytest.raises(ValueError, match="pose"):
        runner.execute(dataset, [2], tmp_path / "runs", repo)
    statuses = [
        json.loads(p.read_text())["status"]
        for p in (tmp_path / "runs").glob("*/metadata/status.json")
    ]
    assert sorted(statuses) == ["complete", "failed"]


def test_cli_requires_explicit_selection():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-B", "-m", "experiments.geometry_validation.src.run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--frame-ids" in result.stderr


def test_nonfirst_pose_composition(dataset):
    import shutil

    for kind in ("rgb", "depth"):
        shutil.copyfile(
            dataset / f"trajectory2/{kind}/1.png", dataset / f"trajectory2/{kind}/2.png"
        )
    # 90 degrees about Y maps [0,0,1] to [1,0,0]; then translate [1,2,3].
    with (dataset / "trajectory2/livingRoom2.gt.freiburg").open("a") as stream:
        stream.write(f"2 1 2 3 0 {np.sqrt(.5)} 0 {np.sqrt(.5)}\n")
    result = control.compute(icl.load_frame(dataset, 2))
    np.testing.assert_allclose(result.world, [[2, 2, 3]], atol=1e-10)
    # First-camera inverse adds +2.25 Z; fixture basis reflects Z then adds [1,2,3].
    np.testing.assert_allclose(result.model, [[3, 4, -2.25]], atol=1e-10)


def test_acquired_frame_conformance():
    repo = Path(__file__).resolve().parents[3]
    if not (repo / "data/icl_nuim/trajectory2/rgb/1.png").is_file():
        pytest.skip(
            "Acquired dataset remains local; synthetic control is always tested"
        )
    frame = icl.load_frame(repo / "data/icl_nuim", 1)
    assert frame.raw_depth.shape == (480, 640)
    np.testing.assert_allclose(frame.observation.pose.matrix[:3, 3], [0, 0, -2.25])
    result = control.compute(frame)
    assert result.mask.all()
    assert np.abs(result.projection_error).max() < 1e-10
