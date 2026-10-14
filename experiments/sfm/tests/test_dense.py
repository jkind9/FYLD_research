"""Dense structure contracts: fusion, reference frames, depth sizing from points."""

import json

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

pytest.importorskip("open3d")

from experiments.sfm import run_dense
from experiments.sfm.src import dense, references, sequences

CAMERA = dense.Pinhole(160, 120, 100.0, 100.0, 80.0, 60.0)


def pose(position, euler_deg=(0, 0, 0)):
    out = np.eye(4)
    out[:3, :3] = Rotation.from_euler("xyz", euler_deg, degrees=True).as_matrix()
    out[:3, 3] = position
    return out


def plane_depth(world_from_camera, camera=CAMERA):
    """Camera-axis depth of a floor (y = 1) and back wall (z = 4) seen by a y-down camera."""
    u, v = np.meshgrid(np.arange(camera.width), np.arange(camera.height))
    rays_camera = np.stack([(u - camera.cx) / camera.fx, (v - camera.cy) / camera.fy, np.ones(u.shape)], -1)
    rays = rays_camera @ world_from_camera[:3, :3].T
    origin = world_from_camera[:3, 3]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.fmin(np.where(rays[..., 1] > 0, (1 - origin[1]) / rays[..., 1], np.inf),
                    np.where(rays[..., 2] > 0, (4 - origin[2]) / rays[..., 2], np.inf))
    return t, np.isfinite(t) & (t < 4)


def views():
    return [pose((-0.3 + 0.12 * i, 0.0, 0.05 * i), (-15, 4 * i - 10, 0)) for i in range(6)]


def distance_to_planes(points):
    return np.minimum(np.abs(points[:, 1] - 1.0), np.abs(points[:, 2] - 4.0))


def test_fusing_exact_depth_reproduces_the_surface():
    frames = [dense.DepthFrame(*plane_depth(p), p) for p in views()]
    points, counts = dense.fuse_tsdf(frames, CAMERA, voxel_m=0.02, truncation_voxels=4, min_depth_m=0.1, max_depth_m=4.0)
    assert counts["frames_fused"] == 6
    assert np.median(distance_to_planes(points)) < 0.02


def test_a_wrongly_sized_frame_moves_the_surface():
    exact = [dense.DepthFrame(*plane_depth(p), p) for p in views()]
    wrong = list(exact)
    depth, valid = plane_depth(views()[0])
    wrong[0] = dense.DepthFrame(depth * 1.3, valid, views()[0])
    good = dense.accumulate(exact, CAMERA, voxel_m=0.02, min_depth_m=0.1, max_depth_m=6.0)
    bad = dense.accumulate(wrong, CAMERA, voxel_m=0.02, min_depth_m=0.1, max_depth_m=6.0)
    assert distance_to_planes(bad).mean() > 2 * distance_to_planes(good).mean()


def test_frame_without_depth_is_skipped_and_counted():
    depth, valid = plane_depth(views()[0])
    frames = [dense.DepthFrame(depth, valid, views()[0]), dense.DepthFrame(depth, np.zeros_like(valid), views()[1])]
    _, counts = dense.fuse_tsdf(frames, CAMERA, voxel_m=0.05, truncation_voxels=4, min_depth_m=0.1, max_depth_m=4.0)
    assert counts == {"frames_fused": 1, "frames_without_depth": 1}


def test_icl_model_to_world_is_proper_and_matches_the_flipped_pose_world(tmp_path):
    model_from_world = np.array([[0.9998, 0.0034, 0.0186, -0.74], [-0.0035, 0.99999, 0.0036, 1.29],
                                 [0.0185, 0.0037, -0.9998, -0.79], [0, 0, 0, 1.0]])
    (tmp_path / "conventions.json").write_text(json.dumps(
        {"alignment": {"derived_model_from_compatible_world": model_from_world.tolist()}}))
    transform = references.icl_model_to_world(tmp_path / "conventions.json")
    assert np.linalg.det(transform[:3, :3]) == pytest.approx(1.0, abs=1e-3)
    world_point = np.array([0.3, -0.2, 1.5, 1.0])
    model_point = model_from_world @ world_point
    assert transform @ model_point == pytest.approx(sequences.FLIP_Y @ world_point, abs=1e-9)


