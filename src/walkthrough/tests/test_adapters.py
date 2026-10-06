"""Known arrays test organisation and contracts, not camera/site accuracy."""

import hashlib
import importlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.walkthrough import pipeline, validation
from src.walkthrough.config import Configuration
from src.walkthrough.steps import depth
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
    return Configuration(
        tmp_path / "runs",
        Path.cwd(),
        bundle(tmp_path / "bundle"),
        tmp_path / "bundle",
        software_control=True,
        max_distance_m=0.35,
        ambiguity_margin_m=0.05,
    )


def controls():
    return {
        "depth": providers.depth,
        "mapping": providers.mapping,
        "backend": providers.Backend(),
        "detector": providers.Detector(),
    }


def read(result, name):
    return json.loads((result.path / f"output/predictions/{name}.json").read_text())


def test_actual_six_adapters_keep_origins_and_full_geometry(config):
    result = pipeline.run(config, test_providers=controls())
    assert result.complete and result.software_control
    assert [s.name for s in result.steps] == [
        "capture",
        "depth",
        "tracking",
        "surface",
        "mapping",
        "objects",
    ]
    captured = read(result, "capture")
    assert captured["depth"] == captured["pose"] == "unavailable"
    assert all(row["pose"] is None for row in captured["frames"])
    tracked = read(result, "tracking")
    assert [r["status"] for r in tracked["records"]] == [
        "initialized",
        "tracked",
        "reset",
    ]
    geometry = read(result, "surface")
    assert [s["point_count"] for s in geometry["shards"]] == [12, 12, 12]
    points = np.load(result.path / geometry["shards"][0]["points"])
    np.testing.assert_array_equal(points[0], [-1, -1, 2])
    counted = read(result, "objects")
    assert [o["distinct_provisional_count"] for o in counted["origins"]] == [1, 1]
    assert counted["whole_site_distinct_count"] is None
    assert (
        counted["frames"][0]["proposals"][0]["object_id"]
        == counted["frames"][1]["proposals"][0]["object_id"]
    )
    assert (
        counted["frames"][2]["proposals"][0]["object_id"]
        != counted["frames"][0]["proposals"][0]["object_id"]
    )


def test_partial_mapping_missing_keeps_objects_visible_but_run_incomplete(config):
    selected = controls()
    selected.pop("mapping")
    result = pipeline.run(replace(config, partial=True), test_providers=selected)
    assert [s.status for s in result.steps] == [
        "complete",
        "complete",
        "complete",
        "complete",
        "unavailable",
        "complete",
    ]
    assert not result.complete
    from experiments.shared.runs import verify_run

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
    from experiments.shared.phone_session import read_phone_session

    owner = importlib.import_module(
        "experiments.01_camera_capture_delivery.app.capture_report"
    )
    from dataclasses import asdict

    row = asdict(
        read_phone_session(
            json.loads(config.report.read_text()),
            config.bundle,
            owner.validate_phone_session_export,
        )[0]
    )
    with pytest.raises(ValueError, match=reason):
        depth.calibration({**row, **change})


def test_tracking_range_is_refused_without_clipping(config):
    def out_of_range(row, calibration):
        return np.full((3, 4), 4.0), np.ones((3, 4), bool)

    result = pipeline.run(config, test_providers={**controls(), "depth": out_of_range})
    assert result.steps[2].status == "failed"
    assert "out-of-range" in result.steps[2].reason
    assert all(s.status == "skipped" for s in result.steps[3:])


def test_test_providers_cannot_be_used_as_predictive_methods(config):
    with pytest.raises(ValueError, match="labelled software control"):
        pipeline.run(replace(config, software_control=False), test_providers=controls())


def test_disabled_optional_validation_never_reads_truth_or_imports(config, monkeypatch):
    requests = tuple(
        validation.ScoreRequest(name, lambda: pytest.fail("Truth loaded"), {})
        for name in ("segmentation", "appearance")
    )
    imported = []
    original = importlib.import_module

    def record(name, *args):
        imported.append(name)
        return original(name, *args)

    monkeypatch.setattr(importlib, "import_module", record)
    result = pipeline.run(config, test_providers=controls(), scores=requests)
    assert not any(
        "02_segmentation" in name or "03_appearance" in name for name in imported
    )
    scores = json.loads((result.path / "output/scores.json").read_text())
    assert (
        scores["segmentation"]["status"]
        == scores["appearance"]["status"]
        == "unavailable"
    )


def test_tracking_score_reads_truth_after_seal_and_uses_validation(config):
    calls = []

    def references():
        calls.append("truth")
        return [(1.7, np.eye(4)), (1.72, np.eye(4)), (1.9, np.eye(4))]

    result = pipeline.run(
        config,
        test_providers=controls(),
        scores=(validation.ScoreRequest("tracking", references, {"tolerance": 0.0}),),
    )
    scores = json.loads((result.path / "output/scores.json").read_text())
    assert calls == ["truth"]
    assert scores["tracking"]["tracked_edges"] == 1
    assert scores["tracking"]["failed_observations"] == 0


