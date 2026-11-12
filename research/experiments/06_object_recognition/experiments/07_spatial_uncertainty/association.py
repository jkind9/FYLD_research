"""Isolated support-aware association for Task32 evaluator handoff."""

from __future__ import annotations

import importlib
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore[import-untyped]
from scipy.spatial import cKDTree

_support = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.spatial_support"
)
SupportSummary = _support.SupportSummary
summarise = _support.summarise

HYPERPARAMETERS = {
    "surface_depth_gap_m": {
        "value": 0.08,
        "source": "confirmed 2026-10-05 Task32 synthetic fixture partition only",
    },
    "support_distance_aggregation": {
        "value": "symmetric median bidirectional nearest-sample distance",
        "source": "confirmed 2026-10-05 Task32 empirical support metric",
    },
    "covariance_regularisation_m2": {
        "value": 1e-6,
        "source": "inherited experiments/06_object_recognition/experiments/04_geometry_identity/spatial_support.py:10",
    },
    "minimum_samples_for_mahalanobis": {
        "value": 4,
        "source": "inherited experiments/06_object_recognition/experiments/04_geometry_identity/spatial_support.py:11",
    },
    "location_uncertainty_calibration": {
        "value": "unavailable",
        "source": "confirmed 2026-10-05 raw support spread is not calibrated probability",
    },
    "nearest_sample_search": {
        "value": "SciPy cKDTree exact nearest neighbour, workers=1",
        "source": "inherited SciPy dependency; confirmed for bounded support matching",
    },
}


@dataclass(frozen=True)
class VisibleExtent:
    """Observed world-space extent, kept separate from location uncertainty."""

    min_m: tuple[float, float, float]
    max_m: tuple[float, float, float]
    span_m: tuple[float, float, float]
    diagonal_m: float