def test_fit_size_is_robust_and_recovers_a_shift():
    rng = np.random.default_rng(1)
    target = rng.uniform(1, 4, 100)
    model = 2.5 * target
    assert dense.fit_size(model, target)[0] == pytest.approx(0.4)
    noisy = model.copy()
    noisy[:20] *= rng.uniform(0.2, 5, 20)
    assert dense.fit_size(noisy, target)[0] == pytest.approx(0.4, rel=0.02)
    size, shift = dense.fit_size(model, 0.4 * model + 0.2, with_shift=True)
    assert (size, shift) == pytest.approx((0.4, 0.2))
    assert dense.fit_size(np.array([1.0]), np.array([1.0])) is None


def test_frames_with_few_points_borrow_the_nearest_size():
    observations = {"frame_index": np.repeat([0, 1, 2], [30, 5, 30]), "uv": np.zeros((65, 2))}
    camera_depth = np.concatenate([np.full(30, 2.0), np.full(5, 2.0), np.full(30, 3.0)])
    model = {0: 1.0, 1: 1.0, 2: 1.0}
    rows = dense.frame_sizes(3, observations, camera_depth, lambda k, uv: np.full(len(uv), model[k]), min_points=20)
    assert rows[0]["size"] == pytest.approx(2.0) and rows[2]["size"] == pytest.approx(3.0)
    assert rows[1]["borrowed_from"] in (0, 2) and rows[1]["points"] == 0


def test_reference_size_per_frame_inverts_a_known_bias():
    sensor = np.random.default_rng(2).uniform(1, 3, (10, 10))
    valid = np.ones_like(sensor, bool)
    assert run_dense.reference_size_per_frame(1.3 * sensor, valid, sensor, valid) == pytest.approx(1 / 1.3)


def test_inputs_are_not_changed():
    depth, valid = plane_depth(views()[0])
    before = depth.copy()
    dense.fuse_tsdf([dense.DepthFrame(depth, valid, views()[0])], CAMERA, voxel_m=0.05, truncation_voxels=4,
                    min_depth_m=0.1, max_depth_m=4.0)
    assert np.array_equal(depth, before, equal_nan=True)


def test_dense_report_row_and_table(tmp_path):
    from experiments.sfm import report

    run = tmp_path / "run"
    (run / "metadata").mkdir(parents=True)
    (run / "output").mkdir()
    (run / "metadata/status.json").write_text(json.dumps({"status": "complete"}))
    (run / "metadata/configuration.json").write_text(json.dumps(
        {"recording": "icl:data/icl_nuim/trajectory2", "depth": "model", "poses": "true", "sfm_size": "best-fit"}))
    (run / "output/scores.json").write_text(json.dumps({
        "surface": {"accuracy": {"mean_m": 0.0111, "rmse_m": 0.02}, "reconstruction_within_threshold_fraction": 0.5,
                    "reference_coverage_fraction": 0.25}, "points": 10, "poses": {"source": "ground truth"}}))
    text = report.dense_table([report.dense_row(run)])
    assert "| trajectory2 | model | true | 11.1 mm | 20.0 mm | 50.0% | 25.0% | 10 |" in text


def test_depth_model_size_prefers_the_saved_value_then_computes_from_maps(tmp_path):
    camera = pose((0.0, 0.0, 0.0))
    rng = np.random.default_rng(4)
    points_camera = np.column_stack([rng.uniform(-1, 1, 40), rng.uniform(-0.5, 0.5, 40), rng.uniform(2, 3, 40)])
    u = 100 * points_camera[:, 0] / points_camera[:, 2] + 80
    v = 100 * points_camera[:, 1] / points_camera[:, 2] + 60
    depth = np.zeros((120, 160))
    depth[np.rint(v).astype(int), np.rint(u).astype(int)] = 1.7 * points_camera[:, 2]
    np.savez(tmp_path / "depth.npz", depth=depth, valid=depth > 0)
    (tmp_path / "frames.json").write_text(json.dumps({"frames": [{"T_world_camera": camera.tolist()}]}))
    np.savez(tmp_path / "points.npz", xyz=points_camera)
    np.savez(tmp_path / "observations.npz", frame_index=np.zeros(40, int), point_index=np.arange(40), uv=np.column_stack([u, v]))
    sequence = sequences.Sequence("s", tmp_path, ("a.png",), ("a",), (0.0,), "PINHOLE", (100.0, 100.0, 80.0, 60.0), tmp_path / "gt")
    (tmp_path / "scores.json").write_text(json.dumps({}))
    assert run_dense.depth_model_size(sequence, tmp_path, {"a": tmp_path / "depth.npz"}) == pytest.approx(1.7)
    (tmp_path / "scores.json").write_text(json.dumps({"depth_model_size": {"size": 0.33}}))
    assert run_dense.depth_model_size(sequence, tmp_path, {}) == 0.33
