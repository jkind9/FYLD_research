"""Swappable named site measurements, with optional top-down grids for each origin."""

import importlib
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .contracts import MappingOutput, MethodChoice, SurfaceOutput, method_label

footprint_owner = importlib.import_module("experiments.05_birds_eye_mapping.measure")


@dataclass(frozen=True)
class MappingResult:
    """Named measurements plus one map record per tracking origin.

    Each map record holds JSON metadata and, under "grids", in-memory arrays. The mapping
    layer saves the grids only after the measurements pass validation.
    """

    measurements: dict[str, Any]
    maps: tuple[dict[str, Any], ...] = ()


MappingEstimator = Callable[[SurfaceOutput, Path], "dict[str, Any] | MappingResult"]


class MappingMethod(MethodChoice, Protocol):
    """Load a method receiving the saved surface and returning measurements (and maps)."""

    def load(self) -> MappingEstimator: ...


@dataclass(frozen=True)
class GridFootprint:
    """Experiment 05's grid footprint, measured separately for each tracking origin.

    Settings are Task55's frozen values. Up points towards the origin's mean camera
    centre, so heights are measured on the side the cameras were on.
    """

    cell_size_m: float = 0.05
    inlier_distance_m: float = 0.02
    iterations: int = 500
    sample_size: int = 50_000
    seed: int = 0
    name: str = field(default="grid_footprint", init=False)
    control: str | None = field(default=None, init=False)

    def load(self) -> MappingEstimator:
        return partial(measure_grid_footprint, settings=self)


def measure_grid_footprint(
    surface: SurfaceOutput, run_path: Path, *, settings: GridFootprint
) -> MappingResult:
    """Group surface shards by origin, fit each origin's plane and measure its footprint."""
    origins: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for shard in surface["shards"]:
        origins.setdefault((shard["world_id"], shard["segment_id"]), []).append(shard)

    measurements: dict[str, Any] = {}
    maps: list[dict[str, Any]] = []
    for index, ((world_id, segment_id), shards) in enumerate(origins.items()):
        record: dict[str, Any] = {"origin": index, "world_id": world_id, "segment_id": segment_id}
        try:
            origin_measurements, origin_map = _measure_origin(index, shards, run_path, settings)
        except ValueError as error:
            # One unmeasurable origin (too few points, a line, no plane) must not hide the
            # others. Its reason is saved in its map record and shown in the visual index.
            maps.append({**record, "skipped": str(error)})
            continue
        measurements.update(origin_measurements)
        maps.append({**record, "skipped": None, **origin_map})
    if not measurements:
        reasons = "; ".join(f"origin {row['origin']}: {row['skipped']}" for row in maps)
        raise ValueError(f"No origin could be measured ({reasons})")
    return MappingResult(measurements, tuple(maps))


