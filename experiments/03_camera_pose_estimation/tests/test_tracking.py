"""CPU tracking contracts, independent reference scoring and publication."""

import importlib
from dataclasses import fields

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

package = "experiments.03_camera_pose_estimation.src"
dataset = importlib.import_module(package + ".dataset")
backend = importlib.import_module(package + ".backend")
tracking = importlib.import_module(package + ".tracking")
evaluation = importlib.import_module(package + ".evaluation")


def frame(index, depth=True):
    from experiments.shared.contracts import Calibration

    calibration = Calibration(80, 60, 70, 70, 39.5, 29.5, "x-right_y-down_z-forward")
    rng = np.random.default_rng(12)
    colour = rng.integers(0, 256, (60, 80, 3), dtype=np.uint8)
    values = np.full((60, 80), 2.0 if depth else np.nan)
    return dataset.RGBDFrame(
        str(index),
        index * 0.03,
        index * 0.03,
        calibration,
        colour,
        values,
        np.isfinite(values),
    )


class FakeBackend:
    def __init__(self, transforms):
        self.transforms = iter(transforms)

    def estimate(self, source, target):
        transform = next(self.transforms)
        return backend.PairResult(transform is not None, transform, "fixture")


def translation(x):
    matrix = np.eye(4)
    matrix[0, 3] = x
    return matrix


def test_pose_free_input_and_noncommuting_composition():
    assert not {"pose", "reference_path"} & {
        field.name for field in fields(dataset.RGBDFrame)
    }
    first = translation(-0.1)
    second = np.eye(4)
    second[:3, :3] = Rotation.from_euler("z", 0.2).as_matrix()
    records = tracking.track([frame(i) for i in range(3)], FakeBackend([first, second]))
    assert records[0].status == "initialized"
    np.testing.assert_allclose(records[1].pose.matrix, np.linalg.inv(first))
    np.testing.assert_allclose(
        records[2].pose.matrix, np.linalg.inv(first) @ np.linalg.inv(second)
    )


def test_failure_zero_depth_and_gap_reset():
    # One failed edge must not connect the next camera to the old origin.
    records = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([None, translation(-0.1)])
    )
    assert [r.status for r in records] == ["initialized", "failed", "reset", "tracked"]
    assert records[1].pose is None
    assert records[0].pose.world_id != records[2].pose.world_id
    records = tracking.track(
        [frame(0), frame(1, False), frame(2), frame(10)], FakeBackend([])
    )
    assert [r.status for r in records] == ["initialized", "failed", "reset", "reset"]


def test_invalid_backend_transform_rejected():
    invalid = np.eye(4)
    invalid[0, 0] = 2
    records = tracking.track([frame(0), frame(1)], FakeBackend([invalid]))
    assert records[1].status == "failed" and records[1].pose is None


def test_independent_fixed_scale_errors_and_anchor_only():
    references = [(i * 0.03, translation(i * 0.1)) for i in range(4)]
    exact = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([translation(-0.1)] * 3)
    )
    doubled = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([translation(-0.2)] * 3)
    )
    reversed_motion = tracking.track(
        [frame(i) for i in range(4)], FakeBackend([translation(0.1)] * 3)
    )
    clean = evaluation.evaluate(exact, references)
    assert clean["position_rmse_m"] == pytest.approx(0, abs=1e-12)
    for wrong in (doubled, reversed_motion):
        assert evaluation.evaluate(wrong, references)["position_rmse_m"] > 0.1
    assert evaluation.evaluate(exact[:1], references)["position_rmse_m"] is None


def test_reference_matching_never_skips_unmatched_observation():
    records = tracking.track(
        [frame(i) for i in range(3)], FakeBackend([translation(-0.1)] * 2)
    )
    scored = evaluation.evaluate(
        records, [(0.0, translation(0)), (0.06, translation(0.2))], tolerance=0.001
    )
    assert scored["relative_pairs"] == 0
    assert scored["unmatched_estimates"] == 1


