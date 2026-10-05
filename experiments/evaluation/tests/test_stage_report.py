"""Contract tests for the per-stage accuracy report (Task 44)."""

import math

import pytest

from experiments.evaluation import compare, render, schema
from experiments.evaluation.stages import camera, detection, identity, surface
from experiments.evaluation.tests import fixtures


def _measure(
    name="error", value=1.0, *, method="m", coverage="complete", better="lower"
):
    return schema.measure(
        method, name, value, "m", samples=3, coverage=coverage, better=better
    )


def _section(stage="camera_path", measures=None, **overrides):
    arguments = {
        "run": {"id": "run-a", "manifest_sha256": "a" * 64},
        "dataset": "fixture",
        "reference": {
            "id": "ref",
            "version": "1",
            "sha256": "b" * 64,
            "kind": "independent",
        },
        "input_mode": "isolated",
        "scope": {"items": 3, "sha256": "d" * 64},
        "measures": measures if measures is not None else [_measure()],
    }
    arguments.update(overrides)
    return schema.section(stage, **arguments)


# --- schema --------------------------------------------------------------------


def test_report_lists_every_stage_and_marks_missing_ones_unavailable():
    report = schema.build_report([_section()])
    assert [s["stage"] for s in report["sections"]] == list(schema.STAGES)
    missing = [s for s in report["sections"] if s["stage"] != "camera_path"]
    assert len(missing) == 7
    for entry in missing:
        assert entry["status"] == "unavailable"
        assert entry["measures"] == []
        assert entry["reason"]


def test_unavailable_measure_needs_reason_and_is_never_zero():
    value = schema.measure(
        "m",
        "recall",
        None,
        "fraction",
        samples=0,
        coverage="subset",
        better="higher",
        reason="subset labels",
    )
    assert value["value"] is None and value["reason"] == "subset labels"
    with pytest.raises(ValueError, match="reason"):
        schema.measure(
            "m",
            "recall",
            None,
            "fraction",
            samples=0,
            coverage="subset",
            better="higher",
        )


@pytest.mark.parametrize(
    "change",
    [
        {"input_mode": "sideways"},
        {"reference": {"id": "r", "version": "1", "sha256": "c", "kind": "guess"}},
    ],
)
def test_section_rejects_unknown_mode_or_reference_kind(change):
    with pytest.raises(ValueError):
        _section(**change)


def test_measure_rejects_nonfinite_and_bad_coverage():
    with pytest.raises(ValueError):
        _measure(value=math.nan)
    with pytest.raises(ValueError):
        _measure(coverage="most")


def test_duplicate_or_unknown_stage_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        schema.build_report([_section(), _section()])
    with pytest.raises(ValueError, match="stage"):
        _section(stage="vibes")


# --- compare -------------------------------------------------------------------


def _row(rows, name="error"):
    return next(r for r in rows if r["name"] == name)


def test_compare_labels_direction_and_change():
    base = schema.build_report([_section(measures=[_measure(value=0.2)])])
    worse = schema.build_report([_section(measures=[_measure(value=0.3)])])
    row = _row(compare.compare(base, worse))
    assert row["comparable"] is True
    assert row["change"] == pytest.approx(0.1)
    assert row["verdict"] == "worse"
    assert _row(compare.compare(worse, base))["verdict"] == "better"


@pytest.mark.parametrize(
    "field, change, reason",
    [
        (
            "reference",
            {"id": "ref", "version": "1", "sha256": "c" * 64, "kind": "independent"},
            "reference",
        ),
        ("input_mode", "chained", "input mode"),
        ("dataset", "other", "dataset"),
    ],
)
def test_compare_refuses_section_mismatches(field, change, reason):
    base = schema.build_report([_section()])
    other = schema.build_report([_section(**{field: change})])
    row = _row(compare.compare(base, other))
    assert row["comparable"] is False
    assert reason in row["reason"]
    assert row["verdict"] is None


def test_compare_refuses_coverage_mismatch_per_measure():
    base = schema.build_report([_section(measures=[_measure(coverage="complete")])])
    other = schema.build_report([_section(measures=[_measure(coverage="subset")])])
    row = _row(compare.compare(base, other))
    assert row["comparable"] is False and "coverage" in row["reason"]


def test_compare_keys_measures_by_method():
    base = schema.build_report([_section(measures=[_measure(method="a")])])
    other = schema.build_report([_section(measures=[_measure(method="b")])])
    rows = compare.compare(base, other)
    assert {(r["method"], r["comparable"]) for r in rows} == {
        ("a", False),
        ("b", False),
    }
    assert all("method" in r["reason"] for r in rows)


# --- wrappers on sealed fixtures ------------------------------------------------


def test_camera_wrapper_reproduces_offset_error(tmp_path):
    digest = fixtures.camera_run(tmp_path, offset_m=0.05, frames=3)
    section = camera.camera_section(tmp_path, dataset="fixture", pinned_sha256=digest)
    by_frame = {row["frame_id"]: row["position_error_m"] for row in section["rows"]}
    assert by_frame["0"] == 0.0
    assert by_frame["1"] == pytest.approx(0.05) and by_frame["2"] == pytest.approx(0.05)
    rmse = next(m for m in section["measures"] if m["name"] == "position_rmse")
    assert rmse["value"] == pytest.approx(0.05 * math.sqrt(2 / 3))
    assert section["reference"]["kind"] == "independent"


