"""Rebuild derived surface positions under one complete pose revision."""

from __future__ import annotations

import hashlib
import importlib
from collections import defaultdict
from typing import Any

import numpy as np

from experiments.shared.contracts import Pose
from experiments.shared.geometry import transform_points

pose_revisions = importlib.import_module(
    "experiments.06_object_recognition.shared.pose_revisions"
)
PoseRevision = pose_revisions.PoseRevision
validate_pose_revisions = pose_revisions.validate_pose_revisions

from .locations import Location, add, summary


def recompute_generation(
    observations: list[dict],
    decisions: list[dict],
    poses: dict[str, dict],
    revision_id: str,
) -> dict:
    """Apply a complete per-frame pose map without rerunning identity decisions."""
    if not revision_id or revision_id == "supplied-base-v1":
        raise ValueError("A new non-base pose revision is required")
    accepted = {
        row["observation_id"]: row
        for row in decisions
        if row.get("object_id") is not None
    }
    if any(
        row["frame_id"] not in poses
        for row in observations
        if row.get("pose_camera_to_world") is not None
    ):
        raise ValueError(
            "Revision must cover every observed pose frame; mixed generations are rejected"
        )
    revised: list[dict] = []
    groups: dict[str, list[dict]] = defaultdict(list)
    frame_observations: dict[str, dict] = {}
    for source in observations:
        frame_observations.setdefault(source["frame_id"], source)
    revisions: list[Any] = []
    for frame_id, pose_row in poses.items():
        original = frame_observations.get(frame_id)
        if original is None or original.get("pose_camera_to_world") is None:
            raise ValueError("Revision names a frame without an original supplied pose")
        original_pose = Pose(
            np.asarray(original["pose_camera_to_world"]),
            original["world_id"],
            original["segment_id"],
            "supplied",
        )
        new_pose = Pose(
            np.asarray(pose_row["camera_to_world"], dtype=float),
            pose_row["world_id"],
            pose_row["segment_id"],
            "supplied",
        )
        base_digest = hashlib.sha256(
            repr(original_pose.matrix.tolist()).encode()
        ).hexdigest()
        revision_digest = pose_row.get("source_sha256")
        if not revision_digest:
            raise ValueError("Pose revision source hash is required")
        revisions.extend(
            (
                PoseRevision(
                    "revision-fixture",
                    frame_id,
                    "supplied-base-v1",
                    original_pose,
                    base_digest,
                    None,
                    (("source", "original supplied pose"),),
                ),
                PoseRevision(
                    "revision-fixture",
                    frame_id,
                    revision_id,
                    new_pose,
                    revision_digest,
                    "supplied-base-v1",
                    (("source", "explicit revised supplied pose"),),
                ),
            )
        )
    validate_pose_revisions(revisions)
    for source in observations:
        row = dict(source)
        if row["frame_id"] in poses and row.get("position_camera_m") is not None:
            pose_row = poses[row["frame_id"]]
            pose = Pose(
                np.asarray(pose_row["camera_to_world"], dtype=float),
                pose_row["world_id"],
                pose_row["segment_id"],
                "supplied",
            )
            point = transform_points(
                np.asarray(row["position_camera_m"], dtype=float)[None, :], pose.matrix
            )[0]
            row["position_world_m"] = [float(value) for value in point]
            row["world_id"] = pose.world_id
            row["segment_id"] = pose.segment_id
            row["pose_camera_to_world"] = pose.matrix.tolist()
            row["pose_revision_id"] = revision_id
        elif row["observation_id"] in accepted:
            raise ValueError("Accepted original camera coordinate is missing")
        revised.append(row)
        if (
            row["observation_id"] in accepted
            and row.get("position_world_m") is not None
        ):
            groups[accepted[row["observation_id"]]["object_id"]].append(row)
    positions = {}
    for object_id, rows in groups.items():
        location: Location | None = None
        for row in sorted(
            rows, key=lambda value: (value["timestamp_s"], value["observation_id"])
        ):
            location, _ = add(location, row)
        if location is None:
            continue
        positions[object_id] = {
            "revision_id": revision_id,
            "position_world_m": summary(location, "viewmedian", None)["estimate_m"],
            "location": summary(location, "viewmedian", None),
            "observation_ids": [row["observation_id"] for row in rows],
        }
    return {
        "revision_id": revision_id,
        "observations": revised,
        "decisions": decisions,
        "positions": positions,
        "source_sha256": hashlib.sha256(
            repr(sorted(poses.items())).encode()
        ).hexdigest(),
        "claim": "Synthetic complete pose revision; stable identity decisions retained, all derived groups rebuilt from original camera coordinates.",
    }


def start_explicit_location_generation(
    object_id: str,
    category: str,
    world_id: str,
    segment_id: str,
    first_observation: dict,
    previous_history: list[dict],
) -> dict:
    """Represent an externally confirmed relocation without averaging old history."""
    if not all((object_id, category, world_id, segment_id)):
        raise ValueError(
            "Explicit relocation needs stable identity and explicit origin"
        )
    location, _ = add(None, first_observation)
    return {
        "object_id": object_id,
        "category": category,
        "world_id": world_id,
        "segment_id": segment_id,
        "generation_index": len(previous_history) + 1,
        "location": summary(location, "viewmedian", None),
        "previous_generations": previous_history,
        "decision_source": "explicit external relocation decision; not autonomous trial success",
    }
