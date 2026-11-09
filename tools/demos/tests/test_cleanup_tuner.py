"""The clean-up tuner page: every parameter has a slider range and a description; data has one value per point."""

import json

import numpy as np
import open3d as o3d
from PIL import Image

from tools.demos import cleanup_tuner


def test_every_parameter_has_a_description_and_a_default_inside_its_range():
    stages = {s["id"] for s in cleanup_tuner.STAGES}
    assert {"vote", "seen", "spots", "sor", "radius", "chain"} <= stages
    assert all(s["description"] for s in cleanup_tuner.STAGES)
    for p in cleanup_tuner.PARAMS:
        assert p["stage"] in stages and p["label"] and len(p["description"]) > 40
        assert p["min"] <= p["value"] <= p["max"] and p["step"] > 0
    chain = [p["id"] for p in cleanup_tuner.PARAMS if p["stage"] == "chain"]
    assert {"linkCm", "linkMinNeighbours", "pieceMin", "pieceKeep", "linkNormalDeg"} <= set(chain)


def test_page_data_holds_one_value_per_point_and_marks_unmeasured_points(tmp_path):
    points = np.array([[0.0, 0.0, 2.0], [0.1, 0.0, 2.0], [0.0, 0.1, 2.0], [0.0, 0.0, 1.0]])
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    cloud.colors = o3d.utility.Vector3dVector(np.full((4, 3), 0.5))
    o3d.io.write_point_cloud(str(tmp_path / "raw.ply"), cloud)
    np.savez(tmp_path / "attributes.npz", seen=np.array([3, 3, 3, 0]), see_through=np.array([0.0, 0.0, 0.5, 1.0]),
             nearest_m=np.array([2.0, 2.0, 2.0, np.inf]), second_angle_deg=np.array([0.0, 7.1, 40.0, 0.0]),
             knn_mean_m=np.array([0.02, 0.02, 0.02, 1.0]))
    session = tmp_path / "session"
    (session / "frames").mkdir(parents=True)
    Image.new("RGB", (64, 48)).save(session / "frames" / "000065.jpg")
    row = {"seq": 65, "arcore": {"pose": [0, 0, 0, 0, 0, 0, 1], "intrinsics": [50.0, 50.0, 32.0, 24.0]}}
    (session / "frames.jsonl").write_text(json.dumps(row) + "\n")
    data = cleanup_tuner.tuner_data(tmp_path, session, [65])
    assert data["positions"]["count"] == 4 and data["seen"]["shape"] == [4]
    assert data["compare"][0]["frame"] == 65
    page = cleanup_tuner.tuner_page(data)
    assert all(p["description"] in page or json.dumps(p["description"])[1:-1] in page for p in cleanup_tuner.PARAMS)
