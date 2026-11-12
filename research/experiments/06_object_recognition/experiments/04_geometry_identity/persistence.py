"""Private per-condition databases and a hash-checked generation reader."""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import verify_run, write_json

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
IdentityStore = importlib.import_module("identity_store").IdentityStore


def digest_json(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def write_condition(
    run_path: Path,
    condition: str,
    observations: list[dict],
    decisions: list[dict],
    tracks: list[dict],
    *,
    settings: dict,
    revision_id: str = "supplied-base-v1",
) -> dict:
    """Persist a complete immutable decision set in one private DB."""
    target = run_path / "output/conditions" / condition
    target.mkdir(parents=True, exist_ok=False)
    database = target / "identity.sqlite3"
    store = IdentityStore(database)
    by_key = {row["observation_id"]: row for row in observations}
    ledger_rows = []
    for decision in decisions:
        row = by_key[decision["observation_id"]]
        origin_known = bool(row.get("world_id") and row.get("segment_id"))
        persist = origin_known
        store_decision = decision["decision"] if persist else None
        object_id = decision.get("object_id") if persist else None
        if persist:
            payload = {
                "schema_version": 1,
                "condition": condition,
                "settings": settings,
                "observation": row,
                "decision": decision["decision"],
                "reason": decision["reason"],
                "candidates": decision.get("candidates", []),
                "pose_revision_id": revision_id,
            }
            label = row["category"] if store_decision == "new" else None
            store.record_observation(
                session_id=row["session_id"],
                source_id=row["frame_id"],
                observation_id=row["observation_id"],
                source_payload=payload,
                decision=store_decision,
                world_id=row["world_id"],
                segment_id=row["segment_id"],
                label=label,
                object_id=object_id,
                pose_revision_id=revision_id,
                position_m=row.get("position_world_m"),
            )
        ledger_rows.append(
            {
                **decision,
                "origin_known": origin_known,
                "persisted": persist,
                "store_decision": store_decision,
                "store_object_id": object_id,
                "coordinate_evidence": row.get("geometry"),
                "pose_revision_id": revision_id,
            }
        )
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        connection.execute("PRAGMA journal_mode=DELETE")
        database_counts = connection.execute(
            "SELECT COUNT(*) FROM observations"
        ).fetchone()[0]
        object_count = connection.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
        db_rows = connection.execute(
            "SELECT observation_id, decision, object_id FROM observations ORDER BY observation_id"
        ).fetchall()
    finally:
        connection.close()
    if list(db_rows) != sorted(
        [
            (row["observation_id"], row["store_decision"], row["store_object_id"])
            for row in ledger_rows
            if row["persisted"]
        ],
        key=lambda item: item[0],
    ):
        raise ValueError(
            "Private identity database decisions differ from the immutable ledger"
        )
    if database_counts != sum(row["persisted"] for row in ledger_rows):
        raise ValueError("Private identity database membership differs from the ledger")
    ledger_path = target / "decisions.json"
    location_path = target / "locations.json"
    write_json(
        ledger_path,
        {
            "schema_version": 1,
            "condition": condition,
            "observations": ledger_rows,
            "tracks": tracks,
        },
    )
    write_json(
        location_path, {"schema_version": 1, "condition": condition, "tracks": tracks}
    )
    generation = {
        "schema_version": 1,
        "condition": condition,
        "revision_id": revision_id,
        "database": database.name,
        "database_sha256": sha256(database),
        "ledger": ledger_path.name,
        "ledger_sha256": sha256(ledger_path),
        "locations": location_path.name,
        "locations_sha256": sha256(location_path),
        "configuration_sha256": digest_json(settings),
        "origin": "tum_freiburg1_desk_mocap/continuous_capture",
        "observation_count": len(ledger_rows),
        "persisted_observation_count": int(database_counts),
        "unpersisted_unknown_origin_count": len(ledger_rows) - int(database_counts),
        "object_count": int(object_count),
    }
    write_json(target / "generation-v1.json", generation)
    return generation


def read_generation(run_path: Path, condition: str) -> dict:
    """Read one completed generation only after verifying Run and linked hashes."""
    verify_run(run_path)
    folder = run_path / "output/conditions" / condition
    generation = json.loads((folder / "generation-v1.json").read_text(encoding="utf-8"))
    if (
        generation.get("schema_version") != 1
        or generation.get("condition") != condition
    ):
        raise ValueError("Generation schema or condition differs")
    for field in ("database", "ledger", "locations"):
        value = generation[field]
        if Path(value).name != value:
            raise ValueError("Generation artifact path must be a basename")
        if sha256(folder / value) != generation[f"{field}_sha256"]:
            raise ValueError(f"Generation {field} hash differs")
    ledger = json.loads((folder / generation["ledger"]).read_text(encoding="utf-8"))
    with sqlite3.connect(
        f"file:{folder / generation['database']}?mode=ro", uri=True
    ) as connection:
        rows = connection.execute(
            "SELECT observation_id, decision, object_id FROM observations ORDER BY observation_id"
        ).fetchall()
    expected = sorted(
        [
            (row["observation_id"], row["store_decision"], row["store_object_id"])
            for row in ledger["observations"]
            if row["persisted"]
        ],
        key=lambda item: item[0],
    )
    if (
        rows != expected
        or len(ledger["observations"]) != generation["observation_count"]
    ):
        raise ValueError("Generation ledger/database membership differs")
    return {"generation": generation, "ledger": ledger, "tracks": ledger["tracks"]}


def copy_for_resume(source: Path, condition: str, destination: Path) -> dict:
    """Copy a verified closed generation into private staging; source stays untouched."""
    checked = read_generation(source, condition)
    destination.mkdir(parents=True, exist_ok=False)
    source_folder = source / "output/conditions" / condition
    for name in (
        "identity.sqlite3",
        "decisions.json",
        "locations.json",
        "generation-v1.json",
    ):
        shutil.copyfile(source_folder / name, destination / name)
        if sha256(source_folder / name) != sha256(destination / name):
            raise ValueError("Resume copy changed a completed source artifact")
    return checked
