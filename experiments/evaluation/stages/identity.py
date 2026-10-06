"""Identity stage: Task21 merges, splits and unresolved counts for every condition."""

from pathlib import Path

from experiments.evaluation import schema
from experiments.evaluation.stages.common import (
    file_sha256,
    owner,
    read_json,
    require_same,
    scope,
    verified_run,
)

VALIDATION = "experiments.06_object_recognition.experiments.04_geometry_identity.validation"
SCORES = (
    # Any assignment counts as matched, right or wrong, so neither count has a
    # better direction; correctness lives in the other three measures.
    ("matched", "neither"),
    ("unresolved", "neither"),
    ("false_merges", "lower"),
    ("false_splits", "lower"),
    ("correctly_associated_observations", "higher"),
)


def _values(score: dict) -> dict:
    return {
        "matched": score["matched"],
        "unresolved": score["unresolved"],
        "false_merges": len(score["wrong_merge_object_ids"]),
        "false_splits": len(score["wrong_split_reference_ids"]),
        "correctly_associated_observations": score["correctly_associated_observations"],
    }


def identity_section(
    run_path: Path,
    *,
    dataset: str,
    pinned_sha256: str | None = None,
    input_mode: str = "isolated",
    reference_kind: str = "provisional",
) -> dict:
    run_path = Path(run_path)
    run = verified_run(run_path, pinned_sha256)
    validation = owner(VALIDATION)
    truth = read_json(run_path / "input/evaluator_truth.json")
    observations = read_json(run_path / "input/method_observations.json")
    stored = read_json(run_path / "output/summary.json")["conditions"]
    measures, rows = [], []
    for condition in sorted(stored):
        decisions = read_json(
            run_path / "output/conditions" / condition / "decisions.json"
        )["observations"]
        score = validation.score_identity(decisions, truth, observations)
        require_same(stored[condition]["score"], score, f"identity {condition}")
        values = _values(score)
        samples = len(decisions)
        for name, better in SCORES:
            measures.append(
                schema.measure(
                    condition,
                    name,
                    values[name],
                    "count",
                    samples=samples,
                    coverage="complete",
                    better=better,
                )
            )
        rows.append({"condition": condition, **values, "observations": samples})
    return schema.section(
        "identity",
        run=run,
        dataset=dataset,
        reference={
            "id": "evaluator_truth.json",
            "version": "copied into run input",
            "sha256": file_sha256(run_path / "input/evaluator_truth.json"),
            "kind": reference_kind,
        },
        input_mode=input_mode,
        scope=scope([row["observation_id"] for row in truth]),
        measures=measures,
        rows=rows,
    )
