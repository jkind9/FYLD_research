"""Task45 Part A contract: box placement, outlines, crowd handling and clutter."""

import importlib
import math

import numpy as np
import pytest

PACKAGE = "experiments.06_object_recognition.experiments.01_detection"
scoring = importlib.import_module(f"{PACKAGE}.scoring")
placement = importlib.import_module(f"{PACKAGE}.placement")


def _prediction(xyxy, label="cup", class_id=41):
    return {"xyxy": xyxy, "label": label, "class_id": class_id, "confidence": 0.9}


def _reference(xyxy, identity="r1", category="cup"):
    return {"bbox_xyxy": xyxy, "category": category, "instance_id": identity}


# --- image size in matching (Task18 defaults unchanged) -------------------------


def test_score_category_accepts_portrait_image_box_below_480():
    rows = [_prediction([10, 500, 60, 600])]
    refs = [_reference([10, 500, 60, 600])]
    result = scoring.score_category(
        rows, refs, "cup", "complete", 0.5, width=480, height=640
    )
    assert result["matched"] == 1


def test_score_category_rejects_box_past_small_image_edge():
    with pytest.raises(ValueError, match="bounds"):
        scoring.score_category(
            [_prediction([400, 10, 520, 60])],
            [_reference([10, 10, 60, 60])],
            "cup",
            "complete",
            0.5,
            width=500,
            height=375,
        )


def test_score_category_default_size_is_still_640_by_480():
    with pytest.raises(ValueError, match="bounds"):
        scoring.score_category(
            [_prediction([10, 500, 60, 600])], [], "cup", "complete", 0.5
        )


# --- rasterising -----------------------------------------------------------------


def test_pixel_centre_rule_gives_exactly_100_pixels_for_10_by_10():
    square = [[2, 2, 12, 2, 12, 12, 2, 12]]
    outline = placement.polygon_mask(square, width=20, height=20)
    box = placement.box_mask([2, 2, 12, 12], width=20, height=20)
    assert outline.sum() == 100 and box.sum() == 100
    assert np.array_equal(outline, box)


def test_polygon_parts_are_united_and_triangle_follows_centres():
    parts = [[0, 0, 2, 0, 2, 2, 0, 2], [5, 5, 7, 5, 7, 7, 5, 7]]
    assert placement.polygon_mask(parts, width=10, height=10).sum() == 8
    triangle = [[0, 0, 4, 0, 0, 4]]
    # Pixel centres (i+0.5, j+0.5) strictly under x + y = 4: 6 of 16.
    assert placement.polygon_mask(triangle, width=4, height=4).sum() == 6


def test_crowd_run_length_is_column_major():
    # 3 rows x 2 columns; counts alternate background/foreground starting with background.
    mask = placement.decode_rle([1, 2, 3], height=3, width=2)
    assert mask.tolist() == [[False, False], [True, False], [True, False]]
    with pytest.raises(ValueError):
        placement.decode_rle([1, 2], height=3, width=2)


# --- placement -------------------------------------------------------------------


def test_identical_box_has_zero_error_and_full_coverage():
    result = placement.placement([10, 10, 50, 30], [10, 10, 50, 30])
    assert result["iou"] == 1.0
    assert result["centre_dx"] == 0 and result["centre_dy"] == 0
    assert all(
        result[f"edge_{side}"] == 0 for side in ("left", "top", "right", "bottom")
    )


def test_shifted_box_gives_signed_offsets_and_edge_errors():
    result = placement.placement([20, 6, 60, 26], [10, 10, 50, 30])
    assert (result["centre_dx"], result["centre_dy"]) == (10, -4)
    assert result["centre_offset"] == pytest.approx(math.sqrt(116))
    assert result["centre_offset_fraction"] == pytest.approx(
        math.sqrt(116) / math.hypot(40, 20)
    )
    assert (result["edge_left"], result["edge_right"]) == (10, 10)
    assert (result["edge_top"], result["edge_bottom"]) == (-4, -4)


def test_wider_box_keeps_centre_and_reports_width_ratio():
    result = placement.placement([2, 10, 58, 30], [10, 10, 50, 30])
    assert result["centre_dx"] == 0 and result["width_ratio"] == pytest.approx(1.4)


def test_excess_background_and_outline_coverage_separate_big_and_small_boxes():
    reference_mask = placement.box_mask([10, 10, 30, 30], width=60, height=60)
    same = placement.background_and_coverage(
        [10, 10, 30, 30], [10, 10, 30, 30], reference_mask
    )
    assert same == {"excess_background": 0.0, "outline_coverage": 1.0, "reason": None}
    wide = placement.background_and_coverage(
        [10, 10, 50, 30], [10, 10, 30, 30], reference_mask
    )
    assert (
        wide["excess_background"] == pytest.approx(0.5)
        and wide["outline_coverage"] == 1.0
    )
    narrow = placement.background_and_coverage(
        [10, 10, 20, 30], [10, 10, 30, 30], reference_mask
    )
    assert narrow["excess_background"] == 0.0 and narrow[
        "outline_coverage"
    ] == pytest.approx(0.5)


def test_sub_pixel_box_or_outline_is_unavailable_not_zero():
    empty = np.zeros((20, 20), dtype=bool)
    result = placement.background_and_coverage([1, 1, 5, 5], [1, 1, 5, 5], empty)
    assert result["excess_background"] is None and result["outline_coverage"] is None
    assert "1 px" in result["reason"]


def test_size_band_uses_annotation_area():
    assert placement.size_band(32 * 32 - 1) == "small"
    assert placement.size_band(32 * 32) == "medium"
    assert placement.size_band(96 * 96) == "large"


