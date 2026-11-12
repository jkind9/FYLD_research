"""Cached identity replay contracts and fail-closed publication."""

import copy
import importlib
import json

import pytest

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, verify_run, write_json

cached = importlib.import_module(
    "experiments.06_object_recognition.experiments.06_identity_policy.cached_replay"
)
SOURCE_HASH = "a" * 64


def ledger():
    frames = []
    for index, positions in enumerate(([0.0], [1.0], [1.02, 0.02, None], [])):
        detections = [
            {
                "frame_index": index,
                "detection_index": proposal_index,
                "class_id": 73,
                "label": "book 📚",
                "world_position_m": (
                    [position, 0.0, 1.0] if position is not None else None
                ),
                "camera_position_m": [0, 0, 1],
                "xyxy": [1, 2, 3, 4],
                "confidence": 0.9,
                "localisation": {"status": "located", "world_id": "desk"},
                "association": "unresolved_outside_gate" if index else "new",
                "object_id": None if index else "object-0001",
                "coordinate_delta_m": None,
                "association_distance_m": None,
            }
            for proposal_index, position in enumerate(positions)
        ]
        frames.append(
            {
                "frame_index": index,
                "frame_id": str(index),
                "timestamp_s": index * 0.1,
                "pose": {"T_world_camera": [[1, 0], [0, 1]]},
                "rgb": f"rgb/{index}.png",
                "depth": f"depth/{index}.png",
                "cloud_start": index,
                "cloud_stop": index + 1,
                "detections": detections,
                "tracks": {},
                "failures": [],
            }
        )
    return {
        "world_id": "desk",
        "segment_id": "one",
        "position_method": "recorded median",
        "association_max_distance_m": 0.35,
        "ambiguity_margin_m": 0.05,
        "frames": frames,
        "tracks": {},
        "counts": {"frames": 4, "detections": 5, "object_ids": 1, "unresolved": 4},
    }


def test_cached_replay_preserves_proposals_and_updates_snapshots_and_counts():
    baseline = ledger()
    original = copy.deepcopy(baseline)
    corrected = cached.recompute(baseline, SOURCE_HASH)
    assert baseline == original
    cached.validate_overlay(baseline, corrected)
    assert corrected["counts"] == {
        "frames": 4,
        "detections": 5,
        "object_ids": 2,
        "unresolved": 1,
    }
    assert [item["object_id"] for item in corrected["frames"][2]["detections"]] == [
        "object-0002",
        "object-0001",
        None,
    ]
    assert corrected["frames"][3]["tracks"] == corrected["tracks"]
    assert corrected["frames"][0]["tracks"]["object-0001"]["observation_count"] == 1
    assert corrected["tracks"]["object-0001"]["observation_count"] == 2
    assert corrected["frames"][2]["failures"] == [
        {
            "detection_index": 2,
            "label": "book 📚",
            "association": "unresolved_no_position",
        }
    ]
    assigned = [
        item
        for frame in corrected["frames"]
        for item in frame["detections"]
        if item["object_id"]
    ]
    assert all(item["identity_state"] == "provisional" for item in assigned)
    report = corrected["policy_report"]
    assert report["before"]["books"]["reasons"]["unresolved_outside_gate"] == 4
    assert report["after"]["books"]["reasons"] == {
        "new": 2,
        "matched": 2,
        "unresolved_no_position": 1,
    }
    assert report["after"]["books"]["object_ids"] == 2
    assert report["association_elapsed_seconds"] >= 0
    assert "physical accuracy" in report["interpretation"]
    assert corrected["hyperparameters"] == cached.HYPERPARAMETERS


def test_observation_ids_are_unique_stable_and_source_specific():
    first = cached.recompute(ledger(), SOURCE_HASH)
    again = cached.recompute(ledger(), SOURCE_HASH)
    other = cached.recompute(ledger(), "b" * 64)

    def ids(result):
        return [
            item["observation_id"]
            for frame in result["frames"]
            for item in frame["detections"]
        ]

    assert len(set(ids(first))) == 5
    assert ids(first) == ids(again)
    assert set(ids(first)).isdisjoint(ids(other))


