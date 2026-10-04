"""Contract tests for the demo generator: geometry helpers, data packing and page assembly."""

from __future__ import annotations

import base64
import json
import re

import numpy as np
import pytest

from tools.demos.geometry import (
    Intrinsics,
    backproject,
    camera_normals,
    depth_edges,
    render_points,
    surfel_covariance,
    to_world,
    top_down_grid,
    voxel_fuse,
)
from tools.demos.pack import encode_array, encode_positions
from tools.demos.page import EXTERNAL_RESOURCE, build_page

K = Intrinsics(width=64, height=48, fx=50.0, fy=40.0, cx=31.5, cy=23.5)


def test_backproject_recovers_known_point() -> None:
    depth = np.zeros((48, 64))
    depth[10, 20] = 2.0
    points, pixels = backproject(depth, K)
    assert pixels.tolist() == [[10, 20]]
    np.testing.assert_allclose(points[0], [(20 - 31.5) * 2.0 / 50.0, (10 - 23.5) * 2.0 / 40.0, 2.0])


def test_backproject_rejects_wrong_shape_and_skips_invalid() -> None:
    with pytest.raises(ValueError, match="does not match"):
        backproject(np.ones((10, 10)), K)
    depth = np.full((48, 64), np.nan)
    depth[0, 0] = 0.0
    assert backproject(depth, K)[0].shape == (0, 3)


def test_depth_edges_flags_only_the_jump() -> None:
    depth = np.ones((48, 64))
    depth[:, 32:] = 3.0
    edges = depth_edges(depth, relative_jump=0.1)
    assert edges[:, 31].all() and edges[:, 32].all()
    assert not edges[:, :31].any() and not edges[:, 33:].any()


def test_normals_of_a_facing_plane_point_back_at_the_camera() -> None:
    normals = camera_normals(np.full((48, 64), 2.0), K)
    np.testing.assert_allclose(normals[24, 32], [0.0, 0.0, -1.0], atol=1e-9)
    assert not normals[0].any() and not normals[:, -1].any()


def test_to_world_applies_rotation_and_translation() -> None:
    pose = np.eye(4)
    pose[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    pose[:3, 3] = [1.0, 2.0, 3.0]
    np.testing.assert_allclose(to_world(np.array([[1.0, 0.0, 0.0]]), pose), [[1.0, 3.0, 3.0]])
    with pytest.raises(ValueError):
        to_world(np.zeros((1, 3)), np.eye(3))


def test_voxel_fuse_averages_duplicates_and_drops_singletons() -> None:
    points = np.array([[0.01, 0.01, 0.01], [0.03, 0.03, 0.03], [0.5, 0.5, 0.5]])
    colours = np.array([[0, 0, 0], [200, 100, 50], [255, 255, 255]])
    normals = np.array([[0, 0, 1.0], [0, 0, 1.0], [1.0, 0, 0]])
    fused = voxel_fuse(points, colours, normals, voxel_m=0.05, min_count=2)
    np.testing.assert_allclose(fused["positions"], [[0.02, 0.02, 0.02]])
    assert fused["colours"].tolist() == [[100, 50, 25]]
    assert fused["counts"].tolist() == [2]
    with pytest.raises(ValueError):
        voxel_fuse(points, colours, normals, voxel_m=0.0)


def test_surfel_covariance_is_thin_along_the_normal() -> None:
    normal = np.array([[0.0, 0.6, 0.8]])
    six = surfel_covariance(normal, np.array([0.02]), np.array([0.002]))[0]
    cov = np.array([[six[0], six[1], six[2]], [six[1], six[3], six[4]], [six[2], six[4], six[5]]])
    np.testing.assert_allclose(cov @ normal[0], 0.002**2 * normal[0], atol=1e-12)
    tangent = np.array([1.0, 0.0, 0.0])
    np.testing.assert_allclose(cov @ tangent, 0.02**2 * tangent, atol=1e-12)


def test_top_down_grid_keeps_highest_point_and_marks_unseen() -> None:
    points = np.array([[0.0, 0.0, 0.1], [0.0, 0.0, 0.7], [0.25, 0.0, 0.2], [0.0, 0.0, 2.5]])
    colours = np.array([[1, 1, 1], [9, 9, 9], [5, 5, 5], [7, 7, 7]], dtype=np.uint8)
    grid = top_down_grid(points, colours, up_axis=2, cell_m=0.1, height_range=(0.0, 2.0))
    assert grid["height"].shape == (1, 3)
    assert grid["height"][0, 0] == pytest.approx(0.7)
    assert grid["colour"][0, 0].tolist() == [9, 9, 9]
    assert np.isnan(grid["height"][0, 1]) and not grid["observed"][0, 1]
    assert grid["counts"][0, 0] == 2


def test_position_packing_round_trips_within_quantisation() -> None:
    rng = np.random.default_rng(0)
    positions = rng.uniform(-2, 3, size=(500, 3))
    packed = encode_positions(positions)
    q = np.frombuffer(base64.b64decode(packed["b64"]), dtype="<u2").reshape(-1, 3)
    lo, hi = np.array(packed["min"]), np.array(packed["max"])
    restored = lo + q / 65535.0 * (hi - lo)
    assert np.abs(restored - positions).max() <= (hi - lo).max() / 65535.0
    raw = encode_array(np.array([1.5, -2.0], dtype=np.float32))
    assert raw["dtype"] == "f32" and np.frombuffer(base64.b64decode(raw["b64"]), "<f4").tolist() == [1.5, -2.0]


def test_page_is_self_contained_and_escapes_embedded_data() -> None:
    html = build_page("Demo", "One sentence.", "<main>hi</main>", {"label": "</script><b>"}, ["viewer.js"], "")
    assert not EXTERNAL_RESOURCE.search(html)
    payload = re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', html, re.DOTALL).group(1)
    assert json.loads(payload)["label"] == "</script><b>"
    assert "<title>Demo</title>" in html


def test_render_points_keeps_the_nearest_point_per_pixel() -> None:
    k = Intrinsics(width=8, height=6, fx=4.0, fy=4.0, cx=3.5, cy=2.5)
    pose = np.eye(4)
    points = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
    colours = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8)
    image = render_points(points, colours, pose, k, radius_px=0, background=(1, 2, 3))
    assert image[2, 4].tolist() == [0, 255, 0]
    assert image[0, 0].tolist() == [1, 2, 3]
    assert not (image == [0, 0, 255]).all(axis=2).any()


def test_page_refuses_external_scripts() -> None:
    with pytest.raises(ValueError, match="external resource"):
        build_page("Bad", "x", '<script src="https://cdn.example.com/x.js"></script>', {}, [], "")

