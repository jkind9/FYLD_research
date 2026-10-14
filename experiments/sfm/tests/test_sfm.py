"""Standalone SfM experiment contracts: readers, export, scoring and one end-to-end COLMAP run."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageFilter
from scipy.spatial.transform import Rotation

pycolmap = pytest.importorskip("pycolmap")

from experiments.sfm.src import export, reconstruct, scoring, sequences

REPO = Path(__file__).resolve().parents[3]
COLMAP = REPO / "third_party/colmap-4.2.1-windows-nocuda/bin/colmap.exe"


def pose(position, euler_deg=(0, 0, 0)):
    out = np.eye(4)
    out[:3, :3] = Rotation.from_euler("xyz", euler_deg, degrees=True).as_matrix()
    out[:3, 3] = position
    return out


def gt_line(stamp, matrix):
    qx, qy, qz, qw = Rotation.from_matrix(matrix[:3, :3]).as_quat()
    return f"{stamp} {matrix[0, 3]} {matrix[1, 3]} {matrix[2, 3]} {qx} {qy} {qz} {qw}\n"


def tum_fixture(root, count=6):
    root.mkdir(parents=True)
    (root / "rgb.txt").write_text("# rgb\n" + "".join(f"{10 + 0.1 * i:.6f} rgb/{i}.png\n" for i in range(count)))
    (root / "depth.txt").write_text("".join(f"{10 + 0.1 * i + 0.005:.6f} depth/{i}.png\n" for i in range(count)))
    (root / "groundtruth.txt").write_text("".join(gt_line(10 + 0.1 * i, pose((i, 0, 0))) for i in range(count)))
    (root / "rgb").mkdir()
    for i in range(count):
        Image.fromarray(np.full((4, 4, 3), i, np.uint8)).save(root / f"rgb/{i}.png")
    return root


def test_tum_reader_orders_frames_samples_and_pairs_depth(tmp_path):
    sequence = sequences.tum(tum_fixture(tmp_path / "clip"), every=2)
    assert sequence.image_names == ("rgb/0.png", "rgb/2.png", "rgb/4.png")
    assert sequence.timestamps_s == pytest.approx((10.0, 10.2, 10.4))
    assert sequence.camera_model == "PINHOLE" and sequence.camera_params == (525.0, 525.0, 319.5, 239.5)
    assert sequence.depth_names == ("depth/0.png", "depth/2.png", "depth/4.png")
    assert len(sequence.manifest()["frames"]) == 3


def test_tum_fr1_calibration_is_the_published_distortion_set(tmp_path):
    sequence = sequences.tum(tum_fixture(tmp_path / "clip"), calibration="fr1")
    assert sequence.camera_model == "FULL_OPENCV" and len(sequence.camera_params) == 12
    assert sequence.camera_params[:5] == (517.3, 516.5, 318.6, 255.3, 0.2624)


def test_icl_reader_skips_unposed_frame_and_flips_to_right_handed(tmp_path):
    root = tmp_path / "icl"
    root.mkdir()
    (root / "associations.txt").write_text("".join(f"{i} depth/{i}.png {i} rgb/{i}.png\n" for i in range(5)))
    truth = {i: pose((0.1 * i, 0.2, -2.0), (0, 10 * i, 5)) for i in range(1, 5)}
    (root / "living.gt.freiburg").write_text("".join(gt_line(i, m) for i, m in truth.items()))
    sequence = sequences.icl(root)
    assert sequence.frame_ids == ("1", "2", "3", "4")
    assert sequence.image_names[0] == "rgb/1.png" and sequence.depth_names[0] == "depth/1.png"
    references = sequence.references()
    for (stamp, matrix), original in zip(references, truth.values()):
        assert np.linalg.det(matrix[:3, :3]) == pytest.approx(1.0)
        assert matrix[:3, 3] == pytest.approx(np.array([1, -1, 1]) * original[:3, 3])


def test_camera_to_world_inverts_world_to_camera():
    world_from_camera = pose((1, 2, 3), (10, 20, 30))
    cam_from_world = np.linalg.inv(world_from_camera)[:3, :]
    assert export.camera_to_world(cam_from_world) == pytest.approx(world_from_camera, abs=1e-12)


def synthetic_models():
    reconstruction = pycolmap.synthesize_dataset(pycolmap.SyntheticDatasetOptions())
    names = sorted(image.name for image in reconstruction.images.values())
    sequence = sequences.Sequence("syn", Path("."), tuple(names), tuple(names), tuple(float(i) for i in range(len(names))),
                                  "PINHOLE", (1.0, 1.0, 0.0, 0.0), Path("unused"))
    return reconstruction, sequence


def test_export_frames_poses_and_unplaced_frames():
    reconstruction, sequence = synthetic_models()
    extra = sequences.Sequence("syn", Path("."), (*sequence.image_names, "missing.png"),
                               (*sequence.frame_ids, "missing.png"), (*sequence.timestamps_s, 99.0),
                               "PINHOLE", (1.0, 1.0, 0.0, 0.0), Path("unused"))
    rows = export.frames(extra, {0: reconstruction})
    assert rows[-1]["model_id"] is None and rows[-1]["T_world_camera"] is None
    image = next(iter(reconstruction.images.values()))
    row = next(r for r in rows if r["image"] == image.name)
    expected = np.linalg.inv(np.vstack([image.cam_from_world().matrix(), [0, 0, 0, 1]]))
    assert np.array(row["T_world_camera"]) == pytest.approx(expected, abs=1e-9)


def test_export_points_and_observations_round_trip(tmp_path):
    reconstruction, sequence = synthetic_models()
    summary = export.write(sequence, {0: reconstruction}, tmp_path)
    points = np.load(tmp_path / "points.npz")
    observations = np.load(tmp_path / "observations.npz")
    assert summary["points"] == reconstruction.num_points3D()
    assert len(observations["uv"]) == int(points["track_length"].sum())
    assert (tmp_path / "trajectory.txt").read_text().count("\n") == 1 + reconstruction.num_reg_images()
    assert json.loads((tmp_path / "frames.json").read_text())["frames"][0]["model_id"] == 0


def scored_rows(truth, transform_scale, unplaced=()):
    rotation = Rotation.from_euler("z", 40, degrees=True).as_matrix()
    rows = []
    for i, (stamp, matrix) in enumerate(truth):
        placed = i not in unplaced
        moved = np.eye(4)
        moved[:3, :3] = rotation @ matrix[:3, :3]
        moved[:3, 3] = transform_scale * rotation @ matrix[:3, 3] + np.array([3.0, -1.0, 2.0])
        rows.append({"frame_id": f"f{i}", "timestamp_s": stamp, "image": f"{i}.png",
                     "model_id": 0 if placed else None, "T_world_camera": moved.tolist() if placed else None})
    return rows


def test_score_recovers_size_and_counts_unplaced(tmp_path):
    root = tmp_path / "rec"
    root.mkdir()
    truth = [(10.0 + 0.1 * i, pose((np.cos(0.3 * i), np.sin(0.3 * i), 0.05 * i))) for i in range(30)]
    (root / "groundtruth.txt").write_text("".join(gt_line(t, m) for t, m in truth))
    sequence = sequences.Sequence("s", root, tuple(f"{i}.png" for i in range(30)), tuple(f"f{i}" for i in range(30)),
                                  tuple(t for t, _ in truth), "PINHOLE", (1.0, 1.0, 0.0, 0.0), root / "groundtruth.txt")
    result = scoring.score(sequence, scored_rows(truth, 0.5, unplaced=(3,)))
    assert result["placed_fraction_any_model"] == pytest.approx(29 / 30)
    assert result["largest_model"]["ate_scaled_rmse_m"] < 1e-9
    assert result["largest_model"]["ate_scaled_size"] == pytest.approx(2.0)


def test_depth_model_size_matches_a_known_factor():
    world_from_camera = pose((0.5, 0.0, 0.0), (0, 15, 0))
    rng = np.random.default_rng(0)
    camera_points = np.column_stack([rng.uniform(-1, 1, 60), rng.uniform(-0.7, 0.7, 60), rng.uniform(2, 4, 60)])
    xyz = camera_points @ world_from_camera[:3, :3].T + world_from_camera[:3, 3]
    u = 100 * camera_points[:, 0] / camera_points[:, 2] + 160
    v = 100 * camera_points[:, 1] / camera_points[:, 2] + 120
    depth = np.zeros((240, 320))
    depth[np.rint(v).astype(int), np.rint(u).astype(int)] = 2.5 * camera_points[:, 2]
    observations = {"frame_index": np.zeros(60, int), "point_index": np.arange(60), "uv": np.column_stack([u, v])}
    rows = [{"T_world_camera": world_from_camera.tolist()}]
    size = scoring.depth_model_size(rows, xyz, observations, lambda k: (depth, depth > 0))
    assert size["size"] == pytest.approx(2.5, rel=1e-9)
    assert scoring.depth_model_size(rows, xyz, observations, lambda k: (depth, depth > 0), min_points=61)["size"] is None


def test_settings_reject_unknown_features():
    with pytest.raises(ValueError):
        reconstruct.Settings("orb")


def render_two_planes(world_from_camera, texture, size=(320, 240), focal=250.0):
    """Ray-cast a textured floor (y = 1) and back wall (z = 4) seen by a y-down camera."""
    width, height = size
    u, v = np.meshgrid(np.arange(width) + 0.5, np.arange(height) + 0.5)
    rays = np.stack([(u - width / 2) / focal, (v - height / 2) / focal, np.ones_like(u)], -1) @ world_from_camera[:3, :3].T
    origin = world_from_camera[:3, 3]
    with np.errstate(divide="ignore", invalid="ignore"):
        t_floor = (1.0 - origin[1]) / rays[..., 1]
        t_wall = (4.0 - origin[2]) / rays[..., 2]
    t_floor[t_floor <= 0] = np.inf
    t_wall[t_wall <= 0] = np.inf
    use_floor = t_floor < t_wall
    t = np.where(use_floor, t_floor, t_wall)
    hit = origin + rays * t[..., None]
    a = np.where(use_floor, hit[..., 0], hit[..., 0])
    b = np.where(use_floor, hit[..., 2], hit[..., 1])
    rows = np.clip(((b + 4) * 64).astype(int), 0, texture.shape[0] - 1)
    cols = np.clip(((a + 4) * 64).astype(int), 0, texture.shape[1] - 1)
    image = texture[rows, cols]
    image[~np.isfinite(t)] = 0
    return image


@pytest.mark.skipif(not COLMAP.is_file(), reason="COLMAP 4.2.1 command-line build not downloaded")
def test_sift_incremental_recovers_a_rendered_path(tmp_path):
    rng = np.random.default_rng(3)
    texture = (rng.random((512, 512, 3)) * 255).astype(np.uint8)
    texture = np.asarray(Image.fromarray(texture).resize((1024, 1024), Image.NEAREST).filter(ImageFilter.GaussianBlur(1)))
    root = tmp_path / "rec"
    (root / "rgb").mkdir(parents=True)
    truth = []
    for i in range(12):
        world_from_camera = pose((-0.6 + 0.1 * i, 0.0, 0.004 * (i - 6) ** 2), (-10, 3 * i - 15, 0))
        Image.fromarray(render_two_planes(world_from_camera, texture)).save(root / f"rgb/{i}.png")
        truth.append((float(i), world_from_camera))
    (root / "groundtruth.txt").write_text("".join(gt_line(t, m) for t, m in truth))
    sequence = sequences.Sequence("render", root, tuple(f"rgb/{i}.png" for i in range(12)), tuple(str(i) for i in range(12)),
                                  tuple(float(i) for i in range(12)), "PINHOLE", (250.0, 250.0, 160.0, 120.0),
                                  root / "groundtruth.txt")
    settings = reconstruct.Settings("sift")
    work = tmp_path / "work"
    reconstruct.features_and_matches(COLMAP, sequence, settings, work)
    reconstruct.map_models(COLMAP, sequence, settings, work, "incremental")
    rows = export.frames(sequence, reconstruct.read_models(work, "incremental"))
    result = scoring.score(sequence, rows)
    path_length = sum(np.linalg.norm(truth[i + 1][1][:3, 3] - truth[i][1][:3, 3]) for i in range(11))
    assert result["placed_fraction_largest_model"] == 1.0
    assert result["largest_model"]["ate_scaled_rmse_m"] < 0.01 * path_length


def test_report_lists_complete_and_failed_mappers_and_skips_unfinished_runs(tmp_path):
    from experiments.sfm import report

    def fake(name, status):
        run = tmp_path / name
        (run / "metadata").mkdir(parents=True)
        (run / "output").mkdir()
        (run / "metadata/status.json").write_text(json.dumps({"status": status}))
        (run / "metadata/configuration.json").write_text(json.dumps(
            {"recording": "tum:clips/desk", "calibration": "default", "settings": {"features": "sift"}}))
        scores = {"placed_fraction_largest_model": 0.5, "models": 2,
                  "largest_model": {"ate_scaled_rmse_m": 0.024, "ate_scaled_size": 0.23},
                  "depth_model_sized": {"size": 0.33, "ate_rigid_rmse_m": 0.36}}
        (run / "output/summary.json").write_text(json.dumps({
            "frames": 10, "seconds": {"extract": 1.0, "match": 2.0, "map_incremental": 3.0},
            "frames_per_second": {"incremental": 10 / 6},
            "mappers": {"incremental": {"status": "complete", "scores": scores},
                        "global": {"status": "failed", "reason": "no points"}}}))
        return run

    rows = report.rows(fake("done", "complete"))
    assert report.rows(fake("running", "running")) == []
    text = report.table(rows)
    assert "| desk | default | sift | incremental | 5 / 10 | 2 | 24.0 mm | 0.230 | 0.330, 360 mm | 6 | 1.67 |" in text
    assert "| desk | default | sift | global | failed |" in text
