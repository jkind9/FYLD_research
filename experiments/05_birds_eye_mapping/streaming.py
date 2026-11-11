"""Checked adapters for array and chunk-based mapping experiments."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from sitescan.mapping import fit_dominant_plane as fit_array
from sitescan.mapping import footprint as footprint_array
from sitescan.mapping.footprint import grid_shape
from sitescan.mapping.footprint import onto_plane as _onto_plane
from sitescan.mapping.footprint import signed_axes as _signed
from sitescan.mapping.plane import ransac
from sitescan.mapping.types import Footprint, Plane

from .chunks import PointChunks, _as_chunks, _Scatter

PointSource = ArrayLike | PointChunks


def fit_dominant_plane(
    points: PointSource, *, inlier_distance_m: float, iterations: int, sample_size: int, seed: int
) -> Plane:
    """Checked experiment input adapted to shared array methods or retained chunk processing."""
    source = _as_chunks(points)
    if not np.isfinite(inlier_distance_m) or inlier_distance_m <= 0:
        raise ValueError("Plane inlier distance must be positive and finite")
    if not isinstance(points, PointChunks):
        return fit_array(
            next(iter(source)),
            inlier_distance_m=inlier_distance_m,
            iterations=iterations,
            sample_size=sample_size,
            seed=seed,
        )
    rng = np.random.default_rng(seed)
    if source.total > sample_size:
        subset = source.take(rng.choice(source.total, size=sample_size, replace=False))
    else:
        subset = np.concatenate(list(source))
    best_point, best_normal = ransac(
        subset, rng, inlier_distance_m=inlier_distance_m, iterations=iterations
    )
    moments = _Scatter(best_point)
    for array in source:
        moments.add(array[np.abs((array - best_point) @ best_normal) <= inlier_distance_m])
    centre, axes = moments.principal_axes()
    return Plane(
        point=centre,
        normal=axes[2],
        inlier_fraction=moments.count / source.total,
        source="fitted_dominant_plane",
    )


def footprint(
    points: PointSource,
    plane: Plane,
    up: np.ndarray | list[float] | tuple,
    *,
    cell_size_m: float,
    band_m: float,
    units: str = "metres",
) -> Footprint:
    """Checked experiment input adapted to shared array methods or retained chunk processing."""
    _check_grid(cell_size_m, band_m, units)
    source = _as_chunks(points)
    direction = np.asarray(up, dtype=np.float64)
    if direction.shape != (3,) or not np.isfinite(direction).all() or (not direction.any()):
        raise ValueError("Up direction must be a finite, non-zero 3-vector")
    if not isinstance(points, PointChunks):
        return footprint_array(
            next(iter(source)), plane, direction, cell_size_m=cell_size_m, band_m=band_m
        )
    normal = plane.normal / np.linalg.norm(plane.normal)
    if normal @ direction < 0:
        normal = -normal
    reference = Plane(plane.point, normal, plane.inlier_fraction, plane.source)
    moments = _Scatter(plane.point)
    for array in source:
        height_m, projection = _onto_plane(array, plane.point, normal)
        moments.add(projection[np.abs(height_m) <= band_m])
    if moments.count < 3:
        raise ValueError("Fewer than 3 points lie on the reference plane")
    axes = _signed(moments.principal_axes()[1][:2])
    return _chunk_grid(source, reference, axes, cell_size_m, band_m)


def _chunk_grid(source, reference, axes, cell_size_m, band_m):
    """A footprint grid accumulated over checked experimental point chunks."""
    normal = reference.normal
    lower = np.full(2, np.inf)
    upper = np.full(2, -np.inf)
    for array in source:
        if len(array):
            coordinates = _onto_plane(array, reference.point, normal)[1] @ axes.T
            lower = np.minimum(lower, coordinates.min(axis=0))
            upper = np.maximum(upper, coordinates.max(axis=0))
    lower, shape = grid_shape(np.vstack([lower, upper]), cell_size_m)
    occupied = np.zeros(shape, dtype=np.bool_)
    plane_mask = np.zeros(shape, dtype=np.bool_)
    height_grid = np.full(shape, -np.inf)
    for array in source:
        height_m, projection = _onto_plane(array, reference.point, normal)
        indices = np.floor((projection @ axes.T - lower) / cell_size_m).astype(np.int64)
        occupied[indices[:, 0], indices[:, 1]] = True
        in_band = np.abs(height_m) <= band_m
        plane_mask[indices[in_band, 0], indices[in_band, 1]] = True
        np.maximum.at(height_grid, (indices[:, 0], indices[:, 1]), height_m)
    height_grid[~occupied] = np.nan
    origin = lower @ axes + reference.point @ normal * normal
    return Footprint(
        plane=reference,
        basis=axes,
        grid_origin=origin,
        cell_size_m=float(cell_size_m),
        observed=occupied,
        on_plane=plane_mask,
        max_height_m=height_grid,
        point_count=source.total,
    )


def _check_grid(cell_m, plane_band_m, distance_units):
    """Check experiment grid settings before passing arrays into the product stage."""
    if distance_units != "metres":
        raise ValueError(f"Footprint needs points in metres, got {distance_units!r}")
    if not np.isfinite(cell_m) or cell_m <= 0:
        raise ValueError("Grid cell size must be positive and finite")
    if not np.isfinite(plane_band_m) or plane_band_m <= 0:
        raise ValueError("Plane band must be positive and finite")
