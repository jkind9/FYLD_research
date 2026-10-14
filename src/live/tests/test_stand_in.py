"""A recorded TUM-style clip becomes a phone session v1 folder that the host reader accepts."""

import json

import numpy as np
from PIL import Image

from src.live import stand_in
from src.live.stream import session_v1


def tum_folder(root, frames=9, step_s=0.2):
    (root / "rgb").mkdir(parents=True)
    (root / "depth").mkdir()
    rgb, depth, truth = ["# rgb"], ["# depth"], ["# truth"]
    for i in range(frames):
        t = 100.0 + i * step_s
        Image.fromarray(np.random.default_rng(i).integers(0, 255, (48, 64, 3), np.uint8)).save(root / f"rgb/{i}.png")
        Image.fromarray(np.full((48, 64), 10000, np.uint16)).save(root / f"depth/{i}.png")  # 2 m at 5000 per metre
        rgb.append(f"{t:.4f} rgb/{i}.png")
        depth.append(f"{t:.4f} depth/{i}.png")
        truth.append(f"{t:.4f} {0.1 * i} 0 0 0 0 0 1")
    for name, lines in (("rgb.txt", rgb), ("depth.txt", depth), ("groundtruth.txt", truth)):
        (root / name).write_text("\n".join(lines) + "\n")
    return root


def test_stand_in_session_reads_back_as_v1(tmp_path):
    folder = tum_folder(tmp_path / "clip")
    out = stand_in.write_session(f"tum:{folder}", tmp_path / "session", depth_size=(16, 12))
    frames = list(session_v1.read_session(out))
    assert [f.seq for f in frames] == list(range(9))
    assert [f.seq for f in frames if f.depth is not None] == [0, 3, 6]
    assert [f.anchor_created[0] for f in frames if f.anchor_created] == [0, 1]  # one per second
    assert all(len(f.point_ids) == stand_in.POINTS_PER_FRAME for f in frames)
    assert np.allclose(frames[3].depth.depth_m, 2.0)
    # ground truth is in OpenCV camera axes; the session carries ARCore axes
    assert np.allclose(session_v1.world_from_camera_cv(frames[4].pose)[:3, 3], [0.4, 0, 0])
    assert np.allclose(session_v1.world_from_camera_cv(frames[4].pose)[:3, :3], np.eye(3))
    record = json.loads((out / "session.json").read_text())
    assert record["control"] == "reference" and record["version"] == 1