def test_wrapper_refuses_wrong_pin_and_damaged_run(tmp_path):
    fixtures.camera_run(tmp_path)
    with pytest.raises(ValueError, match="pinned"):
        camera.camera_section(tmp_path, dataset="fixture", pinned_sha256="0" * 64)
    (tmp_path / "output/poses.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        camera.camera_section(tmp_path, dataset="fixture")


def test_wrapper_refuses_run_whose_stored_score_differs(tmp_path):
    fixtures.camera_run(tmp_path)
    stored = fixtures.read(tmp_path / "output/metrics.json")
    fixtures.write_json(
        tmp_path / "output/metrics.json", {**stored, "position_rmse_m": 0.5}
    )
    fixtures.seal(tmp_path)
    with pytest.raises(ValueError, match="reproduce"):
        camera.camera_section(tmp_path, dataset="fixture")


def test_inherited_error_split_uses_same_frames(tmp_path):
    clean, offset = tmp_path / "clean", tmp_path / "offset"
    fixtures.camera_run(clean, offset_m=0.0)
    fixtures.camera_run(offset, offset_m=0.05)
    own = camera.camera_section(clean, dataset="fixture", input_mode="isolated")
    total = camera.camera_section(offset, dataset="fixture", input_mode="chained")
    split = {r["name"]: r for r in compare.inherited(own, total)}
    expected = 0.05 * math.sqrt(2 / 3)
    assert split["position_rmse"]["own"] == pytest.approx(0.0)
    assert split["position_rmse"]["inherited_loss"] == pytest.approx(expected)
    assert split["position_rmse"]["inherited_loss"] > 0
    with pytest.raises(ValueError, match="mode"):
        compare.inherited(own, own)


def test_detection_wrapper_and_recall_direction(tmp_path):
    full, dropped = tmp_path / "full", tmp_path / "dropped"
    fixtures.detection_run(full)
    fixtures.detection_run(dropped, drop_second=True)
    good = detection.detection_section(
        full, dataset="fixture", reference_kind="provisional"
    )
    bad = detection.detection_section(
        dropped, dataset="fixture", reference_kind="provisional"
    )
    name = "cup.recall@iou0.5"
    recall = {m["method"]: m["value"] for m in good["measures"] if m["name"] == name}
    assert recall == {
        "synthetic_control_fixture": 1.0,
        "empty_prediction_software_control": 0.0,
    }
    row = next(
        r
        for r in compare.compare(
            schema.build_report([good]), schema.build_report([bad])
        )
        if r["name"] == name and r["method"] == "synthetic_control_fixture"
    )
    assert row["change"] == pytest.approx(-0.5) and row["verdict"] == "worse"
    tv = [m for m in good["measures"] if m["name"].startswith("tv.precision")]
    assert tv and all(m["value"] is None and m["coverage"] == "subset" for m in tv)


def test_surface_wrapper_replays_frame_order(tmp_path):
    fixtures.surface_run(tmp_path)
    section = surface.surface_section(tmp_path, dataset="fixture")
    values = {m["name"]: m["value"] for m in section["measures"]}
    assert values["accuracy_mean"] == pytest.approx((0.01 + 0.03 + 0.07) / 3, abs=0)
    assert values["accuracy_max"] == 0.07
    assert values["within_threshold_fraction"] == pytest.approx(2 / 3)
    assert values["reference_coverage_fraction"] == 0.5


def test_identity_wrapper_reports_each_condition(tmp_path):
    fixtures.identity_run(tmp_path)
    section = identity.identity_section(tmp_path, dataset="fixture")
    value = {(m["method"], m["name"]): m["value"] for m in section["measures"]}
    assert value[("good", "false_merges")] == 0
    assert value[("merged", "false_merges")] == 1
    assert value[("merged", "correctly_associated_observations")] == 0
    assert value[("good", "correctly_associated_observations")] == 3


def test_provisional_reference_is_visible_in_table(tmp_path):
    fixtures.detection_run(tmp_path)
    section = detection.detection_section(
        tmp_path, dataset="fixture", reference_kind="provisional"
    )
    table = render.table(schema.build_report([section]))
    assert "provisional" in table
    assert "unavailable" in table


def test_publish_writes_verified_run_with_rows_split_out(tmp_path):
    from pathlib import Path

    from experiments.evaluation import run as runner
    from experiments.shared.runs import verify_run

    fixtures.camera_run(tmp_path / "camera")
    report = schema.build_report(
        [camera.camera_section(tmp_path / "camera", dataset="fixture")]
    )
    repo = Path(__file__).resolve().parents[3]
    published = runner.publish(report, repo, tmp_path / "reports")
    assert verify_run(published)["status"] == "complete"
    stored = fixtures.read(published / "output/report.json")
    camera_entry = stored["sections"][0]
    assert camera_entry["rows"] == "output/rows/camera_path.json"
    assert len(fixtures.read(published / camera_entry["rows"])) == 3
    assert all(s["rows"] is None for s in stored["sections"][1:])
    assert "unavailable" in (published / "output/report.md").read_text(encoding="utf-8")
    config = fixtures.read(published / "metadata/configuration.json")
    assert set(config["pinned_runs"]) == set(runner.PINNED)


def test_comparison_table_shows_reasons_and_unavailable():
    base = schema.build_report([_section(measures=[_measure(value=0.2)])])
    other = schema.build_report([_section(dataset="other")])
    text = render.comparison_table(compare.compare(base, other))
    assert "differs in dataset" in text and "0.2" in text


# --- diff review 2026-10-05: DR-1 to DR-5 ----------------------------------------


def test_compare_refuses_different_scored_items_of_same_sequence(tmp_path):
    short, long = tmp_path / "short", tmp_path / "long"
    fixtures.camera_run(short, frames=3)
    fixtures.camera_run(long, frames=5)
    rows = compare.compare(
        schema.build_report([camera.camera_section(short, dataset="fixture")]),
        schema.build_report([camera.camera_section(long, dataset="fixture")]),
    )
    rmse = _row(rows, "position_rmse")
    assert rmse["comparable"] is False and "scored items" in rmse["reason"]


def test_inherited_loss_points_the_right_way_for_higher_is_better():
    own = _section(measures=[_measure("recall", 1.0, better="higher")])
    total = _section(
        measures=[_measure("recall", 0.6, better="higher")], input_mode="chained"
    )
    row = compare.inherited(own, total)[0]
    assert row["inherited_loss"] == pytest.approx(0.4)
    assert row["better"] == "higher"
    lower_own = _section(measures=[_measure("error", 0.1)])
    lower_total = _section(measures=[_measure("error", 0.3)], input_mode="chained")
    assert compare.inherited(lower_own, lower_total)[0]["inherited_loss"] == (
        pytest.approx(0.2)
    )


def test_inherited_refuses_coverage_or_scope_mismatch():
    own = _section(measures=[_measure(coverage="complete")])
    total = _section(measures=[_measure(coverage="subset")], input_mode="chained")
    with pytest.raises(ValueError, match="coverage"):
        compare.inherited(own, total)
    other = _section(input_mode="chained", scope={"items": 4, "sha256": "e" * 64})
    with pytest.raises(ValueError, match="scope"):
        compare.inherited(_section(), other)


def test_identity_counts_without_a_good_direction_are_not_called_better(tmp_path):
    fixtures.identity_run(tmp_path)
    section = identity.identity_section(tmp_path, dataset="fixture")
    better = {m["name"]: m["better"] for m in section["measures"]}
    assert better["matched"] == "neither" and better["unresolved"] == "neither"
    base = schema.build_report([_section(measures=[_measure(better="neither")])])
    more = schema.build_report(
        [_section(measures=[_measure(value=2.0, better="neither")])]
    )
    assert _row(compare.compare(base, more))["verdict"] == "changed"


def test_surface_uses_copied_reference_file_without_recovery_key(tmp_path):
    fixtures.surface_run(tmp_path, recovery=False)
    section = surface.surface_section(tmp_path, dataset="fixture")
    reference = tmp_path / "input/evaluation/living-room.ply"
    assert section["reference"]["sha256"] == fixtures.sha256(reference)


@pytest.mark.parametrize("stage", ["camera", "surface"])
def test_wrapper_refuses_stored_metrics_missing_reported_keys(tmp_path, stage):
    if stage == "camera":
        fixtures.camera_run(tmp_path)
        wrapper = camera.camera_section
    else:
        fixtures.surface_run(tmp_path)
        wrapper = surface.surface_section
    stored = fixtures.read(tmp_path / "output/metrics.json")
    kept = {"threshold_m": stored["threshold_m"]} if stage == "surface" else {}
    fixtures.write_json(tmp_path / "output/metrics.json", kept)
    fixtures.seal(tmp_path)
    with pytest.raises(ValueError, match="stored"):
        wrapper(tmp_path, dataset="fixture")


def test_table_escapes_pipes_and_keeps_scored_stage_without_measures():
    entry = _section(measures=[], dataset="a|b")
    text = render.table(schema.build_report([entry]))
    assert r"a\|b" in text
    assert "no measures" in text


def test_compare_refuses_reports_from_another_format_version():
    current = schema.build_report([_section()])
    old = {**current, "schema_version": 1}
    for entry in old["sections"]:
        entry.pop("scope", None)
    with pytest.raises(ValueError, match="format version"):
        compare.compare(old, current)
    assert current["schema_version"] == 2


def test_surface_tolerates_null_recovery_record(tmp_path):
    fixtures.surface_run(tmp_path, recovery=False)
    stored = fixtures.read(tmp_path / "output/metrics.json")
    fixtures.write_json(tmp_path / "output/metrics.json", {**stored, "recovery": None})
    fixtures.seal(tmp_path)
    assert surface.surface_section(tmp_path, dataset="fixture")["status"] == "scored"