@pytest.mark.parametrize(
    "field",
    [
        "world_id",
        "segment_id",
        "position_method",
        "association_max_distance_m",
        "ambiguity_margin_m",
    ],
)
def test_overlay_rejects_changed_settings_or_coordinate_context(field):
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    corrected[field] = "changed"
    with pytest.raises(ValueError, match="immutable"):
        cached.validate_overlay(baseline, corrected)


@pytest.mark.parametrize(
    "location,field",
    [
        ("frame", "pose"),
        ("frame", "timestamp_s"),
        ("frame", "cloud_stop"),
        ("proposal", "xyxy"),
        ("proposal", "world_position_m"),
        ("proposal", "localisation"),
        ("proposal", "confidence"),
    ],
)
def test_overlay_rejects_changed_frame_or_proposal_content(location, field):
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    target = corrected["frames"][0]
    if location == "proposal":
        target = target["detections"][0]
    target[field] = "changed"
    with pytest.raises(ValueError, match="immutable"):
        cached.validate_overlay(baseline, corrected)


def test_overlay_rejects_reordered_or_missing_proposals():
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    corrected["frames"][2]["detections"].reverse()
    with pytest.raises(ValueError, match="immutable"):
        cached.validate_overlay(baseline, corrected)
    corrected = cached.recompute(baseline, SOURCE_HASH)
    corrected["frames"].pop()
    with pytest.raises(ValueError, match="immutable"):
        cached.validate_overlay(baseline, corrected)


@pytest.mark.parametrize("bad", [None, [], {}, {"frames": None}])
def test_invalid_ledgers_fail_clearly(bad):
    with pytest.raises(ValueError):
        cached.recompute(bad, SOURCE_HASH)


@pytest.mark.parametrize("bad_hash", [None, "", "a" * 63, "z" * 64])
def test_source_hash_requires_sha256(bad_hash):
    with pytest.raises(ValueError, match="SHA-256"):
        cached.recompute(ledger(), bad_hash)


def test_empty_sequence_is_valid():
    baseline = {**ledger(), "frames": [], "tracks": {}, "counts": {}}
    corrected = cached.recompute(baseline, SOURCE_HASH)
    assert corrected["counts"] == {
        "frames": 0,
        "detections": 0,
        "object_ids": 0,
        "unresolved": 0,
    }
    cached.validate_overlay(baseline, corrected)


@pytest.mark.parametrize("value", [None, "0.35", True, 0.4, float("nan")])
def test_recompute_rejects_changed_or_invalid_inherited_settings(value):
    baseline = ledger()
    baseline["association_max_distance_m"] = value
    with pytest.raises(ValueError, match="inherited"):
        cached.recompute(baseline, SOURCE_HASH)


@pytest.mark.parametrize(
    "target,field,value",
    [
        ("frame", "frame_index", 0.0),
        ("frame", "frame_index", True),
        ("frame", "detections", None),
        ("proposal", "detection_index", 0.0),
        ("proposal", "detection_index", True),
        ("proposal", "frame_index", 1),
        ("proposal", "class_id", []),
        ("proposal", "class_id", True),
        ("proposal", "label", None),
    ],
)
def test_invalid_frame_and_proposal_schema_fails_clearly(target, field, value):
    baseline = ledger()
    item = baseline["frames"][0]
    if target == "proposal":
        item = item["detections"][0]
    item[field] = value
    with pytest.raises(ValueError):
        cached.recompute(baseline, SOURCE_HASH)


def test_missing_original_decision_fails_with_schema_error():
    baseline = ledger()
    baseline["frames"][0]["detections"][0].pop("association")
    with pytest.raises(ValueError):
        cached.recompute(baseline, SOURCE_HASH)


