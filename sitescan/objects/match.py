"""One-to-one matching of placed detections to counted objects of the same class."""

import numpy as np
from scipy.optimize import linear_sum_assignment

MAX_DISTANCE_M = 0.35
AMBIGUITY_MARGIN_M = 0.05


def placed(row: dict) -> bool:
    """Whether a detection has a finite 3D position."""
    position = row.get("world_position_m")
    if position is None:
        return False
    point = np.asarray(position, dtype=float)
    return point.shape == (3,) and bool(np.isfinite(point).all())


def candidates(position, class_id: int, tracks: dict[str, dict], max_distance_m: float) -> list[tuple[float, str]]:
    """(distance, object id) for same-class objects within reach, nearest first."""
    point = np.asarray(position, dtype=float)
    near = []
    for object_id, track in tracks.items():
        if track["class_id"] == class_id:
            distance = float(np.linalg.norm(point - np.asarray(track["last_position_m"], dtype=float)))
            if distance <= max_distance_m:
                near.append((distance, object_id))
    return sorted(near)


def assign(
    rows: list[list[tuple[float, str]]], track_ids: list[str], max_distance_m: float, ambiguity_margin_m: float
) -> dict[int, str | None]:
    """Shortest one-to-one assignment of rows to objects within reach.

    Each matched row maps to its object id, or to None when forbidding that pair still leaves an
    assignment of the same size whose total distance is within the margin.
    """
    unmatched = max_distance_m * (min(len(rows), len(track_ids)) + 1) + 1
    forbidden = unmatched * (len(rows) + len(track_ids) + 1)
    # One extra "unmatched" column per row lets a row stay unassigned.
    costs = np.full((len(rows), len(track_ids) + len(rows)), unmatched)
    costs[:, : len(track_ids)] = forbidden
    column = {object_id: index for index, object_id in enumerate(track_ids)}
    for row, near in enumerate(rows):
        for distance, object_id in near:
            costs[row, column[object_id]] = distance

    def solve(matrix: np.ndarray) -> tuple[dict[int, int], float]:
        chosen = {
            int(row): int(col)
            for row, col in zip(*linear_sum_assignment(matrix), strict=True)
            if col < len(track_ids) and matrix[row, col] < unmatched
        }
        return chosen, sum(float(matrix[row, col]) for row, col in chosen.items())

    best, best_total = solve(costs)
    result = {}
    for row, col in best.items():
        without = costs.copy()
        without[row, col] = forbidden
        other, other_total = solve(without)
        close = len(other) == len(best) and other_total - best_total < ambiguity_margin_m
        result[row] = None if close else track_ids[col]
    return result


def associate_frame(
    detections: list[dict],
    tracks: dict[str, dict],
    next_number: int,
    max_distance_m: float = MAX_DISTANCE_M,
    ambiguity_margin_m: float = AMBIGUITY_MARGIN_M,
) -> tuple[list[dict], dict[str, dict], int]:
    """Match one frame's detections to counted objects; returns rows, updated objects and the next number.

    Each row is its detection plus an outcome: matched, new, unresolved_no_position,
    unresolved_ambiguous or unresolved_track_already_assigned. Only matched and new rows get an object id.
    """
    tracks = {object_id: {**track, "last_position_m": list(track["last_position_m"])} for object_id, track in tracks.items()}
    rows = [dict(detection) for detection in detections]
    near = {
        index: candidates(row["world_position_m"], row["class_id"], tracks, max_distance_m)
        for index, row in enumerate(rows)
        if placed(row)
    }
    unresolved = {index: "unresolved_no_position" for index in range(len(rows)) if index not in near}
    matched: dict[int, str] = {}
    for class_id in {row["class_id"] for row in rows}:
        indexes = [index for index, found in near.items() if found and rows[index]["class_id"] == class_id]
        track_ids = sorted(object_id for object_id, track in tracks.items() if track["class_id"] == class_id)
        if not indexes or not track_ids:
            continue
        assigned = assign([near[index] for index in indexes], track_ids, max_distance_m, ambiguity_margin_m)
        for row, object_id in assigned.items():
            if object_id is None:
                unresolved[indexes[row]] = "unresolved_ambiguous"
            else:
                matched[indexes[row]] = object_id

    for index, row in enumerate(rows):
        frame_index = int(row.get("frame_index", 0))
        row.update(coordinate_delta_m=None, association_distance_m=None, identity_state=None)
        if index in unresolved:
            row.update(association=unresolved[index], object_id=None)
        elif index in matched:
            object_id = matched[index]
            track = tracks[object_id]
            old = track["last_position_m"]
            new = [float(value) for value in row["world_position_m"]]
            row.update(
                association="matched",
                object_id=object_id,
                identity_state=track.get("identity_state", "provisional"),
                association_distance_m={o: d for d, o in near[index]}[object_id],
                coordinate_delta_m=[float(new[axis] - old[axis]) for axis in range(3)],
            )
            tracks[object_id] = {
                **track,
                "last_position_m": new,
                "last_frame_index": frame_index,
                "observation_count": track["observation_count"] + 1,
            }
        elif near.get(index):
            row.update(association="unresolved_track_already_assigned", object_id=None)
        else:
            object_id = f"object-{next_number:04d}"
            next_number += 1
            row.update(association="new", object_id=object_id, identity_state="provisional")
            tracks[object_id] = {
                "object_id": object_id,
                "identity_state": "provisional",
                "class_id": int(row["class_id"]),
                "label": str(row["label"]),
                "last_position_m": [float(value) for value in row["world_position_m"]],
                "last_frame_index": frame_index,
                "observation_count": 1,
            }
    return rows, tracks, next_number
