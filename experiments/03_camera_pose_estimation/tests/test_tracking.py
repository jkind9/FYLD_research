"""CPU tracking contracts, independent reference scoring and publication."""

import gc
import hashlib
import importlib
import json
import weakref
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

package = "experiments.03_camera_pose_estimation.src"
dataset = importlib.import_module(package + ".dataset")
backend = importlib.import_module(package + ".backend")
tracking = importlib.import_module(package + ".tracking")
evaluation = importlib.import_module(package + ".evaluation")
supervisor = importlib.import_module(package + ".supervisor")


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
    root = tmp_path / "rgbd_dataset_freiburg1_desk"
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
    (root / "rgb.txt").write_text(
        "\n".join(f"{i * 0.03} rgb/{i}.png" for i in range(3))
    )
    (root / "depth.txt").write_text(
        "\n".join(f"{i * 0.03} depth/{i}.png" for i in range(3))
    )
    (root / "groundtruth.txt").write_text(
        "\n".join(f"{i * 0.03} {i * 0.1} 0 0 0 0 0 1" for i in range(3))
    )
    original = evaluation.read_references
    called = []

    def guarded(path):
        assert len(called) == 2
        run_path = next(result_path.iterdir())
        saved = json.loads((run_path / "output/poses.json").read_text())
        assert len(saved["records"]) == 3
        assert all(
            row["status"] in {"initialized", "tracked"} for row in saved["records"]
        )
        return original(path)

    class GuardedBackend:
        def estimate(self, source, target):
            called.append(target.frame_id)
            return backend.PairResult(True, translation(-0.1), "test")

    result_path = tmp_path / "runs"
    monkeypatch.setattr(evaluation, "read_references", guarded)
    result = runner.execute(root, result_path, count=3, engine=GuardedBackend())
    assert verify_run(result)["status"] == "complete"
    configuration = json.loads((result / "metadata/configuration.json").read_text())
    assert configuration["sequence"] == "rgbd_dataset_freiburg1_desk"
    assert configuration["selected_frames"] == 3
    assert (
        configuration["hyperparameters"]["sequence"]["value"]
        == configuration["sequence"]
    )
    assert configuration["hyperparameters"]["frames"]["value"] == 3
    manifest = json.loads((result / "metadata/manifest.json").read_text())
    manifest_files = set(manifest["files"])
    for row in json.loads((result / "output/associations.json").read_text())["rows"]:
        for kind in ("rgb", "depth"):
            assert f"input/observations/{row[kind]}" in manifest_files
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
    failed = next((tmp_path / "failed_runs").iterdir())
    assert (
        json.loads((failed / "metadata/status.json").read_text())["status"] == "failed"
    )


@pytest.mark.parametrize(
    ("dataset_name", "frames"),
    [("rgbd_dataset_freiburg1_xyz", "792"), ("rgbd_dataset_freiburg1_desk", "573")],
)
def test_cli_accepts_full_sequence_counts(monkeypatch, tmp_path, dataset_name, frames):
    runner = importlib.import_module(package + ".run")
    dataset_root = tmp_path / dataset_name
    dataset_root.mkdir()
    run_root = tmp_path / "runs"
    selected = []
    verified_identity = {
        "status": (
            "archive provenance checked; completed runs hash selected inputs "
            "in the run manifest"
        ),
        "sequence": dataset_name,
        "archive_sha256": "a" * 64,
    }

    def execute(**kwargs):
        selected.append(kwargs)
        return run_root

    monkeypatch.setattr(runner, "supervise", execute)
    monkeypatch.setattr(
        runner, "_archive_provenance", lambda root, repo: verified_identity
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "tracking",
            "--dataset",
            str(dataset_root),
            "--frames",
            frames,
            "--runs",
            str(run_root),
        ],
    )
    runner.main()
    assert len(selected) == 1
    call = selected[0]
    assert call["dataset_path"] == dataset_root
    assert call["run_root"] == run_root
    assert call["frames"] == int(frames)
    assert call["repo"] == Path(__file__).resolve().parents[3]
    identity = call["sequence_identity"]
    assert identity["sequence"] == dataset_name
    assert identity["status"].startswith("archive provenance checked")
    assert identity["archive_sha256"]


def test_cli_rejects_named_but_unverified_dataset_path(monkeypatch, tmp_path):
    runner = importlib.import_module(package + ".run")
    dataset_root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    dataset_root.mkdir()
    monkeypatch.setattr(
        "sys.argv",
        ["tracking", "--dataset", str(dataset_root), "--frames", "792"],
    )
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2


