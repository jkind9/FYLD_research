import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

import pytest

from identity_store import IdentityStore, IdentityStoreError


@pytest.fixture
def database_path():
    database = Path(__file__).with_name(f".test-{uuid.uuid4().hex}.sqlite3")
    yield database
    for suffix in ("", "-wal", "-shm"):
        Path(f"{database}{suffix}").unlink(missing_ok=True)


def test_first_open_creates_schema_and_records_a_new_identity(database_path):
    database = database_path
    store = IdentityStore(database)

    result = store.record_observation(
        session_id="walk-1",
        source_id="camera-a",
        observation_id="frame-10/detection-2",
        source_payload={"image": "frame-10.png", "sha256": "abc"},
        decision="new",
        label="ladder",
        world_id="world-1",
        segment_id="segment-1",
        pose_revision_id="pose-1",
        position_m=(1.0, 2.0, 3.0),
    )

    assert result.object_id
    with closing(sqlite3.connect(database)) as connection, connection:
        objects = connection.execute("SELECT label, world_id, segment_id FROM objects").fetchall()
        observations = connection.execute(
            "SELECT session_id, source_payload_json, position_x_m, position_y_m, position_z_m "
            "FROM observations"
        ).fetchall()
    assert objects == [("ladder", "world-1", "segment-1")]
    assert observations == [("walk-1", '{"image":"frame-10.png","sha256":"abc"}', 1.0, 2.0, 3.0)]


def test_matched_observation_reuses_identity_but_identical_labels_can_be_distinct(database_path):
    store = IdentityStore(database_path)
    first = store.record_observation(
        session_id="walk-1", source_id="cam", observation_id="one",
        source_payload={"box": [1, 2]}, decision="new", label="cone",
        world_id="w", segment_id="s",
    )
    second = store.record_observation(
        session_id="walk-1", source_id="cam", observation_id="two",
        source_payload={"box": [3, 4]}, decision="new", label="cone",
        world_id="w", segment_id="s",
    )
    revisit = store.record_observation(
        session_id="walk-1", source_id="cam", observation_id="three",
        source_payload={"box": [5, 6]}, decision="matched", object_id=first.object_id,
        world_id="w", segment_id="s",
    )
    replay = store.record_observation(
        session_id="walk-1", source_id="cam", observation_id="three",
        source_payload={"box": [5, 6]}, decision="matched", object_id=first.object_id,
        world_id="w", segment_id="s",
    )

    assert second.object_id != first.object_id
    assert revisit.object_id == first.object_id
    assert replay.object_id == first.object_id
    assert store.count_objects(session_id="walk-1", world_id="w", segment_id="s") == 2


def test_unresolved_observation_has_no_identity(database_path):
    store = IdentityStore(database_path)

    result = store.record_observation(
        session_id="walk-1", source_id="cam", observation_id="uncertain",
        source_payload={"box": [0, 0]}, decision="unresolved",
        world_id="w", segment_id="s",
    )

    assert result.object_id is None
    assert store.count_objects(session_id="walk-1", world_id="w", segment_id="s") == 0


def test_match_cannot_cross_session_world_or_segment(database_path):
    store = IdentityStore(database_path)
    created = store.record_observation(
        session_id="walk-1", source_id="cam", observation_id="one",
        source_payload={"box": [1, 2]}, decision="new", label="cone",
        world_id="w", segment_id="s1",
    )

    for session_id, world_id, segment_id in (
        ("walk-2", "w", "s1"),
        ("walk-1", "other", "s1"),
        ("walk-1", "w", "s2"),
    ):
        with pytest.raises(IdentityStoreError):
            store.record_observation(
                session_id=session_id, source_id="cam", observation_id=f"{session_id}-{segment_id}",
                source_payload={"box": [3, 4]}, decision="matched", object_id=created.object_id,
                world_id=world_id, segment_id=segment_id,
            )


def test_exact_replay_returns_same_identity_without_adding_rows(database_path):
    database = database_path
    first_store = IdentityStore(database)
    arguments = dict(
        session_id="walk-1", source_id="cam", observation_id="one",
        source_payload={"box": [1, 2]}, decision="new", label="cone",
        world_id="w", segment_id="s",
    )
    first = first_store.record_observation(**arguments)
    reopened = IdentityStore(database)
    replay = reopened.record_observation(**arguments)

    assert replay.object_id == first.object_id
    assert reopened.count_objects(session_id="walk-1", world_id="w", segment_id="s") == 1
    assert reopened.count_observations(session_id="walk-1") == 1


def test_replay_with_changed_payload_or_decision_fails(database_path):
    store = IdentityStore(database_path)
    arguments = dict(
        session_id="walk-1", source_id="cam", observation_id="one",
        source_payload={"box": [1, 2]}, decision="new", label="cone",
        world_id="w", segment_id="s",
    )
    store.record_observation(**arguments)

    with pytest.raises(IdentityStoreError):
        store.record_observation(**{**arguments, "source_payload": {"box": [9, 9]}})
    with pytest.raises(IdentityStoreError):
        store.record_observation(**{**arguments, "decision": "unresolved", "label": None})


def test_failed_observation_insert_rolls_back_new_object(database_path):
    database = database_path
    store = IdentityStore(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_observation BEFORE INSERT ON observations "
            "BEGIN SELECT RAISE(ABORT, 'forced failure'); END"
        )

    with pytest.raises(sqlite3.IntegrityError, match="forced failure"):
        store.record_observation(
            session_id="walk-1", source_id="cam", observation_id="one",
            source_payload={"box": [1, 2]}, decision="new", label="cone",
            world_id="w", segment_id="s",
        )

    assert store.count_objects(session_id="walk-1", world_id="w", segment_id="s") == 0
    assert store.count_observations(session_id="walk-1") == 0


def test_invalid_position_and_unresolved_identity_are_rejected(database_path):
    store = IdentityStore(database_path)
    with pytest.raises(IdentityStoreError):
        store.record_observation(
            session_id="walk-1", source_id="cam", observation_id="bad-position",
            source_payload={}, decision="new", label="cone", world_id="w", segment_id="s",
            position_m=(1.0, float("nan"), 3.0),
        )
    with pytest.raises(IdentityStoreError, match="sequence of three numbers"):
        store.record_observation(
            session_id="walk-1", source_id="cam", observation_id="text-position",
            source_payload={}, decision="new", label="cone", world_id="w", segment_id="s",
            position_m="123",
        )
    with pytest.raises(IdentityStoreError):
        store.record_observation(
            session_id="walk-1", source_id="cam", observation_id="bad-unresolved",
            source_payload={}, decision="unresolved", object_id="given",
            world_id="w", segment_id="s",
        )


def test_source_descriptor_must_be_an_object(database_path):
    store = IdentityStore(database_path)
    with pytest.raises(IdentityStoreError, match="JSON object"):
        store.record_observation(
            session_id="walk-1", source_id="cam", observation_id="scalar",
            source_payload=["not", "an", "object"], decision="unresolved",
            world_id="w", segment_id="s",
        )


def test_newer_database_schema_is_not_downgraded(database_path):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA user_version = 2")
    with pytest.raises(IdentityStoreError, match="Unsupported identity database version: 2"):
        IdentityStore(database_path)
