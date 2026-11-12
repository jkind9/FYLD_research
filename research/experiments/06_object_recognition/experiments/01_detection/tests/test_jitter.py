"""Task45 Part B contract: warp, depth timing, interpolation, linking and jitter."""

import importlib
import math

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter
from scipy.spatial.transform import Rotation

from experiments.shared.contracts import Calibration

jitter = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.jitter"
)
CAMERA = Calibration(640, 480, 525.0, 525.0, 319.5, 239.5, "x-right_y-down_z-forward")
SEED = 20261005


def _pose(x=0.0, y=0.0, z=0.0, rotation_deg=(0.0, 0.0, 0.0)):
    matrix = np.eye(4)
    matrix[:3, :3] = Rotation.from_euler("xyz", rotation_deg, degrees=True).as_matrix()
    matrix[:3, 3] = (x, y, z)
    return matrix


# --- warp and depth timing -----------------------------------------------------------


def test_warp_follows_camera_to_world_convention():
    world = jitter.backproject_pixel(319.5, 239.5, 1.0, CAMERA, _pose())
    u, v = jitter.project_world(world, CAMERA, _pose(x=0.1))
    assert u == pytest.approx(267.0, abs=1e-9) and v == pytest.approx(239.5, abs=1e-9)
    wrong_u, _ = jitter.project_world(world, CAMERA, np.linalg.inv(_pose(x=0.1)))
    assert abs(wrong_u - 267.0) > 50


def _plane_depth(colour_pose, depth_pose):
    """Depth image at depth time of the plane z = 1 m in the colour-time camera."""
    v, u = np.mgrid[0:480, 0:640].astype(float)
    rays = np.stack(((u - 319.5) / 525, (v - 239.5) / 525, np.ones_like(u)), axis=-1)
    to_colour = np.linalg.inv(colour_pose) @ depth_pose
    origin = to_colour[:3, 3]
    direction = rays @ to_colour[:3, :3].T
    scale = (1.0 - origin[2]) / direction[..., 2]
    return scale, np.isfinite(scale) & (scale > 0)


def test_depth_moved_to_colour_time_removes_timing_error():
    colour = _pose()
    depth_time = _pose(rotation_deg=(0.0, 1.0, 0.0))
    depth, valid = _plane_depth(colour, depth_time)
    moved, moved_valid = jitter.depth_to_colour_time(
        depth, valid, CAMERA, depth_time, colour
    )
    box = [280, 200, 360, 280]
    stats = jitter.centre_depth(moved, moved_valid, box)
    assert stats["median"] == pytest.approx(1.0, abs=1e-12)
    u, v = 320.0, 240.0
    after = _pose(x=0.1)
    predicted = jitter.project_world(
        jitter.backproject_pixel(u, v, stats["median"], CAMERA, colour), CAMERA, after
    )
    truth = jitter.project_world(
        jitter.backproject_pixel(u, v, 1.0, CAMERA, colour), CAMERA, after
    )
    assert np.allclose(predicted, truth, atol=1e-6)
    wrong = jitter.project_world(
        jitter.backproject_pixel(u, v, stats["median"], CAMERA, depth_time),
        CAMERA,
        after,
    )
    assert np.linalg.norm(np.subtract(wrong, truth)) > 5


def test_centre_depth_flags_sparse_and_spread_windows():
    depth = np.full((480, 640), 1.0)
    valid = np.zeros((480, 640), dtype=bool)
    valid[230:235, 310:313] = True
    stats = jitter.centre_depth(depth, valid, [280, 200, 360, 280])
    assert stats["valid_pixels"] == 15 and stats["flag_sparse"] is True
    empty = jitter.centre_depth(depth, np.zeros_like(valid), [280, 200, 360, 280])
    assert empty["median"] is None and empty["reason"]


# --- interpolation ---------------------------------------------------------------------


