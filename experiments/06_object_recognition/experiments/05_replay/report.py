"""Write compact numeric receipts for the integrated offline replay."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from experiments.shared.runs import write_json


def write(
    run_path: Path,
    sources: dict,
    automatic: dict,
    proposal_count: int,
    copied: dict,
    feature_source: dict,
) -> None:
    coordinates = {"schema_version": 1, "units": "metres", "conditions": {}}
    summary = {
        "schema_version": 1,
        "baseline_frames": 60,
        "baseline_proposals": proposal_count,
        "automatic_frames": 6,
        "automatic_observations": sum(
            len(f["observations"]) for f in automatic["frames"]
        ),
        "new_detector_forwards": 0,
        "new_feature_embedding_forwards": (
            0
            if "run" in feature_source
            else automatic["feature_receipt"]["requested_embedding_count"]
        ),
        "inherited_feature_embedding_count": (
            automatic["feature_receipt"]["requested_embedding_count"]
            if "run" in feature_source
            else 0
        ),
        "feature_source": feature_source,
        "inherited_gpu_receipt": automatic["feature_receipt"],
        "source_pins": sources["pins"],
        "copied_inputs": copied,
        "viewer": "review.html",
    }
    if summary["baseline_proposals"] != 457 or summary["automatic_observations"] != 17:
        raise ValueError("Task22 trial accounting differs from the pinned inputs")
    for condition, records in automatic["conditions"].items():
        cup = []
        failures = []
        decisions = {"new": 0, "matched": 0, "unresolved": 0}
        object_ids_by_class: dict[str, set[str]] = {}
        for frame in records:
            for observation in frame["observations"]:
                decisions[observation["decision"]] = (
                    decisions.get(observation["decision"], 0) + 1
                )
                if observation["object_id"]:
                    object_ids_by_class.setdefault(observation["category"], set()).add(
                        observation["object_id"]
                    )
                if observation["category"] == "cup":
                    cup.append(observation)
                if observation["decision"] == "unresolved":
                    failures.append(observation)
        before = next(row for row in cup if row["frame_id"] == "104")
        returned = next(row for row in cup if row["frame_id"] == "359")
        gap_state = next(frame for frame in records if frame["frame_index"] == 27)
        gap_track = next(
            (
                track
                for track in gap_state["tracks"]
                if track["object_id"] == before["object_id"]
            ),
            None,
        )
        survived = (
            before["object_id"] is not None
            and before["object_id"] == returned["object_id"]
        )
        first = np.asarray(before["position_world_m"], dtype=float)
        later = np.asarray(returned["position_world_m"], dtype=float)
        delta = later - first
        coordinates["conditions"][condition] = {
            "cup_id_before_gap": before["object_id"],
            "cup_id_after_return": returned["object_id"],
            "same_id_survived_return": survived,
            "last_position_retained_during_physical_gap": (
                gap_track is not None and gap_track["last_frame_id"] == "104"
            ),
            "decision_counts": decisions,
            "distinct_persistent_ids_by_class": {
                category: len(object_ids)
                for category, object_ids in sorted(object_ids_by_class.items())
            },
            "cup_frame104_world_m": first.tolist(),
            "cup_frame359_world_m": later.tolist(),
            "return_minus_before_m": delta.tolist(),
            "return_shift_norm_m": float(np.linalg.norm(delta)),
            "unresolved_count": len(failures),
            "failed_associations": failures,
        }
        if not survived:
            summary.setdefault("cup_identity_failures", []).append(condition)
    summary["cup_identity_survived_all_conditions"] = not bool(
        summary.get("cup_identity_failures")
    )
    summary["not_claimed"] = [
        "object-centre accuracy",
        "unseen-recording identity accuracy",
        "Task16 broad protocol approval",
        "Task13 estimated camera path",
    ]
    write_json(run_path / "output/coordinate_differences.json", coordinates)
    write_json(run_path / "output/summary.json", summary)
