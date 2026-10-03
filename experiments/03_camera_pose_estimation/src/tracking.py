"""Bounded pair state with explicit failures and independent segment origins."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

import numpy as np

from experiments.shared.contracts import Pose
from experiments.shared.geometry import validate_transform

from .backend import PairResult
from .dataset import RGBDFrame


class Backend(Protocol):
    def estimate(self, source: RGBDFrame, target: RGBDFrame) -> PairResult: ...


@dataclass(frozen=True)
class Record:
    frame_id: str
    timestamp_s: float
    status: str
    pose: Pose | None
    reason: str

    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp_s": self.timestamp_s,
            "status": self.status,
            "pose": None if self.pose is None else self.pose.to_dict(),
            "reason": self.reason,
        }


def track(
    frames: Iterable[RGBDFrame],
    backend: Backend,
    run=None,
    origin_namespace: str | None = None,
) -> list[Record]:
    namespace = uuid4().hex if origin_namespace is None else origin_namespace
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("Origin namespace must be nonblank")
    previous, pose, segment, records = None, None, -1, []
    last_timestamp = None
    ids = set()
    for current in frames:
        if current.frame_id in ids or (
            last_timestamp is not None and current.timestamp_s <= last_timestamp
        ):
            raise ValueError("Tracking frames require unique IDs and increasing times")
        ids.add(current.frame_id)
        last_timestamp = current.timestamp_s
        if not current.valid.any():
            records.append(
                Record(
                    current.frame_id,
                    current.timestamp_s,
                    "failed",
                    None,
                    "no valid depth",
                )
            )
            previous, pose = None, None
            continue
        if previous is None or current.timestamp_s - previous.timestamp_s > 0.1:
            segment += 1
            pose = Pose(
                np.eye(4),
                f"tracking-world-{namespace}-{segment}",
                str(segment),
                "estimated",
            )
            status = "initialized" if not records else "reset"
            records.append(
                Record(
                    current.frame_id, current.timestamp_s, status, pose, "new origin"
                )
            )
            previous = current
            continue
        if run is None:
            result = backend.estimate(previous, current)
        else:
            with run.measure("odometry_pairs", frames=1):
                result = backend.estimate(previous, current)
        valid = result.success and result.transform is not None
        if valid:
            assert result.transform is not None
            try:
                validate_transform(result.transform)
            except ValueError:
                valid = False
        if valid:
            assert pose is not None
            assert result.transform is not None
            pose = Pose(
                pose.matrix @ np.linalg.inv(result.transform),
                pose.world_id,
                pose.segment_id,
                "estimated",
            )
            records.append(
                Record(
                    current.frame_id,
                    current.timestamp_s,
                    "tracked",
                    pose,
                    result.reason,
                )
            )
            previous = current
        else:
            records.append(
                Record(
                    current.frame_id, current.timestamp_s, "failed", None, result.reason
                )
            )
            previous, pose = None, None
    return records