def test_single_matched_tracked_pose_is_not_independent_accuracy():
    records = tracking.track(
        [frame(i) for i in range(3)], FakeBackend([translation(-0.1)] * 2)
    )
    scored = evaluation.evaluate(records, [(0.03, translation(0.1))], tolerance=0.001)
    assert scored["position_rmse_m"] is None
    assert scored["position_samples"] == 0
    assert scored["segments"][0]["position_rmse_m"] is None


@pytest.mark.parametrize(
    "rows",
    [
        "1 rgb/a.png\n1 rgb/b.png",
        "2 rgb/a.png\n1 rgb/b.png",
        "nan rgb/a.png",
        "1 ../bad.png",
        "1 C:/bad.png",
    ],
)
def test_invalid_timestamp_tables(tmp_path, rows):
    path = tmp_path / "rgb.txt"
    path.write_text(rows)
    with pytest.raises(ValueError):
        dataset.read_table(path)


def test_actual_cpu_backend_known_motion_and_empty_depth():
    engine = backend.CPUOdometry()
    source = frame(0)
    colour = np.roll(source.colour, -1, axis=1)
    target = dataset.RGBDFrame(
        "1", 0.03, 0.03, source.calibration, colour, source.depth, source.valid
    )
    result = engine.estimate(source, target)
    assert result.success
    assert result.transform[0, 3] == pytest.approx(-2 / 70, abs=0.012)
    assert not engine.estimate(source, frame(1, False)).success


def test_missing_or_malformed_reference(tmp_path):
    with pytest.raises(FileNotFoundError):
        evaluation.read_references(tmp_path / "absent")
    path = tmp_path / "groundtruth.txt"
    path.write_text("0 0 0 0 0 0 0 0\n")
    with pytest.raises(ValueError):
        evaluation.read_references(path)


def test_publisher_rounded_quaternion_is_normalized_without_mutating_input(tmp_path):
    path = tmp_path / "groundtruth.txt"
    payload = "0 1 2 3 0 0 0 0.9999\n"
    path.write_text(payload)
    rows = evaluation.read_references(path)
    np.testing.assert_allclose(
        rows[0][1],
        translation(1)
        + np.array([[0, 0, 0, 0], [0, 0, 0, 2], [0, 0, 0, 3], [0, 0, 0, 0]]),
    )
    assert path.read_text() == payload


def test_pipeline_reference_separation_and_required_artifacts(tmp_path, monkeypatch):
    from PIL import Image

    from experiments.shared.runs import verify_run

    runner = importlib.import_module(package + ".run")
    root = tmp_path / "dataset"
    root.mkdir()
    for name in ("rgb", "depth"):
        (root / name).mkdir()
    for i in range(3):
        Image.fromarray(np.full((480, 640, 3), 128, np.uint8)).save(
            root / f"rgb/{i}.png"
        )
        Image.fromarray(np.full((480, 640), 10000, np.uint16)).save(
            root / f"depth/{i}.png"
        )
    (root / "rgb.txt").write_text("\n".join(f"{i*.03} rgb/{i}.png" for i in range(3)))
    (root / "depth.txt").write_text(
        "\n".join(f"{i*.03} depth/{i}.png" for i in range(3))
    )
    (root / "groundtruth.txt").write_text(
        "\n".join(f"{i*.03} {i*.1} 0 0 0 0 0 1" for i in range(3))
    )
    original = evaluation.read_references
    called = []

    def guarded(path):
        assert len(called) == 2
        return original(path)

    class GuardedBackend:
        def estimate(self, source, target):
            called.append(target.frame_id)
            return backend.PairResult(True, translation(-0.1), "test")

    monkeypatch.setattr(evaluation, "read_references", guarded)
    result = runner.execute(root, tmp_path / "runs", count=3, engine=GuardedBackend())
    assert verify_run(result)["status"] == "complete"
    assert (result / "review.html").exists()
    (result / "output/metrics.json").unlink()
    with pytest.raises(ValueError):
        runner.validate_outputs(result, 3)

    called.clear()
    validation = runner.validate_outputs

    def missing_output(path, count):
        (path / "output/metrics.json").unlink()
        validation(path, count)

    monkeypatch.setattr(runner, "validate_outputs", missing_output)
    with pytest.raises(ValueError, match="Required tracking artifact"):
        runner.execute(root, tmp_path / "failed_runs", count=3, engine=GuardedBackend())
    import json

    failed = next((tmp_path / "failed_runs").iterdir())
    assert (
        json.loads((failed / "metadata/status.json").read_text())["status"] == "failed"
    )