@dataclass(frozen=True)
class BoxObservation:
    """Immutable box support with source and pose lineage."""

    observation_id: str
    class_id: int
    label: str
    bbox_xyxy: tuple[float, float, float, float]
    camera_depth_m: tuple[float, ...]
    pixel_vu: tuple[tuple[int, int], ...]
    world_samples_m: tuple[tuple[float, float, float], ...]
    coordinate_frame: str
    world_id: str
    segment_id: str
    pose_revision_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.observation_id, str) or not self.observation_id.strip():
            raise ValueError("Observation ID must be a non-empty string")
        if (
            not isinstance(self.class_id, int)
            or isinstance(self.class_id, bool)
            or self.class_id < 0
        ):
            raise ValueError("Observation class ID must be a non-negative integer")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("Observation label must be a non-empty string")
        box = np.asarray(self.bbox_xyxy, dtype=float)
        if (
            box.shape != (4,)
            or not np.isfinite(box).all()
            or box[2] <= box[0]
            or box[3] <= box[1]
        ):
            raise ValueError("Observation box must contain finite ordered coordinates")
        depths = np.asarray(self.camera_depth_m, dtype=float)
        pixels_float = np.asarray(self.pixel_vu, dtype=float)
        samples = np.asarray(self.world_samples_m, dtype=float)
        if len(self.world_samples_m) == 0:
            samples = np.empty((0, 3), dtype=float)
        empty_support = (
            len(depths) == 0
            and len(self.pixel_vu) == 0
            and len(self.world_samples_m) == 0
        )
        if not empty_support and (
            depths.ndim != 1
            or pixels_float.shape != (len(depths), 2)
            or not np.isfinite(pixels_float).all()
            or not np.equal(pixels_float, np.floor(pixels_float)).all()
            or samples.shape != (len(depths), 3)
            or not np.isfinite(depths).all()
            or np.any(depths <= 0)
            or not np.isfinite(samples).all()
        ):
            raise ValueError("Observation support arrays must be finite and aligned")
        object.__setattr__(self, "bbox_xyxy", tuple(float(value) for value in box))
        object.__setattr__(
            self, "camera_depth_m", tuple(float(value) for value in depths)
        )
        object.__setattr__(
            self,
            "pixel_vu",
            tuple(tuple(int(value) for value in pixel) for pixel in pixels_float),
        )
        object.__setattr__(
            self,
            "world_samples_m",
            tuple(_tuple3(sample) for sample in samples),
        )
        if self.coordinate_frame != "world":
            raise ValueError("Task32 association requires world-coordinate samples")
        for value in (
            self.coordinate_frame,
            self.world_id,
            self.segment_id,
            self.pose_revision_id,
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Observation lineage fields must be non-empty strings")


@dataclass(frozen=True)
class SurfaceCandidate:
    """One depth-layer hypothesis retained from a detection box."""

    candidate_index: int
    sample_indexes: tuple[int, ...]
    world_samples_m: tuple[tuple[float, float, float], ...]
    depth_range_m: tuple[float, float]
    summary: SupportSummary
    visible_extent: VisibleExtent
    location_uncertainty_status: str = "unavailable_calibrated_model"


@dataclass(frozen=True)
class AssociationResult:
    """JSON-ready decisions, copied tracks and evaluator diagnostics."""

    decisions: tuple[dict[str, Any], ...]
    tracks: dict[str, dict[str, Any]]
    next_number: int
    diagnostics: tuple[dict[str, Any], ...]
    processing_time_ms: float


def _tuple3(values: np.ndarray) -> tuple[float, float, float]:
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def _extent(samples: np.ndarray) -> VisibleExtent:
    minimum, maximum = samples.min(axis=0), samples.max(axis=0)
    span = maximum - minimum
    return VisibleExtent(
        _tuple3(minimum), _tuple3(maximum), _tuple3(span), float(np.linalg.norm(span))
    )


def _validate_gap(depth_gap_m: float) -> float:
    try:
        gap = float(depth_gap_m)
    except (TypeError, ValueError) as error:
        raise ValueError("Depth-layer gap must be positive and finite") from error
    if gap <= 0.0 or not np.isfinite(gap):
        raise ValueError("Depth-layer gap must be positive and finite")
    return gap


def surface_candidates(
    observation: BoxObservation, *, depth_gap_m: float = 0.08
) -> tuple[SurfaceCandidate, ...]:
    """Split valid box samples into deterministic camera-depth surface candidates."""
    gap = _validate_gap(depth_gap_m)
    if not observation.world_samples_m:
        return ()
    depths = np.asarray(observation.camera_depth_m, dtype=float)
    order = np.argsort(depths, kind="stable")
    groups: list[list[int]] = [[int(order[0])]]
    for previous, current in pairwise(order):
        if depths[current] - depths[previous] > gap:
            groups.append([])
        groups[-1].append(int(current))
    candidates = []
    samples = np.asarray(observation.world_samples_m, dtype=float)
    for candidate_index, indexes in enumerate(groups):
        selected = samples[indexes]
        summary = summarise(
            selected,
            coordinate_frame=observation.coordinate_frame,
            world_id=observation.world_id,
            segment_id=observation.segment_id,
            pose_revision_id=observation.pose_revision_id,
        )
        candidates.append(
            SurfaceCandidate(
                candidate_index,
                tuple(indexes),
                tuple(_tuple3(row) for row in selected),
                (float(depths[indexes].min()), float(depths[indexes].max())),
                summary,
                _extent(selected),
            )
        )
    return tuple(candidates)


def _iou(left: Sequence[float], right: Sequence[float]) -> float:
    x1, y1 = max(left[0], right[0]), max(left[1], right[1])
    x2, y2 = min(left[2], right[2]), min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union > 0.0 else 0.0


def _support_distance(
    current: SurfaceCandidate,
    previous_samples: np.ndarray,
    *,
    current_tree: cKDTree | None = None,
    previous_tree: cKDTree | None = None,
) -> float:
    current_samples = np.asarray(current.world_samples_m, dtype=float)
    current_index = current_tree or cKDTree(current_samples)
    previous_index = previous_tree or cKDTree(previous_samples)

    def median_nearest(source: np.ndarray, index: cKDTree) -> float:
        nearest, _ = index.query(source, k=1, workers=1)
        return float(np.median(nearest))

    current_to_previous = median_nearest(current_samples, previous_index)
    previous_to_current = median_nearest(previous_samples, current_index)
    return float(max(current_to_previous, previous_to_current))


class _SupportTreeCache:
    """Reuse exact candidate and track indexes for one association frame."""

    def __init__(self) -> None:
        self._candidate_trees: dict[int, cKDTree] = {}
        self._track_trees: dict[str, cKDTree] = {}

    def candidate_tree(self, candidate: SurfaceCandidate) -> cKDTree:
        key = id(candidate)
        if key not in self._candidate_trees:
            self._candidate_trees[key] = cKDTree(
                np.asarray(candidate.world_samples_m, dtype=float)
            )
        return self._candidate_trees[key]

    def track_tree(self, track_key: str, samples: np.ndarray) -> cKDTree:
        if track_key not in self._track_trees:
            self._track_trees[track_key] = cKDTree(samples)
        return self._track_trees[track_key]


def _track_samples(track: Mapping[str, Any]) -> np.ndarray:
    values = track.get("last_support_samples_m")
    if values is None:
        values = [track.get("last_position_m")]
    samples = np.asarray(values, dtype=float)
    if samples.ndim != 2 or samples.shape[1:] != (3,) or not np.isfinite(samples).all():
        raise ValueError("Track support must contain finite Nx3 samples")
    return samples


def _candidate_edge(
    observation: BoxObservation,
    candidate: SurfaceCandidate,
    track: Mapping[str, Any],
    track_key: str,
    max_distance_m: float,
    support_trees: _SupportTreeCache | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    object_id = track.get("object_id")
    rejected = {"object_id": object_id, "candidate_index": candidate.candidate_index}
    if track.get("class_id") != observation.class_id:
        return None, {**rejected, "reason": "class mismatch"}
    if (
        track.get("world_id"),
        track.get("segment_id"),
        track.get("pose_revision_id"),
    ) != (observation.world_id, observation.segment_id, observation.pose_revision_id):
        return None, {**rejected, "reason": "lineage mismatch"}
    previous_position = np.asarray(track.get("last_position_m"), dtype=float)
    if previous_position.shape != (3,) or not np.isfinite(previous_position).all():
        return None, {**rejected, "reason": "invalid track position"}
    previous_samples = _track_samples(track)
    current_tree = None
    previous_tree = None
    if support_trees is not None:
        current_tree = support_trees.candidate_tree(candidate)
        previous_tree = support_trees.track_tree(track_key, previous_samples)
    support_distance = _support_distance(
        candidate,
        previous_samples,
        current_tree=current_tree,
        previous_tree=previous_tree,
    )
    anchor_distance = float(
        np.linalg.norm(np.asarray(candidate.summary.mean_m) - previous_position)
    )
    mahalanobis = candidate.summary.squared_mahalanobis(previous_position)
    details = {
        **rejected,
        "support_distance_m": support_distance,
        "anchor_distance_m": anchor_distance,
        "squared_mahalanobis_m2": mahalanobis,
        "location_uncertainty_status": candidate.location_uncertainty_status,
    }
    if support_distance > max_distance_m:
        return None, {**details, "reason": "support-distance gate failed"}
    return (
        {
            "object_id": str(object_id),
            "candidate_index": candidate.candidate_index,
            "cost": support_distance,
            **details,
        },
        details,
    )


def _assignment(
    options: list[list[dict[str, Any]]], ambiguity_margin_m: float
) -> tuple[dict[int, dict[str, Any]], set[int]]:
    track_ids = sorted(
        {edge["object_id"] for row_options in options for edge in row_options}
    )
    if not options or not track_ids:
        return {}, set()

    track_columns = {object_id: index for index, object_id in enumerate(track_ids)}
    edge_by_pair: dict[tuple[int, str], dict[str, Any]] = {}
    for row, row_options in enumerate(options):
        for edge in row_options:
            key = (row, edge["object_id"])
            previous = edge_by_pair.get(key)
            if previous is None or (edge["cost"], edge["candidate_index"]) < (
                previous["cost"],
                previous["candidate_index"],
            ):
                edge_by_pair[key] = edge

    row_count, track_count = len(options), len(track_ids)
    maximum_cost = max(edge["cost"] for edge in edge_by_pair.values())
    unmatched_cost = (maximum_cost + 1.0) * (min(row_count, track_count) + 1)
    invalid_cost = unmatched_cost * (row_count + track_count + 1)
    costs = np.full((row_count, track_count + row_count), invalid_cost, dtype=float)
    for row in range(row_count):
        costs[row, track_count + row] = unmatched_cost
    for (row, object_id), edge in edge_by_pair.items():
        costs[row, track_columns[object_id]] = edge["cost"]

    def solve(matrix: np.ndarray) -> tuple[dict[int, dict[str, Any]], float]:
        assigned_rows, assigned_columns = linear_sum_assignment(matrix)
        assignment: dict[int, dict[str, Any]] = {}
        for row, column in zip(assigned_rows, assigned_columns, strict=True):
            if column >= track_count or matrix[row, column] >= unmatched_cost:
                continue
            object_id = track_ids[column]
            assignment[int(row)] = edge_by_pair[(int(row), object_id)]
        total_cost = sum(edge["cost"] for edge in assignment.values())
        return assignment, float(total_cost)

    best, best_cost = solve(costs)
    ambiguous: set[int] = set()
    for row, edge in best.items():
        alternatives = [
            candidate
            for candidate in options[row]
            if candidate["object_id"] == edge["object_id"]
            and candidate["candidate_index"] != edge["candidate_index"]
            and candidate["cost"] - edge["cost"] <= ambiguity_margin_m
        ]
        if alternatives:
            ambiguous.add(row)

        alternative_costs = costs.copy()
        alternative_costs[row, track_columns[edge["object_id"]]] = invalid_cost
        alternate, alternate_cost = solve(alternative_costs)
        if (
            len(alternate) != len(best)
            or alternate_cost - best_cost > ambiguity_margin_m
        ):
            continue
        for changed_row in set(best) | set(alternate):
            current = best.get(changed_row)
            replacement = alternate.get(changed_row)
            if (
                current is None
                or replacement is None
                or (current["object_id"], current["candidate_index"])
                != (replacement["object_id"], replacement["candidate_index"])
            ):
                ambiguous.add(changed_row)
    return best, ambiguous


def _duplicate_groups(
    observations: Sequence[BoxObservation],
    candidates: Sequence[tuple[SurfaceCandidate, ...]],
) -> tuple[tuple[int, ...], ...]:
    adjacency: dict[int, set[int]] = {}
    for left_index, left in enumerate(observations):
        for right_index in range(left_index + 1, len(observations)):
            right = observations[right_index]
            if (
                left.class_id != right.class_id
                or (
                    left.coordinate_frame,
                    left.world_id,
                    left.segment_id,
                    left.pose_revision_id,
                )
                != (
                    right.coordinate_frame,
                    right.world_id,
                    right.segment_id,
                    right.pose_revision_id,
                )
                or _iou(left.bbox_xyxy, right.bbox_xyxy) < 0.90
            ):
                continue
            if not candidates[left_index] or not candidates[right_index]:
                continue
            if (
                min(
                    np.linalg.norm(
                        np.asarray(a.summary.mean_m) - np.asarray(b.summary.mean_m)
                    )
                    for a in candidates[left_index]
                    for b in candidates[right_index]
                )
                <= 0.02
            ):
                adjacency.setdefault(left_index, set()).add(right_index)
                adjacency.setdefault(right_index, set()).add(left_index)
    groups: list[tuple[int, ...]] = []
    remaining = set(adjacency)
    while remaining:
        start = min(remaining)
        group = [start]
        for candidate in sorted(remaining - {start}):
            if all(candidate in adjacency.get(member, set()) for member in group):
                group.append(candidate)
        remaining.difference_update(group)
        if len(group) > 1:
            groups.append(tuple(group))
    return tuple(groups)


def _candidate_record(candidate: SurfaceCandidate) -> dict[str, Any]:
    return {
        "candidate_index": candidate.candidate_index,
        "sample_indexes": list(candidate.sample_indexes),
        "sample_count": candidate.summary.sample_count,
        "rank": candidate.summary.rank,
        "mean_m": list(candidate.summary.mean_m),
        "depth_range_m": list(candidate.depth_range_m),
        "visible_extent": {
            "min_m": list(candidate.visible_extent.min_m),
            "max_m": list(candidate.visible_extent.max_m),
            "span_m": list(candidate.visible_extent.span_m),
            "diagonal_m": candidate.visible_extent.diagonal_m,
        },
        "location_uncertainty_status": candidate.location_uncertainty_status,
    }


def associate_frame(
    observations: Sequence[BoxObservation],
    tracks: Mapping[str, Mapping[str, Any]],
    next_number: int,
    max_distance_m: float,
    ambiguity_margin_m: float,
    *,
    depth_gap_m: float = 0.08,
) -> AssociationResult:
    """Associate immutable box supports while preserving explicit abstentions."""
    started = time.perf_counter()
    settings = np.asarray([max_distance_m, ambiguity_margin_m], dtype=float)
    if not np.isfinite(settings).all() or max_distance_m <= 0 or ambiguity_margin_m < 0:
        raise ValueError("Association settings must be finite and positive")
    if (
        isinstance(next_number, bool)
        or not isinstance(next_number, int)
        or next_number < 1
    ):
        raise ValueError("Next object number must be a positive integer")
    observation_ids = [row.observation_id for row in observations]
    if len(set(observation_ids)) != len(observation_ids):
        raise ValueError("Observation IDs must be unique within a frame")
    candidates = [
        surface_candidates(row, depth_gap_m=depth_gap_m) for row in observations
    ]
    duplicate_groups = _duplicate_groups(observations, candidates)
    duplicate_suppressed = {
        index for group in duplicate_groups for index in group if index != min(group)
    }
    options: list[list[dict[str, Any]]] = []
    rejected: list[list[dict[str, Any]]] = []
    support_trees = _SupportTreeCache()
    for index, row in enumerate(observations):
        row_options: list[dict[str, Any]] = []
        row_rejected: list[dict[str, Any]] = []
        for candidate in candidates[index]:
            for track_key in sorted(tracks):
                edge, rejection = _candidate_edge(
                    row,
                    candidate,
                    tracks[track_key],
                    track_key,
                    float(max_distance_m),
                    support_trees,
                )
                if edge is not None:
                    row_options.append(edge)
                else:
                    row_rejected.append(rejection)
        options.append(
            sorted(
                row_options,
                key=lambda edge: (
                    edge["cost"],
                    edge["object_id"],
                    edge["candidate_index"],
                ),
            )
        )
        rejected.append(row_rejected)

    assignment_options = [
        [] if index in duplicate_suppressed else row_options
        for index, row_options in enumerate(options)
    ]
    best, ambiguous = _assignment(assignment_options, float(ambiguity_margin_m))

    updated_tracks = {object_id: dict(track) for object_id, track in tracks.items()}
    decisions: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for index, row in enumerate(observations):
        decision_started = time.perf_counter()
        candidate_records = [
            _candidate_record(candidate) for candidate in candidates[index]
        ]
        edge = best.get(index)
        if index in duplicate_suppressed:
            decision, reason, object_id = "unresolved", "unresolved_duplicate_box", None
        elif index in ambiguous:
            decision, reason, object_id = "unresolved", "unresolved_ambiguous", None
        elif edge is not None:
            decision, reason, object_id = (
                "matched",
                "support_assignment",
                edge["object_id"],
            )
        elif not candidates[index]:
            decision, reason, object_id = "unresolved", "unresolved_no_support", None
        elif len(candidates[index]) > 1:
            decision, reason, object_id = (
                "unresolved",
                "unresolved_competing_support",
                None,
            )
        elif options[index]:
            decision, reason, object_id = (
                "unresolved",
                "unresolved_track_already_assigned",
                None,
            )
        else:
            decision, reason = "new", "late_or_unmatched_provisional_birth"
            object_id = f"object-{next_number:04d}"
            while object_id in updated_tracks:
                next_number += 1
                object_id = f"object-{next_number:04d}"
            next_number += 1
        if object_id is not None:
            candidate_index = int(edge["candidate_index"]) if edge else 0
            candidate = candidates[index][candidate_index]
            prior_track = dict(updated_tracks.get(object_id, {}))
            updated_tracks[object_id] = {
                **prior_track,
                "object_id": object_id,
                "identity_state": prior_track.get("identity_state", "provisional"),
                "class_id": row.class_id,
                "label": row.label,
                "last_position_m": list(candidate.summary.mean_m),
                "last_support_samples_m": [
                    list(sample) for sample in candidate.world_samples_m
                ],
                "last_observation_id": row.observation_id,
                "world_id": row.world_id,
                "segment_id": row.segment_id,
                "pose_revision_id": row.pose_revision_id,
            }
        elapsed_ms = (time.perf_counter() - decision_started) * 1000.0
        record = {
            "observation_id": row.observation_id,
            "class_id": row.class_id,
            "label": row.label,
            "bbox_xyxy": list(row.bbox_xyxy),
            "decision": decision,
            "reason": reason,
            "object_id": object_id,
            "identity_state": (
                updated_tracks[object_id].get("identity_state")
                if object_id is not None
                else None
            ),
            "candidate_count": len(candidates[index]),
            "candidates": candidate_records,
            "rejected_candidates": rejected[index],
            "support_distance_m": edge.get("support_distance_m") if edge else None,
            "anchor_distance_m": edge.get("anchor_distance_m") if edge else None,
            "squared_mahalanobis_m2": (
                edge.get("squared_mahalanobis_m2") if edge else None
            ),
            "processing_time_ms": elapsed_ms,
            "source_lineage": {
                "coordinate_frame": row.coordinate_frame,
                "world_id": row.world_id,
                "segment_id": row.segment_id,
                "pose_revision_id": row.pose_revision_id,
            },
        }
        decisions.append(record)
        diagnostics.append(
            {
                "observation_id": row.observation_id,
                "decision": decision,
                "reason": reason,
                "candidate_count": len(candidates[index]),
                "processing_time_ms": elapsed_ms,
                "candidate_diagnostics": candidate_records,
            }
        )
    return AssociationResult(
        tuple(decisions),
        updated_tracks,
        next_number,
        tuple(diagnostics),
        (time.perf_counter() - started) * 1000.0,
    )
