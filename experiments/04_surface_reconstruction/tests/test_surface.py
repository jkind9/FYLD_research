"""Independent surface fixtures, fault sensitivity and publication boundaries."""

import importlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.geometry_validation.src.icl import load_frame
from experiments.shared.contracts import Pose
from experiments.shared.runs import verify_run

backend = importlib.import_module("experiments.04_surface_reconstruction.src.backend")
evaluation = importlib.import_module(
    "experiments.04_surface_reconstruction.src.evaluation"
)
dataset_module = importlib.import_module(
    "experiments.04_surface_reconstruction.src.dataset"
)
runner = importlib.import_module("experiments.04_surface_reconstruction.src.run")


def write_ply(path, points):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(
            (
                "ply\nformat binary_little_endian 1.0\n"
                f"element vertex {len(points)}\nproperty float x\n"
                "property float y\nproperty float z\nend_header\n"
            ).encode()
        )
        stream.write(np.asarray(points, dtype="<f4").tobytes())


@pytest.fixture
def dataset(tmp_path):
    root = tmp_path / "dataset"
    for kind in ("rgb", "depth"):
        (root / "trajectory2" / kind).mkdir(parents=True)
    for key in (1, 2):
        Image.fromarray(np.array([[5000, 0]], dtype=np.uint16)).save(
            root / f"trajectory2/depth/{key}.png"
        )
        Image.new("RGB", (2, 1), "red").save(root / f"trajectory2/rgb/{key}.png")
    (root / "trajectory2/livingRoom2.gt.freiburg").write_text(
        "1 0 0 0 0 0 0 1\n2 1 0 0 0 0 0 1\n"
    )
    (root / "conventions.json").write_text(
        json.dumps(
            {
                "calibration": {
                    "width": 2,
                    "height": 1,
                    "fx": 2,
                    "fy": -2,
                    "cx": 0,
                    "cy": 0,
                },
                "alignment": {"S_model_first_camera": np.eye(4).tolist()},
            }
        )
    )
    write_ply(root / "reference_surface/living-room.ply", [[0, 0, 1], [1, 0, 1]])
    return root


def test_independent_points_faults_and_immutability(dataset):
    first, second = (load_frame(dataset, i) for i in (1, 2))
    result = backend.reconstruct(second, first.observation.pose)
    np.testing.assert_array_equal(result.world, [[1, 0, 1]])
    np.testing.assert_array_equal(result.model, [[1, 0, 1]])
    score = evaluation.SurfaceScorer(np.array([[1.0, 0, 1]]), 0.05)
    assert score.observe(result.model)[0] == 0
    for fault in ("double_depth", "inverse_pose"):
        assert score.distances(backend.fault_points(second, fault)).mean() > 0.5
    np.testing.assert_array_equal(second.raw_depth, [[5000, 0]])
    assert not result.model.flags.writeable
    bad = replace(
        second,
        observation=replace(
            second.observation, pose=Pose(np.eye(4), "reset", "other", "supplied")
        ),
    )
    with pytest.raises(ValueError, match="origins"):
        backend.reconstruct(bad, first.observation.pose)
    with pytest.raises(ValueError, match="fault"):
        backend.fault_points(second, "other")


def test_coverage_missing_patch_duplicates_and_boundary():
    reference = np.array([[0.0, 0, 1], [1, 0, 1]])
    full = evaluation.SurfaceScorer(reference, 0.05)
    full.observe(reference)
    assert full.summary()["reference_coverage_fraction"] == 1
    partial = evaluation.SurfaceScorer(reference, 0.05)
    partial.observe(reference[:1])
    partial.observe(reference[:1])
    assert partial.summary()["reference_coverage_fraction"] == 0.5
    np.testing.assert_array_equal(partial.reference_distances, [0, 1])
    boundary = evaluation.SurfaceScorer(np.array([[0.0, 0, 0]]), 0.05)
    boundary.observe(np.array([[0.05, 0, 0]]))
    assert boundary.summary()["reference_coverage_fraction"] == 1
    assert boundary.summary()["accuracy"]["mean_m"] == 0.05


def test_rotated_pose_and_reflected_reference(dataset):
    frame = load_frame(dataset, 2)
    rotation = np.array([[0.0, -1, 0, 1], [1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]])
    reflection = np.array([[1.0, 0, 0, 4], [0, 1, 0, 5], [0, 0, -1, 6], [0, 0, 0, 1]])
    pose = Pose(
        rotation,
        frame.observation.pose.world_id,
        frame.observation.pose.segment_id,
        "supplied",
    )
    changed = replace(
        frame,
        raw_depth=np.array([[0, 10000]], dtype=np.uint16),
        observation=replace(frame.observation, pose=pose),
        model_from_first=reflection,
    )
    result = backend.reconstruct(changed, pose)
    np.testing.assert_allclose(result.camera, [[1, 0, 2]])
    np.testing.assert_allclose(result.world, [[1, 3, 5]])
    np.testing.assert_allclose(result.model, [[5, 8, 1]])


