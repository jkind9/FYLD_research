"""Known-shape contracts for the grid footprint measurement.

Every expected value below comes from the shape definition, not from the projection code.
Each shape has one sample at its corner (0, 0) and all other samples at 0.005 + 0.01k, so
with 0.05 m cells measured from the corner no sample lies on a cell edge.
"""

import importlib

import numpy as np
import pytest

measure = importlib.import_module("experiments.05_birds_eye_mapping.measure")

CELL_M = 0.05
UP = np.array([0.0, 0.0, 1.0])
FLOOR = measure.Plane(point=np.zeros(3), normal=UP, inlier_fraction=1.0, source="declared")


def _rectangle(width_m=2.0, length_m=3.0, z_m=0.0, *, hole=None):
    """Interior lattice on [0, width) x [0, length) at height z, plus the exact corner."""
    xs = 0.005 + 0.01 * np.arange(round(width_m / 0.01))
    ys = 0.005 + 0.01 * np.arange(round(length_m / 0.01))
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="ij")
    keep = np.ones(grid_x.shape, dtype=bool)
    if hole is not None:
        (x0, x1), (y0, y1) = hole
        keep &= ~((grid_x >= x0) & (grid_x < x1) & (grid_y >= y0) & (grid_y < y1))
    points = np.column_stack(
        (grid_x[keep], grid_y[keep], np.full(int(keep.sum()), z_m))
    )
    return np.vstack(([[0.0, 0.0, z_m]], points))


def _board(x0, y0, side_m=0.5, height_m=0.8):
    xs = x0 + 0.005 + 0.01 * np.arange(round(side_m / 0.01))
    ys = y0 + 0.005 + 0.01 * np.arange(round(side_m / 0.01))
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="ij")
    return np.column_stack((grid_x.ravel(), grid_y.ravel(), np.full(grid_x.size, height_m)))


def _footprint(points, plane=FLOOR, up=UP):
    return measure.footprint(points, plane, up, cell_size_m=CELL_M, band_m=0.02)


def test_flat_rectangle_measures_exact_area_and_sides():
    result = _footprint(_rectangle())

    assert result.observed.shape == (60, 40)  # first axis is the longer side
    assert result.observed_area_m2 == pytest.approx(6.00, abs=1e-9)
    assert result.plane_area_m2 == pytest.approx(6.00, abs=1e-9)
    assert result.unknown_area_m2 == pytest.approx(0.00, abs=1e-9)
    assert result.length_m == pytest.approx(3.00, abs=1e-9)
    assert result.width_m == pytest.approx(2.00, abs=1e-9)


def test_hole_is_unknown_not_empty_ground():
    result = _footprint(_rectangle(hole=((0.5, 1.5), (1.0, 2.0))))

    assert result.observed_area_m2 == pytest.approx(5.00, abs=1e-9)
    assert result.unknown_area_m2 == pytest.approx(1.00, abs=1e-9)
    assert (result.length_m, result.width_m) == pytest.approx((3.00, 2.00), abs=1e-9)
    assert np.isnan(result.max_height_m[30, 20])  # a cell in the hole stays unseen


