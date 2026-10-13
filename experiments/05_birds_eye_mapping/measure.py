"""Measure a top-down footprint, sizes and unseen area from metric 3D points.

The steps follow this folder's README: choose a reference plane and an up direction, lay a
square grid over the plane, mark each cell that holds at least one point as observed, and
measure. A cell with no points is unknown, never empty ground.

Points can be passed as one array or as `PointChunks` (for example one chunk per frame).
Chunks are read one at a time on every pass, so memory stays at about one chunk plus the
grid however long the recording is.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

# Refuse grids above this many cells (200 m x 200 m at 5 cm); a stray far point would
# otherwise allocate gigabytes. Task55 setting, chosen under the owner's delegation.
MAX_GRID_CELLS = 16_000_000


class PointChunks:
    """Nx3 metre points held as chunks and loaded one at a time by their loaders."""

    def __init__(self, loaders: Sequence[Callable[[], ArrayLike]], counts: Sequence[int]) -> None:
        if len(loaders) != len(counts):
            raise ValueError("Each point chunk needs exactly one declared point count")
        self._loaders = tuple(loaders)
        self.counts = tuple(int(count) for count in counts)

    @classmethod
    def from_arrays(cls, arrays: Sequence[ArrayLike]) -> PointChunks:
        checked = [_checked_chunk(array) for array in arrays]
        loaders = [lambda chunk=chunk: chunk for chunk in checked]
        return cls(loaders, [len(chunk) for chunk in checked])

    @property
    def total(self) -> int:
        return sum(self.counts)

    def __iter__(self) -> Iterator[NDArray[np.float64]]:
        for loader, count in zip(self._loaders, self.counts, strict=True):
            chunk = _checked_chunk(loader())
            if len(chunk) != count:
                raise ValueError(f"A point chunk holds {len(chunk)} points but declared {count}")
            yield chunk

    def take(self, indices: NDArray[np.int64]) -> NDArray[np.float64]:
        """Points at global positions `indices`, returned in the order given."""
        order = np.argsort(indices, kind="stable")
        wanted = np.asarray(indices)[order]
        gathered = np.empty((len(wanted), 3))
        offset = 0
        for chunk in self:
            low, high = np.searchsorted(wanted, [offset, offset + len(chunk)])
            gathered[order[low:high]] = chunk[wanted[low:high] - offset]
            offset += len(chunk)
        return gathered


@dataclass(frozen=True)
class Plane:
    """A reference plane: a point on it, a unit normal, and where it came from."""

    point: NDArray[np.float64]
    normal: NDArray[np.float64]
    inlier_fraction: float
    source: str  # "declared" or "fitted_dominant_plane"


@dataclass(frozen=True)
class Footprint:
    """One origin's grid and the measurements derived from it.

    Grids are indexed [i, j]: i runs along the first in-plane axis (the longer spread of
    the plane's own points), j along the second. `max_height_m` holds the highest point
    above the plane in each cell and NaN where nothing was seen.
    """

    plane: Plane
    basis: NDArray[np.float64]  # 2x3: first and second in-plane axes, unit vectors
    grid_origin: NDArray[np.float64]  # 3D point at the corner of cell [0, 0]
    cell_size_m: float
    observed: NDArray[np.bool_]
    on_plane: NDArray[np.bool_]
    max_height_m: NDArray[np.float64]
    point_count: int

    @property
    def cell_area_m2(self) -> float:
        return self.cell_size_m**2

    @property
    def observed_area_m2(self) -> float:
        """Ground area under any observed surface, seen from above."""
        return float(np.count_nonzero(self.observed)) * self.cell_area_m2

    @property
    def plane_area_m2(self) -> float:
        """Area of cells holding at least one point on the reference plane itself."""
        return float(np.count_nonzero(self.on_plane)) * self.cell_area_m2

    @property
    def length_m(self) -> float:
        """Region rectangle side along the first axis, measured on cell edges."""
        return self.observed.shape[0] * self.cell_size_m

    @property
    def width_m(self) -> float:
        return self.observed.shape[1] * self.cell_size_m

    @property
    def unknown_area_m2(self) -> float:
        """Unseen cells inside the region rectangle; nothing outside it is claimed."""
        return float(np.count_nonzero(~self.observed)) * self.cell_area_m2

    @property
    def highest_m(self) -> float:
        return float(np.nanmax(self.max_height_m))

    @property
    def lowest_m(self) -> float:
        return float(np.nanmin(self.max_height_m))


def fit_dominant_plane(
    points: ArrayLike | PointChunks,
    *,
    inlier_distance_m: float,
    iterations: int,
    sample_size: int,
    seed: int,
) -> Plane:
    """Find the plane holding the most points (RANSAC), then refit it by least squares.

    Candidate planes are scored on a seeded random subset of at most `sample_size`
    points. The winner is refitted on its inliers among all points: the normal is the
    smallest principal axis of their scatter, accumulated chunk by chunk.
    """
    chunks = _as_chunks(points)
    if not np.isfinite(inlier_distance_m) or inlier_distance_m <= 0:
        raise ValueError("Plane inlier distance must be positive and finite")
    rng = np.random.default_rng(seed)
    if chunks.total > sample_size:
        subset = chunks.take(rng.choice(chunks.total, size=sample_size, replace=False))
    else:
        subset = np.concatenate(list(chunks))

    best_count, best_point, best_normal = -1, None, None
    for _ in range(iterations):
        first, second, third = subset[rng.choice(len(subset), size=3, replace=False)]
        normal = np.cross(second - first, third - first)
        length = np.linalg.norm(normal)
        if length < 1e-12:
            continue  # the three points are on one line
        normal = normal / length
        count = int(np.count_nonzero(np.abs((subset - first) @ normal) <= inlier_distance_m))
        if count > best_count:
            best_count, best_point, best_normal = count, first, normal
    if best_normal is None:
        raise ValueError("Points do not span a plane")

    scatter = _Scatter(best_point)
    for chunk in chunks:
        scatter.add(chunk[np.abs((chunk - best_point) @ best_normal) <= inlier_distance_m])
    centre, axes = scatter.principal_axes()
    return Plane(
        point=centre,
        normal=axes[2],
        inlier_fraction=scatter.count / chunks.total,
        source="fitted_dominant_plane",
    )


def footprint(
    points: ArrayLike | PointChunks,
    plane: Plane,
    up: ArrayLike,
    *,
    cell_size_m: float,
    band_m: float,
    units: str = "metres",
) -> Footprint:
    """Grid the points over the plane and summarise each cell.

    `up` only chooses which side of the plane is positive height; the plane normal sets
    the direction. Points within `band_m` of the plane count as on the plane and alone
    set the in-plane axes, so objects standing on the plane cannot turn the grid. Three
    passes over the chunks: axes, then grid extent, then cell contents.
    """
    if units != "metres":
        raise ValueError(f"Footprint needs points in metres, got {units!r}")
    if not np.isfinite(cell_size_m) or cell_size_m <= 0:
        raise ValueError("Grid cell size must be positive and finite")
    if not np.isfinite(band_m) or band_m <= 0:
        raise ValueError("Plane band must be positive and finite")
    chunks = _as_chunks(points)
    up_vector = np.asarray(up, dtype=np.float64)
    if up_vector.shape != (3,) or not np.isfinite(up_vector).all() or not up_vector.any():
        raise ValueError("Up direction must be a finite, non-zero 3-vector")

    normal = plane.normal / np.linalg.norm(plane.normal)
    if normal @ up_vector < 0:
        normal = -normal
    oriented = Plane(plane.point, normal, plane.inlier_fraction, plane.source)

    scatter = _Scatter(plane.point)
    for chunk in chunks:
        heights, projected = _onto_plane(chunk, plane.point, normal)
        scatter.add(projected[np.abs(heights) <= band_m])
    if scatter.count < 3:
        raise ValueError("Fewer than 3 points lie on the reference plane")
    basis = _signed(scatter.principal_axes()[1][:2])

    minimum = np.full(2, np.inf)
    maximum = np.full(2, -np.inf)
    for chunk in chunks:
        if len(chunk):
            coordinates = _onto_plane(chunk, plane.point, normal)[1] @ basis.T
            minimum = np.minimum(minimum, coordinates.min(axis=0))
            maximum = np.maximum(maximum, coordinates.max(axis=0))
    shape = tuple(int(size) for size in np.floor((maximum - minimum) / cell_size_m) + 1)
    if shape[0] * shape[1] > MAX_GRID_CELLS:
        raise ValueError(
            f"Grid would need {shape[0] * shape[1]:,} cells (limit {MAX_GRID_CELLS:,}); "
            f"the points span {maximum[0] - minimum[0]:.1f} m by {maximum[1] - minimum[1]:.1f} m"
        )

    observed = np.zeros(shape, dtype=np.bool_)
    plane_cells = np.zeros(shape, dtype=np.bool_)
    max_height = np.full(shape, -np.inf)
    for chunk in chunks:
        heights, projected = _onto_plane(chunk, plane.point, normal)
        cells = np.floor((projected @ basis.T - minimum) / cell_size_m).astype(np.int64)
        observed[cells[:, 0], cells[:, 1]] = True
        on_plane = np.abs(heights) <= band_m
        plane_cells[cells[on_plane, 0], cells[on_plane, 1]] = True
        np.maximum.at(max_height, (cells[:, 0], cells[:, 1]), heights)
    max_height[~observed] = np.nan

    grid_origin = minimum @ basis + (plane.point @ normal) * normal
    return Footprint(
        plane=oriented,
        basis=basis,
        grid_origin=grid_origin,
        cell_size_m=float(cell_size_m),
        observed=observed,
        on_plane=plane_cells,
        max_height_m=max_height,
        point_count=chunks.total,
    )


class _Scatter:
    """Running count, mean and scatter matrix of 3D points, relative to a fixed reference."""

    def __init__(self, reference: NDArray) -> None:
        self.reference = np.asarray(reference, dtype=np.float64)
        self.count = 0
        self._sum = np.zeros(3)
        self._outer = np.zeros((3, 3))

    def add(self, points: NDArray) -> None:
        relative = points - self.reference
        self.count += len(relative)
        self._sum += relative.sum(axis=0)
        self._outer += relative.T @ relative

    def principal_axes(self) -> tuple[NDArray, NDArray]:
        """Centre and unit axes as rows: largest spread first, smallest (the normal) last."""
        if self.count < 3:
            raise ValueError("Fewer than 3 points lie on the plane")
        mean = self._sum / self.count
        covariance = self._outer / self.count - np.outer(mean, mean)
        _, vectors = np.linalg.eigh(covariance)  # eigenvalues ascending
        return self.reference + mean, vectors[:, ::-1].T


def _onto_plane(chunk: NDArray, point: NDArray, normal: NDArray) -> tuple[NDArray, NDArray]:
    """Signed height above the plane and the foot of each point on the plane."""
    heights = (chunk - point) @ normal
    return heights, chunk - np.outer(heights, normal)


def _signed(axes: NDArray) -> NDArray:
    """Sign each axis so its largest-magnitude component is positive."""
    return np.vstack([axis * np.sign(axis[np.argmax(np.abs(axis))]) for axis in axes])


def _as_chunks(points: ArrayLike | PointChunks) -> PointChunks:
    chunks = points if isinstance(points, PointChunks) else PointChunks.from_arrays([points])
    if chunks.total < 3:
        raise ValueError("Footprint needs at least 3 points")
    return chunks


def _checked_chunk(points: ArrayLike) -> NDArray[np.float64]:
    chunk = np.asarray(points, dtype=np.float64)
    if chunk.ndim != 2 or chunk.shape[1] != 3:
        raise ValueError("Points must be an Nx3 array")
    if not np.isfinite(chunk).all():
        raise ValueError("Points must all be finite")
    return chunk
