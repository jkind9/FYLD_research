"""The grid-footprint mapping method inside the walkthrough: origins, saving and visuals."""

import argparse
import json
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from src.walkthrough import pipeline
from src.walkthrough.steps import mapping
from src.walkthrough.tests.test_adapters import config, read  # noqa: F401  (fixture)


def _floor(offset_x: float = 0.0) -> np.ndarray:
    """A 1 m x 2 m floor at y = 1.5 m below cameras looking along +z (camera y points down)."""
    xs = offset_x + 0.005 + 0.01 * np.arange(100)
    zs = 0.005 + 0.01 * np.arange(200)
    grid_x, grid_z = np.meshgrid(xs, zs, indexing="ij")
    floor = np.column_stack((grid_x.ravel(), np.full(grid_x.size, 1.5), grid_z.ravel()))
    return np.vstack(([[offset_x, 1.5, 0.0]], floor))


def _surface(tmp_path: Path, origins: dict[str, np.ndarray]) -> dict:
    shards = []
    for index, (world, points) in enumerate(origins.items()):
        relative = f"output/predictions/surface/{index:06d}.npy"
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        np.save(tmp_path / relative, points)
        shards.append(
            {
                "frame_id": f"frame-{index}",
                "points": relative,
                "point_count": len(points),
                "world_id": world,
                "segment_id": "0",
                "units": "metres",
                "camera_centre_m": [0.5, 0.0, 1.0],
            }
        )
    return {"methods": {"surface": "fixture"}, "shards": shards, "coverage": "observed"}


