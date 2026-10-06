"""Identity analysis has a public boundary and keeps historical score semantics."""

import importlib
import subprocess
import sys
from copy import deepcopy

import pytest

PACKAGE = "experiments.06_object_recognition.experiments"


@pytest.mark.parametrize(
    "experiment, owner, names",
    [
        ("01_detection", "scoring", ("evaluate",)),
        ("02_segmentation", "scoring", ("mask_scores", "instance_events")),
        ("03_appearance", "evaluator", ("label_pairs", "rank_queries")),
    ],
)
def test_validation_facades_forward_existing_functions(experiment, owner, names):
    validation = importlib.import_module(f"{PACKAGE}.{experiment}.validation")
    original = importlib.import_module(f"{PACKAGE}.{experiment}.{owner}")
    for name in names:
        assert getattr(validation, name) is getattr(original, name)


def test_identity_public_score_is_historical_runner_alias():
    validation = importlib.import_module(f"{PACKAGE}.04_geometry_identity.validation")
    runner = importlib.import_module(f"{PACKAGE}.04_geometry_identity.run")
    assert validation.score_identity is runner._score


def test_public_identity_score_keeps_merges_splits_and_surface_deltas():
    score = importlib.import_module(
        f"{PACKAGE}.04_geometry_identity.validation"
    ).score_identity
    truth = [
        {"observation_id": key, "instance_id": identity}
        for key, identity in [("a", "cup"), ("b", "cup"), ("c", "monitor"), ("d", "cup")]
    ]
    decisions = [
        {"observation_id": key, "object_id": object_id, "decision": decision}
        for key, object_id, decision in [
            ("a", "one", "new"), ("b", "two", "new"),
            ("c", "one", "matched"), ("d", None, "unresolved"),
        ]
    ]
    observations = [
        {"observation_id": key, "timestamp_s": timestamp, "position_world_m": position}
        for key, timestamp, position in [
            ("a", 0, [0, 0, 0]), ("b", 2, [3, 4, 0]),
            ("c", 3, [1, 1, 1]), ("d", 4, None),
        ]
    ]
    original = deepcopy((decisions, truth, observations))
    result = score(decisions, truth, observations)
    assert result["matched"] == 3 and result["unresolved"] == 1
    assert result["wrong_merge_object_ids"] == ["one"]
    assert result["wrong_split_reference_ids"] == ["cup"]
    assert result["correctly_associated_observations"] == 1
    assert result["coordinate_comparisons_scorer_only"] == [{
        "reference_identity_scorer_only": "cup", "from_observation": "a",
        "to_observation": "b", "elapsed_s": 2.0,
        "world_surface_delta_m": [3.0, 4.0, 0.0],
        "world_surface_delta_norm_m": 5.0, "same_assigned_object_id": False,
        "interpretation": "Difference between observed surface medians across views; not localization error.",
    }]
    assert (decisions, truth, observations) == original


def test_identity_score_keeps_missing_truth_error():
    score = importlib.import_module(
        f"{PACKAGE}.04_geometry_identity.validation"
    ).score_identity
    with pytest.raises(KeyError, match="missing"):
        score([{"observation_id": "missing", "object_id": "one"}], [], [])


@pytest.mark.parametrize("experiment", ["01_detection", "02_segmentation", "03_appearance", "04_geometry_identity"])
def test_validation_import_does_not_load_trial_or_optional_models(experiment):
    script = (
        "import importlib, sys; "
        f"importlib.import_module('{PACKAGE}.{experiment}.validation'); "
        f"assert '{PACKAGE}.{experiment}.run' not in sys.modules; "
        "assert not {'torch', 'ultralytics', 'cv2'}.intersection(sys.modules)"
    )
    subprocess.run([sys.executable, "-B", "-c", script], check=True)
