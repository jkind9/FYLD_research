"""Pose sidecar records; original matrices and revision parentage remain explicit."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from experiments.shared.contracts import Pose

from .validation import identifier, pairs, sha256_value


@dataclass(frozen=True)
class PoseRevision:
    run_id: str
    frame_id: str
    revision_id: str
    pose: Pose
    source_sha256: str
    parent_revision_id: str | None
    provenance: tuple[tuple[str, str], ...]
    units: str = "metres"
    direction: str = "camera_to_world"

    def __post_init__(self) -> None:
        for name in ("run_id", "frame_id", "revision_id"):
            identifier(getattr(self, name), name)
        if not isinstance(self.pose, Pose):
            raise ValueError("PoseRevision requires a validated Pose")  # noqa: TRY004
        sha256_value(self.source_sha256)
        if self.units != "metres" or self.direction != "camera_to_world":
            raise ValueError("PoseRevision requires metre camera_to_world pose")
        if self.parent_revision_id is not None:
            identifier(self.parent_revision_id, "parent revision")
            if self.parent_revision_id == self.revision_id:
                raise ValueError("Revision cannot parent itself")
        object.__setattr__(self, "provenance", pairs(self.provenance, "provenance"))

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        return (
            self.run_id,
            self.pose.world_id,
            self.pose.segment_id,
            self.frame_id,
            self.revision_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "frame_id": self.frame_id,
            "revision_id": self.revision_id,
            "camera_to_world": self.pose.matrix.tolist(),
            "world_id": self.pose.world_id,
            "segment_id": self.pose.segment_id,
            "pose_source": self.pose.source,
            "source_sha256": self.source_sha256,
            "parent_revision_id": self.parent_revision_id,
            "provenance": dict(self.provenance),
            "units": self.units,
            "direction": self.direction,
        }


def validate_pose_revisions(records: Iterable[PoseRevision]) -> None:
    records = tuple(records)
    by_key = {record.key: record for record in records}
    if len(by_key) != len(records):
        raise ValueError("Duplicate pose revision key")
    groups: dict[tuple[str, ...], list[PoseRevision]] = defaultdict(list)
    for record in records:
        groups[record.key[:-1]].append(record)
        if record.parent_revision_id is not None:
            parent_key = (*record.key[:-1], record.parent_revision_id)
            if parent_key not in by_key:
                raise ValueError(
                    "Missing parent or cross-run/world/segment/frame parent"
                )
    for group in groups.values():
        if sum(record.parent_revision_id is None for record in group) != 1:
            raise ValueError("Every frame origin requires exactly one root revision")
        for record in group:
            visited: set[tuple[str, ...]] = set()
            while record.parent_revision_id is not None:
                if record.key in visited:
                    raise ValueError("Pose revision cycle")
                visited.add(record.key)
                record = by_key[(*record.key[:-1], record.parent_revision_id)]