def test_interpolation_blends_and_refuses_wide_gaps():
    times = np.array([0.0, 0.01, 0.06])
    poses = [_pose(), _pose(x=0.1, rotation_deg=(0, 0, 10)), _pose(x=0.2)]
    middle = jitter.interpolate_pose(times, poses, 0.005)
    assert middle[0, 3] == pytest.approx(0.05)
    angle = Rotation.from_matrix(middle[:3, :3]).as_euler("xyz", degrees=True)[2]
    assert angle == pytest.approx(5.0)
    with pytest.raises(ValueError, match="gap"):
        jitter.interpolate_pose(times, poses, 0.03)
    with pytest.raises(ValueError, match="outside"):
        jitter.interpolate_pose(times, poses, 0.07)


# --- linking ----------------------------------------------------------------------------


def test_linking_is_one_to_one_same_class_within_gate_and_counts_jumps():
    previous = [
        {"label": "cup", "predicted": (100.0, 100.0), "diagonal": 40.0},
        {"label": "cup", "predicted": (300.0, 100.0), "diagonal": 40.0},
    ]
    current = [
        {"label": "cup", "centre": (105.0, 100.0)},
        {"label": "tv", "centre": (300.0, 100.0)},
        {"label": "cup", "centre": (350.0, 100.0)},
    ]
    result = jitter.link(previous, current, gate=0.5)
    assert result["links"] == [(0, 0)]
    assert result["unlinked"] == [{"index": 1, "nearest_px": 50.0, "outcome": "jump"}]


def test_box_vanishing_next_to_a_followed_neighbour_is_not_a_jump():
    previous = [
        {"label": "cup", "predicted": (100.0, 100.0), "diagonal": 50.0},
        {"label": "cup", "predicted": (150.0, 100.0), "diagonal": 50.0},
    ]
    current = [{"label": "cup", "centre": (150.0, 100.0)}]
    result = jitter.link(previous, current, gate=0.5)
    assert result["links"] == [(1, 0)]
    assert result["unlinked"] == [{"index": 0, "nearest_px": 50.0, "outcome": "gone"}]


def test_nearby_box_claimed_by_another_track_is_reported_separately():
    previous = [
        {"label": "cup", "predicted": (100.0, 100.0), "diagonal": 50.0},
        {"label": "cup", "predicted": (120.0, 100.0), "diagonal": 50.0},
    ]
    current = [{"label": "cup", "centre": (120.0, 100.0)}]
    result = jitter.link(previous, current, gate=0.5)
    assert result["links"] == [(1, 0)]
    assert result["unlinked"] == [{"index": 0, "nearest_px": 20.0, "outcome": "claimed"}]


def test_jump_targets_are_assigned_at_most_once():
    previous = [
        {"label": "cup", "predicted": (100.0, 100.0), "diagonal": 40.0},
        {"label": "cup", "predicted": (100.0, 160.0), "diagonal": 40.0},
    ]
    current = [{"label": "cup", "centre": (100.0, 130.0)}]
    result = jitter.link(previous, current, gate=0.5)
    assert [row["outcome"] for row in result["unlinked"]] == ["jump", "gone"]
    assert [row["nearest_px"] for row in result["unlinked"]] == [30.0, 30.0]


def test_redetection_without_depth_is_reported_as_no_depth():
    previous = [{"label": "cup", "predicted": (100.0, 100.0), "diagonal": 40.0}]
    current = [{"label": "cup", "centre": (102.0, 100.0), "linkable": False}]
    result = jitter.link(previous, current, gate=0.5)
    assert result["links"] == []
    assert result["unlinked"] == [
        {"index": 0, "nearest_px": 2.0, "outcome": "no_depth"}
    ]


# --- jitter statistics -----------------------------------------------------------------


