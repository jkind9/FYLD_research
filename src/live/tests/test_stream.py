"""Replay reads a phone session v2 folder from the capture receiver as well as a v1 folder."""

import sys
from pathlib import Path

from src.live import stream

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "experiments" / "01_camera_capture_delivery" / "tests"))
import fake_phone  # noqa: E402


def test_replay_reads_a_v2_session_folder(tmp_path):
    folder = fake_phone.write_session(tmp_path, fake_phone.walk(5))
    delivered = []
    assert stream.replay(folder, lambda frame, path: delivered.append((frame, path)), speed=0) == 5
    assert [frame.seq for frame, _ in delivered] == list(range(5))
    assert all(path == folder / "frames" / f"{frame.seq:06d}.jpg" and path.is_file() for frame, path in delivered)
    second = delivered[1][0]
    assert second.pose[0] == 0.01 and second.t_ns == second.camera_t_ns and second.grey.shape == (3, 4)
