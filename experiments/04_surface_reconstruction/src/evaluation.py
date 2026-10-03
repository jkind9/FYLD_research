"""Exact bidirectional point distances, with no registration or scale fitting."""

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import cKDTree

# Engineering scheduling only: every point is scored exactly, on one CPU worker.
QUERY_BATCH = 100_000


def validate_points(points: NDArray, *, empty: bool = False) -> NDArray:
    values = np.asarray(points, dtype=np.float64)
    if (
        values.ndim != 2
        or values.shape[1] != 3
        or not np.isfinite(values).all()
        or (not empty and len(values) == 0)
    ):
        raise ValueError(
            "Expected finite nonempty Nx3 points"
            if not empty
            else "Expected finite Nx3 points"
        )
    return values


def nearest(tree: cKDTree, points: NDArray) -> NDArray:
    distances = np.empty(len(points), dtype=np.float64)
    for start in range(0, len(points), QUERY_BATCH):
        end = start + QUERY_BATCH
        distances[start:end] = tree.query(
            points[start:end], k=1, eps=0, p=2, workers=1
        )[0]
    return distances


def distance_summary(distances: NDArray) -> dict:
    values = np.asarray(distances, dtype=np.float64)
    if (
        values.ndim != 1
        or not len(values)
        or not np.isfinite(values).all()
        or np.any(values < 0)
    ):
        raise ValueError("Distances must be nonempty finite nonnegative values")
    return {
        "points": len(values),
        "mean_m": float(values.mean()),
        "rmse_m": float(np.sqrt(np.mean(values**2))),
        "max_m": float(values.max()),
    }


class DistanceTotals:
    """Scalar accumulation avoids retaining distance arrays across observations."""

    def __init__(self) -> None:
        self.count = 0
        self.total = 0.0
        self.square_total = 0.0
        self.maximum = 0.0

    def add(self, distances: NDArray) -> None:
        if len(distances):
            checked = distance_summary(distances)
            self.count += len(distances)
            self.total += float(distances.sum())
            self.square_total += float(np.sum(distances**2))
            self.maximum = max(self.maximum, checked["max_m"])

    def summary(self) -> dict:
        if not self.count:
            raise ValueError("Cannot score an empty reconstruction")
        return {
            "points": self.count,
            "mean_m": self.total / self.count,
            "rmse_m": float(np.sqrt(self.square_total / self.count)),
            "max_m": self.maximum,
        }


class SurfaceScorer:
    """Reference-only evaluator; reconstruction can be processed one shard at a time."""

    def __init__(self, reference: NDArray, threshold_m: float) -> None:
        if not np.isfinite(threshold_m) or threshold_m <= 0:
            raise ValueError("Reporting threshold must be positive finite metres")
        self.reference = np.array(validate_points(reference), copy=True)
        self.reference.setflags(write=False)
        self.threshold_m = float(threshold_m)
        self.tree = cKDTree(self.reference)
        self.reference_distances = np.full(len(self.reference), np.inf)
        self.accuracy = DistanceTotals()
        self.within_threshold = 0

    def distances(self, points: NDArray) -> NDArray:
        return nearest(self.tree, validate_points(points, empty=True))

    def observe(self, points: NDArray, *, update_reference: bool = True) -> NDArray:
        values = validate_points(points, empty=True)
        distances = self.distances(values)
        if len(values):
            if update_reference:
                tree = cKDTree(values)
                # Update by batch: memory does not grow with the number of frames.
                for start in range(0, len(self.reference), QUERY_BATCH):
                    end = start + QUERY_BATCH
                    incoming = nearest(tree, self.reference[start:end])
                    self.reference_distances[start:end] = np.minimum(
                        self.reference_distances[start:end], incoming
                    )
            self.accuracy.add(distances)
            self.within_threshold += int(
                np.count_nonzero(distances <= self.threshold_m)
            )
        return distances

    def cover_accumulated(self, points: NDArray) -> None:
        """Desktop batch equivalent of shard minima; cloud memory grows with inputs."""
        values = validate_points(points)
        if len(values) != self.accuracy.count:
            raise ValueError("Accumulated point count differs from scored observations")
        self.reference_distances = nearest(cKDTree(values), self.reference)

    def summary(self) -> dict:
        accuracy = self.accuracy.summary()
        covered = int(np.count_nonzero(self.reference_distances <= self.threshold_m))
        return {
            "accuracy": accuracy,
            "reconstruction_points": accuracy["points"],
            "reconstruction_within_threshold_fraction": self.within_threshold
            / accuracy["points"],
            "reference_distance": distance_summary(self.reference_distances),
            "reference_points": len(self.reference),
            "reference_covered_points": covered,
            "reference_coverage_fraction": covered / len(self.reference),
            "threshold_m": self.threshold_m,
            "coverage_population": "all published reference vertices; includes unseen regions",
            "coverage_weighting": "vertex count, not surface area",
            "alignment": "fixed publisher conversion; no fitted transform or scale",
        }