def test_nonzero_error_statistics_and_reverse_distance():
    scorer = evaluation.SurfaceScorer(np.array([[0.0, 0, 0], [0, 4, 0]]), 3)
    distances = scorer.observe(np.array([[0.0, 0, 3], [0, 4, 4]]))
    np.testing.assert_array_equal(distances, [3, 4])
    np.testing.assert_array_equal(scorer.reference_distances, [3, 4])
    metrics = scorer.summary()
    assert metrics["accuracy"]["mean_m"] == 3.5
    assert metrics["accuracy"]["rmse_m"] == pytest.approx(np.sqrt(12.5))
    assert metrics["accuracy"]["max_m"] == 4
    assert metrics["reference_coverage_fraction"] == 0.5


def test_exact_batch_matches_incremental():
    reference = np.array([[0.0, 0, 0], [0, 4, 0], [8, 0, 0]])
    shards = [np.array([[0.0, 0, 3]]), np.array([[0.0, 4, 4]])]
    incremental = evaluation.SurfaceScorer(reference, 3)
    batch = evaluation.SurfaceScorer(reference, 3)
    for shard in shards:
        expected = incremental.observe(shard)
        np.testing.assert_array_equal(
            batch.observe(shard, update_reference=False), expected
        )
    batch.cover_accumulated(np.concatenate(shards))
    np.testing.assert_array_equal(
        batch.reference_distances, incremental.reference_distances
    )
    assert batch.summary() == incremental.summary()
    with pytest.raises(ValueError, match="count"):
        batch.cover_accumulated(shards[0])


def test_recovered_inspection_and_mismatch(dataset, tmp_path):
    inspection = importlib.import_module(
        "experiments.04_surface_reconstruction.src.inspection"
    )
    repo = Path(__file__).resolve().parents[3]
    prior = runner.execute(dataset, [1, 2], 0.05, tmp_path / "prior", repo)
    (prior / "metadata/status.json").write_text('{"status":"running"}')
    path = inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "new", repo)
    assert verify_run(path)["status"] == "complete"
    assert (
        json.loads((prior / "metadata/status.json").read_text())["status"] == "running"
    )
    metrics = json.loads((path / "output/metrics.json").read_text())
    assert metrics["accuracy"]["mean_m"] == 0
    assert metrics["reference_coverage_fraction"] == 1
    assert metrics["negative_control_frame_ids"] == []
    assert metrics["negative_controls"] is None
    assert metrics["negative_control_clean_accuracy"] is None
    assert (path / "debug/surface.png").is_file()
    republished = inspection.republish_review(path, tmp_path / "republished", repo)
    assert verify_run(republished)["status"] == "complete"
    assert (
        json.loads((republished / "output/metrics.json").read_text())["accuracy"]
        == metrics["accuracy"]
    )
    np.save(prior / "output/2/model.npy", np.zeros((1, 3)))
    with pytest.raises(ValueError, match="Recovered geometry"):
        inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "bad", repo)
    failed = next((tmp_path / "bad").iterdir())
    assert (
        json.loads((failed / "metadata/status.json").read_text())["status"] == "failed"
    )


def test_recovery_rejects_changed_scoring_dependencies(dataset, tmp_path):
    inspection = importlib.import_module(
        "experiments.04_surface_reconstruction.src.inspection"
    )
    repo = Path(__file__).resolve().parents[3]
    prior = runner.execute(dataset, [1, 2], 0.05, tmp_path / "prior", repo)
    reference = dataset / "reference_surface/living-room.ply"
    original = reference.read_bytes()
    reference.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="reference differs"):
        inspection.execute(
            dataset, [1, 2], 0.05, prior, tmp_path / "different_ref", repo
        )
    reference.write_bytes(original)
    with pytest.raises(ValueError, match="selection or threshold"):
        inspection.execute(
            dataset, [1, 2], 0.1, prior, tmp_path / "different_threshold", repo
        )
    old_query = (
        prior
        / "metadata/source/experiments/04_surface_reconstruction/src/evaluation.py"
    )
    old_query.write_text(old_query.read_text().replace("k=1, eps=0", "k=1, eps=0.1"))
    (prior / "metadata/status.json").write_text('{"status":"running"}')
    with pytest.raises(ValueError, match="query implementation"):
        inspection.execute(
            dataset, [1, 2], 0.05, prior, tmp_path / "different_query", repo
        )


