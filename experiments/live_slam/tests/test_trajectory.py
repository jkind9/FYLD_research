"""Live SLAM pose files to per-frame rows, frame lists and WSL paths."""

from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.live_slam.src import trajectory


def line(t, segment, matrix):
    qx, qy, qz, qw = Rotation.from_matrix(matrix[:3, :3]).as_quat()
    x, y, z = matrix[:3, 3]
    return f"{t:.6f} {segment} {x} {y} {z} {qx} {qy} {qz} {qw}"


def pose(position, euler):
    out = np.eye(4)
    out[:3, :3] = Rotation.from_euler("xyz", euler, degrees=True).as_matrix()
    out[:3, 3] = position
    return out


def test_tracked_lost_and_missing_frames_become_rows_in_order(tmp_path):
    a, b, c = pose((0, 0, 0), (0, 0, 0)), pose((0.1, 0, 0), (0, 5, 0)), pose((0.2, 0.1, 0), (3, 10, 0))
    file = tmp_path / "live.txt"
    file.write_text("\n".join([line(1.0, 0, a), line(1.1, 0, b), "1.200000 lost", line(1.3, 1, c)]) + "\n")
    times = [1.0, 1.1, 1.2, 1.3, 1.4]
    rows = trajectory.rows([f"f{i}" for i in range(5)], times, trajectory.read_poses(file))
    assert [r["model_id"] for r in rows] == [0, 0, None, 1, None]
    assert np.allclose(rows[3]["T_world_camera"], c)
    assert rows[2]["T_world_camera"] is None and rows[4]["T_world_camera"] is None


def test_times_match_within_a_millisecond_only(tmp_path):
    file = tmp_path / "live.txt"
    file.write_text(line(2.0005, 0, np.eye(4)) + "\n" + line(3.03, 0, np.eye(4)) + "\n")
    rows = trajectory.rows(["a", "b"], [2.0, 3.0], trajectory.read_poses(file))
    assert rows[0]["model_id"] == 0
    assert rows[1]["model_id"] is None


def test_wsl_paths_and_frame_list():
    assert trajectory.to_wsl(Path("C:/Users/x/rgb/1.png")) == "/mnt/c/Users/x/rgb/1.png"
    text = trajectory.frame_list([1.5, 2.25], [Path("C:/d/a.png"), Path("D:/e/b.png")])
    assert text.splitlines() == ["1.500000 /mnt/c/d/a.png", "2.250000 /mnt/d/e/b.png"]


def test_final_trajectory_files_without_segments_read_as_one_map(tmp_path):
    file = tmp_path / "final_euroc.txt"
    m = pose((0.5, 0, 1), (0, 20, 0))
    file.write_text(line(1.5e9, 0, m).replace(" 0 ", " ", 1) + "\n")
    (t, segment, matrix), = trajectory.read_trajectory(file, time_scale=1e-9)
    assert t == 1.5 and segment == 0 and np.allclose(matrix, m)


def test_camera_file_gets_this_recordings_pinhole_and_no_distortion():
    from experiments.live_slam import run_live
    stella = "Camera:\n  fx: 517.3\n  fy: 516.4\n  cx: 318.6\n  cy: 255.3\n  k1: 0.26\n  k3: 1.16\n  fps: 30.0\n"
    got = run_live.config_text(stella, run_live.SYSTEMS["stella"]["key"], (525.0, 525.0, 319.5, 239.5))
    assert "  fx: 525.0" in got and "  cy: 239.5" in got and "  k1: 0.0" in got and "  k3: 0.0" in got and "fps: 30.0" in got
    orb = "Camera1.fx: 517.3\nCamera1.k1: 0.26\nCamera.fps: 30\n"
    got = run_live.config_text(orb, run_live.SYSTEMS["orbslam3"]["key"], (481.2, 480.0, 319.5, 239.5))
    assert got.splitlines() == ["Camera1.fx: 481.2", "Camera1.k1: 0.0", "Camera.fps: 30"]


def test_report_takes_the_median_and_range_over_repeats():
    from experiments.live_slam import report
    runs = [{"live_mm": v, "final_mm": v - 1, "placed": 0.9, "models": 1, "median_ms": 8.0, "p95_ms": 20.0} for v in (10.0, 30.0, 20.0)]
    row = report.combine(runs)
    assert row["live_mm"] == (20.0, 10.0, 30.0)
    assert row["final_mm"] == (19.0, 9.0, 29.0)
    assert row["repeats"] == 3
