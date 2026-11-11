"""Chunk loading and streaming scatter state retained for mapping experiments."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray


class PointChunks:
    """Nx3 metre points held as chunks and loaded one at a time by their loaders."""

    def __init__(self, loaders: Sequence[Callable[[], ArrayLike]], counts: Sequence[int]) -> None:
        if len(loaders) != len(counts):
            raise ValueError("Each point chunk needs exactly one declared point count")
        self._sources = tuple(loaders)
        self.counts = tuple(int(count) for count in counts)

    @classmethod
    def from_arrays(cls, arrays: Sequence[ArrayLike]) -> PointChunks:
        """An in-memory chunk source retaining each array and its point count."""
        validated = [_checked_chunk(array) for array in arrays]
        sources = [lambda array=array: array for array in validated]
        return cls(sources, [len(array) for array in validated])

    @property
    def total(self) -> int:
        return sum(self.counts)

    def __iter__(self) -> Iterator[NDArray[np.float64]]:
        """Checked point arrays loaded one at a time."""
        for source, declared_count in zip(self._sources, self.counts, strict=True):
            array = _checked_chunk(source())
            if len(array) != declared_count:
                raise ValueError(
                    f"A point chunk holds {len(array)} points but declared {declared_count}"
                )
            yield array

    def take(self, indices: NDArray[np.int64]) -> NDArray[np.float64]:
        """Selected global points in the requested order."""
        order = np.argsort(indices, kind="stable")
        selected = np.asarray(indices)[order]
        result = np.empty((len(selected), 3))
        start = 0
        for array in self:
            first, last = np.searchsorted(selected, [start, start + len(array)])
            result[order[first:last]] = array[selected[first:last] - start]
            start += len(array)
        return result


class _Scatter:
    """Running count, mean and scatter matrix of 3D points, relative to a fixed reference."""

    def __init__(self, reference: NDArray) -> None:
        """Retain a reference and the moments accumulated over incoming chunks."""
        self.reference = np.asarray(reference, dtype=np.float64)
        self.count = 0
        self._sum = np.zeros(3)
        self._outer = np.zeros((3, 3))

    def add(self, points: NDArray) -> None:
        """Accumulate point moments relative to the fixed reference."""
        local = points - self.reference
        self.count += len(local)
        self._sum += local.sum(axis=0)
        self._outer += local.T @ local

    def principal_axes(self) -> tuple[NDArray, NDArray]:
        """Centre and unit axes as rows: largest spread first, smallest (the normal) last."""
        if self.count < 3:
            raise ValueError("Fewer than 3 points lie on the plane")
        mean = self._sum / self.count
        _, vectors = np.linalg.eigh(self._outer / self.count - np.outer(mean, mean))
        return self.reference + mean, vectors[:, ::-1].T


def _as_chunks(points: ArrayLike | PointChunks) -> PointChunks:
    """A checked experimental chunk source with at least three points."""
    source = points if isinstance(points, PointChunks) else PointChunks.from_arrays([points])
    if source.total < 3:
        raise ValueError("Footprint needs at least 3 points")
    return source


def _checked_chunk(points: ArrayLike) -> NDArray[np.float64]:
    """A finite Nx3 float64 array checked at the experiment boundary."""
    array = np.asarray(points, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("Points must be an Nx3 array")
    if not np.isfinite(array).all():
        raise ValueError("Points must all be finite")
    return array