def _measure_origin(
    index: int, shards: list[dict[str, Any]], run_path: Path, settings: GridFootprint
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Measure one origin, reading its saved points one shard at a time."""
    if any("camera_centre_m" not in shard for shard in shards):
        raise ValueError("surface shards lack camera_centre_m (saved before this field existed)")
    counts = [int(shard["point_count"]) for shard in shards]
    if sum(counts) < 3:
        raise ValueError("fewer than 3 points")
    points = footprint_owner.PointChunks(
        [partial(np.load, run_path / shard["points"], allow_pickle=False) for shard in shards],
        counts,
    )
    plane = footprint_owner.fit_dominant_plane(
        points,
        inlier_distance_m=settings.inlier_distance_m,
        iterations=settings.iterations,
        sample_size=settings.sample_size,
        seed=settings.seed,
    )
    cameras = np.asarray([shard["camera_centre_m"] for shard in shards], dtype=float)
    measured = footprint_owner.footprint(
        points,
        plane,
        cameras.mean(axis=0) - plane.point,
        cell_size_m=settings.cell_size_m,
        band_m=settings.inlier_distance_m,
    )
    prefix = f"origin {index}"
    origin_measurements = {
        f"{prefix} observed footprint area": _value(measured.observed_area_m2, "square metres"),
        f"{prefix} plane area": _value(measured.plane_area_m2, "square metres"),
        f"{prefix} unknown area": _value(measured.unknown_area_m2, "square metres"),
        f"{prefix} region length": _value(measured.length_m, "metres"),
        f"{prefix} region width": _value(measured.width_m, "metres"),
        f"{prefix} highest point": _value(measured.highest_m, "metres"),
        f"{prefix} lowest point": _value(measured.lowest_m, "metres"),
    }
    origin_map = {
        "plane_source": measured.plane.source,
        "plane_point_m": measured.plane.point.tolist(),
        "plane_normal": measured.plane.normal.tolist(),
        "plane_inlier_fraction": float(measured.plane.inlier_fraction),
        "basis": measured.basis.tolist(),
        "grid_origin_m": measured.grid_origin.tolist(),
        "cell_size_m": measured.cell_size_m,
        "point_count": measured.point_count,
        "grids": {
            "observed": measured.observed,
            "on_plane": measured.on_plane,
            "max_height_m": measured.max_height_m,
        },
    }
    return origin_measurements, origin_map


def _value(number: float, units: str) -> dict[str, Any]:
    return {"value": float(number), "units": units}


def run(
    run_context: Run, surface: SurfaceOutput, method: MappingMethod | None
) -> tuple[StepResult, MappingOutput | None]:
    artifact = "output/predictions/mapping.json"
    name = method.name if method is not None else None
    try:
        if method is None:
            raise Unavailable("Task55 mapping, dimensions and area implementation is unavailable")
        with run_context.measure("load_mapping"):
            measure_site = method.load()
        with run_context.measure("prediction_mapping"):
            measured = measure_site(surface, run_context.path)
            if not isinstance(measured, MappingResult):
                measured = MappingResult(measured)
            output: MappingOutput = {
                "methods": {"mapping": method_label(method)},
                "control": method.control,
                "measurements": measured.measurements,
                "maps": [],
            }
            validate(output)
            validate_maps(measured.maps)
            output["maps"] = _save_maps(run_context.path, measured.maps)
            write_json(run_context.path / artifact, output)
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("mapping", error, name), None
    return (
        StepResult("mapping", "complete", "Method outputs saved", name, None, artifact),
        output,
    )


def _save_maps(run_path: Path, maps: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """Write each origin's grids to output/predictions/mapping/ and keep the metadata."""
    saved = []
    for index, record in enumerate(maps):
        metadata = {key: value for key, value in record.items() if key != "grids"}
        if record.get("grids") is not None:
            relative = f"output/predictions/mapping/{index:06d}.npz"
            (run_path / relative).parent.mkdir(parents=True, exist_ok=True)
            np.savez(run_path / relative, **record["grids"])
            metadata["arrays"] = relative
        saved.append(metadata)
    return saved


def validate_maps(maps: tuple[dict[str, Any], ...]) -> None:
    """Every map record must carry what the saved output and the top-down picture read."""
    for position, record in enumerate(maps):
        label = f"Map record {position}"
        if not isinstance(record, dict) or type(record.get("origin")) is not int:
            raise ValueError(f"{label} needs an integer origin")
        if not all(isinstance(record.get(key), str) for key in ("world_id", "segment_id")):
            raise ValueError(f"{label} needs world_id and segment_id strings")
        if record.get("skipped") is not None:
            if not isinstance(record["skipped"], str) or record.get("grids") is not None:
                raise ValueError(f"{label} is skipped, so it needs a reason and no grids")
            continue
        cell = record.get("cell_size_m")
        if type(cell) is not float or not math.isfinite(cell) or cell <= 0:
            raise ValueError(f"{label} needs a positive finite cell_size_m")
        if not isinstance(record.get("plane_source"), str):
            # ValueError, not TypeError: mapping.run turns it into a failed layer row.
            raise ValueError(f"{label} needs a plane_source")  # noqa: TRY004
        grids = record.get("grids")
        if not isinstance(grids, dict) or set(grids) != {"observed", "on_plane", "max_height_m"}:
            raise ValueError(f"{label} needs observed, on_plane and max_height_m grids")
        shape = np.shape(grids["observed"])
        if (
            len(shape) != 2
            or np.asarray(grids["observed"]).dtype != np.bool_
            or np.asarray(grids["on_plane"]).dtype != np.bool_
            or any(np.shape(grids[name]) != shape for name in grids)
        ):
            raise ValueError(f"{label} grids must be matching 2D arrays, boolean masks")


def validate(output: MappingOutput) -> None:
    """Completed mapping must state at least one named measurement."""
    if not isinstance(output["measurements"], dict) or not output["measurements"]:
        raise ValueError("Completed mapping output must contain measurements")
    if output["control"] is None:
        for name, measurement in output["measurements"].items():
            if (
                not isinstance(measurement, dict)
                or type(measurement.get("value")) not in (int, float)
                or not math.isfinite(measurement["value"])
                or not isinstance(measurement.get("units"), str)
                or not measurement["units"].strip()
            ):
                raise ValueError(f"Measurement {name} needs a finite value and explicit units")