def test_touches_edge_within_two_pixels():
    assert placement.touches_edge([1.5, 10, 20, 20], width=100, height=100)
    assert not placement.touches_edge([3, 3, 97, 97], width=100, height=100)


# --- crowd and clutter -------------------------------------------------------------


def test_crowd_absorbs_mostly_inside_predictions_only():
    crowd = [{"bbox_xyxy": [0, 0, 60, 100], "category": "person"}]
    inside = {"xyxy": [0, 0, 100, 100], "label": "person"}  # 60% inside
    mostly_out = {"xyxy": [20, 0, 120, 100], "label": "person"}  # 40% inside
    other_class = {"xyxy": [0, 0, 50, 50], "label": "cup"}
    ignored = placement.crowd_ignored(
        [inside, mostly_out, inside, other_class], crowd, threshold=0.5
    )
    assert ignored == [0, 2]


def test_clutter_counts_overlapping_boxes_and_covered_share():
    target = [0, 0, 20, 10]
    others = [{"bbox_xyxy": [10, 0, 30, 10]}, {"bbox_xyxy": [50, 50, 60, 60]}]
    other_mask = placement.box_mask([10, 0, 30, 10], width=80, height=80)
    result = placement.clutter(target, others, other_mask, width=80, height=80)
    assert result == {"overlapping_objects": 1, "covered_by_others": 0.5}


def _brute_force(vertices_list, width, height):
    x, y = np.meshgrid(np.arange(width) + 0.5, np.arange(height) + 0.5)
    mask = np.zeros((height, width), dtype=bool)
    for flat in vertices_list:
        vertices = np.asarray(flat, dtype=float).reshape(-1, 2)
        mask |= placement._even_odd(vertices, x, y)
    return mask


def test_windowed_masks_equal_full_image_brute_force():
    generator = np.random.default_rng(20261005)
    for _ in range(50):
        points = generator.uniform(-5, 45, size=(int(generator.integers(3, 9)), 2))
        parts = [points.ravel().tolist()]
        assert np.array_equal(
            placement.polygon_mask(parts, width=40, height=30),
            _brute_force(parts, 40, 30),
        )
        x1, y1 = generator.uniform(-3, 30, size=2)
        box = [x1, y1, x1 + generator.uniform(0, 15), y1 + generator.uniform(0, 15)]
        corners = [box[0], box[1], box[2], box[1], box[2], box[3], box[0], box[3]]
        assert np.array_equal(
            placement.box_mask(box, width=40, height=30),
            _brute_force([corners], 40, 30),
        )


coco_scoring = importlib.import_module(f"{PACKAGE}.coco_scoring")


def _record():
    square = lambda x1, y1, x2, y2: [[x1, y1, x2, y1, x2, y2, x1, y2]]
    return {
        "image_id": 1,
        "width": 100,
        "height": 80,
        "references": [
            {
                "bbox_xyxy": [10, 10, 30, 30],
                "category": "cup",
                "instance_id": "a",
                "area": 400.0,
                "segmentation": square(10, 10, 30, 30),
            },
            {
                "bbox_xyxy": [20, 10, 40, 30],
                "category": "bottle",
                "instance_id": "b",
                "area": 400.0,
                "segmentation": square(20, 10, 40, 30),
            },
        ],
        "crowds": [
            {
                "bbox_xyxy": [60, 0, 100, 80],
                "category": "person",
                "instance_id": "c",
                "area": 3200.0,
                "segmentation": {"size": [80, 100], "counts": [80 * 60, 80 * 40]},
            },
        ],
    }


def test_score_image_counts_crowd_separately_and_measures_placement():
    proposals = [
        {"xyxy": [12, 10, 32, 30], "label": "cup", "class_id": 41, "confidence": 0.9},
        {"xyxy": [50, 50, 55, 55], "label": "cup", "class_id": 41, "confidence": 0.4},
        {"xyxy": [65, 10, 95, 70], "label": "person", "class_id": 0, "confidence": 0.8},
        {"xyxy": [0, 0, 0, 5], "label": "cup", "class_id": 41, "confidence": 0.3},
    ]
    result = coco_scoring.score_image(_record(), proposals)
    assert result["rejected_proposals"] == 1
    count = {(c["category"], c["threshold"]): c for c in result["counts"]}
    cup = count[("cup", 0.5)]
    assert (cup["matched"], cup["false_detections"], cup["ignored_crowd"]) == (1, 1, 0)
    person = count[("person", 0.5)]
    assert (person["false_detections"], person["ignored_crowd"]) == (0, 1)
    assert count[("bottle", 0.5)]["missed"] == 1
    rows = [r for r in result["placement"] if r["threshold"] == 0.5]
    assert len(rows) == 1
    (row,) = rows
    assert row["centre_dx"] == 2 and row["excess_background"] == pytest.approx(0.1)
    assert row["overlapping_objects"] == 1 and row[
        "covered_by_others"
    ] == pytest.approx(0.5)
    assert row["size_band"] == "small" and row["truncated"] is False
    assert {r["threshold"] for r in result["placement"]} == {0.3, 0.5}


def test_summarise_reports_recall_precision_and_unavailable_groups():
    result = coco_scoring.score_image(
        _record(),
        [{"xyxy": [12, 10, 32, 30], "label": "cup", "class_id": 41, "confidence": 0.9}],
    )
    summary = coco_scoring.summarise(result["counts"], result["placement"])
    hits = summary["hits"]["0.5"]
    assert hits["recall"] == pytest.approx(0.5) and hits["precision"] == 1.0
    large = summary["placement"]["0.5"]["by_size"]["large"]["iou"]
    assert large["n"] == 0 and large["median"] is None and large["reason"]
