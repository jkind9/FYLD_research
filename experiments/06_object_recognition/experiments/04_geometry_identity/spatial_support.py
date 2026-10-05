"""Immutable empirical 3D support summaries for later association tests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

DEFAULT_REGULARISATION_M2 = 1e-6
DEFAULT_MIN_SAMPLES = 4
RANK_TOLERANCE = 1e-10


def _tuple3(values: np.ndarray) -> tuple[float, float, float]:
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def _matrix_tuple(values: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in values)


@dataclass(frozen=True)
class SupportSummary:
    """A finite empirical support with an explicitly regularised covariance."""

    mean_m: tuple[float, float, float]
    covariance_m2: tuple[tuple[float, ...], ...]
    sample_count: int
    regularisation_m2: float
    min_samples_for_distance: int
    coordinate_frame: str
    world_id: str
    segment_id: str
    pose_revision_id: str
    rank: int

    def __post_init__(self) -> None:
        try:
            mean = np.asarray(self.mean_m, dtype=float)
            covariance = np.asarray(self.covariance_m2, dtype=float)
            regularisation = float(self.regularisation_m2)
        except (TypeError, ValueError) as error:
            raise ValueError("Support numeric fields are invalid") from error
        if mean.shape != (3,) or not np.isfinite(mean).all():
            raise ValueError("Support mean must contain three finite coordinates")
        if covariance.shape != (3, 3) or not np.isfinite(covariance).all():
            raise ValueError("Support covariance must be a finite 3x3 matrix")
        if not np.allclose(covariance, covariance.T):
            raise ValueError("Support covariance must be symmetric")
        if (
            not isinstance(self.sample_count, int)
            or isinstance(self.sample_count, bool)
            or self.sample_count < 1
            or not isinstance(self.rank, int)
            or isinstance(self.rank, bool)
            or self.rank not in {0, 1, 2, 3}
            or self.rank > min(3, self.sample_count - 1)
        ):
            raise ValueError("Support count and rank are invalid")
        if regularisation <= 0.0 or not np.isfinite(regularisation):
            raise ValueError("Support regularisation must be positive and finite")
        if (
            not isinstance(self.min_samples_for_distance, int)
            or isinstance(self.min_samples_for_distance, bool)
            or self.min_samples_for_distance < 1
        ):
            raise ValueError("Minimum sample count must be positive")
        try:
            eigenvalues = np.linalg.eigvalsh(covariance)
        except np.linalg.LinAlgError as error:
            raise ValueError("Support covariance must be positive definite") from error
        if not np.all(eigenvalues > 0.0):
            raise ValueError("Support covariance must be positive definite")
        if any(not isinstance(value, str) or not value.strip() for value in (
            self.coordinate_frame, self.world_id, self.segment_id, self.pose_revision_id
        )):
            raise ValueError("Support lineage fields must be non-empty strings")

    def squared_mahalanobis(
        self, point_m: Iterable[float]
    ) -> float | None:
        """Return squared distance, or ``None`` when support is insufficient."""
        try:
            point = np.asarray(tuple(point_m), dtype=float)
        except (TypeError, ValueError) as error:
            raise ValueError("Point must contain three finite coordinates") from error
        if point.shape != (3,) or not np.isfinite(point).all():
            raise ValueError("Point must contain three finite coordinates")
        if (
            self.sample_count < self.min_samples_for_distance
            or self.rank < 3
        ):
            return None
        delta = point - np.asarray(self.mean_m, dtype=float)
        covariance = np.asarray(self.covariance_m2, dtype=float)
        value = float(delta @ np.linalg.solve(covariance, delta))
        return max(0.0, value)


def summarise(
    samples_m: Iterable[Iterable[float]] | np.ndarray,
    *,
    regularisation_m2: float = DEFAULT_REGULARISATION_M2,
    min_samples_for_distance: int = DEFAULT_MIN_SAMPLES,
    coordinate_frame: str,
    world_id: str,
    segment_id: str,
    pose_revision_id: str,
) -> SupportSummary:
    """Summarise finite 3D samples without mutating the caller's array."""
    try:
        regularisation = float(regularisation_m2)
    except (TypeError, ValueError) as error:
        raise ValueError("Covariance regularisation must be positive and finite") from error
    if regularisation <= 0.0 or not np.isfinite(regularisation):
        raise ValueError("Covariance regularisation must be positive and finite")
    if (
        not isinstance(min_samples_for_distance, int)
        or isinstance(min_samples_for_distance, bool)
        or min_samples_for_distance < 1
    ):
        raise ValueError("Minimum sample count must be positive")
    try:
        samples = np.asarray(tuple(tuple(row) for row in samples_m), dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("Support must contain finite 3D samples") from error
    if samples.ndim != 2 or samples.shape[1:] != (3,) or not samples.size:
        raise ValueError("Support must contain at least one 3D sample")
    if not np.isfinite(samples).all():
        raise ValueError("Support samples must be finite")
    mean = samples.mean(axis=0)
    centred = samples - mean
    covariance = (centred.T @ centred) / max(samples.shape[0] - 1, 1)
    covariance = covariance + np.eye(3, dtype=float) * regularisation
    rank = int(np.linalg.matrix_rank(centred, tol=RANK_TOLERANCE))
    return SupportSummary(
        mean_m=_tuple3(mean),
        covariance_m2=_matrix_tuple(covariance),
        sample_count=int(samples.shape[0]),
        regularisation_m2=regularisation,
        min_samples_for_distance=int(min_samples_for_distance),
        coordinate_frame=coordinate_frame,
        world_id=world_id,
        segment_id=segment_id,
        pose_revision_id=pose_revision_id,
        rank=rank,
    )
