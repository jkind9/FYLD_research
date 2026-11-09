"""The room build's grid size: learned depth fitted to ARCore depth cell by cell."""

from types import SimpleNamespace

import numpy as np
import pytest

from src.live import room_build


def targets(w=80, h=60, step=2):
    u, v = np.meshgrid(np.arange(0, w, step), np.arange(0, h, step))
    return np.c_[u.ravel(), v.ravel()].astype(float)


def test_each_side_gets_its_own_size():
    model = np.ones((60, 80))
    uv = targets()
    target = np.where(uv[:, 0] < 40, 2.0, 4.0)
    field = room_build.grid_size(model, np.ones_like(model, bool), uv, target, cells=(2, 1))
    assert field[30, 5] == pytest.approx(2.0)
    assert field[30, 75] == pytest.approx(4.0)


def test_cells_without_enough_targets_take_the_frame_median():
    model = np.ones((60, 80))
    uv = targets()
    uv = uv[uv[:, 0] < 40]  # ARCore depth covers only the left half
    field = room_build.grid_size(model, np.ones_like(model, bool), uv, np.full(len(uv), 3.0), cells=(2, 1))
    assert field[30, 75] == pytest.approx(3.0)


def test_a_given_fallback_sizes_the_cells_without_enough_targets():
    model = np.ones((60, 80))
    uv = targets()
    uv = uv[uv[:, 0] < 40]
    field = room_build.grid_size(model, np.ones_like(model, bool), uv, np.full(len(uv), 3.0), cells=(2, 1),
                                 fallback=np.log(5.0))
    assert field[30, 75] == pytest.approx(5.0)
    assert field[30, 5] == pytest.approx(3.0)


def test_too_few_targets_give_no_size():
    model = np.ones((60, 80))
    uv = targets()[:10]
    assert room_build.grid_size(model, np.ones_like(model, bool), uv, np.ones(10)) is None


@pytest.mark.parametrize(("age_s", "fresh"), [(0.008, True), (0.1, True), (4.4, False)])
def test_depth_older_than_one_depth_period_is_stale(age_s, fresh):
    frame = SimpleNamespace(camera_t_ns=10_000_000_000, depth=SimpleNamespace(t_ns=10_000_000_000 - round(age_s * 1e9)))
    assert room_build.fresh_depth(frame) is fresh


def test_cell_index_numbers_cells_row_by_row():
    uv = np.array([[0, 0], [79, 0], [0, 59], [79, 59]], float)
    assert room_build.cell_index(uv, (80, 60), cells=(2, 1)).tolist() == [0, 1, 0, 1]
    assert room_build.cell_index(uv, (80, 60), cells=(1, 2)).tolist() == [0, 0, 1, 1]


def test_only_cells_with_enough_arcore_pixels_are_supported():
    uv = targets()
    uv = uv[uv[:, 0] < 40]  # ARCore depth covers only the left half
    mask = room_build.supported_pixels(uv, (60, 80), cells=(2, 1))
    assert mask[:, :40].all() and not mask[:, 40:].any()


def test_vote_views_move_each_camera_by_its_anchor_correction_since_fusion():
    moved = np.eye(4)
    moved[0, 3] = 1.0  # the anchor placing keyframe 3 has moved 1 m along x since the frame was fused
    fragments = SimpleNamespace(placing_anchor=lambda keyframe: moved if keyframe == 3 else np.eye(4))
    evidence = np.ones((2, 2))
    placed = [(np.eye(4), (1.0, 1.0, 0.0, 0.0), 3, np.eye(4), evidence),
              (np.eye(4), (1.0, 1.0, 0.0, 0.0), 0, np.eye(4), evidence)]
    (first, k, depth), (second, _, _) = room_build.vote_views(fragments, placed)
    assert first[0, 3] == -1.0 and second[0, 3] == 0.0  # camera_from_world of a camera now at x = 1 m, and at 0
    assert k == (1.0, 1.0, 0.0, 0.0) and depth is evidence
