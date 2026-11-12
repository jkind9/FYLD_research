"""Per-point clean-up evidence for the tuner page: frames measuring each point, see-through share and spacing."""

import numpy as np

from research.experiments.surface_cleanup import cleanup_attributes

K = (100.0, 100.0, 32.0, 24.0)


def test_attributes_of_a_wall_and_a_speck_in_front_of_it():
    u, v = np.meshgrid(np.arange(-5, 6) * 0.02, np.arange(-5, 6) * 0.02)
    wall = np.c_[u.ravel(), v.ravel(), np.full(121, 2.0)]  # 20 cm square, 2 m ahead, 2 cm spacing
    points = np.vstack([wall, [[0.0, 0.0, 1.0]]])
    depth = np.full((48, 64), 2.0)
    views = [(np.eye(4), K, depth, depth)] * 3  # camera, intrinsics, fused depth, see-through evidence
    a = cleanup_attributes.point_attributes(points, views)
    assert a["seen"][:121].tolist() == [3] * 121 and a["seen"][-1] == 0
    assert (a["see_through"][:121] == 0).all() and a["see_through"][-1] == 1.0
    assert np.allclose(a["nearest_m"][:121], 2.0) and np.isinf(a["nearest_m"][-1])
    assert np.allclose(a["second_angle_deg"], 0.0, atol=1e-4)  # one camera position, so no wide views
    assert a["knn_mean_m"][-1] > 10 * np.median(a["knn_mean_m"][:121])
