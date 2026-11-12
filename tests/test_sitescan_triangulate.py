"""Triangulation recovers known depth: two rays, matched features and a plane sweep over a rendered wall."""

import cv2
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from sitescan import triangulate
from sitescan.triangulate import sweep
from sitescan.types import Camera

CAMERA = Camera(200.0, 200.0, 79.5, 59.5, 160, 120)
WALL_M = 2.0


def pose(x=0.0, y=0.0, z=0.0, yaw_deg=0.0):
    matrix = np.eye(4)
    matrix[:3, :3] = Rotation.from_euler("y", yaw_deg, degrees=True).as_matrix()
    matrix[:3, 3] = x, y, z
    return matrix


@pytest.fixture(scope="module")
def texture():
    noise = np.random.default_rng(0).uniform(0, 255, (1024, 1024)).astype(np.float32)
    return cv2.normalize(cv2.GaussianBlur(noise, (0, 0), 2.0), None, 0, 255, cv2.NORM_MINMAX)


def render(texture, world_from_camera, camera=CAMERA, wall_m=WALL_M):
    """A grey image of a textured wall at z = wall_m, seen from an OpenCV camera."""
    rows, cols = np.mgrid[0 : camera.height, 0 : camera.width]
    rays = np.stack(
        [(cols - camera.cx) / camera.fx, (rows - camera.cy) / camera.fy, np.ones(rows.shape)], -1
    )
    rays = rays @ world_from_camera[:3, :3].T
    along = (wall_m - world_from_camera[2, 3]) / rays[..., 2]
    x = world_from_camera[0, 3] + along * rays[..., 0]
    y = world_from_camera[1, 3] + along * rays[..., 1]
    return cv2.remap(
        texture,
        (x * 200 + 512).astype(np.float32),
        (y * 200 + 512).astype(np.float32),
        cv2.INTER_LINEAR,
    ).astype(np.uint8)


def test_rays_through_projected_pixels_triangulate_back_to_the_points():
    points = np.array([[0.1, -0.2, 2.0], [-0.5, 0.3, 4.0]])
    a, b = pose(), pose(0.3, 0.0, 0.1, 5.0)
    uv_a, depth_a = triangulate.project(points, CAMERA, a)
    uv_b, _ = triangulate.project(points, CAMERA, b)
    np.testing.assert_allclose(depth_a, [2.0, 4.0])
    np.testing.assert_allclose(
        triangulate.triangulate(uv_a, uv_b, CAMERA, CAMERA, a, b), points, atol=1e-9
    )


def test_depth_error_follows_the_stereo_rule_for_side_by_side_cameras():
    point = np.array([[0.0, 0.0, 3.0]])
    angle = triangulate.parallax(point, pose(), pose(0.2))
    sigma = triangulate.depth_sigma(3.0, angle, 200.0, 1.0)
    assert sigma == pytest.approx(3.0**2 * 1.0 / (200.0 * 0.2), rel=0.01)


def test_epipolar_distance_is_zero_for_true_matches_and_the_offset_otherwise():
    points = np.array([[0.1, -0.2, 2.0], [-0.5, 0.3, 4.0]])
    a, b = pose(), pose(0.3)
    uv_a, _ = triangulate.project(points, CAMERA, a)
    uv_b, _ = triangulate.project(points, CAMERA, b)
    np.testing.assert_allclose(
        triangulate.epipolar_distance(uv_a, uv_b, CAMERA, CAMERA, a, b), 0, atol=1e-9
    )
    # A sideways camera move puts epipolar lines along rows, so a 3 px vertical shift is 3 px off.
    shifted = uv_b + [0.0, 3.0]
    np.testing.assert_allclose(
        triangulate.epipolar_distance(uv_a, shifted, CAMERA, CAMERA, a, b), 3.0
    )


def test_identical_images_match_every_feature_to_itself(texture):
    features = triangulate.detect(render(texture, pose()))
    first, second = triangulate.match(features, features)
    assert len(first) > 100 and np.array_equal(first, second)