@pytest.mark.parametrize(
    ("dataset_name", "archive_name"),
    [
        ("rgbd_dataset_freiburg1_xyz", "rgbd_dataset_freiburg1_xyz.tgz"),
        ("rgbd_dataset_freiburg1_desk", "rgbd_dataset_freiburg1_desk.tgz"),
    ],
)
def test_archive_provenance_binds_receipts_to_archive_bytes(
    tmp_path, dataset_name, archive_name
):
    from pathlib import Path

    runner = importlib.import_module(package + ".run")
    repo = tmp_path
    relative_root = (
        Path("data/tum/rgbd_dataset_freiburg1_xyz")
        if dataset_name == "rgbd_dataset_freiburg1_xyz"
        else Path("data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk")
    )
    relative_secondary = (
        relative_root / "provenance.json"
        if dataset_name == "rgbd_dataset_freiburg1_xyz"
        else relative_root.parent / "EXTRACTION.json"
    )
    relative_acquisition = Path("data/archives") / f"{archive_name}.json"
    dataset_root = repo / relative_root
    dataset_root.mkdir(parents=True)
    archive_path = repo / "data/archives" / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive = b"verified archive fixture"
    archive_path.write_bytes(archive)
    digest = hashlib.sha256(archive).hexdigest()
    official_url = "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/" + archive_name
    resolved_url = (
        "https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/" + archive_name
    )
    acquisition = {
        "source_url": official_url,
        "resolved_url": resolved_url,
        "local_sha256": digest,
    }
    secondary = {"local_sha256": digest}
    if dataset_name == "rgbd_dataset_freiburg1_xyz":
        acquisition["size_bytes"] = len(archive)
        secondary.update({"source_url": official_url, "size_bytes": len(archive)})
    else:
        acquisition["bytes"] = len(archive)
        secondary.update({"archive": archive_name, "compressed_bytes": len(archive)})
    (repo / relative_acquisition).write_text(json.dumps(acquisition))
    secondary_path = repo / relative_secondary
    secondary_path.parent.mkdir(parents=True, exist_ok=True)
    secondary_path.write_text(json.dumps(secondary))
    member_manifest = repo / "experiments/datasets/tum_freiburg1_member_hashes.json"
    member_manifest.parent.mkdir(parents=True, exist_ok=True)
    member_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sequences": {
                    dataset_name: {
                        "archive_sha256": digest,
                        "archive_bytes": len(archive),
                        "members": {
                            "rgb.txt": {"bytes": 1, "sha256": "a" * 64},
                            "depth.txt": {"bytes": 1, "sha256": "b" * 64},
                            "groundtruth.txt": {"bytes": 1, "sha256": "c" * 64},
                        },
                    }
                },
            }
        )
    )

    identity = runner._archive_provenance(dataset_root, repo)
    assert identity["sequence"] == dataset_name
    assert identity["archive_sha256"] == digest
    assert (
        identity["member_manifest_sha256"]
        == hashlib.sha256(member_manifest.read_bytes()).hexdigest()
    )
    acquisition["source_url"] = "https://untrusted.example/" + archive_name
    (repo / relative_acquisition).write_text(json.dumps(acquisition))
    with pytest.raises(ValueError, match="receipts do not match"):
        runner._archive_provenance(dataset_root, repo)


