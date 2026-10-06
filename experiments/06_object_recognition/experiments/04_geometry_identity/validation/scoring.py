"""Identity error analysis; independent references enter only this scorer."""

import itertools
from collections import defaultdict

import numpy as np


def score_identity(
    decisions: list[dict], truth: list[dict], observations: list[dict]
) -> dict:
    labels = {row["observation_id"]: row["instance_id"] for row in truth}
    observation_by_key = {row["observation_id"]: row for row in observations}
    assigned = [
        (row["object_id"], labels[row["observation_id"]])
        for row in decisions
        if row.get("object_id") is not None
    ]
    mapping: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    for object_id, instance_id in assigned:
        mapping[object_id].add(instance_id)
        reverse[instance_id].add(object_id)
    by_reference: dict[str, list[dict]] = defaultdict(list)
    assignment = {row["observation_id"]: row.get("object_id") for row in decisions}
    for key, identity in labels.items():
        row = observation_by_key[key]
        if row.get("position_world_m") is not None:
            by_reference[identity].append(row)
    coordinate_comparisons = []
    for identity, rows in sorted(by_reference.items()):
        ordered = sorted(
            rows, key=lambda row: (row["timestamp_s"], row["observation_id"])
        )
        for left, right in itertools.pairwise(ordered):
            delta = [
                float(b - a)
                for a, b in zip(left["position_world_m"], right["position_world_m"])
            ]
            coordinate_comparisons.append(
                {
                    "reference_identity_scorer_only": identity,
                    "from_observation": left["observation_id"],
                    "to_observation": right["observation_id"],
                    "elapsed_s": float(right["timestamp_s"] - left["timestamp_s"]),
                    "world_surface_delta_m": delta,
                    "world_surface_delta_norm_m": float(np.linalg.norm(delta)),
                    "same_assigned_object_id": assignment[left["observation_id"]]
                    is not None
                    and assignment[left["observation_id"]]
                    == assignment[right["observation_id"]],
                    "interpretation": "Difference between observed surface medians across views; not localization error.",
                }
            )
    return {
        "scorer_only": True,
        "matched": len(assigned),
        "unresolved": sum(row["decision"] == "unresolved" for row in decisions),
        "wrong_merge_object_ids": sorted(
            key for key, values in mapping.items() if len(values) > 1
        ),
        "wrong_split_reference_ids": sorted(
            key for key, values in reverse.items() if len(values) > 1
        ),
        "correctly_associated_observations": sum(
            object_id is not None
            and len(mapping[object_id]) == 1
            and next(iter(mapping[object_id])) == instance_id
            for object_id, instance_id in assigned
        ),
        "coordinate_comparisons_scorer_only": coordinate_comparisons,
    }