def test_recovered_summary_weighting():
    recovery = importlib.import_module(
        "experiments.04_surface_reconstruction.src.recovery"
    )
    result = recovery.combine_summaries(
        [
            {"points": 1, "mean_m": 3.0, "rmse_m": 3.0, "max_m": 3.0},
            {"points": 1, "mean_m": 4.0, "rmse_m": 4.0, "max_m": 4.0},
        ]
    )
    assert result["mean_m"] == 3.5
    assert result["rmse_m"] == pytest.approx(np.sqrt(12.5))
    assert result["max_m"] == 4


def test_recovery_empty_frame_and_bad_fault_summary(dataset, tmp_path):
    inspection = importlib.import_module(
        "experiments.04_surface_reconstruction.src.inspection"
    )
    repo = Path(__file__).resolve().parents[3]
    Image.fromarray(np.zeros((1, 2), dtype=np.uint16)).save(
        dataset / "trajectory2/depth/1.png"
    )
    prior = runner.execute(dataset, [1, 2], 0.05, tmp_path / "prior", repo)
    path = inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "new", repo)
    metrics = json.loads((path / "output/metrics.json").read_text())
    assert metrics["negative_control_frame_ids"] == [2]
    (prior / "metadata/status.json").write_text('{"status":"running"}')
    record = prior / "output/2/stages.json"
    saved = json.loads(record.read_text())
    for fault in (
        {"points": 2, "mean_m": 1, "rmse_m": 1, "max_m": 1},
        {"points": 1, "mean_m": -1, "rmse_m": 0, "max_m": 0},
    ):
        record.write_text(
            json.dumps(
                {
                    **saved,
                    "negative_controls": {
                        **saved["negative_controls"],
                        "double_depth": fault,
                    },
                }
            )
        )
        with pytest.raises(ValueError, match="fault summary"):
            inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "bad", repo)


def test_recovery_rejects_plausible_complete_run_fault_tampering(dataset, tmp_path):
    inspection = importlib.import_module(
        "experiments.04_surface_reconstruction.src.inspection"
    )
    repo = Path(__file__).resolve().parents[3]
    prior = runner.execute(dataset, [1, 2], 0.05, tmp_path / "prior", repo)
    record = prior / "output/2/stages.json"
    saved = json.loads(record.read_text())
    saved["negative_controls"]["double_depth"] = {
        "points": 1,
        "mean_m": 0,
        "rmse_m": 0,
        "max_m": 0,
    }
    record.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="inventory"):
        inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "new", repo)
    (prior / "metadata/status.json").write_text('{"status":"running"}')
    path = inspection.execute(
        dataset, [1, 2], 0.05, prior, tmp_path / "unverified", repo
    )
    assert (
        json.loads((path / "output/metrics.json").read_text())["negative_controls"]
        is None
    )


def test_completed_inspection_without_controls_can_be_reused(dataset, tmp_path):
    inspection = importlib.import_module(
        "experiments.04_surface_reconstruction.src.inspection"
    )
    repo = Path(__file__).resolve().parents[3]
    prior = runner.execute(dataset, [1, 2], 0.05, tmp_path / "prior", repo)
    (prior / "metadata/status.json").write_text('{"status":"running"}')
    first = inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "first", repo)
    second = inspection.execute(dataset, [1, 2], 0.05, first, tmp_path / "second", repo)
    assert verify_run(second)["status"] == "complete"
    assert (
        json.loads((second / "output/metrics.json").read_text())["negative_controls"]
        is None
    )


def test_recovery_rejects_changes_after_initial_verification(
    dataset, tmp_path, monkeypatch
):
    inspection = importlib.import_module(
        "experiments.04_surface_reconstruction.src.inspection"
    )
    repo = Path(__file__).resolve().parents[3]
    prior = runner.execute(dataset, [1, 2], 0.05, tmp_path / "prior", repo)
    original = inspection.validate_prior

    def change_after_verification(*args):
        provenance = original(*args)
        for key in (1, 2):
            record = prior / f"output/{key}/stages.json"
            saved = json.loads(record.read_text())
            saved["negative_controls"]["double_depth"] = {
                "points": 1,
                "mean_m": 0,
                "rmse_m": 0,
                "max_m": 0,
            }
            record.write_text(json.dumps(saved))
        return provenance

    monkeypatch.setattr(inspection, "validate_prior", change_after_verification)
    with pytest.raises(ValueError, match="integrity"):
        inspection.execute(dataset, [1, 2], 0.05, prior, tmp_path / "new", repo)


