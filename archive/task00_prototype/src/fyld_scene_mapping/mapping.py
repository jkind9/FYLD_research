"""Bounded observed-surface rasters; no hole filling or free-space claims."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def project(
    points: NDArray,
    colours: NDArray,
    resolution: float = 0.02,
    max_extent: float = 20.0,
    max_cells: int = 2_000_000,
    height_slice: tuple[float, float] | None = None,
    statistic: str = "maximum",
) -> dict:
    """Project +Z-up geometry; arrays [y,x] increase +Y/+X, PNGs flip Y upward."""
    if points.ndim != 2 or points.shape[1] != 3 or colours.shape != points.shape:
        raise ValueError("Expected matching Nx3 points and RGB")
    if (
        not np.isfinite([resolution, max_extent]).all()
        or resolution <= 0
        or max_extent <= 0
        or max_cells < 1
    ):
        raise ValueError("Invalid map limits")
    if statistic not in {"maximum", "minimum", "median"}:
        raise ValueError("Unknown height statistic")
    keep = np.isfinite(points).all(axis=1) & np.isfinite(colours).all(axis=1)
    # Absolute bound is checked BEFORE integer conversion or allocation.
    keep &= (np.abs(points) <= max_extent).all(axis=1)
    if height_slice is not None:
        slice_low, slice_high = height_slice
        if not np.isfinite([slice_low, slice_high]).all() or slice_low > slice_high:
            raise ValueError("Invalid height slice")
        keep &= (points[:, 2] >= slice_low) & (points[:, 2] <= slice_high)
    xyz, rgb = points[keep], colours[keep]
    if not len(xyz):
        raise ValueError("No points remain inside map bounds/slice")
    origin = np.floor(xyz[:, :2].min(axis=0) / resolution) * resolution
    extent = xyz[:, :2].max(axis=0) - origin
    shape_xy = np.floor(extent / resolution).astype(np.int64) + 1
    if np.any(extent > max_extent) or int(shape_xy[0]) * int(shape_xy[1]) > max_cells:
        raise ValueError("Map allocation exceeds bounded extent/cell budget")
    ix, iy = np.floor((xyz[:, :2] - origin) / resolution).astype(np.int64).T
    nx, ny = map(int, shape_xy)
    flat = iy * nx + ix
    count = np.bincount(flat, minlength=nx * ny).reshape(ny, nx)
    low = np.full(nx * ny, np.inf)
    high = np.full(nx * ny, -np.inf)
    np.minimum.at(low, flat, xyz[:, 2])
    np.maximum.at(high, flat, xyz[:, 2])
    height = high.copy() if statistic == "maximum" else low.copy()
    if statistic == "median":
        order = np.argsort(flat, kind="stable")
        groups, starts, sizes = np.unique(
            flat[order], return_index=True, return_counts=True
        )
        height[:] = np.nan
        for group, start, size in zip(groups, starts, sizes):
            height[group] = np.median(xyz[order[start : start + size], 2])
    colour: NDArray[np.uint8] = np.zeros((nx * ny, 3), dtype=np.uint8)
    # Colour always comes from highest observed sample, including median-height maps.
    order = np.lexsort((xyz[:, 2], flat))
    last = np.r_[flat[order][1:] != flat[order][:-1], True]
    top = order[last]
    colour[flat[top]] = np.clip(rgb[top] * 255, 0, 255).astype(np.uint8)
    unknown = count.ravel() == 0
    height[unknown] = np.nan
    low[unknown], high[unknown] = np.nan, np.nan
    metadata = {
        "grid_origin_xy_m": origin.tolist(),
        "bounds_xy_m": [origin.tolist(), (origin + shape_xy * resolution).tolist()],
        "cell_resolution_m": resolution,
        "shape_yx": [ny, nx],
        "axes": "+X columns, +Y rows in NPY; PNG rows increase -Y; +Z supplied up",
        "vertical_reference": "Z=0 supplied alignment plane",
        "units": "metres",
        "height_statistic": statistic,
        "colour_rule": "RGB of highest retained observed sample",
        "height_slice_m": height_slice,
        "sample_count_meaning": "retained fused voxel centres per cell, not probability or independent observations",
        "unknown": "NaN heights; zero counts; mask=0; black colour can also be observed",
        "free_space": "not inferred",
        "rejected_points": int(len(points) - len(xyz)),
        "max_extent_m": max_extent,
        "max_cells": max_cells,
    }
    return {
        "height": height.reshape(ny, nx),
        "minimum": low.reshape(ny, nx),
        "maximum": high.reshape(ny, nx),
        "count": count,
        "colour": colour.reshape(ny, nx, 3),
        "metadata": metadata,
    }


def save_maps(products: dict, output: Path) -> None:
    """Save measurement arrays and display rasters; display scaling is in metadata."""
    height, count = products["height"], products["count"]
    np.save(output / "height_map.npy", height)
    np.save(output / "height_min.npy", products["minimum"])
    np.save(output / "height_max.npy", products["maximum"])
    np.save(output / "vertical_range.npy", products["maximum"] - products["minimum"])
    np.save(output / "sample_count.npy", count)
    Image.fromarray(np.flipud(products["colour"])).save(output / "topdown_colour.png")
    Image.fromarray(np.flipud((count > 0).astype(np.uint8) * 255)).save(
        output / "observed_mask.png"
    )
    finite = height[np.isfinite(height)]
    lo, hi = float(finite.min()), float(finite.max())
    scaled = np.zeros(height.shape, dtype=np.uint8)
    observed = np.isfinite(height)
    scaled[observed] = 1 + (
        np.clip((height[observed] - lo) / max(hi - lo, 1e-9), 0, 1) * 254
    ).astype(np.uint8)
    Image.fromarray(np.flipud(scaled)).save(output / "height_map.png")
    products["metadata"]["height_png"] = {"zero": "unknown", "range_1_255_m": [lo, hi]}