def test_matched_features_on_a_wall_triangulate_to_its_depth(texture):
    a, b = pose(), pose(0.2)
    frame = triangulate.detect(render(texture, a))
    keyframe = triangulate.detect(render(texture, b))
    found = triangulate.triangulate_pair(frame, CAMERA, a, keyframe, CAMERA, b)
    assert len(found.depth_m) > 50
    assert np.median(found.depth_m) == pytest.approx(WALL_M, rel=0.01)
    assert np.median(found.sigma_m) == pytest.approx(WALL_M**2 / (200.0 * 0.2), rel=0.1)


def test_a_wrong_keyframe_pose_rejects_the_matches(texture):
    a, b = pose(), pose(0.2)
    frame = triangulate.detect(render(texture, a))
    keyframe = triangulate.detect(render(texture, b))
    wrong = pose(0.2, 0.2)  # the keyframe claims to be 20 cm higher than it was
    assert len(triangulate.triangulate_pair(frame, CAMERA, a, keyframe, CAMERA, wrong).depth_m) == 0


def test_merge_keeps_one_inverse_variance_depth_per_feature():
    first = triangulate.SparseDepth(
        np.array([[1.0, 1.0], [2.0, 2.0]]),
        np.array([2.0, 5.0]),
        np.array([0.1, 0.1]),
        np.array([7, 9]),
    )
    second = triangulate.SparseDepth(
        np.array([[1.0, 1.0]]), np.array([2.3]), np.array([0.2]), np.array([7])
    )
    merged = triangulate.merge([first, second])
    np.testing.assert_array_equal(merged.index, [7, 9])
    np.testing.assert_allclose(
        merged.depth_m, [(2.0 / 0.01 + 2.3 / 0.04) / (1 / 0.01 + 1 / 0.04), 5.0]
    )
    np.testing.assert_allclose(merged.sigma_m, [(1 / 0.01 + 1 / 0.04) ** -0.5, 0.1])
    assert len(triangulate.merge([]).depth_m) == 0


def keyframe_at(matrix):
    return triangulate.Keyframe(
        np.zeros((2, 2), np.uint8), CAMERA, matrix, triangulate.Features(None, None)
    )


def test_references_are_the_newest_usable_keyframes_or_those_nearest_a_baseline():
    window = [keyframe_at(pose(x)) for x in (0.0, 0.3, 0.6, 0.97, 1.0)]
    window.append(keyframe_at(pose(1.3, yaw_deg=40.0)))  # facing too far away
    here = pose(1.0)
    newest = triangulate.references(window, here, 2)
    assert [k.pose[0, 3] for k in newest] == [
        0.6,
        0.3,
    ]  # 1.0 and 0.97 are too close, 0.0 is 1 m away
    assert [k.pose[0, 3] for k in triangulate.references(window, here, 3, 0.62)][:2] == [0.3, 0.6]


def test_a_frame_joins_the_window_after_moving_a_keyframe_step(texture):
    triangulator = triangulate.Triangulator(keyframes=2)
    for x in (0.0, 0.05, 0.12, 0.25):
        triangulator.sparse(render(texture, pose(x)), CAMERA, pose(x))
    assert [k.pose[0, 3] for k in triangulator.window] == [
        0.12,
        0.25,
    ]  # 0.05 was too close; 0.0 left
    assert triangulator.typical_depth_m == pytest.approx(WALL_M, rel=0.02)


def test_census_bits_mark_neighbours_darker_than_the_centre():
    grey = np.array([[0, 0, 0], [0, 5, 9], [0, 0, 0]], np.uint8)
    codes = sweep.census(grey, radius=1)
    # Neighbours in row order, skipping the centre: seven darker, one (the 9 to the right) brighter.
    assert int(codes[1, 1]) == 0b11101111
    assert np.bitwise_count(codes[1, 1] ^ codes[1, 1]) == 0