def test_all_invalid_dataset_fails_without_publishing(dataset, tmp_path):
    Image.fromarray(np.array([[0, 0]], dtype=np.uint16)).save(
        dataset / "trajectory2/depth/1.png"
    )
    with pytest.raises(ValueError, match="empty reconstruction"):
        runner.execute(
            dataset, [1], 0.05, tmp_path / "runs", Path(__file__).resolve().parents[3]
        )
    run = next((tmp_path / "runs").iterdir())
    assert json.loads((run / "metadata/status.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("points", [np.empty((0, 3)), [[np.nan, 0, 0]], [[0, 1]]])
def test_invalid_reference(points):
    with pytest.raises(ValueError):
        evaluation.SurfaceScorer(np.asarray(points), 0.05)


@pytest.mark.parametrize("threshold", [0, -1, np.nan, np.inf])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        evaluation.SurfaceScorer(np.zeros((1, 3)), threshold)


def test_empty_observation_and_bad_shape():
    scorer = evaluation.SurfaceScorer(np.zeros((1, 3)), 0.1)
    assert scorer.observe(np.empty((0, 3))).size == 0
    with pytest.raises(ValueError, match="empty"):
        scorer.summary()
    with pytest.raises(ValueError):
        scorer.observe(np.array([[np.inf, 0, 0]]))
    with pytest.raises(ValueError):
        evaluation.distance_summary(np.array([]))


def test_ply_exact_and_truncated(dataset, tmp_path):
    path = dataset / "reference_surface/living-room.ply"
    np.testing.assert_array_equal(
        dataset_module.read_reference(path), [[0, 0, 1], [1, 0, 1]]
    )
    bad = tmp_path / "bad.ply"
    bad.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError, match="size"):
        dataset_module.read_reference(bad)
    bad.write_bytes(b"ply\nformat ascii 1.0\nend_header\n")
    with pytest.raises(ValueError):
        dataset_module.read_reference(bad)


def test_publisher_ply_trailing_newline_only(dataset, tmp_path):
    source = dataset / "reference_surface/living-room.ply"
    path = tmp_path / "publisher.ply"
    path.write_bytes(source.read_bytes() + b"\n")
    np.testing.assert_array_equal(
        dataset_module.read_reference(path), [[0, 0, 1], [1, 0, 1]]
    )
    for trailer in (b"unexpected", b"\n\n", b"\x00"):
        path.write_bytes(source.read_bytes() + trailer)
        with pytest.raises(ValueError, match="size"):
            dataset_module.read_reference(path)


def test_run_complete_inputs_scores_and_tampering(dataset, tmp_path):
    repo = Path(__file__).resolve().parents[3]
    path = runner.execute(dataset, [1, 2], 0.05, tmp_path / "runs", repo)
    assert verify_run(path)["status"] == "complete"
    result = json.loads((path / "output/metrics.json").read_text())
    assert result["accuracy"]["mean_m"] == 0
    assert result["reference_coverage_fraction"] == 1
    assert result["reconstruction_points"] == 2
    assert result["negative_controls"]["double_depth"]["mean_m"] > 0
    assert result["negative_controls"]["inverse_pose"]["mean_m"] > 0
    assert (path / "input/1/depth.png").read_bytes() == (
        dataset / "trajectory2/depth/1.png"
    ).read_bytes()
    index = json.loads((path / "output/surface.json").read_text())
    assert [s["frame_id"] for s in index["shards"]] == ["1", "2"]
    assert (path / "review.html").is_file()
    review = (path / "review.html").read_text(encoding="utf-8")
    assert '<iframe title="Interactive 3D point surface" src="viewer.html"' in review
    assert "1 valid, 1 missing of 2 pixels" in review
    assert 'src="debug/1/depth_metres_valid.png"' in review
    assert (
        "white means valid depth; black means missing depth. This is not an object mask."
        in review
    )
    (path / "output/metrics.json").write_text("{}")
    with pytest.raises(ValueError):
        verify_run(path)


def test_failed_run_keeps_receipt(dataset, tmp_path):
    (dataset / "trajectory2/depth/2.png").unlink()
    repo = Path(__file__).resolve().parents[3]
    with pytest.raises(FileNotFoundError):
        runner.execute(dataset, [1, 2], 0.05, tmp_path / "runs", repo)
    paths = list((tmp_path / "runs").iterdir())
    assert len(paths) == 1
    status = json.loads((paths[0] / "metadata/status.json").read_text())
    assert status["status"] == "failed"
    with pytest.raises(ValueError):
        verify_run(paths[0])
