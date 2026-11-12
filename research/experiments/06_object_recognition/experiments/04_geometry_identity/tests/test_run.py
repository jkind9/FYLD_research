from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from experiments.shared.runs import verify_run

runner = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.run"
)
association = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.association"
)
persistence = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.persistence"
)


def test_bounded_frozen_replay_publishes_five_checked_generations_and_review():
    repo = Path(__file__).resolve().parents[5]
    verified_run = os.environ.get("TASK21_VERIFIED_RUN")
    run_path = Path(verified_run) if verified_run else runner.run_evaluation(repo)
    assert verify_run(run_path)["status"] == "complete"
    summary = json.loads((run_path / "output/summary.json").read_text(encoding="utf-8"))
    assert summary["source_observations"] == 11
    assert summary["gpu_forwards"] == 0
    assert summary["appearance_vectors_reused"] == 11
    assert set(summary["conditions"]) == set(association.CONDITIONS)
    for condition in association.CONDITIONS:
        generation = persistence.read_generation(run_path, condition)["generation"]
        assert generation["observation_count"] == 11
        assert generation["persisted_observation_count"] == 11
    method = json.loads(
        (run_path / "input/method_observations.json").read_text(encoding="utf-8")
    )
    assert len(method) == 11
    assert not any("instance_id" in row for row in method)
    truth = json.loads(
        (run_path / "input/evaluator_truth.json").read_text(encoding="utf-8")
    )
    frame_sources = json.loads(
        (run_path / "input/source_receipt.json").read_text(encoding="utf-8")
    )["frame_sources"]
    assert {row["frame_id"] for row in frame_sources} == {
        "23",
        "104",
        "268",
        "359",
        "405",
        "560",
    }
    history = json.loads(
        (run_path / "output/frame_history.json").read_text(encoding="utf-8")
    )["combined-viewmedian"]
    gap = next(row for row in history if row["frame_id"] == "268")
    assert gap["no_observation"] is True
    cup_keys = {
        row["observation_id"] for row in truth if row["instance_id"] == "reference-cup"
    }
    cup_decisions = [
        row
        for row in persistence.read_generation(run_path, "combined-viewmedian")[
            "ledger"
        ]["observations"]
        if row["observation_id"] in cup_keys
    ]
    assert len({row["object_id"] for row in cup_decisions}) == 1
    assert {row["decision"] for row in cup_decisions} == {"new", "matched"}
    cup_object_id = cup_decisions[0]["object_id"]
    assert (
        gap["tracks"]
        and next(row for row in gap["tracks"] if row["object_id"] == cup_object_id)[
            "location"
        ]["accepted_count"]
        == 2
    )
    cup_frame = {row["observation_id"]: row["frame_id"] for row in method}
    before_key = next(key for key in cup_keys if cup_frame[key] == "104")
    return_key = next(key for key in cup_keys if cup_frame[key] == "359")
    cup_pair = next(
        row
        for row in summary["conditions"]["combined-viewmedian"]["score"][
            "coordinate_comparisons_scorer_only"
        ]
        if row["from_observation"] == before_key and row["to_observation"] == return_key
    )
    assert cup_pair["same_assigned_object_id"] is True
    before_decision = next(
        row for row in cup_decisions if row["observation_id"] == before_key
    )
    return_decision = next(
        row for row in cup_decisions if row["observation_id"] == return_key
    )
    assert before_decision["object_id"] == return_decision["object_id"] == cup_object_id
    assert before_decision["decision"] == return_decision["decision"] == "matched"
    assert all(
        "box_support_comparison" in row
        and "polygon_vs_box_coordinate_difference" in row
        for row in method
    )
    assert any(
        row["polygon_vs_box_coordinate_difference"][
            "box_minus_polygon_world_delta_norm_m"
        ]
        is not None
        for row in method
    )
    html = (run_path / "review.html").read_text(encoding="utf-8")
    assert "Measured coordinate differences across views" in html
    assert "position_world_m" in html
