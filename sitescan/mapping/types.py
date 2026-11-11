"""Plane and footprint records used within the mapping stage."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Plane:
    """A point, normal and measured support for the reference plane."""

    point: np.ndarray
    normal: np.ndarray
    inlier_fraction: float
    source: str


@dataclass(frozen=True)
class Footprint:
    """Observed cells and heights on a metric plane-aligned grid."""

    plane: Plane
    basis: np.ndarray
    grid_origin: np.ndarray
    cell_size_m: float
    observed: np.ndarray
    on_plane: np.ndarray
    max_height_m: np.ndarray
    point_count: int

    @property
    def cell_area_m2(self) -> float:
        """The area covered by one square grid cell."""
        return self.cell_size_m**2

    @property
    def observed_area_m2(self) -> float:
        """Area under cells containing any observed surface."""
        return float(np.count_nonzero(self.observed)) * self.cell_area_m2

    @property
    def plane_area_m2(self) -> float:
        """Area of cells with observations inside the reference plane band."""
        return float(np.count_nonzero(self.on_plane)) * self.cell_area_m2

    @property
    def length_m(self) -> float:
        """Extent along the first grid axis, measured at cell edges."""
        return self.observed.shape[0] * self.cell_size_m

    @property
    def width_m(self) -> float:
        """Extent along the second grid axis, measured at cell edges."""
        return self.observed.shape[1] * self.cell_size_m

    @property
    def unknown_area_m2(self) -> float:
        """Unobserved cell area within the grid rectangle."""
        return float(np.count_nonzero(~self.observed)) * self.cell_area_m2

    @property
    def highest_m(self) -> float:
        """Largest observed signed height above the oriented reference plane."""
        return float(np.nanmax(self.max_height_m))

    @property
    def lowest_m(self) -> float:
        """Smallest observed signed height above the oriented reference plane."""
        return float(np.nanmin(self.max_height_m))