def test_dataset_association_resolution_and_zero_count(tmp_path):
    from PIL import Image

    (tmp_path / "rgb.txt").write_text("0 rgb.png\n.1 rgb2.png\n")
    (tmp_path / "depth.txt").write_text(".02 depth.png\n.119 depth2.png\n")
    rows, counts = dataset.associations(tmp_path, 1)
    assert rows[0]["depth_timestamp_s"] == 0.02 and counts["matched_rows"] == 2
    with pytest.raises(ValueError):
        dataset.associations(tmp_path, 0)
    Image.fromarray(np.zeros((2, 2, 3), np.uint8)).save(tmp_path / "rgb.png")
    Image.fromarray(np.full((2, 2), 5000, np.uint16)).save(tmp_path / "depth.png")
    with pytest.raises(ValueError):
        dataset.load_frame(tmp_path, rows[0])


def test_invalid_frame_arrays_and_duplicate_ids():
    source = frame(0)
    with pytest.raises(ValueError):
        dataset.RGBDFrame(
            "bad",
            float("nan"),
            0,
            source.calibration,
            source.colour,
            source.depth,
            source.valid,
        )
    with pytest.raises(ValueError):
        dataset.RGBDFrame(
            "bad",
            0,
            0,
            source.calibration,
            source.colour,
            source.depth * 3,
            source.valid,
        )
    with pytest.raises(ValueError):
        tracking.track([source, source], FakeBackend([]))


def test_all_failed_and_empty_tracking():
    records = tracking.track([frame(0, False), frame(1, False)], FakeBackend([]))
    scored = evaluation.evaluate(records, [(0, translation(0)), (0.03, translation(0))])
    assert scored["failed_observations"] == 2
    assert scored["position_rmse_m"] is None
    assert scored["tracked_fraction"] == 0
    assert tracking.track([], FakeBackend([])) == []


def test_independent_runs_have_distinct_origins():
    from experiments.shared.contracts import require_same_origin

    first = tracking.track([frame(0)], FakeBackend([]))
    second = tracking.track([frame(0)], FakeBackend([]))
    with pytest.raises(ValueError):
        require_same_origin(first[0].pose, second[0].pose)


def test_runner_associations_use_snapshot_tables(tmp_path, monkeypatch):
    runner = importlib.import_module(package + ".run")
    root = tmp_path / "dataset"
    root.mkdir()
    for name in ("rgb.txt", "depth.txt"):
        (root / name).write_text("0 rgb.png\n")
    seen = []

    def association(path, count):
        seen.append(path)
        assert (
            path != root
            and (path / "rgb.txt").read_bytes() == (root / "rgb.txt").read_bytes()
        )
        raise ValueError("fixture stop")

    monkeypatch.setattr(dataset, "associations", association)
    with pytest.raises(ValueError, match="fixture stop"):
        runner.execute(root, tmp_path / "runs", count=1, engine=FakeBackend([]))
    assert len(seen) == 1


def test_depth_truncation_boundary_is_not_usable():
    source = frame(0)
    with pytest.raises(ValueError):
        dataset.RGBDFrame(
            "boundary",
            0,
            0,
            source.calibration,
            source.colour,
            np.full(source.depth.shape, 4.0),
            source.valid,
        )


def test_backend_rejects_empty_converted_images(monkeypatch):
    from types import SimpleNamespace

    engine = backend.CPUOdometry()
    monkeypatch.setattr(
        engine,
        "_image",
        lambda frame: SimpleNamespace(depth=np.zeros(frame.depth.shape)),
    )
    result = engine.estimate(frame(0), frame(1))
    assert not result.success and result.reason == "no usable converted depth"
