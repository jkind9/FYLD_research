"""Persistent records for manually checked object identity decisions."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence


Decision = Literal["new", "matched", "unresolved"]


class IdentityStoreError(ValueError):
    """A checked identity request violates the store's data contract."""


@dataclass(frozen=True)
class ObservationResult:
    """Committed result for one source observation."""

    session_id: str
    source_id: str
    observation_id: str
    decision: Decision
    object_id: str | None


class IdentityStore:
    """Store identity decisions with atomic writes and replay protection."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise IdentityStoreError(f"Unsupported identity database version: {version}")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS objects (
                    object_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    world_id TEXT NOT NULL,
                    segment_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS observations (
                    session_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    observation_id TEXT NOT NULL,
                    source_payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    object_id TEXT REFERENCES objects(object_id) ON DELETE RESTRICT,
                    decision TEXT NOT NULL CHECK (decision IN ('new', 'matched', 'unresolved')),
                    world_id TEXT NOT NULL,
                    segment_id TEXT NOT NULL,
                    pose_revision_id TEXT,
                    position_x_m REAL,
                    position_y_m REAL,
                    position_z_m REAL,
                    PRIMARY KEY (session_id, source_id, observation_id),
                    CHECK (
                        (position_x_m IS NULL AND position_y_m IS NULL AND position_z_m IS NULL)
                        OR
                        (position_x_m IS NOT NULL AND position_y_m IS NOT NULL AND position_z_m IS NOT NULL)
                    ),
                    CHECK ((decision = 'unresolved' AND object_id IS NULL)
                        OR (decision IN ('new', 'matched') AND object_id IS NOT NULL))
                );
                CREATE INDEX IF NOT EXISTS observations_by_object
                    ON observations(object_id);
                PRAGMA user_version = 1;
                """
            )
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != 1:
                raise IdentityStoreError(f"Unsupported identity database version: {version}")

    def record_observation(
        self,
        *,
        session_id: str,
        source_id: str,
        observation_id: str,
        source_payload: Any,
        decision: Decision,
        world_id: str,
        segment_id: str,
        label: str | None = None,
        object_id: str | None = None,
        pose_revision_id: str | None = None,
        position_m: Sequence[float] | None = None,
    ) -> ObservationResult:
        """Record one checked decision, or return its exact prior replay."""
        identifiers = (session_id, source_id, observation_id, world_id, segment_id)
        if any(not isinstance(value, str) or not value.strip() for value in identifiers):
            raise IdentityStoreError("Session, source, observation, world and segment IDs are required")
        if decision not in ("new", "matched", "unresolved"):
            raise IdentityStoreError(f"Unsupported identity decision: {decision!r}")
        if decision == "new" and (not isinstance(label, str) or not label.strip()):
            raise IdentityStoreError("A new identity requires a non-empty checked label")
        if decision == "matched" and (not object_id or label is not None):
            raise IdentityStoreError("A matched observation requires an object ID and no new label")
        if decision == "unresolved" and (object_id is not None or label is not None):
            raise IdentityStoreError("An unresolved observation cannot assign an identity or label")
        if object_id is not None and (not isinstance(object_id, str) or not object_id.strip()):
            raise IdentityStoreError("Object IDs must be non-empty strings")

        coordinates = self._position(position_m)
        if not isinstance(source_payload, Mapping):
            raise IdentityStoreError("Source descriptor must be a JSON object")
        try:
            source_json = json.dumps(
                source_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
            )
        except (TypeError, ValueError) as error:
            raise IdentityStoreError(f"Source descriptor must be finite JSON data: {error}") from error
        payload_hash = hashlib.sha256(source_json.encode("utf-8")).hexdigest()

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """SELECT o.source_payload_json, o.decision, o.object_id, o.world_id,
                          o.segment_id, o.pose_revision_id, o.position_x_m, o.position_y_m,
                          o.position_z_m, ob.label
                   FROM observations o LEFT JOIN objects ob ON ob.object_id = o.object_id
                   WHERE o.session_id = ? AND o.source_id = ? AND o.observation_id = ?""",
                (session_id, source_id, observation_id),
            ).fetchone()
            if existing:
                self._check_replay(
                    existing, source_json, decision, object_id, label, world_id, segment_id,
                    pose_revision_id, coordinates,
                )
                connection.rollback()
                return ObservationResult(session_id, source_id, observation_id, decision, existing[2])

            if decision == "new":
                assigned_id = object_id or uuid.uuid4().hex
                connection.execute(
                    "INSERT INTO objects(object_id, session_id, label, world_id, segment_id) VALUES (?, ?, ?, ?, ?)",
                    (assigned_id, session_id, label, world_id, segment_id),
                )
            elif decision == "matched":
                assigned_id = object_id
                owner = connection.execute(
                    "SELECT session_id, world_id, segment_id FROM objects WHERE object_id = ?",
                    (assigned_id,),
                ).fetchone()
                if owner != (session_id, world_id, segment_id):
                    raise IdentityStoreError("An identity can only be matched within its session, world and segment")
            else:
                assigned_id = None

            connection.execute(
                """INSERT INTO observations(
                       session_id, source_id, observation_id, source_payload_json, payload_sha256,
                       object_id, decision, world_id, segment_id, pose_revision_id,
                       position_x_m, position_y_m, position_z_m
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id, source_id, observation_id, source_json, payload_hash,
                    assigned_id, decision, world_id, segment_id, pose_revision_id,
                    *(coordinates or (None, None, None)),
                ),
            )
            connection.commit()
        return ObservationResult(session_id, source_id, observation_id, decision, assigned_id)

    @staticmethod
    def _position(position_m: Sequence[float] | None) -> tuple[float, float, float] | None:
        if position_m is None:
            return None
        if isinstance(position_m, (str, bytes, bytearray)):
            raise IdentityStoreError("Metric positions must be a sequence of three numbers")
        try:
            coordinate_count = len(position_m)
        except TypeError as error:
            raise IdentityStoreError("Metric positions must contain exactly three coordinates") from error
        if coordinate_count != 3:
            raise IdentityStoreError("Metric positions must contain exactly three coordinates")
        try:
            position = tuple(float(value) for value in position_m)
        except (TypeError, ValueError) as error:
            raise IdentityStoreError("Metric positions must be numeric") from error
        if not all(math.isfinite(value) for value in position):
            raise IdentityStoreError("Metric positions must be finite metres")
        return position  # type: ignore[return-value]

    @staticmethod
    def _check_replay(
        row: tuple[Any, ...], source_json: str, decision: Decision, object_id: str | None,
        label: str | None, world_id: str, segment_id: str, pose_revision_id: str | None,
        coordinates: tuple[float, float, float] | None,
    ) -> None:
        stored_coordinates = row[6:9] if row[6] is not None else None
        requested_label = label if decision == "new" else None
        if (
            row[0] != source_json or row[1] != decision or row[3] != world_id
            or row[4] != segment_id or row[5] != pose_revision_id
            or stored_coordinates != coordinates
            or (decision == "new" and row[9] != requested_label)
            or (object_id is not None and row[2] != object_id)
        ):
            raise IdentityStoreError("The source observation key was replayed with a conflicting payload or decision")

    def count_objects(self, *, session_id: str, world_id: str, segment_id: str) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM objects WHERE session_id = ? AND world_id = ? AND segment_id = ?",
                (session_id, world_id, segment_id),
            ).fetchone()
        return int(row[0])

    def count_observations(self, *, session_id: str) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM observations WHERE session_id = ?", (session_id,)
            ).fetchone()
        return int(row[0])