def _track(offsets):
    """Static point at 1 m; camera translates sideways 1 cm per frame."""
    frames = []
    for k, offset in enumerate(offsets):
        pose = _pose(x=0.01 * k)
        u, v = jitter.project_world(np.array([0.0, 0.0, 1.0]), CAMERA, pose)
        centre = (u + offset[0], v + offset[1])
        world = jitter.backproject_pixel(*centre, 1.0, CAMERA, pose)
        frames.append({"index": k, "centre": centre, "world": world, "pose": pose})
    return frames


def test_constant_offset_gives_zero_jitter():
    track = _track([(10.0, 0.0)] * 50)
    windowed = jitter.windowed_jitter(track, CAMERA, half_window=5)
    pairwise = jitter.pairwise_jitter(track, CAMERA)
    assert windowed["sx"] == pytest.approx(0, abs=1e-9)
    assert pairwise["sx"] == pytest.approx(0, abs=1e-9)


def test_independent_jitter_is_recovered_by_both_estimates():
    noise = np.random.default_rng(SEED).normal(0, 3.0, size=(5000, 2))
    track = _track([tuple(row) for row in noise])
    windowed = jitter.windowed_jitter(track, CAMERA, half_window=5)
    pairwise = jitter.pairwise_jitter(track, CAMERA)
    for axis in ("sx", "sy"):
        assert windowed[axis] == pytest.approx(3.0, rel=0.1)
        assert pairwise[axis] == pytest.approx(3.0, rel=0.1)
    assert pairwise["lag1_x"] == pytest.approx(-0.5, abs=0.1)
    assert windowed["radial_rms"] == pytest.approx(
        math.hypot(windowed["sx"], windowed["sy"]), rel=0.05
    )


def test_slow_drift_is_not_counted_as_jitter_by_local_estimates():
    ramp = [(20.0 * k / 199, 0.0) for k in range(200)]
    track = _track(ramp)
    whole = jitter.windowed_jitter(track, CAMERA, half_window=None)
    local = jitter.windowed_jitter(track, CAMERA, half_window=5)
    pairwise = jitter.pairwise_jitter(track, CAMERA)
    assert whole["sx"] == pytest.approx(5.8, abs=0.1)
    assert local["sx"] < 0.5 and pairwise["sx"] < 0.5


def test_short_track_gives_unavailable_not_zero():
    track = _track([(0.0, 0.0)] * 4)
    assert jitter.windowed_jitter(track, CAMERA, half_window=5)["sx"] is None
    assert jitter.pairwise_jitter(track, CAMERA)["reason"]


def test_track_bootstrap_is_reproducible():
    values = [1.0, 2.0, 3.0, 4.0]
    first = jitter.bootstrap_interval(values, seed=SEED, resamples=1000)
    assert first == jitter.bootstrap_interval(values, seed=SEED, resamples=1000)
    assert first[0] <= np.mean(values) <= first[1]


floor = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.floor"
)


def _frame(gray, pose):
    keypoints, descriptors = floor.features(gray)
    depth = np.ones(gray.shape)
    return {
        "keypoints": keypoints,
        "descriptors": descriptors,
        "depth": depth,
        "valid": np.ones(gray.shape, dtype=bool),
        "pose": pose,
    }


def test_feature_floor_is_near_zero_with_correct_motion_and_large_without():
    generator = np.random.default_rng(SEED)
    smooth = gaussian_filter(generator.random((480, 640)), 2)
    base = ((smooth - smooth.min()) / np.ptp(smooth) * 255).astype(np.uint8)
    shifted = np.zeros_like(base)
    shifted[:, :-10] = base[:, 10:]  # scene moves 10 px left
    before = _frame(base, _pose())
    after = _frame(shifted, _pose(x=10 / 525))
    rows = floor.pair_residuals(before, after, CAMERA)
    residuals = np.array([[r["dx"], r["dy"]] for r in rows])
    assert len(rows) >= 30
    assert np.median(np.abs(residuals)) < 1.0
    static = dict(after, pose=_pose())
    wrong = np.array(
        [[r["dx"], r["dy"]] for r in floor.pair_residuals(before, static, CAMERA)]
    )
    assert np.median(np.abs(wrong[:, 0])) > 9


