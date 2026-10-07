"""Exercise layer substitution, timing and reference controls with known inputs."""

import json
import time
from dataclasses import replace

import numpy as np
import pytest
from PIL import Image

from src.walkthrough import pipeline
from src.walkthrough.steps import objects
from src.walkthrough.steps.capture import TumSequence
from src.walkthrough.steps.depth import RecordedSensorDepth
from src.walkthrough.steps.tracking import ReferencePoses
from src.walkthrough.tests import providers
from src.walkthrough.tests.test_adapters import (
    config as config,  # noqa: PLC0414 - pytest fixture export
)
from src.walkthrough.tests.test_adapters import read


def timing(result):
    return json.loads((result.path / "metadata/timing.json").read_text())


def test_every_completed_layer_records_load_prediction_and_visual_timing(config):
    result = pipeline.run(config)
    assert result.complete
    stages = timing(result)["stages"]
    for row in result.steps:
        assert stages[f"load_{row.name}"]["successful_samples"] == 1
        assert stages[f"prediction_{row.name}"]["successful_samples"] == 1
        assert stages[f"visual_{row.name}"]["successful_samples"] == 1


def test_frame_layers_report_frame_counts_and_fps(config):
    result = pipeline.run(config)
    stages = timing(result)["stages"]
    for name in ("depth", "tracking", "surface", "objects"):
        assert stages[f"prediction_{name}"]["frames"] == 3
        assert stages[f"prediction_{name}"]["fps"] > 0
    assert timing(result)["processed_frames"] == 3
    assert timing(result)["end_to_end_fps"] > 0


def test_per_frame_samples_exist(config):
    result = pipeline.run(config)
    samples = timing(result)["samples"]
    for name in ("depth_frame", "surface_frame", "objects_frame"):
        rows = [row for row in samples if row["stage"] == name]
        assert len(rows) == 3
        assert all(row["frames"] == 1 and row["status"] == "complete" for row in rows)


def test_result_rows_name_method_and_frames(config):
    result = pipeline.run(config)
    rows = {row.name: row for row in result.steps}
    assert rows["depth"].method == "flat_depth"
    assert rows["tracking"].method == "identity_backend"
    assert rows["surface"].method == "metric_points"
    assert rows["objects"].method == "whole_image"
    assert all(
        rows[name].frames == 3
        for name in ("capture", "depth", "tracking", "surface", "objects")
    )
    assert rows["mapping"].frames is None
    saved = json.loads((result.path / "output/result.json").read_text())
    assert saved["controls"] == result.controls and saved["is_measurement"] is False
    assert [(row["method"], row["frames"]) for row in saved["steps"]] == [
        (row.method, row.frames) for row in result.steps
    ]


def test_skip_reason_follows_partial_rule(config):
    no_mapping = pipeline.run(replace(config, mapping=None))
    assert no_mapping.steps[4].status == "unavailable"
    assert no_mapping.steps[5].status == "skipped"
    assert "mapping is unavailable" in no_mapping.steps[5].reason
    partial = pipeline.run(replace(config, mapping=None, partial=True))
    assert partial.steps[5].status == "complete"

    def bad_depth(frames, *, run):
        raise ValueError("deliberate depth failure")

    failed = pipeline.run(
        replace(config, depth=providers.Fixture("bad_depth", bad_depth))
    )
    assert failed.steps[1].status == "failed"
    assert (
        failed.steps[3].reason
        == "Waiting on earlier layers: depth is failed, tracking is skipped"
    )


def test_skip_reasons_trace_to_root_cause(config):
    result = pipeline.run(replace(config, depth=None))
    assert [row.status for row in result.steps] == [
        "complete",
        "unavailable",
        "skipped",
        "skipped",
        "skipped",
        "skipped",
    ]
    assert "Task54" in result.steps[1].reason
    assert all("depth is unavailable" in row.reason for row in result.steps[2:])


@pytest.mark.parametrize(
    "defect,reason",
    [("missing", "too few"), ("extra", "too many"), ("swapped", "order")],
)
def test_depth_contract_refuses_wrong_count_or_order(config, defect, reason):
    def bad_depth(frames, *, run):
        predictions = list(providers.flat_depth(frames, run=run))
        if defect == "missing":
            predictions = predictions[:-1]
        elif defect == "extra":
            predictions = [*predictions, predictions[-1]]
        else:
            predictions = [predictions[1], predictions[0], *predictions[2:]]
        yield from predictions

    result = pipeline.run(
        replace(config, depth=providers.Fixture("bad_depth", bad_depth))
    )
    assert result.steps[1].status == "failed"
    assert reason in result.steps[1].reason
    assert not (result.path / "output/predictions/depth.json").exists()
    assert all(row.status == "skipped" for row in result.steps[2:])


def test_multi_view_depth_fits_contract(config):
    def all_frames_depth(frames, *, run):
        observations = list(frames)
        time.sleep(0.02)
        yield from providers.flat_depth(iter(observations), run=run)

    result = pipeline.run(
        replace(config, depth=providers.Fixture("multi_view", all_frames_depth))
    )
    assert result.complete
    rows = [row for row in timing(result)["samples"] if row["stage"] == "depth_frame"]
    assert len(rows) == 3
    assert rows[0]["elapsed_seconds"] >= 0.02
    assert rows[0]["elapsed_seconds"] > sum(row["elapsed_seconds"] for row in rows[1:])


