"""Windows of frames and sized world-to-camera poses for pose-conditioned depth."""

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.sfm.src import posed


def test_windows_cover_every_frame_once():
    got = posed.windows(10, 5)
    assert got == [([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]), ([5, 6, 7, 8, 9], [5, 6, 7, 8, 9])]


def test_short_last_window_moves_back_and_keeps_only_new_frames():
    got = posed.windows(12, 5)
    assert got[-1] == ([7, 8, 9, 10, 11], [10, 11])
    assert sorted(k for _, keep in got for k in keep) == list(range(12))


def test_fewer_frames_than_a_window_is_one_window_and_none_is_none():
    assert posed.windows(3, 5) == [([0, 1, 2], [0, 1, 2])]
    assert posed.windows(0, 5) == []


def test_spread_windows_take_every_stride_th_frame_inside_a_block():
    got = posed.windows(100, 5, stride=10)
    assert got[0] == ([0, 10, 20, 30, 40], [0, 10, 20, 30, 40])
    assert got[1][0] == [1, 11, 21, 31, 41]
    assert sorted(k for _, keep in got for k in keep) == list(range(100))


def test_spread_windows_handle_a_ragged_end():
    got = posed.windows(57, 5, stride=10)
    assert sorted(k for _, keep in got for k in keep) == list(range(57))
    assert all(len(members) == 5 for members, _ in got)


def test_extrinsics_are_the_inverse_of_the_sized_pose():
    pose = np.eye(4)
    pose[:3, :3] = Rotation.from_euler("xyz", (10, 20, 30), degrees=True).as_matrix()
    pose[:3, 3] = (1.0, 2.0, 3.0)
    ext = posed.sized_extrinsics([pose.tolist()], 0.5)[0]
    sized = pose.copy()
    sized[:3, 3] *= 0.5
    assert np.allclose(ext @ sized, np.eye(4))
    flat = posed.sized_extrinsics([np.array([[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1.0]]).tolist()], 0.5)[0]
    assert np.allclose(flat[:3, 3], (-0.5, -1.0, -1.5))