def test_feature_depth_drops_depth_edges_and_empty_windows():
    depth = np.ones((20, 20))
    depth[:, 10:] = 2.0
    valid = np.ones((20, 20), dtype=bool)
    assert floor.feature_depth(depth, valid, 4.5, 10.5) == 1.0
    assert floor.feature_depth(depth, valid, 9.5, 10.5) is None
    assert floor.feature_depth(depth, np.zeros_like(valid), 4.5, 10.5) is None


def test_floor_splits_outliers_and_needs_thirty_residuals():
    generator = np.random.default_rng(SEED)
    residuals = np.vstack([generator.normal(0, 1.0, size=(200, 2)), [[100.0, 0.0]]])
    result = floor.floor(residuals)
    assert result["outliers"] >= 1 and result["sx"] == pytest.approx(
        1 / math.sqrt(2), rel=0.15
    )
    small = floor.floor(residuals[:10])
    assert small["sx"] is None and "30" in small["reason"]


jitter_tracks = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.jitter_tracks"
)


def _desk_frames(count, gap_after=None):
    frames = []
    for k in range(count):
        pose = _pose(x=0.01 * k)
        u, v = jitter.project_world(np.array([0.0, 0.0, 1.0]), CAMERA, pose)
        world = jitter.backproject_pixel(u, v, 1.0, CAMERA, pose)
        detection = {
            "label": "cup",
            "centre": (u, v),
            "world": world,
            "diagonal": 40.0,
            "xyxy": [u - 14, v - 14, u + 14, v + 14],
            "width": 28.0,
            "height": 28.0,
            "depth": 1.0,
            "flag_sparse": False,
            "flag_spread": False,
            "edge": False,
        }
        sequence = k + (1 if gap_after is not None and k > gap_after else 0)
        frames.append(
            {
                "sequence": sequence,
                "frame_id": str(sequence),
                "pose": pose,
                "detections": [detection],
            }
        )
    return frames


def test_tracks_chain_consecutive_frames_and_break_at_refused_frames():
    frames = _desk_frames(12, gap_after=5)
    tracks, unlinked = jitter_tracks.link_frames(frames, CAMERA)
    assert sorted(len(t) for t in tracks) == [6, 6]
    assert unlinked == []
    features = jitter_tracks.by_position(
        [
            {
                "frame_position": p,
                "u": frames[p]["detections"][0]["centre"][0],
                "v": frames[p]["detections"][0]["centre"][1],
                "dx": 0.1,
                "dy": -0.1,
            }
            for p in range(12)
        ]
    )
    summary = jitter_tracks.summarise_track(tracks[0], frames, features, CAMERA)
    assert summary["status"] == "scored" and summary["clean"] is True
    assert summary["windowed"]["sx"] == pytest.approx(0, abs=1e-9)
    assert summary["camera_baseline_m"] == pytest.approx(0.05)
    assert summary["local_floor"]["sx"] is None  # 6 residuals < 30


def test_detection_without_depth_cannot_join_a_track():
    frames = _desk_frames(6)
    frames[3]["detections"][0]["world"] = None
    tracks, _ = jitter_tracks.link_frames(frames, CAMERA)
    assert sorted(len(t) for t in tracks) == [2, 3]
    short = jitter_tracks.summarise_track(tracks[0], frames, {}, CAMERA)
    assert short["status"] == "too_short"


jitter_run = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.jitter_run"
)


def test_tertile_bands_count_every_residual_exactly_once():
    rows = [
        {"gap_rotation_rad": value, "dx": float(i % 3), "dy": 0.0}
        for i, value in enumerate([0.1] * 30 + [0.2] * 60 + [0.3] * 30)
    ]
    bands = jitter_run._tertile_floors(rows)
    assert sum(b["n"] + b["outliers"] for b in bands) == len(rows)