def _run_context(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(path=tmp_path, measure=lambda *_args, **_kwargs: nullcontext())


def test_surface_shards_record_the_camera_centre_of_their_pose(config):  # noqa: F811
    result = pipeline.run(config)

    tracking = {row["frame_id"]: row for row in read(result, "tracking")["records"]}
    for shard in read(result, "surface")["shards"]:
        matrix = np.asarray(tracking[shard["frame_id"]]["pose"]["T_world_camera"])
        np.testing.assert_allclose(shard["camera_centre_m"], matrix[:3, 3])


def test_grid_footprint_measures_each_origin_separately_as_plain_floats(tmp_path):
    surface = _surface(tmp_path, {"world-a": _floor(), "world-b": _floor(offset_x=5.0)})

    measured = mapping.GridFootprint().load()(surface, tmp_path)

    assert isinstance(measured, mapping.MappingResult)
    area_names = sorted(name for name in measured.measurements if name.endswith("observed footprint area"))
    assert area_names == ["origin 0 observed footprint area", "origin 1 observed footprint area"]
    for name in area_names:
        value = measured.measurements[name]["value"]
        assert type(value) is float and value == pytest.approx(2.00, abs=1e-9)
        assert measured.measurements[name]["units"] == "square metres"
    assert [row["world_id"] for row in measured.maps] == ["world-a", "world-b"]
    assert all(row["plane_source"] == "fitted_dominant_plane" for row in measured.maps)
    # Cameras sit above the floor (smaller camera y), so heights above the plane are >= 0.
    assert all(measured.measurements[f"origin {i} highest point"]["value"] < 0.03 for i in (0, 1))


def test_origin_with_too_few_points_is_skipped_and_all_skipped_fails(tmp_path):
    surface = _surface(tmp_path, {"world-a": _floor(), "world-b": np.zeros((2, 3))})

    measured = mapping.GridFootprint().load()(surface, tmp_path)

    assert measured.maps[1]["skipped"] == "fewer than 3 points"
    assert not any(name.startswith("origin 1 ") for name in measured.measurements)
    empty = _surface(tmp_path / "empty", {"world-c": np.zeros((2, 3))})
    with pytest.raises(ValueError, match="No origin"):
        mapping.GridFootprint().load()(empty, tmp_path / "empty")


def test_mapping_run_saves_grids_only_after_validation(tmp_path):
    surface = _surface(tmp_path, {"world-a": _floor()})
    good = mapping.GridFootprint()

    row, output = mapping.run(_run_context(tmp_path), surface, good)

    assert row.status == "complete", row.reason
    (saved,) = output["maps"]
    with np.load(tmp_path / saved["arrays"]) as arrays:
        assert arrays["observed"].sum() == 800  # 1 m x 2 m at 5 cm cells
    bad_root = tmp_path / "bad"
    bad = _surface(bad_root, {"world-a": _floor()})

    class NonFinite(mapping.GridFootprint):
        def load(self):
            def estimate(surface, run_path):
                result = super(NonFinite, self).load()(surface, run_path)
                return replace(
                    result,
                    measurements={"broken": {"value": float("nan"), "units": "metres"}},
                )

            return estimate

    row, output = mapping.run(_run_context(bad_root), bad, NonFinite())

    assert row.status == "failed"
    assert not (bad_root / "output/predictions/mapping").exists()


def test_plain_measurement_dicts_still_work(tmp_path):
    class PlainDict:
        name = "plain"
        control = "software"

        def load(self):
            return lambda surface, run_path: {"status": "fixture_only"}

    row, output = mapping.run(_run_context(tmp_path), _surface(tmp_path, {}), PlainDict())

    assert row.status == "complete"
    assert output["maps"] == []


def test_six_layer_run_with_grid_footprint_shows_a_map_per_origin(config):  # noqa: F811
    result = pipeline.run(replace(config, mapping=mapping.GridFootprint()))

    assert result.steps[4].status == "complete", result.steps[4].reason
    manifest = json.loads(
        (result.path / "output/visualizations/manifest.json").read_text()
    )
    (stage,) = [row for row in manifest["stages"] if row["stage"] == "mapping"]
    images = [row for row in stage["artifacts"] if row["kind"] == "image"]
    assert len(images) == len(read(result, "mapping")["maps"]) >= 1
    for image in images:
        assert (result.path / image["path"]).is_file()
        assert image["producer_method"].startswith("grid_footprint")


def test_cli_mapping_choice():
    from src.walkthrough.cli import mapping_choice

    assert isinstance(mapping_choice(argparse.Namespace(mapping="grid-footprint")), mapping.GridFootprint)
    assert mapping_choice(argparse.Namespace(mapping=None)) is None


@pytest.mark.parametrize(
    "bad_points,reason",
    [
        (np.column_stack((np.arange(10.0), np.zeros(10), np.zeros(10))), "span a plane"),
        (np.ones((5, 3)), "span a plane"),
    ],
    ids=["collinear", "repeated"],
)
def test_one_unmeasurable_origin_does_not_hide_the_others(tmp_path, bad_points, reason):
    surface = _surface(tmp_path, {"world-a": _floor(), "world-b": bad_points})

    measured = mapping.GridFootprint().load()(surface, tmp_path)

    assert measured.measurements["origin 0 observed footprint area"]["value"] == pytest.approx(2.0)
    assert reason in measured.maps[1]["skipped"]


def test_shards_saved_before_camera_centres_existed_are_skipped_with_a_reason(tmp_path):
    surface = _surface(tmp_path, {"world-a": _floor(), "world-b": _floor(offset_x=5.0)})
    del surface["shards"][1]["camera_centre_m"]

    measured = mapping.GridFootprint().load()(surface, tmp_path)

    assert "camera_centre_m" in measured.maps[1]["skipped"]
    assert "origin 0 observed footprint area" in measured.measurements


def test_map_records_are_validated_before_the_layer_completes(tmp_path):
    class LooseMaps:
        name = "loose"
        control = None

        def load(self):
            grids = {"observed": np.ones((2, 2), bool), "max_height_m": np.zeros((2, 2))}
            return lambda surface, run_path: mapping.MappingResult(
                {"area": {"value": 1.0, "units": "square metres"}}, ({"grids": grids},)
            )

    row, _ = mapping.run(_run_context(tmp_path), _surface(tmp_path, {}), LooseMaps())

    assert row.status == "failed"
    assert "Map record" in row.reason
    assert not (tmp_path / "output/predictions/mapping").exists()