def test_tracking_lost_frame_reason_is_visible(config):
    def lost_frame(frames, *, run):
        records = providers.pose_tracking.track(
            frames, providers.IdentityBackend(), run=run
        )
        return [
            records[0],
            replace(records[1], pose=None, reason="deliberate lost observation"),
            records[2],
        ]

    result = pipeline.run(
        replace(config, tracking=providers.Fixture("lost_frame", lost_frame))
    )
    assert result.steps[2].status == "failed"
    frame_id = read(result, "capture")["frames"][1]["frame_id"]
    assert f"first {frame_id}: deliberate lost observation" in result.steps[2].reason
    assert "1 of 3" in result.steps[2].reason


def test_tracking_contract_refuses_changed_source_timestamp(config):
    def changed_timestamp(frames, *, run):
        records = providers.pose_tracking.track(
            frames, providers.IdentityBackend(), run=run
        )
        return [replace(records[0], timestamp_s=999.0), *records[1:]]

    result = pipeline.run(
        replace(
            config, tracking=providers.Fixture("changed_timestamp", changed_timestamp)
        )
    )
    assert result.steps[2].status == "failed"
    frame_id = read(result, "capture")["frames"][0]["frame_id"]
    assert frame_id in result.steps[2].reason
    assert "timestamp" in result.steps[2].reason.lower()
    assert not (result.path / "output/predictions/tracking.json").exists()
    assert not (result.path / "metadata/manifest.json").exists()


def test_reference_depth_on_tum_sample(config, tmp_path):
    root = tmp_path / "tum_sample"
    (root / "rgb").mkdir(parents=True)
    (root / "depth").mkdir()
    Image.new("RGB", (640, 480), (10, 20, 30)).save(root / "rgb/0.png")
    encoded = np.full((480, 640), 10000, dtype=np.uint16)
    encoded[0, :2] = [0, 20000]
    Image.fromarray(encoded).save(root / "depth/0.png")
    (root / "rgb.txt").write_text("1.7 rgb/0.png\n")
    (root / "depth.txt").write_text("1.7 depth/0.png\n")
    result = pipeline.run(
        replace(
            config,
            source=TumSequence(root),
            depth=RecordedSensorDepth(root),
            requested=("capture", "depth"),
        )
    )
    assert result.steps[1].status == "complete"
    assert result.controls["depth"] == "reference"
    assert read(result, "depth")["control"] == "reference"
    assert not result.is_measurement
    with np.load(result.path / read(result, "depth")["frames"][0]["arrays"]) as arrays:
        assert arrays["depth"][1, 1] == 2.0
        assert not arrays["valid"][0, :2].any()
        assert arrays["valid"][1:, :].all()


def test_reference_poses_reach_objects_only_under_control(config, tmp_path):
    groundtruth = tmp_path / "groundtruth.txt"
    groundtruth.write_text("1.7 0 0 0 0 0 0 1\n1.72 0 0 0 0 0 0 1\n1.9 0 0 0 0 0 0 1\n")
    choice = ReferencePoses(groundtruth)
    result = pipeline.run(replace(config, tracking=choice))
    assert result.complete
    assert result.steps[3].status == result.steps[5].status == "complete"
    assert result.controls["tracking"] == "reference" and not result.is_measurement
    records = read(result, "tracking")["records"]
    assert all(row["pose"]["source"] == "supplied" for row in records)
    assert all(
        row["world_id"] == "tum_groundtruth"
        for row in read(result, "surface")["shards"]
    )
    assert len(read(result, "objects")["origins"]) == 1
    unlabelled = pipeline.run(
        replace(
            config,
            tracking=providers.Fixture("unlabelled_poses", choice.load()),
            partial=True,
        )
    )
    assert unlabelled.steps[3].status == "failed"
    assert unlabelled.steps[5].status == "failed"
    assert "outside a labelled reference control" in unlabelled.steps[5].reason


@pytest.mark.parametrize("defect", ["nonfinite", "wrong_count"])
def test_surface_contract_refuses_bad_points(config, defect):
    def bad_surface(depth, valid, calibration, pose):
        count = int(valid.sum())
        return (
            np.full((count, 3), np.nan)
            if defect == "nonfinite"
            else np.zeros((count - 1, 3))
        )

    result = pipeline.run(
        replace(config, surface=providers.Fixture("bad_surface", bad_surface))
    )
    assert result.steps[3].status == "failed"
    frame_id = read(result, "capture")["frames"][0]["frame_id"]
    assert frame_id in result.steps[3].reason
    assert not (result.path / "output/predictions/surface.json").exists()


def test_object_contract_refuses_proposal_without_identity(config, monkeypatch):
    original = objects.association.associate_frame

    def missing_identity(*args, **kwargs):
        decisions, tracks, next_number = original(*args, **kwargs)
        return (
            [
                {key: value for key, value in row.items() if key != "object_id"}
                for row in decisions
            ],
            tracks,
            next_number,
        )

    monkeypatch.setattr(objects.association, "associate_frame", missing_identity)
    result = pipeline.run(config)
    assert result.steps[5].status == "failed"
    frame_id = read(result, "capture")["frames"][0]["frame_id"]
    assert frame_id in result.steps[5].reason and "object_id" in result.steps[5].reason
    assert not (result.path / "output/predictions/objects.json").exists()