@pytest.mark.parametrize("field,value", [("frames", None), ("detections", None)])
def test_overlay_rejects_invalid_lists(field, value):
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    target = corrected if field == "frames" else corrected["frames"][0]
    target[field] = value
    with pytest.raises(ValueError, match="immutable"):
        cached.validate_overlay(baseline, corrected)


def test_overlay_rejects_non_dictionary():
    with pytest.raises(ValueError, match="immutable"):
        cached.validate_overlay(ledger(), None)


@pytest.mark.parametrize("field", ["frames", "detections", "object_ids", "unresolved"])
@pytest.mark.parametrize(
    "value", ["<img src=x onerror=alert(1)>", True, -1, 1.0, None, 999]
)
def test_overlay_rejects_invalid_or_inconsistent_counts(field, value):
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    corrected["counts"][field] = value
    with pytest.raises(ValueError, match="counts"):
        cached.validate_overlay(baseline, corrected)


@pytest.mark.parametrize("counts", [None, {}, []])
def test_overlay_requires_complete_counts(counts):
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    corrected["counts"] = counts
    with pytest.raises(ValueError, match="counts"):
        cached.validate_overlay(baseline, corrected)


def test_overlay_rejects_object_count_inconsistent_with_track_snapshot():
    baseline = ledger()
    corrected = cached.recompute(baseline, SOURCE_HASH)
    corrected["tracks"].pop("object-0001")
    with pytest.raises(ValueError, match="counts"):
        cached.validate_overlay(baseline, corrected)


@pytest.fixture
def source_run(tmp_path, monkeypatch):
    runs = importlib.import_module("experiments.shared.runs")
    monkeypatch.setattr(runs, "_git", lambda *_: "fixture")
    monkeypatch.setattr(runs, "_environment", dict)
    with Run(tmp_path / "source", tmp_path, {}) as run:
        write_json(run.path / "input/baseline_observations.json", ledger())
    return tmp_path, run.path


def test_execute_publishes_verified_lineage_and_exact_input_snapshot(source_run):
    repo, source = source_run
    before_manifest = sha256(source / "metadata/manifest.json")
    before_ledger = sha256(source / "input/baseline_observations.json")
    output = cached.execute(repo, source)
    assert output.parent == repo / cached.RUNS_RELATIVE
    assert verify_run(output)["status"] == "complete"
    assert verify_run(source)["status"] == "complete"
    result = json.loads((output / "output/observations.json").read_text())
    assert result["source"] == {
        "run": source.relative_to(repo).as_posix(),
        "manifest_sha256": before_manifest,
        "ledger_sha256": before_ledger,
    }
    assert sha256(output / "input/baseline_observations.json") == before_ledger
    assert (
        json.loads((output / "metadata/configuration.json").read_text())[
            "hyperparameters"
        ]
        == cached.HYPERPARAMETERS
    )
    second = cached.execute(repo, source)
    assert second != output


def test_execute_rejects_corrupted_source_before_publication(source_run):
    repo, source = source_run
    (source / "input/baseline_observations.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        cached.execute(repo, source)
    assert not (repo / cached.RUNS_RELATIVE).exists()


def test_execute_detects_source_changes_after_recompute_and_leaves_failed_run(
    source_run, monkeypatch
):
    repo, source = source_run
    original = cached.recompute

    def mutate_after_recompute(data, digest):
        result = original(data, digest)
        (source / "input/baseline_observations.json").write_text("{}")
        return result

    monkeypatch.setattr(cached, "recompute", mutate_after_recompute)
    with pytest.raises(ValueError, match="inventory"):
        cached.execute(repo, source)
    paths = list((repo / cached.RUNS_RELATIVE).iterdir())
    assert len(paths) == 1
    assert (
        json.loads((paths[0] / "metadata/status.json").read_text())["status"]
        == "failed"
    )


def test_execute_refuses_source_outside_repository(source_run):
    repo, source = source_run
    with pytest.raises(ValueError, match="repository"):
        cached.execute(repo / "other", source)
