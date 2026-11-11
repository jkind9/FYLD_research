"""Plane fits and footprint grids preserve site dimensions and observed area."""

import numpy as np
import pytest

from sitescan import mapping


def rectangle():
    x, y = np.meshgrid(np.arange(12) * 0.1, np.arange(8) * 0.1)
    return np.c_[x.ravel(), y.ravel(), np.zeros(x.size)]


@pytest.mark.parametrize("sample_size", [30, 1000])
def test_plane_fit_is_seeded_and_refits_the_dominant_plane(sample_size):
    points = np.vstack([rectangle(), [[0.5, 0.5, 1.0]]])
    first = mapping.fit_dominant_plane(points, iterations=40, sample_size=sample_size, seed=2)
    second = mapping.fit_dominant_plane(points, iterations=40, sample_size=sample_size, seed=2)
    np.testing.assert_array_equal(first.point, second.point)
    np.testing.assert_array_equal(first.normal, second.normal)
    assert abs(first.normal[2]) == pytest.approx(1.0)
    assert first.inlier_fraction == pytest.approx(96 / 97)


@pytest.mark.parametrize("normal", [[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
def test_footprint_orients_height_towards_up_and_keeps_unknown_cells(normal):
    plane = mapping.Plane(np.zeros(3), np.array(normal), 1.0, "declared")
    points = np.vstack([rectangle(), [[1.8, 1.5, 1.0]]])
    measured = mapping.footprint(
        points, plane, np.array([0.0, 0.0, 1.0]), cell_size_m=0.1, band_m=0.02
    )
    assert measured.highest_m == pytest.approx(1.0)
    assert measured.lowest_m == pytest.approx(0.0)
    assert measured.unknown_area_m2 > 0
    assert measured.observed_area_m2 >= measured.plane_area_m2
    assert measured.point_count == 97


def test_site_measurement_reports_the_existing_summary_fields():
    measured = mapping.measure_site(
        rectangle(), [[0.0, 0.0, 1.0]], min_points=3, cell_size_m=0.1, iterations=40
    )
    assert set(measured) == {
        "observed_area_m2",
        "plane_area_m2",
        "length_m",
        "width_m",
        "highest_m",
        "plane_normal",
    }
    assert measured["length_m"] > measured["width_m"] > 0
    assert measured["highest_m"] == pytest.approx(0.0)


def test_site_measurement_skips_short_or_degenerate_surfaces():
    assert "skipped" in mapping.measure_site(np.empty((0, 3)), [])
    line = np.c_[np.arange(20), np.zeros((20, 2))]
    assert "skipped" in mapping.measure_site(line, [[0.0, 0.0, 1.0]], min_points=3, iterations=10)
