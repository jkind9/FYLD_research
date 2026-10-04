"""Independent expected answers for box accounting, assignment and cache integrity."""

import importlib
from copy import deepcopy

import pytest

scoring = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.scoring"
)


def prediction(box=(0, 0, 10, 10), category="cup", class_id=41):
    return {
        "xyxy": list(box),
        "label": category,
        "class_id": class_id,
        "confidence": 0.8,
    }


def reference(box=(0, 0, 10, 10), category="cup", identity="a"):
    return {"bbox_xyxy": list(box), "category": category, "instance_id": identity}


def score(predictions, references, coverage="complete", category="cup", threshold=0.5):
    return scoring.score_category(
        predictions, references, category, coverage, threshold
    )


def test_duplicate_preserves_false_detection_and_candidate():
    result = score([prediction(), prediction()], [reference()])
    assert (result["matched"], result["false_detections"], result["missed"]) == (
        1,
        1,
        0,
    )
    assert result["precision"] == 0.5 and result["recall"] == 1
    assert len(result["duplicate_candidates"]) == 1
    assert len(result["unmatched_predictions"]) == 1


def test_crossed_neighbours_maximise_cardinality_before_overlap():
    # Broad proposal overlaps both references; narrow proposal only the first.
    references = [reference(), reference((8, 0, 18, 10), identity="b")]
    predictions = [prediction((0, 0, 18, 10)), prediction()]
    result = score(predictions, references)
    assert {
        (m["prediction_index"], m["reference_index"]) for m in result["matches"]
    } == {(0, 1), (1, 0)}
    assert result["missed"] == 0 and result["matched"] == 2
    reversed_result = score(list(reversed(predictions)), list(reversed(references)))
    assert reversed_result["matched"] == 2
    assert sum(m["iou"] for m in result["matches"]) == pytest.approx(1 + 10 / 18)


def test_equal_cardinality_maximises_sum_overlap():
    refs = [reference(), reference((5, 0, 15, 10), identity="b")]
    result = score([prediction((5, 0, 15, 10)), prediction()], refs, threshold=0.3)
    assert sum(m["iou"] for m in result["matches"]) == 2


@pytest.mark.parametrize(
    "predictions,references,matched,false,missed,precision,recall",
    [
        ([], [reference()], 0, 0, 1, None, 0),
        ([prediction()], [], 0, 1, 0, 0, None),
        ([], [], 0, 0, 0, None, None),
    ],
)
def test_empty_denominators(
    predictions, references, matched, false, missed, precision, recall
):
    result = score(predictions, references)
    assert (
        result["matched"],
        result["false_detections"],
        result["missed"],
        result["precision"],
        result["recall"],
    ) == (matched, false, missed, precision, recall)


def test_subset_never_claims_false_positives_or_precision_recall():
    result = score(
        [prediction(category="tv", class_id=62)] * 2,
        [reference(category="tv")],
        "subset",
        "tv",
    )
    assert result["matched"] == 1 and result["missed"] == 0
    assert result["false_detections"] is None
    assert result["precision"] is None and result["recall"] is None
    assert len(result["unmatched_predictions"]) == 1


@pytest.mark.parametrize(
    "box",
    [
        (-1, 0, 10, 10),
        (0, 0, 641, 10),
        (0, 0, 10, 481),
        (0, 0, 0, 10),
        (10, 0, 0, 10),
        (0, 0, float("nan"), 10),
        (0, 0, float("inf"), 10),
        (0, 0, True, 10),
        (0, 0, 1),
    ],
)
def test_invalid_bounds(box):
    with pytest.raises(ValueError):
        scoring.validate_predictions([prediction(box)], 640, 480, {"41": "cup"})


@pytest.mark.parametrize(
    "field,value",
    [
        ("confidence", -0.1),
        ("confidence", 1.1),
        ("confidence", True),
        ("class_id", True),
        ("class_id", 42),
        ("label", "tv"),
    ],
)
def test_invalid_category_score(field, value):
    row = {**prediction(), field: value}
    with pytest.raises(ValueError):
        scoring.validate_predictions([row], 640, 480, {"41": "cup"})


def test_threshold_and_coverage_rejected():
    for threshold in [0, 1.1, float("nan"), True]:
        with pytest.raises(ValueError):
            score([], [], threshold=threshold)
    with pytest.raises(ValueError):
        score([], [], coverage="unlabelled")


def test_category_isolation_and_no_input_mutation():
    rows = [prediction(), prediction(category="tv", class_id=62)]
    original = deepcopy(rows)
    assert score(rows, [reference()])["matched"] == 1
    assert rows == original


@pytest.mark.parametrize("label", [None, "", 42])
def test_unknown_class_with_missing_or_bad_label(label):
    row = {**prediction(), "class_id": 999, "label": label}
    with pytest.raises(ValueError):
        scoring.validate_predictions([row], 640, 480, {"41": "cup"})


@pytest.mark.parametrize(
    "predictions,references",
    [
        ([prediction((-1, 0, 10, 10))], [reference()]),
        ([prediction()], [reference((0, 0, float("nan"), 10))]),
        ([prediction()], [reference(), reference()]),
        ([prediction()], [{**reference(), "instance_id": None}]),
        ([prediction()], [{**reference(), "category": None}]),
        ([None], [reference()]),
        ([prediction()], [None]),
        ([{**prediction(), "confidence": float("nan")}], [reference()]),
    ],
)
def test_pure_scorer_rejects_invalid_inputs(predictions, references):
    with pytest.raises(ValueError):
        score(predictions, references)
