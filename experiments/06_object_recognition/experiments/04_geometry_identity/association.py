"""Pure frame-level one-to-one identity decisions with conservative abstention."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import numpy as np

from .locations import Location, add, estimate, summary

MAX_DISTANCE_M = 0.35
APPEARANCE_MIN = 0.80
AMBIGUITY_GAP = 0.05
NUMERIC_TOLERANCE = 1e-12
CONDITIONS = (
    "geometry-last",
    "geometry-viewmedian",
    "appearance-viewmedian",
    "combined-last",
    "combined-viewmedian",
)


@dataclass(frozen=True)
class Track:
    object_id: str
    category: str
    session_id: str
    world_id: str
    segment_id: str
    location: Location | None
    gallery: tuple[tuple[str, tuple[float, ...]], ...] = ()


def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if (
        a.shape != b.shape
        or a.ndim != 1
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
    ):
        raise ValueError(
            "Appearance vectors must be finite and have matching dimensions"
        )
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator else 0.0


def _iou(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    x1, y1 = max(left[0], right[0]), max(left[1], right[1])
    x2, y2 = min(left[2], right[2]), min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    area_b = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    return (
        intersection / (area_a + area_b - intersection)
        if area_a + area_b > intersection
        else 0.0
    )


def duplicates(rows: list[dict]) -> set[str]:
    suspects: set[str] = set()
    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            if (
                left["category"] != right["category"]
                or left["position_world_m"] is None
                or right["position_world_m"] is None
            ):
                continue
            distance = float(
                np.linalg.norm(
                    np.asarray(left["position_world_m"])
                    - np.asarray(right["position_world_m"])
                )
            )
            if (
                _iou(tuple(left["bbox_xyxy"]), tuple(right["bbox_xyxy"])) >= 0.90
                and distance <= 0.02
            ):
                suspects.update((left["observation_id"], right["observation_id"]))
    return suspects


def _edge(row: dict, track: Track, condition: str) -> dict | None:
    if track.location is None:
        return None
    if (row.get("session_id"), row.get("world_id"), row.get("segment_id")) != (
        track.session_id,
        track.world_id,
        track.segment_id,
    ):
        return None
    appearance_only = condition.startswith("appearance")
    combined = condition.startswith("combined")
    geometry = row.get("position_world_m")
    current = np.asarray(
        estimate(track.location, "last" if condition.endswith("last") else "viewmedian")
    )
    anchor = np.asarray(track.location.anchor_m)
    distance = (
        float(np.linalg.norm(np.asarray(geometry) - current))
        if geometry is not None
        else None
    )
    anchor_distance = (
        float(np.linalg.norm(np.asarray(geometry) - anchor))
        if geometry is not None
        else None
    )
    similarity = None
    representative = None
    vector = row.get("appearance")
    if vector is not None and track.gallery:
        ranked = [
            (cosine(tuple(vector), descriptor), key)
            for key, descriptor in track.gallery
        ]
        similarity, representative = max(ranked, key=lambda item: (item[0], item[1]))
    if not appearance_only and (
        geometry is None
        or distance is None
        or anchor_distance is None
        or distance > MAX_DISTANCE_M
        or anchor_distance > MAX_DISTANCE_M
    ):
        return None
    if (combined or appearance_only) and (
        similarity is None or similarity < APPEARANCE_MIN
    ):
        return None
    if appearance_only:
        assert similarity is not None
        cost = (1.0 - similarity) / 2.0
    elif combined:
        assert distance is not None and similarity is not None
        cost = 0.5 * (distance / MAX_DISTANCE_M) + 0.5 * ((1.0 - similarity) / 2.0)
    else:
        assert distance is not None
        cost = distance / MAX_DISTANCE_M
    return {
        "object_id": track.object_id,
        "cost": float(cost),
        "distance_m": distance,
        "anchor_distance_m": anchor_distance,
        "cosine": similarity,
        "winning_gallery_observation": representative,
    }


def _rejection(row: dict, track: Track, condition: str) -> dict:
    if row.get("session_id") != track.session_id:
        return {"object_id": track.object_id, "reason": "session mismatch"}
    if (row.get("world_id"), row.get("segment_id")) != (
        track.world_id,
        track.segment_id,
    ):
        return {"object_id": track.object_id, "reason": "origin mismatch"}
    geometry = row.get("position_world_m")
    current = (
        np.asarray(
            estimate(
                track.location, "last" if condition.endswith("last") else "viewmedian"
            )
        )
        if track.location
        else None
    )
    distance = (
        float(np.linalg.norm(np.asarray(geometry) - current))
        if geometry is not None and current is not None
        else None
    )
    anchor_distance = (
        float(
            np.linalg.norm(np.asarray(geometry) - np.asarray(track.location.anchor_m))
        )
        if geometry is not None and track.location
        else None
    )
    similarity = None
    if row.get("appearance") is not None and track.gallery:
        similarity = max(
            cosine(tuple(row["appearance"]), descriptor)
            for _, descriptor in track.gallery
        )
    if condition.startswith("combined") and similarity is None:
        reason = "missing appearance evidence"
    elif (
        condition.startswith("combined")
        and similarity is not None
        and similarity < APPEARANCE_MIN
    ):
        reason = "appearance gate failed"
    elif not condition.startswith("appearance") and geometry is None:
        reason = "missing metric position"
    elif (
        not condition.startswith("appearance")
        and geometry is not None
        and (
            distance is not None
            and distance > MAX_DISTANCE_M
            or anchor_distance is not None
            and anchor_distance > MAX_DISTANCE_M
        )
    ):
        reason = "fixed anchor/current position gate failed"
    elif condition.startswith("appearance") and similarity is None:
        reason = "missing appearance evidence"
    elif (
        condition.startswith("appearance")
        and similarity is not None
        and similarity < APPEARANCE_MIN
    ):
        reason = "appearance gate failed"
    else:
        reason = "no compatible edge"
    return {
        "object_id": track.object_id,
        "reason": reason,
        "distance_m": distance,
        "anchor_distance_m": anchor_distance,
        "cosine": similarity,
    }


def _solutions(candidates: list[list[dict]]) -> list[tuple[dict[int, dict], float]]:
    results: list[tuple[dict[int, dict], float]] = []

    def visit(
        index: int, used: set[str], selected: dict[int, dict], cost: float
    ) -> None:
        if index == len(candidates):
            results.append((dict(selected), cost))
            return
        visit(index + 1, used, selected, cost)
        for edge in candidates[index]:
            object_id = edge["object_id"]
            if object_id in used:
                continue
            selected[index] = edge
            visit(index + 1, used | {object_id}, selected, cost + edge["cost"])
            del selected[index]

    visit(0, set(), {}, 0.0)
    max_cardinality = max((len(mapping) for mapping, _ in results), default=0)
    return sorted(
        (
            (mapping, cost)
            for mapping, cost in results
            if len(mapping) == max_cardinality
        ),
        key=lambda item: (
            item[1],
            tuple(sorted((i, edge["object_id"]) for i, edge in item[0].items())),
        ),
    )


def _object_id(
    condition: str, session: str, world: str, segment: str, first_key: str
) -> str:
    namespace = uuid.UUID("63bf4f80-112a-4a55-bf51-2537bd5d16e1")
    return uuid.uuid5(
        namespace, f"v1:{condition}:{session}:{world}:{segment}:{first_key}"
    ).hex


def associate_frame(
    rows: list[dict], tracks: tuple[Track, ...], condition: str
) -> tuple[tuple[Track, ...], list[dict], list[dict]]:
    """Decide a whole frame against frozen pre-frame tracks; then update locations."""
    if condition not in CONDITIONS:
        raise ValueError("Unknown association condition")
    ordered = sorted(rows, key=lambda row: row["observation_id"])
    prior = {track.object_id: track for track in tracks}
    suspects = duplicates(ordered)
    decisions: dict[str, dict] = {}
    for key in suspects:
        decisions[key] = {
            "decision": "unresolved",
            "reason": "same-class overlapping duplicate suspect",
            "object_id": None,
            "candidates": [],
        }
    by_category: dict[str, list[int]] = {}
    for index, row in enumerate(ordered):
        by_category.setdefault(row["category"], []).append(index)
    chosen: dict[int, dict] = {}
    unresolved_ambiguity: set[int] = set()
    ambiguity_info: dict[int, dict] = {}
    all_candidates: dict[int, list[dict]] = {}
    rejected_candidates: dict[int, list[dict]] = {}
    for category, indices in by_category.items():
        eligible = [i for i in indices if ordered[i]["observation_id"] not in suspects]
        category_tracks = sorted(
            (track for track in tracks if track.category == category),
            key=lambda track: track.object_id,
        )
        for index in eligible:
            row = ordered[index]
            if row.get("world_id") is None or row.get("segment_id") is None:
                decisions[row["observation_id"]] = {
                    "decision": "unresolved",
                    "reason": "unknown metric origin",
                    "object_id": None,
                    "candidates": [],
                }
                all_candidates[index] = []
                continue
            edges = []
            rejected = []
            for track in category_tracks:
                edge = _edge(row, track, condition)
                if edge is None:
                    rejected.append(_rejection(row, track, condition))
                else:
                    edges.append(edge)
            all_candidates[index] = edges
            rejected_candidates[index] = rejected
        if not category_tracks:
            for index in eligible:
                row = ordered[index]
                if (
                    row["observation_id"] in decisions
                    or row.get("position_world_m") is None
                    or row.get("world_id") is None
                ):
                    continue
                decisions[row["observation_id"]] = {
                    "decision": "new",
                    "reason": "first usable same-class frame",
                    "object_id": _object_id(
                        condition,
                        row["session_id"],
                        row["world_id"],
                        row["segment_id"],
                        row["observation_id"],
                    ),
                    "candidates": [],
                }
            continue
        valid_indices = [
            i for i in eligible if ordered[i]["observation_id"] not in decisions
        ]
        candidates = [all_candidates.get(i, []) for i in valid_indices]
        solutions = _solutions(candidates)
        best, best_cost = solutions[0] if solutions else ({}, 0.0)
        best_count = len(best)
        for local_index, edge in best.items():
            alternatives = []
            for mapping, cost in solutions[1:]:
                if (
                    len(mapping) == best_count
                    and mapping.get(local_index, {}).get("object_id")
                    != edge["object_id"]
                ):
                    gap = max(0.0, (cost - best_cost) / max(1, best_count))
                    if gap <= AMBIGUITY_GAP + NUMERIC_TOLERANCE:
                        alternatives.append((mapping, gap))
            if alternatives:
                unresolved_ambiguity.add(valid_indices[local_index])
                for mapping, gap in alternatives:
                    changed = [
                        row_index
                        for row_index in set(mapping) | set(best)
                        if mapping.get(row_index, {}).get("object_id")
                        != best.get(row_index, {}).get("object_id")
                    ]
                    for row_index in changed:
                        global_index = valid_indices[row_index]
                        unresolved_ambiguity.add(global_index)
                        current = ambiguity_info.setdefault(
                            global_index,
                            {"alternate_cost_gap": gap, "alternative_object_ids": []},
                        )
                        current["alternate_cost_gap"] = min(
                            current["alternate_cost_gap"], gap
                        )
                        alternative_id = mapping.get(row_index, {}).get("object_id")
                        if (
                            alternative_id is not None
                            and alternative_id not in current["alternative_object_ids"]
                        ):
                            current["alternative_object_ids"].append(alternative_id)
            else:
                chosen[valid_indices[local_index]] = edge
        for index in valid_indices:
            row = ordered[index]
            if index in unresolved_ambiguity:
                decisions[row["observation_id"]] = {
                    "decision": "unresolved",
                    "reason": "near-equal full-cardinality assignment",
                    "object_id": None,
                    "candidates": all_candidates.get(index, []),
                    "rejected_candidates": rejected_candidates.get(index, []),
                    **ambiguity_info.get(
                        index,
                        {"alternate_cost_gap": None, "alternative_object_ids": []},
                    ),
                }
            elif index in chosen:
                edge = chosen[index]
                decisions[row["observation_id"]] = {
                    "decision": "matched",
                    "reason": "one-to-one identity assignment",
                    "alternate_cost_gap": None,
                    "rejected_candidates": rejected_candidates.get(index, []),
                    **edge,
                    "candidates": all_candidates[index],
                }
            else:
                matched_ids = {edge["object_id"] for edge in chosen.values()}
                decisions[row["observation_id"]] = {
                    "decision": "unresolved",
                    "reason": "unmatched same-class birth/moved candidate",
                    "object_id": None,
                    "candidates": all_candidates.get(index, []),
                    "rejected_candidates": rejected_candidates.get(index, []),
                    "alternate_cost_gap": None,
                    "pending_location_candidate_ids": [
                        track.object_id
                        for track in category_tracks
                        if track.object_id not in matched_ids
                        and row.get("appearance") is not None
                        and any(
                            cosine(tuple(row["appearance"]), descriptor)
                            >= APPEARANCE_MIN
                            for _, descriptor in track.gallery
                        )
                    ],
                }
    updated = dict(prior)
    for index, row in enumerate(ordered):
        record = decisions.get(
            row["observation_id"],
            {
                "decision": "unresolved",
                "reason": "no safe assignment",
                "object_id": None,
                "candidates": [],
            },
        )
        object_id = record.get("object_id")
        if not object_id:
            continue
        selected_track = updated.get(object_id)
        if record["decision"] == "new":
            if selected_track is not None:
                raise ValueError(
                    "Deterministic birth ID collides with an existing track"
                )
            selected_track = Track(
                object_id,
                row["category"],
                row["session_id"],
                row["world_id"],
                row["segment_id"],
                None,
            )
        if selected_track is None:
            raise ValueError("A matched identity is absent from the frozen track state")
        if row.get("position_world_m") is None:
            if record["decision"] == "new":
                raise ValueError("Metric identity birth requires geometry")
            continue
        before = (
            estimate(
                selected_track.location,
                "last" if condition.endswith("last") else "viewmedian",
            )
            if selected_track.location
            else None
        )
        new_location, vote = add(selected_track.location, row)
        gallery = selected_track.gallery
        if vote["representative"] and row.get("appearance") is not None:
            gallery = (*gallery, (row["observation_id"], tuple(row["appearance"])))
        updated[object_id] = Track(
            selected_track.object_id,
            selected_track.category,
            selected_track.session_id,
            selected_track.world_id,
            selected_track.segment_id,
            new_location,
            gallery,
        )
        record["location_vote"] = vote
        record["location"] = summary(
            new_location, "last" if condition.endswith("last") else "viewmedian", before
        )
    decision_rows = [
        {
            "observation_id": row["observation_id"],
            "frame_id": row["frame_id"],
            "timestamp_s": row["timestamp_s"],
            "category": row["category"],
            "bbox_xyxy": row["bbox_xyxy"],
            "position_camera_m": row.get("position_camera_m"),
            "position_world_m": row.get("position_world_m"),
            "world_id": row.get("world_id"),
            "segment_id": row.get("segment_id"),
            "pose_revision_id": row.get("pose_revision_id"),
            **decisions.get(
                row["observation_id"],
                {
                    "decision": "unresolved",
                    "reason": "no safe assignment",
                    "object_id": None,
                    "candidates": [],
                },
            ),
        }
        for row in ordered
    ]
    return (
        tuple(sorted(updated.values(), key=lambda track: track.object_id)),
        decision_rows,
        [
            {
                "object_id": track.object_id,
                "category": track.category,
                "session_id": track.session_id,
                "world_id": track.world_id,
                "segment_id": track.segment_id,
                "location": summary(
                    track.location,
                    "last" if condition.endswith("last") else "viewmedian",
                    None,
                ),
                "gallery_observations": [key for key, _ in track.gallery],
            }
            for track in sorted(updated.values(), key=lambda track: track.object_id)
            if track.location is not None
        ],
    )
