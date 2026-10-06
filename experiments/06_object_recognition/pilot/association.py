"""Same-class counting method, independent of replay and detector execution."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore[import-untyped]


def associate_frame(
    detections: list[dict],
    tracks: dict[str, dict],
    next_number: int,
    max_distance_m: float,
    ambiguity_margin_m: float,
) -> tuple[list[dict], dict[str, dict], int]:
    """Assign same-class detections one-to-one, preserving ambiguous results."""
    if (
        not np.isfinite([max_distance_m, ambiguity_margin_m]).all()
        or max_distance_m <= 0
        or ambiguity_margin_m < 0
        or isinstance(next_number, bool)
        or not isinstance(next_number, int)
        or next_number < 1
    ):
        raise ValueError("Association settings must be finite and positive")

    updated_tracks = {
        object_id: {
            **track,
            "last_position_m": list(track["last_position_m"]),
        }
        for object_id, track in tracks.items()
    }
    records = [dict(detection) for detection in detections]
    candidates_by_detection: dict[int, list[tuple[float, str]]] = {}
    unresolved: dict[int, str] = {}

    for index, detection in enumerate(records):
        position = detection.get("world_position_m")
        if position is None:
            unresolved[index] = "unresolved_no_position"
            continue
        point = np.asarray(position, dtype=float)
        if point.shape != (3,) or not np.isfinite(point).all():
            unresolved[index] = "unresolved_no_position"
            continue
        candidates = []
        for object_id, track in updated_tracks.items():
            if track["class_id"] != detection["class_id"]:
                continue
            previous = np.asarray(track["last_position_m"], dtype=float)
            distance = float(np.linalg.norm(point - previous))
            if distance <= max_distance_m:
                candidates.append((distance, object_id))
        candidates.sort(key=lambda item: (item[0], item[1]))
        candidates_by_detection[index] = candidates

    matched_detections: dict[int, tuple[str, float]] = {}
    classes = {record["class_id"] for record in records}
    for class_id in classes:
        detection_indexes = [
            index
            for index, candidates in candidates_by_detection.items()
            if index not in unresolved
            and records[index]["class_id"] == class_id
            and candidates
        ]
        track_ids = sorted(
            object_id
            for object_id, track in updated_tracks.items()
            if track["class_id"] == class_id
        )
        if not detection_indexes or not track_ids:
            continue
        dummy_cost = (
            max_distance_m * (min(len(detection_indexes), len(track_ids)) + 1) + 1
        )
        invalid_cost = dummy_cost * (len(detection_indexes) + len(track_ids) + 1)
        costs = np.full(
            (len(detection_indexes), len(track_ids) + len(detection_indexes)),
            dummy_cost,
            dtype=float,
        )
        costs[:, : len(track_ids)] = invalid_cost
        distance_lookup: dict[tuple[int, str], float] = {}
        track_columns = {
            object_id: column for column, object_id in enumerate(track_ids)
        }
        for row, index in enumerate(detection_indexes):
            for distance, object_id in candidates_by_detection[index]:
                costs[row, track_columns[object_id]] = distance
                distance_lookup[(index, object_id)] = distance

        def solve(
            matrix: np.ndarray,
            track_count: int = len(track_ids),
            unmatched_cost: float = dummy_cost,
        ) -> tuple[dict[int, int], float]:
            assignment_rows, assignment_columns = linear_sum_assignment(matrix)
            assignment = {
                int(row): int(column)
                for row, column in zip(assignment_rows, assignment_columns, strict=True)
                if column < track_count and matrix[row, column] < unmatched_cost
            }
            total_distance = sum(
                float(matrix[row, column]) for row, column in assignment.items()
            )
            return assignment, total_distance

        base_assignment, base_distance = solve(costs)
        ambiguous_rows = set()
        for row, column in base_assignment.items():
            alternative_costs = costs.copy()
            alternative_costs[row, column] = invalid_cost
            alternative, alternative_distance = solve(alternative_costs)
            if (
                len(alternative) == len(base_assignment)
                and alternative_distance - base_distance < ambiguity_margin_m
            ):
                ambiguous_rows.add(row)

        for row, column in base_assignment.items():
            index = detection_indexes[row]
            if row in ambiguous_rows:
                unresolved[index] = "unresolved_ambiguous"
                continue
            object_id = track_ids[column]
            matched_detections[index] = (
                object_id,
                distance_lookup[(index, object_id)],
            )

    for index, record in enumerate(records):
        position = record.get("world_position_m")
        frame_index = int(record.get("frame_index", 0))
        record["coordinate_delta_m"] = None
        record["association_distance_m"] = None
        record["identity_state"] = None
        if index in unresolved:
            record["association"] = unresolved[index]
            record["object_id"] = None
            continue
        if index in matched_detections:
            assert position is not None
            object_id, distance = matched_detections[index]
            old_position = updated_tracks[object_id]["last_position_m"]
            new_position = [float(value) for value in position]
            record["association"] = "matched"
            record["object_id"] = object_id
            record["identity_state"] = updated_tracks[object_id].get(
                "identity_state", "provisional"
            )
            record["association_distance_m"] = distance
            record["coordinate_delta_m"] = [
                float(new_position[axis] - old_position[axis]) for axis in range(3)
            ]
            updated_tracks[object_id] = {
                **updated_tracks[object_id],
                "last_position_m": new_position,
                "last_frame_index": frame_index,
                "observation_count": updated_tracks[object_id]["observation_count"] + 1,
            }
            continue

        if candidates_by_detection.get(index):
            record["association"] = "unresolved_track_already_assigned"
            record["object_id"] = None
            continue
        assert position is not None
        object_id = f"object-{next_number:04d}"
        next_number += 1
        record["association"] = "new"
        record["object_id"] = object_id
        record["identity_state"] = "provisional"
        updated_tracks[object_id] = {
            "object_id": object_id,
            "identity_state": "provisional",
            "class_id": int(record["class_id"]),
            "label": str(record["label"]),
            "last_position_m": [float(value) for value in position],
            "last_frame_index": frame_index,
            "observation_count": 1,
        }
    return records, updated_tracks, next_number
