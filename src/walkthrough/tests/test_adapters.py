"""Known arrays test layer contracts, not camera or site accuracy."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.shared.runs import verify_run
from src.walkthrough import pipeline, validation
from src.walkthrough.config import STEP_NAMES, PipelineSpec
from src.walkthrough.records import StepResult, Unavailable
from src.walkthrough.steps.capture import calibration_for
from src.walkthrough.steps.contracts import DepthPrediction
from src.walkthrough.tests import providers


def bundle(root, timestamps=(1_700_000_000, 1_720_000_000, 1_900_000_000)):
    captures, files = [], {}
    for index, timestamp in enumerate(timestamps):
        name = f"images/{index}.png"
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (4, 3), (10, 20, 30)).save(path)
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        files[name] = {"sha256": digest, "bytes": len(payload)}
        captures.append(
            {
                "camera_id": "0",
                "file": name,
                "sha256": digest,
                "width": 4,
                "height": 3,
                "crop_region": [0, 0, 4, 3],
                "rotation_degrees": 0,
                "distortion_correction_mode": 0,
                "distortion_correction_mode_name": "OFF",
                "sensor_timestamp_ns": timestamp,
                "timestamp_source": "SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME",
                "frame_number": index + 1,
            }
        )
    report = {
        "schema_version": 1,
        "session_id": "software_fixture",
        "status": "complete",
        "device": {
            "manufacturer": "fixture",
            "model": "fixture",
            "device": "fixture",
            "product": "fixture",
            "android_release": "fixture",
            "sdk_int": 33,
        },
        "checks": [
            {
                "id": "single_camera_control",
                "status": "PASS",
                "reason": "",
                "details": [
                    {**row, "bytes": files[row["file"]]["bytes"]} for row in captures
                ],
            },
            {
                "id": "arcore_depth_and_pose",
                "status": "SKIPPED",
                "reason": "Fixture has no streams",
            },
        ],
        "cameras": [
            {
                "id": "0",
                "pixel_array_size": [4, 3],
                "active_array_rect": [0, 0, 4, 3],
                "pre_correction_active_array_rect": [0, 0, 4, 3],
                "intrinsic_calibration_grid": "pre_correction_active_array",
                "intrinsic_calibration": {
                    "available": True,
                    "value": [2.0, 2.0, 1.0, 1.0, 0.0],
                },
                "lens_distortion": {"available": True, "value": [0.0] * 5},
            }
        ],
        "captures": captures,
        "files": files,
    }
    report_path = root / "report.json"
    report_path.write_text(json.dumps(report))
    return report_path


@pytest.fixture
def config(tmp_path):
    from src.walkthrough.steps.capture import PhoneExport
    from src.walkthrough.steps.objects import ObjectSettings

    report = bundle(tmp_path / "bundle")
    return providers.with_controls(
        PipelineSpec(
            tmp_path / "runs",
            Path.cwd(),
            PhoneExport(report, report.parent),
            objects=ObjectSettings(max_distance_m=0.35, ambiguity_margin_m=0.05),
        )
    )


def read(result, name):
    return json.loads((result.path / f"output/predictions/{name}.json").read_text())


def test_actual_six_adapters_keep_origins_and_full_geometry(config):
    result = pipeline.run(config)
    assert result.complete and not result.is_measurement
    assert [row.name for row in result.steps] == list(STEP_NAMES)
    captured = read(result, "capture")
    assert captured["withheld_from_methods"]["depth"]
    assert captured["withheld_from_methods"]["pose"]
    assert all("pose" not in row for row in captured["frames"])
    tracked = read(result, "tracking")
    assert [row["status"] for row in tracked["records"]] == [
        "initialized",
        "tracked",
        "reset",
    ]
    geometry = read(result, "surface")
    assert [row["point_count"] for row in geometry["shards"]] == [12, 12, 12]
    points = np.load(result.path / geometry["shards"][0]["points"])
    np.testing.assert_array_equal(points[0], [-1, -1, 2])
    counted = read(result, "objects")
    assert [row["distinct_provisional_count"] for row in counted["origins"]] == [1, 1]
    assert counted["whole_site_distinct_count"] is None
    ids = [frame["proposals"][0]["object_id"] for frame in counted["frames"]]
    assert ids[0] == ids[1] and ids[2] != ids[0]
    stages = json.loads(
        (result.path / "output/visualizations/manifest.json").read_text()
    )["stages"]
    assert [stage["stage"] for stage in stages] == list(STEP_NAMES)
    for stage in stages:
        assert stage["status"] == "complete"
        assert stage["methods"]
        assert stage["artifacts"]
    assert counted["synthetic_detector"] is True


def test_partial_mapping_missing_keeps_objects_visible_but_run_incomplete(config):
    result = pipeline.run(replace(config, partial=True, mapping=None))
    assert [row.status for row in result.steps] == ["complete"] * 4 + [
        "unavailable",
        "complete",
    ]
    assert not result.complete
    with pytest.raises(ValueError, match="not complete"):
        verify_run(result.path)


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"rotation_degrees": 90}, "rotation"),
        ({"geometry_ready": False}, "calibration"),
        ({"lens_distortion": None}, "distortion"),
        ({"lens_distortion": [0.1]}, "distortion"),
        ({"intrinsics": [2, 2, 1, 1, 0.1]}, "skew"),
        ({"sensor_to_image_crop_scale": [0.5, 0.5]}, "grid conversion"),
        ({"pre_correction_active_array_rect": [1, 1, 5, 4]}, "grid conversion"),
    ],
)
def test_unsupported_phone_geometry_refused(config, change, reason):
    result = pipeline.run(replace(config, requested=("capture",)))
    row = read(result, "capture")["frames"][0]
    with pytest.raises((ValueError, Unavailable), match=reason):
        calibration_for({**row, "phone_grid": {**row["phone_grid"], **change}})


def test_tracking_range_is_refused_without_clipping(config):
    def out_of_range(frames, *, run):
        for frame in frames:
            yield DepthPrediction(
                frame.frame_id, np.full((3, 4), 4.0), np.ones((3, 4), bool)
            )

    result = pipeline.run(
        replace(config, depth=providers.Fixture("out_of_range", out_of_range))
    )
    assert result.steps[2].status == "failed"
    assert "out-of-range" in result.steps[2].reason
    assert all(row.status == "skipped" for row in result.steps[3:])
    depth_arrays = np.load(result.path / read(result, "depth")["frames"][0]["arrays"])
    assert depth_arrays["valid"].all()
    assert np.all(depth_arrays["depth"] == 4.0)


def test_fixture_marks_run_as_control(config):
    from src.walkthrough.tests.test_imports_cli import invoke

    result = pipeline.run(config)
    assert result.controls == {
        "depth": "software",
        "tracking": "software",
        "mapping": "software",
        "objects": "software",
    }
    assert not result.is_measurement
    help_result = invoke(["-m", "src.walkthrough.cli", "--help"])
    assert help_result.returncode == 0
    assert (
        "flat_depth" not in help_result.stdout
        and "whole_image" not in help_result.stdout
    )


def test_unscored_components_never_read_truth(config):
    requests = tuple(
        validation.ScoreRequest(name, lambda: pytest.fail("Truth loaded"), {})
        for name in ("detection", "segmentation", "appearance", "identity")
    )
    result = pipeline.run(config, scores=requests)
    scores = json.loads((result.path / "output/scores.json").read_text())
    assert all(
        scores[name]["status"] == "unavailable"
        for name in ("detection", "segmentation", "appearance", "identity")
    )
    assert all("Task56" in scores[name]["reason"] for name in scores)


def test_tracking_score_reads_truth_after_seal_and_uses_validation(config):
    calls = []

    def references():
        run_path = next(config.run_root.iterdir())
        assert (run_path / "metadata/prediction_hashes.json").is_file()
        calls.append("truth")
        return [(1.7, np.eye(4)), (1.72, np.eye(4)), (1.9, np.eye(4))]

    result = pipeline.run(
        config,
        scores=(validation.ScoreRequest("tracking", references, {"tolerance": 0.0}),),
    )
    scores = json.loads((result.path / "output/scores.json").read_text())
    assert calls == ["truth"]
    assert scores["tracking"]["result"]["tracked_edges"] == 1
    assert scores["tracking"]["result"]["failed_observations"] == 0


def test_enabled_optional_evidence_does_not_change_counts(config):
    from src.walkthrough.steps.objects import ClassicalAppearance, ClassicalSegmentation

    settings = replace(
        config.objects,
        segmentation=ClassicalSegmentation("rectangle"),
        appearance=ClassicalAppearance(),
    )
    result = pipeline.run(replace(config, objects=settings))
    counted = read(result, "objects")
    assert result.complete
    assert [row["distinct_provisional_count"] for row in counted["origins"]] == [1, 1]
    proposal = counted["frames"][0]["proposals"][0]
    assert set(proposal["appearance"]) == {"orb", "sift"}
    assert (result.path / proposal["segmentation"]["mask"]).is_file()
    assert counted["optional_evidence_changes_counting"] is False


def test_corrupted_input_hash_stops_at_capture(config):
    (config.source.bundle / "images/0.png").write_bytes(b"corrupted")
    result = pipeline.run(config)
    assert result.steps[0].status == "failed"
    assert all(row.status == "skipped" for row in result.steps[1:])
    assert not result.complete


def test_scorer_error_leaves_failed_run(config):
    def broken_truth():
        raise ValueError("independent reference unavailable")

    with pytest.raises(ValueError, match="independent reference"):
        pipeline.run(
            config, scores=(validation.ScoreRequest("tracking", broken_truth, {}),)
        )
    with pytest.raises(ValueError, match="not complete"):
        verify_run(next(config.run_root.iterdir()))


@pytest.mark.parametrize(
    "changes",
    [
        {"max_distance_m": "0.35"},
        {"max_distance_m": 0},
        {"ambiguity_margin_m": -1},
        {"max_distance_m": float("nan")},
        {"ambiguity_margin_m": float("inf")},
    ],
)
def test_object_settings_reject_unsupported_values(config, changes):
    with pytest.raises(ValueError):
        replace(config.objects, **changes)


@pytest.mark.parametrize("requested", [("unknown",), ([],), ("capture", "capture")])
def test_configuration_rejects_unsupported_values(config, requested):
    with pytest.raises(ValueError):
        replace(config, requested=requested)


def test_segmentation_rejects_unknown_method():
    from src.walkthrough.steps.objects import ClassicalSegmentation

    with pytest.raises(ValueError):
        ClassicalSegmentation("unknown")


def test_single_origin_surface_scoring_uses_full_saved_points(config):
    def references():
        run_path = next(config.run_root.iterdir())
        saved = json.loads((run_path / "output/predictions/surface.json").read_text())
        shard = saved["shards"][0]
        return {
            "world_id": shard["world_id"],
            "segment_id": shard["segment_id"],
            "points": np.array([[x, y, 2] for y in (-1, 0, 1) for x in (-1, 0, 1, 2)]),
        }

    bundle(config.source.bundle, timestamps=(1_700_000_000, 1_720_000_000))
    result = pipeline.run(
        config,
        scores=(validation.ScoreRequest("surface", references, {"threshold_m": 0.01}),),
    )
    scores = json.loads((result.path / "output/scores.json").read_text())
    assert scores["surface"]["result"]["accuracy"]["points"] == 24
    assert scores["surface"]["result"]["accuracy"]["max_m"] == 0


def test_surface_reference_origin_mismatch_is_refused(config):
    request = validation.ScoreRequest(
        "surface",
        lambda: {
            "world_id": "wrong",
            "segment_id": "wrong",
            "points": np.zeros((1, 3)),
        },
        {"threshold_m": 0.01},
    )
    with pytest.raises(ValueError, match="match every scored origin"):
        pipeline.run(config, scores=(request,))


def test_score_refuses_complete_status_without_artifact(config):
    request = validation.ScoreRequest(
        "tracking", lambda: pytest.fail("Truth loaded"), {}
    )
    with pytest.raises(ValueError, match="missing its saved prediction artifact"):
        validation.score(
            config.run_root,
            (StepResult("tracking", "complete", "invalid fixture"),),
            (request,),
        )


@pytest.mark.parametrize("name", STEP_NAMES)
def test_prediction_export_failure_prevents_completion(config, monkeypatch, name):
    layer = getattr(pipeline, name)
    original = layer.write_json

    def fail_export(path, payload):
        if path.name == name + ".json" and path.parent.name == "predictions":
            raise OSError("prediction export failed")
        return original(path, payload)

    monkeypatch.setattr(layer, "write_json", fail_export)
    result = pipeline.run(config)
    index = list(STEP_NAMES).index(name)
    assert result.steps[index].status == "failed"
    assert "prediction export failed" in result.steps[index].reason
    assert all(row.status == "complete" for row in result.steps[:index])
    assert all(row.status == "skipped" for row in result.steps[index + 1 :])
    assert not result.complete
    assert not (result.path / "metadata/manifest.json").exists()


def test_unexpected_method_error_propagates_and_records_failure(config):
    def broken_provider(frames, *, run):
        raise KeyError("method bug")

    with pytest.raises(KeyError, match="method bug"):
        pipeline.run(
            replace(config, depth=providers.Fixture("broken", broken_provider))
        )
    run_path = next(config.run_root.iterdir())
    assert (
        json.loads((run_path / "metadata/status.json").read_text())["status"]
        == "failed"
    )
    assert not (run_path / "metadata/manifest.json").exists()
