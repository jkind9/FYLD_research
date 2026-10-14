"""Reading, checking and converting a phone recording."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

import recording


def test_load_reads_every_stream(make_recording):
    rec = recording.load(make_recording(seconds=2.0))
    assert len(rec.image_times) == 60 and rec.image_times.dtype == np.int64
    assert rec.gyro_times.shape == (800,) and rec.gyro.shape == (800, 3)
    assert rec.accel_times.shape == (400,) and rec.accel.shape == (400, 3)
    assert len(rec.arcore) == 60 and rec.arcore[0]["tracking"] == "TRACKING"
    assert recording.problems(rec) == []


def test_imu_only_recording_needs_no_camera_files(make_recording):
    rec = recording.load(make_recording(kind="imu_only"))
    assert len(rec.image_times) == 0 and recording.problems(rec) == []


def test_missing_file_is_a_problem(make_recording):
    root = make_recording()
    (root / "accel.csv").unlink()
    assert any("accel.csv" in p for p in recording.problems(recording.load(root)))


def test_recording_that_did_not_stop_cleanly_is_reported(make_recording):
    assert any("did not stop" in p for p in recording.problems(recording.load(make_recording(stopped=False))))


def test_timestamps_that_go_backwards_are_reported(make_recording):
    root = make_recording()
    lines = (root / "gyro.csv").read_text().splitlines()
    lines[5], lines[6] = lines[6], lines[5]
    (root / "gyro.csv").write_text("\n".join(lines) + "\n")
    assert any("gyro" in p and "increasing" in p for p in recording.problems(recording.load(root)))


def test_camera_on_another_clock_is_reported(make_recording):
    rec = recording.load(make_recording(camera_clock_shift_ns=3 * 10**9))
    assert any("clock" in p for p in recording.problems(rec))


def test_arcore_frames_that_match_no_image_are_reported(make_recording):
    root = make_recording()
    for image in sorted((root / "cam0").glob("*.pgm"))[::2]:
        image.unlink()
    lines = (root / "cam0.csv").read_text().splitlines()
    kept = {p.stem for p in (root / "cam0").glob("*.pgm")}
    (root / "cam0.csv").write_text("\n".join([lines[0]] + [l for l in lines[1:] if l.split(",")[0] in kept]) + "\n")
    rec = recording.load(root)
    assert recording.arcore_match_fraction(rec) == pytest.approx(0.5, abs=0.02)
    rows = (root / "arcore.csv").read_text().splitlines()
    shifted = [rows[0]]
    for row in rows[1:]:
        cells = row.split(",")
        cells[1] = str(int(cells[1]) + 5)  # camera timestamp 5 ns away from every image
        shifted.append(",".join(cells))
    (root / "arcore.csv").write_text("\n".join(shifted) + "\n")
    rec = recording.load(root)
    assert recording.arcore_match_fraction(rec) == 0.0
    assert any("ARCore" in p for p in recording.problems(rec))


def test_opencv_axes_flip_y_and_z_of_the_arcore_camera():
    gl = Rotation.from_euler("y", 30, degrees=True).as_quat()
    q = recording.opencv_quaternion(gl)
    expected = Rotation.from_quat(gl).as_matrix() @ np.diag([1.0, -1.0, -1.0])
    assert np.allclose(Rotation.from_quat(q).as_matrix(), expected)
    assert np.allclose(Rotation.from_quat(recording.opencv_quaternion(q)).as_matrix(), Rotation.from_quat(gl).as_matrix())


def test_euroc_conversion_writes_images_imu_and_reference(make_recording, tmp_path):
    cv2 = pytest.importorskip("cv2")
    rec = recording.load(make_recording(seconds=1.0))
    out = recording.to_euroc(rec, tmp_path / "euroc")
    cam_rows = (out / "mav0" / "cam0" / "data.csv").read_text().splitlines()
    assert cam_rows[0].startswith("#timestamp [ns]") and len(cam_rows) == 31
    t0, name = cam_rows[1].split(",")
    image = cv2.imread(str(out / "mav0" / "cam0" / "data" / name), cv2.IMREAD_UNCHANGED)
    assert name == f"{t0}.png" and image.shape == (6, 8) and image[0, 1] == 1
    imu = np.loadtxt(out / "mav0" / "imu0" / "data.csv", delimiter=",", comments="#")
    accel_t = rec.accel_times
    inside = (rec.gyro_times >= accel_t[0]) & (rec.gyro_times <= accel_t[-1])
    assert len(imu) == inside.sum() and np.array_equal(imu[:, 0].astype(np.int64), rec.gyro_times[inside])
    assert np.allclose(imu[:, 6], (imu[:, 0] - 5e12) * 1e-9, atol=1e-6)  # accelerometer z = seconds, linear in time
    reference = np.loadtxt(out / "arcore_camera_tum.txt")
    assert reference.shape == (30, 8) and reference[0, 0] == pytest.approx(int(t0) * 1e-9)