def test_prediction_data_are_readonly():
    frozen = validation._readonly({"rows": [{"answer": 1}]})
    with pytest.raises(TypeError):
        frozen["rows"][0]["answer"] = 2


def test_enabled_optional_evidence_does_not_change_counts(config):
    result = pipeline.run(
        replace(config, segmentation="rectangle", appearance=True),
        test_providers=controls(),
    )
    counted = read(result, "objects")
    assert result.complete
    assert [o["distinct_provisional_count"] for o in counted["origins"]] == [1, 1]
    proposal = counted["frames"][0]["proposals"][0]
    assert set(proposal["appearance"]) == {"orb", "sift"}
    assert (result.path / proposal["segmentation"]["mask"]).is_file()
    assert counted["optional_evidence_changes_counting"] is False


def test_corrupted_input_hash_stops_at_capture(config):
    (config.bundle / "images/0.png").write_bytes(b"corrupted")
    result = pipeline.run(config, test_providers=controls())
    assert result.steps[0].status == "failed"
    assert all(step.status == "skipped" for step in result.steps[1:])
    assert not result.complete


def test_scorer_error_leaves_failed_run(config):
    def broken_truth():
        raise ValueError("independent reference unavailable")

    from experiments.shared.runs import verify_run

    with pytest.raises(ValueError, match="independent reference"):
        pipeline.run(
            config,
            test_providers=controls(),
            scores=(validation.ScoreRequest("tracking", broken_truth, {}),),
        )
    failed = next(config.run_root.iterdir())
    with pytest.raises(ValueError, match="not complete"):
        verify_run(failed)


@pytest.mark.parametrize(
    "changes",
    [
        {"max_distance_m": "0.35"},
        {"max_distance_m": 0},
        {"ambiguity_margin_m": -1},
        {"appearance": "yes"},
        {"requested": ("unknown",)},
        {"requested": ([],)},
    ],
)
def test_configuration_rejects_unsupported_values(config, changes):
    with pytest.raises(ValueError):
        replace(config, **changes)


def test_single_origin_surface_scoring_uses_full_saved_points(config):
    # Independent constants specify this software plane. Only its origin label
    # is read from predictions; no points or distances are fitted to the answer.
    def references():
        run_path = next(config.run_root.iterdir())
        saved = json.loads((run_path / "output/predictions/surface.json").read_text())
        shard = saved["shards"][0]
        return {
            "world_id": shard["world_id"],
            "segment_id": shard["segment_id"],
            "points": np.array([[x, y, 2] for y in (-1, 0, 1) for x in (-1, 0, 1, 2)]),
        }

    chosen = replace(
        config, report=bundle(config.bundle, timestamps=(1_700_000_000, 1_720_000_000))
    )
    result = pipeline.run(
        chosen,
        test_providers=controls(),
        scores=(validation.ScoreRequest("surface", references, {"threshold_m": 0.01}),),
    )
    scores = json.loads((result.path / "output/scores.json").read_text())
    assert scores["surface"]["accuracy"]["points"] == 24
    assert scores["surface"]["accuracy"]["max_m"] == 0


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
        pipeline.run(config, test_providers=controls(), scores=(request,))


def test_score_refuses_complete_status_without_artifact(config):
    from types import SimpleNamespace

    from src.walkthrough.records import StepResult

    request = validation.ScoreRequest(
        "tracking", lambda: pytest.fail("Truth loaded"), {}
    )
    with pytest.raises(ValueError, match="missing its saved prediction artifact"):
        validation.score(
            SimpleNamespace(path=config.run_root),
            config,
            (StepResult("tracking", "complete", "invalid fixture"),),
            (request,),
        )


@pytest.mark.parametrize(
    "name", ["capture", "depth", "tracking", "surface", "mapping", "objects"]
)
def test_prediction_export_failure_prevents_completion(config, monkeypatch, name):
    layer = getattr(pipeline, name)
    original = layer.write_json

    def fail_export(path, payload):
        if path.name == name + ".json" and path.parent.name == "predictions":
            raise OSError("prediction export failed")
        return original(path, payload)

    monkeypatch.setattr(layer, "write_json", fail_export)
    result = pipeline.run(config, test_providers=controls())
    index = [step.name for step in result.steps].index(name)
    assert result.steps[index].status == "failed"
    assert "prediction export failed" in result.steps[index].reason
    assert all(step.status == "complete" for step in result.steps[:index])
    assert all(step.status == "skipped" for step in result.steps[index + 1 :])
    assert not result.complete
    assert not (result.path / "metadata/manifest.json").exists()


def test_unexpected_method_error_propagates_and_records_failure(config):
    def broken_provider(*args):
        raise KeyError("method bug")

    with pytest.raises(KeyError, match="method bug"):
        pipeline.run(config, test_providers={**controls(), "depth": broken_provider})
    run_path = next(config.run_root.iterdir())
    assert (
        json.loads((run_path / "metadata/status.json").read_text())["status"]
        == "failed"
    )
    assert not (run_path / "metadata/manifest.json").exists()