def test_selected_observation_hash_must_match_archive_member_manifest(tmp_path):
    runner = importlib.import_module(package + ".run")
    root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    root.mkdir()
    (root / "rgb").mkdir()
    (root / "depth").mkdir()
    members = {}
    for relative, payload in {
        "rgb.txt": b"0 rgb/frame.png\n",
        "depth.txt": b"0 depth/frame.png\n",
        "groundtruth.txt": b"0 0 0 0 0 0 0 1\n",
        "rgb/frame.png": b"rgb pixels",
        "depth/frame.png": b"depth pixels",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        members[relative] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    member_document = {
        "schema_version": 1,
        "sequences": {
            root.name: {
                "archive_sha256": "d" * 64,
                "archive_bytes": 123,
                "members": members,
            }
        },
    }
    manifest_path = tmp_path / "experiments/datasets/tum_freiburg1_member_hashes.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(member_document))
    identity = {
        "sequence": root.name,
        "archive_sha256": "d" * 64,
        "archive_bytes": "123",
        "member_manifest": "experiments/datasets/tum_freiburg1_member_hashes.json",
        "member_manifest_sha256": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
    }
    selected = [{"rgb": "rgb/frame.png", "depth": "depth/frame.png"}]
    assert (
        runner._verified_member_hashes(root, selected, identity, tmp_path)[
            "groundtruth.txt"
        ]
        == members["groundtruth.txt"]
    )
    runner._verify_reference_snapshot(
        root / "groundtruth.txt", members["groundtruth.txt"]["sha256"]
    )
    (root / "groundtruth.txt").write_bytes(b"1 0 0 0 0 0 0 1\n")
    with pytest.raises(ValueError, match="Reference trajectory differs"):
        runner._verify_reference_snapshot(
            root / "groundtruth.txt", members["groundtruth.txt"]["sha256"]
        )
    (root / "rgb/frame.png").write_bytes(b"RGB pixels")
    with pytest.raises(ValueError, match="differs from verified archive"):
        runner._verified_member_hashes(root, selected, identity, tmp_path)


def test_archive_provenance_rejects_archive_receipt_hash_mismatch(tmp_path):
    runner = importlib.import_module(package + ".run")
    repo = tmp_path
    dataset_root = repo / "data/tum/rgbd_dataset_freiburg1_xyz"
    dataset_root.mkdir(parents=True)
    archive_path = repo / "data/archives/rgbd_dataset_freiburg1_xyz.tgz"
    archive_path.parent.mkdir(parents=True)
    archive_path.write_bytes(b"changed archive")
    official_url = (
        "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz"
    )
    resolved_url = (
        "https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/"
        "rgbd_dataset_freiburg1_xyz.tgz"
    )
    receipt = {
        "source_url": official_url,
        "resolved_url": resolved_url,
        "local_sha256": "a" * 64,
        "size_bytes": len(b"changed archive"),
    }
    (repo / "data/archives/rgbd_dataset_freiburg1_xyz.tgz.json").write_text(
        json.dumps(receipt)
    )
    (dataset_root / "provenance.json").write_text(
        json.dumps(
            {
                "source_url": official_url,
                "local_sha256": "a" * 64,
                "size_bytes": len(b"changed archive"),
            }
        )
    )

    with pytest.raises(ValueError, match="receipts do not match"):
        runner._archive_provenance(dataset_root, repo)


@pytest.mark.parametrize(
    ("acquisition", "secondary"),
    [([], {}), ({"local_sha256": None}, {}), ({}, [])],
)
def test_archive_provenance_rejects_malformed_receipt_fields(
    tmp_path, acquisition, secondary
):
    runner = importlib.import_module(package + ".run")
    repo = tmp_path
    dataset_root = repo / "data/tum/rgbd_dataset_freiburg1_xyz"
    dataset_root.mkdir(parents=True)
    acquisition_path = repo / "data/archives/rgbd_dataset_freiburg1_xyz.tgz.json"
    secondary_path = dataset_root / "provenance.json"
    acquisition_path.parent.mkdir(parents=True)
    acquisition_path.write_text(json.dumps(acquisition))
    secondary_path.write_text(json.dumps(secondary))

    with pytest.raises((TypeError, ValueError), match="Dataset receipt"):
        runner._archive_provenance(dataset_root, repo)


def test_runner_rejects_more_frames_than_available_before_backend_calls(tmp_path):
    from PIL import Image

    runner = importlib.import_module(package + ".run")
    root = tmp_path / "rgbd_dataset_freiburg1_xyz"
    root.mkdir()
    for name in ("rgb", "depth"):
        (root / name).mkdir()
    for index in range(2):
        Image.fromarray(np.full((480, 640, 3), 128, np.uint8)).save(
            root / f"rgb/{index}.png"
        )
        Image.fromarray(np.full((480, 640), 10000, np.uint16)).save(
            root / f"depth/{index}.png"
        )
    (root / "rgb.txt").write_text("0 rgb/0.png\n0.03 rgb/1.png\n")
    (root / "depth.txt").write_text("0 depth/0.png\n0.03 depth/1.png\n")

    class MustNotRun:
        def estimate(self, source, target):
            raise AssertionError("backend ran before selection validation")

    with pytest.raises(ValueError, match="Insufficient associated frames"):
        runner.execute(root, tmp_path / "runs", count=3, engine=MustNotRun())
    assert not (tmp_path / "runs").exists()


def test_tracking_consumes_long_stream_without_retaining_old_images():
    references = {"colour": [], "depth": [], "valid": []}
    maximum_live_arrays = {name: 0 for name in references}

    def frames():
        for index in range(80):
            current = frame(index)
            for name, rows in references.items():
                rows.append(weakref.ref(getattr(current, name)))
            yield current

    class StreamingBackend:
        def estimate(self, source, target):
            gc.collect()
            for name, rows in references.items():
                live_arrays = sum(reference() is not None for reference in rows)
                maximum_live_arrays[name] = max(maximum_live_arrays[name], live_arrays)
            return backend.PairResult(True, translation(-0.1), "streaming fixture")

    records = tracking.track(frames(), StreamingBackend())
    assert len(records) == 80
    assert all(count <= 3 for count in maximum_live_arrays.values())


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
    original = dataset.associations

    def association(path, count):
        seen.append(path)
        if path == root:
            return original(path, count)
        assert (path / "rgb.txt").read_bytes() == (root / "rgb.txt").read_bytes()
        raise ValueError("fixture stop")

    monkeypatch.setattr(dataset, "associations", association)
    with pytest.raises(ValueError, match="fixture stop"):
        runner.execute(root, tmp_path / "runs", count=1, engine=FakeBackend([]))
    assert seen == [root, next((tmp_path / "runs").iterdir()) / "input/observations"]


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
