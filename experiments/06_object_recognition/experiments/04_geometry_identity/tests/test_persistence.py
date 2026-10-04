from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

from experiments.shared.runs import Run

association = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.association"
)
persistence = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.persistence"
)


def test_completed_generation_reader_checks_full_membership_and_resume_copy(
    tmp_path, observation_factory
):
    repo = Path(__file__).resolve().parents[5]
    observations = [
        observation_factory("a", "f1", 1.0, 0.0),
        observation_factory("b", "f2", 2.0, 0.1),
        observation_factory("u", "f3", 3.0, 0.2, world=None, segment=None),
    ]
    tracks, first, _ = association.associate_frame(
        observations[:1], (), "geometry-last"
    )
    tracks, second, _ = association.associate_frame(
        observations[1:2], tracks, "geometry-last"
    )
    _, unknown, _ = association.associate_frame(
        observations[2:], tracks, "geometry-last"
    )
    decisions = first + second + unknown
    settings = {"condition": "geometry-last", "gate_m": 0.35}
    root = tmp_path / "runs"
    with Run(root, repo, {"test": True}) as run:
        generation = persistence.write_condition(
            run.path, "geometry-last", observations, decisions, [], settings=settings
        )
        assert generation["unpersisted_unknown_origin_count"] == 1
    source_db = run.path / "output/conditions/geometry-last/identity.sqlite3"
    source_hash = hashlib.sha256(source_db.read_bytes()).hexdigest()
    checked = persistence.read_generation(run.path, "geometry-last")
    assert len(checked["ledger"]["observations"]) == 3
    assert generation["persisted_observation_count"] == 2
    copied = tmp_path / "resume-staging"
    persistence.copy_for_resume(run.path, "geometry-last", copied)
    assert hashlib.sha256(source_db.read_bytes()).hexdigest() == source_hash
    assert (
        hashlib.sha256((copied / "identity.sqlite3").read_bytes()).hexdigest()
        == source_hash
    )


def test_checked_reader_rejects_mutated_artifact_after_completion(
    tmp_path, observation_factory
):
    repo = Path(__file__).resolve().parents[5]
    observation = observation_factory("a", "f1", 1.0, 0.0)
    _, decisions, state = association.associate_frame(
        [observation], (), "geometry-last"
    )
    with Run(tmp_path / "runs", repo, {"test": True}) as run:
        persistence.write_condition(
            run.path,
            "geometry-last",
            [observation],
            decisions,
            state,
            settings={"condition": "geometry-last"},
        )
    ledger = run.path / "output/conditions/geometry-last/decisions.json"
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    payload["observations"].clear()
    ledger.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest"):
        persistence.read_generation(run.path, "geometry-last")


def test_database_replay_is_exact_and_conflicting_evidence_fails(
    tmp_path, observation_factory
):
    IdentityStore = importlib.import_module("identity_store").IdentityStore

    repo = Path(__file__).resolve().parents[5]
    observation = observation_factory("a", "f1", 1.0, 0.0)
    _, decisions, state = association.associate_frame(
        [observation], (), "geometry-last"
    )
    with Run(tmp_path / "runs", repo, {"test": True}) as run:
        persistence.write_condition(
            run.path,
            "geometry-last",
            [observation],
            decisions,
            state,
            settings={"condition": "geometry-last"},
        )
    persistence.read_generation(run.path, "geometry-last")
    source_payload = {
        "schema_version": 1,
        "condition": "geometry-last",
        "settings": {"condition": "geometry-last"},
        "observation": observation,
        "decision": "new",
        "reason": decisions[0]["reason"],
        "candidates": [],
        "pose_revision_id": "supplied-base-v1",
    }
    store = IdentityStore(run.path / "output/conditions/geometry-last/identity.sqlite3")
    result = store.record_observation(
        session_id="session",
        source_id="f1",
        observation_id="a",
        source_payload=source_payload,
        decision="new",
        world_id="w",
        segment_id="s",
        label="tv",
        object_id=decisions[0]["object_id"],
        pose_revision_id="supplied-base-v1",
        position_m=(0.0, 0.0, 1.0),
    )
    assert result.object_id == decisions[0]["object_id"]
    assert store.count_observations(session_id="session") == 1
    with pytest.raises(ValueError, match="conflicting"):
        store.record_observation(
            session_id="session",
            source_id="f1",
            observation_id="a",
            source_payload={**source_payload, "changed": True},
            decision="new",
            world_id="w",
            segment_id="s",
            label="tv",
            object_id=decisions[0]["object_id"],
            pose_revision_id="supplied-base-v1",
            position_m=(0.0, 0.0, 1.0),
        )
