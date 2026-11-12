"""Immutable surface-position estimates with a cap on correlated view votes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]


@dataclass(frozen=True)
class View:
    observation_id: str
    frame_id: str
    timestamp_s: float
    position_m: tuple[float, float, float]
    pose: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Location:
    anchor_m: tuple[float, float, float]
    last_m: tuple[float, float, float]
    views: tuple[View, ...] = ()
    accepted: tuple[View, ...] = ()


def _tuple3(values: np.ndarray) -> tuple[float, float, float]:
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def compatible(first: View, second: View) -> bool:
    a, b = np.asarray(first.pose), np.asarray(second.pose)
    translation = float(np.linalg.norm(a[:3, 3] - b[:3, 3]))
    angle = float(Rotation.from_matrix(a[:3, :3].T @ b[:3, :3]).magnitude())
    return translation <= 0.05 and angle <= np.deg2rad(10.0)


def add(location: Location | None, observation: dict) -> tuple[Location, dict]:
    """Add one accepted measurement, retaining each source coordinate unchanged."""
    position = np.asarray(observation["position_world_m"], dtype=float)
    pose = np.asarray(observation["pose_camera_to_world"], dtype=float)
    candidate = View(
        observation_id=observation["observation_id"],
        frame_id=observation["frame_id"],
        timestamp_s=float(observation["timestamp_s"]),
        position_m=_tuple3(position),
        pose=tuple(tuple(float(value) for value in row) for row in pose),
    )
    if location is None:
        result = Location(
            candidate.position_m, candidate.position_m, (candidate,), (candidate,)
        )
        return result, {"representative": True, "reason": "first accepted observation"}
    if any(row.frame_id == candidate.frame_id for row in location.accepted):
        raise ValueError(
            "One source frame may contribute at most one object observation"
        )
    group = next((row for row in location.views if compatible(row, candidate)), None)
    views = (*location.views, candidate) if group is None else location.views
    result = Location(
        location.anchor_m, candidate.position_m, views, (*location.accepted, candidate)
    )
    return result, {
        "representative": group is None,
        "group_representative": group.observation_id if group else None,
        "reason": (
            "new independent view" if group is None else "correlated view; vote capped"
        ),
    }


def estimate(location: Location, policy: str) -> tuple[float, float, float]:
    if policy == "last":
        return location.last_m
    if policy != "viewmedian":
        raise ValueError("Unknown location policy")
    return _tuple3(
        np.median(np.asarray([view.position_m for view in location.views]), axis=0)
    )


def summary(location: Location, policy: str, before: tuple[float, ...] | None) -> dict:
    values = np.asarray([view.position_m for view in location.views], dtype=float)
    selected = np.asarray(estimate(location, policy))
    spread = np.linalg.norm(values - np.asarray(location.anchor_m), axis=1)
    previous = np.asarray(before, dtype=float) if before is not None else None
    return {
        "anchor_m": list(location.anchor_m),
        "estimate_m": selected.tolist(),
        "last_m": list(location.last_m),
        "view_median_m": estimate(location, "viewmedian"),
        "last_minus_viewmedian_m": (
            np.asarray(location.last_m) - np.median(values, axis=0)
        ).tolist(),
        "estimate_shift_m": (
            (selected - previous).tolist() if previous is not None else None
        ),
        "accepted_count": len(location.accepted),
        "representative_count": len(location.views),
        "coordinate_min_m": values.min(axis=0).tolist(),
        "coordinate_max_m": values.max(axis=0).tolist(),
        "coordinate_iqr_m": (
            np.quantile(values, 0.75, axis=0) - np.quantile(values, 0.25, axis=0)
        ).tolist(),
        "anchor_distance_spread_m": {
            "min": float(spread.min()),
            "max": float(spread.max()),
            "median": float(np.median(spread)),
        },
        "claim": "Observed surface coordinates and spread; not object-centre error or calibrated covariance.",
    }