def test_candidates_are_even_in_inverse_depth_or_banded_around_a_prior():
    depths = sweep.candidate_depths((2, 2), planes=5, near_m=0.5, far_m=10.0)
    np.testing.assert_allclose(np.diff(1 / depths[:, 0, 0]), (1 / 10 - 1 / 0.5) / 4, rtol=1e-6)
    prior = np.array([[1.0, np.nan], [2.0, 4.0]])
    banded = sweep.candidate_depths((2, 2), prior, planes=3, band=0.5)
    np.testing.assert_allclose(banded[:, 1, 1], 4.0 * np.exp([-0.5, 0.0, 0.5]), rtol=1e-6)
    np.testing.assert_allclose(
        banded[:, 0, 1], sweep.candidate_depths((2, 2), planes=3)[:, 0, 1]
    )  # no prior there


def test_plane_count_spaces_candidates_about_a_pixel_apart():
    references = [(None, CAMERA, pose(0.1))]
    expected = np.ceil(200.0 * 0.1 * (1 / sweep.NEAR_M - 1 / sweep.FAR_M))
    assert sweep.plane_count(CAMERA, references, pose()) == expected
    assert sweep.plane_count(CAMERA, [(None, CAMERA, pose(5.0))], pose()) == sweep.MAX_PLANES
    assert sweep.plane_count(CAMERA, references, pose(), np.full((2, 2), 2.0)) == sweep.MIN_PLANES


def test_semi_global_smoothing_lets_neighbours_outvote_a_noisy_pixel():
    costs = np.ones((5, 1, 9), np.float32)
    costs[2] = 0.0  # every pixel prefers candidate 2 ...
    costs[:, 0, 4] = [1, 1, 0.9, 1, 0]  # ... except one, which faintly prefers candidate 4
    assert costs.argmin(axis=0)[0, 4] == 4
    assert sweep.aggregate(costs, p1=0.5, p2=2.0).argmin(axis=0)[0, 4] == 2


def test_best_depth_refines_between_candidates_and_distrusts_the_range_ends():
    depths = np.array([1.0, 2.0, 4.0, 8.0])[:, None, None] * np.ones((1, 1, 3))
    aggregated = np.array([[9, 0, 9], [1, 9, 9], [4, 9, 9], [9, 9, 0]], np.float32)[:, None, :]
    aggregated[:, 0, 0] = [9, 4, 0, 1]  # cheapest at 4 m, leaning toward 8 m
    depth, confidence = sweep.best_depth(aggregated, depths)
    assert 4.0 < depth[0, 0] < 8.0 and confidence[0, 0] > 0
    assert (
        depth[0, 1] == 1.0 and confidence[0, 1] == 0
    )  # the nearest candidate: depth may be nearer still
    assert confidence[0, 2] == 0


@pytest.mark.parametrize("prior_m", [None, 2.2])
def test_a_sweep_finds_a_textured_wall_within_one_candidate(texture, prior_m):
    here, left, right = pose(), pose(0.2), pose(-0.2)
    references = [(render(texture, left), CAMERA, left), (render(texture, right), CAMERA, right)]
    prior = None if prior_m is None else np.full((CAMERA.height, CAMERA.width), prior_m)
    measured = sweep.sweep_depth(
        render(texture, here), CAMERA, here, references, prior=prior, scale=1.0
    )
    confident = measured.confidence >= 128
    assert measured.source == "sweep" and measured.camera == CAMERA
    assert confident.mean() > 0.8
    # Neighbouring candidates are about one pixel of disparity apart: z^2 / (f b) = 0.1 m at 2 m.
    error = np.abs(measured.depth_m[confident] - WALL_M)
    assert np.median(error) < 0.04 and np.percentile(error, 99) < 0.07


def test_a_sweep_at_half_size_reports_its_own_smaller_camera(texture):
    here, left = pose(), pose(0.2)
    measured = sweep.sweep_depth(
        render(texture, here), CAMERA, here, [(render(texture, left), CAMERA, left)]
    )
    assert measured.depth_m.shape == (60, 80) and measured.camera.width == 80
    assert measured.camera.cx == pytest.approx(39.5) and measured.camera.fx == pytest.approx(100.0)