def test_rotated_tilted_rectangle_with_a_fitted_plane():
    yaw, tilt = np.radians(30.0), np.radians(20.0)
    rotate_z = np.array(
        [[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]
    )
    rotate_x = np.array(
        [[1, 0, 0], [0, np.cos(tilt), -np.sin(tilt)], [0, np.sin(tilt), np.cos(tilt)]]
    )
    rotation = rotate_x @ rotate_z
    points = _rectangle() @ rotation.T + np.array([4.0, -2.0, 1.0])
    plane = measure.fit_dominant_plane(
        points, inlier_distance_m=0.02, iterations=500, sample_size=50_000, seed=0
    )

    result = _footprint(points, plane, up=rotation @ UP)

    perimeter_m = 2 * (2.0 + 3.0)
    assert abs(result.observed_area_m2 - 6.00) <= perimeter_m * CELL_M
    assert result.length_m == pytest.approx(3.00, abs=2 * CELL_M)
    assert result.width_m == pytest.approx(2.00, abs=2 * CELL_M)


@pytest.mark.parametrize("board_corner", [(0.75, 1.25), (0.0, 0.0)], ids=["centred", "corner"])
def test_board_above_the_floor_keeps_area_and_reports_its_height(board_corner):
    points = np.vstack((_rectangle(), _board(*board_corner)))

    result = _footprint(points)

    assert result.observed.shape == (60, 40)  # the board cannot turn the grid
    assert result.observed_area_m2 == pytest.approx(6.00, abs=1e-9)
    assert result.plane_area_m2 == pytest.approx(6.00, abs=1e-9)
    assert result.highest_m == pytest.approx(0.80, abs=0.01)


def test_ransac_finds_a_noisy_floor_among_clutter_and_repeats_for_a_seed():
    rng = np.random.default_rng(11)
    floor = np.column_stack(
        (rng.uniform(0, 4, 7000), rng.uniform(0, 3, 7000), rng.normal(0, 0.002, 7000))
    )
    clutter = rng.uniform([0, 0, 0.1], [4, 3, 1.5], size=(3000, 3))
    points = np.vstack((floor, clutter))

    first = measure.fit_dominant_plane(
        points, inlier_distance_m=0.02, iterations=500, sample_size=50_000, seed=0
    )
    again = measure.fit_dominant_plane(
        points, inlier_distance_m=0.02, iterations=500, sample_size=50_000, seed=0
    )

    angle = np.degrees(np.arccos(min(1.0, abs(float(first.normal @ UP)))))
    assert angle < 1.0
    np.testing.assert_array_equal(first.normal, again.normal)
    np.testing.assert_array_equal(first.point, again.point)
    assert first.source == "fitted_dominant_plane"


@pytest.mark.parametrize(
    "points,units,reason",
    [
        (np.empty((0, 3)), "metres", "at least 3"),
        (np.array([[0, 0, 0], [1, 0, 0], [np.nan, 1, 0]]), "metres", "finite"),
        (np.zeros((5, 2)), "metres", "Nx3"),
        (_rectangle(), "millimetres", "metres"),
    ],
)
def test_bad_points_or_units_are_refused(points, units, reason):
    with pytest.raises(ValueError, match=reason):
        measure.footprint(points, FLOOR, UP, cell_size_m=CELL_M, band_m=0.02, units=units)


@pytest.mark.parametrize("cell_size_m", [0.0, -0.05, np.inf, np.nan])
def test_cell_size_must_be_positive_and_finite(cell_size_m):
    with pytest.raises(ValueError, match="cell size"):
        measure.footprint(_rectangle(), FLOOR, UP, cell_size_m=cell_size_m, band_m=0.02)


def test_up_pointing_below_the_plane_flips_heights_to_stay_positive():
    points = np.vstack((_rectangle(), _board(0.75, 1.25)))
    flipped = measure.Plane(point=np.zeros(3), normal=-UP, inlier_fraction=1.0, source="declared")

    result = _footprint(points, flipped, up=UP)

    assert result.highest_m == pytest.approx(0.80, abs=0.01)
    np.testing.assert_allclose(result.plane.normal, UP)


def test_preview_draws_unseen_cells_grey_and_states_its_scale(tmp_path):
    from PIL import Image

    preview = importlib.import_module("experiments.05_birds_eye_mapping.preview")
    result = _footprint(
        np.vstack((_rectangle(hole=((0.5, 1.5), (1.0, 2.0))), _board(0.0, 0.0)))
    )

    scale = preview.footprint_preview(
        result.observed, result.max_height_m, result.cell_size_m, tmp_path / "map.png"
    )

    with Image.open(tmp_path / "map.png") as image:
        step = scale["pixels_per_cell"]
        assert image.getpixel((20 * step + 1, 30 * step + 1)) == preview.UNSEEN_GREY
        assert image.getpixel((1, 1))[2] < 60  # board corner: highest cell is yellow
        assert image.width >= 40 * step and image.height >= 60 * step
    assert scale["colour_top_m"] == pytest.approx(0.80, abs=0.01)


def test_preview_marks_cells_whose_top_is_below_the_plane(tmp_path):
    """A floor seen under a desk-top plane must not look like the plane itself."""
    from PIL import Image

    preview = importlib.import_module("experiments.05_birds_eye_mapping.preview")
    observed = np.ones((2, 2), dtype=bool)
    heights = np.array([[0.0, -0.7], [0.4, 0.0]])

    scale = preview.footprint_preview(observed, heights, CELL_M, tmp_path / "map.png")

    step = scale["pixels_per_cell"]
    with Image.open(tmp_path / "map.png") as image:
        assert image.getpixel((step + 1, 1)) == preview.BELOW_PLANE
        assert image.getpixel((1, 1)) != preview.BELOW_PLANE


def test_streamed_chunks_give_exactly_the_in_memory_result():
    """Reading points one frame at a time must not change any grid cell."""
    points = np.vstack((_rectangle(hole=((0.5, 1.5), (1.0, 2.0))), _board(0.0, 0.0)))
    parts = np.array_split(points, 3)
    chunks = measure.PointChunks.from_arrays(parts)

    streamed = measure.footprint(chunks, FLOOR, UP, cell_size_m=CELL_M, band_m=0.02)
    whole = _footprint(points)

    np.testing.assert_array_equal(streamed.observed, whole.observed)
    np.testing.assert_array_equal(streamed.on_plane, whole.on_plane)
    np.testing.assert_allclose(streamed.max_height_m, whole.max_height_m, equal_nan=True)
    assert streamed.point_count == len(points)
    plane_a = measure.fit_dominant_plane(
        chunks, inlier_distance_m=0.02, iterations=200, sample_size=5000, seed=3
    )
    plane_b = measure.fit_dominant_plane(
        points, inlier_distance_m=0.02, iterations=200, sample_size=5000, seed=3
    )
    np.testing.assert_allclose(abs(plane_a.normal @ plane_b.normal), 1.0, atol=1e-12)
    assert plane_a.inlier_fraction == plane_b.inlier_fraction


def test_chunk_with_a_wrong_point_count_is_refused():
    chunks = measure.PointChunks([lambda: np.zeros((4, 3))], [5])
    with pytest.raises(ValueError, match="declared 5"):
        measure.footprint(chunks, FLOOR, UP, cell_size_m=CELL_M, band_m=0.02)


def test_a_grid_larger_than_the_cell_limit_is_refused():
    # Two stray points 400 m away in different directions span about 400 m x 280 m.
    far = np.vstack((_rectangle(), [[400.0, 0.0, 0.0], [0.0, 400.0, 0.0]]))
    with pytest.raises(ValueError, match="cells"):
        measure.footprint(far, FLOOR, UP, cell_size_m=CELL_M, band_m=0.02)
