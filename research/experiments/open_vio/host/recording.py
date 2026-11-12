"""Read, check and convert a session recorded by the capture app (experiments/01_camera_capture_delivery/capture).

    python experiments/open_vio/host/recording.py <session folder> [--euroc <output folder>]

The session folder is what the PC capture receiver writes (phone session v2, phone_session_v2.md): session.json,
imu.csv, and for a walk frames.jsonl and cam0/<seq>.png. Every camera and motion-sensor time is integer
nanoseconds on the phone's elapsedRealtime clock. The EuRoC/ASL
output (mav0/cam0, mav0/imu0) is the layout Basalt, Kimera-VIO, OKVIS2 and Kalibr's bag creator read;
arcore_camera_tum.txt is ARCore's camera path in OpenCV camera axes, in the live-SLAM harness's format.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

CLOCK_BASE_TOLERANCE_NS = 10**9
ARCORE_MATCH_MINIMUM = 0.5
_GL_TO_CV = Rotation.from_quat([1.0, 0.0, 0.0, 0.0])  # 180 degrees about x: y up -> y down, looking down -z -> +z


@dataclass
class Recording:
    root: Path
    meta: dict
    image_times: np.ndarray
    image_names: dict = field(default_factory=dict)  # t_ns -> file name in cam0/
    camera_rows: dict = field(default_factory=dict)  # t_ns -> {exposure_ns, rolling_shutter_skew_ns, ...}
    gyro_times: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    gyro: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    accel_times: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    accel: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    arcore: list = field(default_factory=list)
    missing: list = field(default_factory=list)

    @property
    def is_walk(self) -> bool:
        return self.meta.get("kind") == "walk"


POSE_KEYS = ("tx", "ty", "tz", "qx", "qy", "qz", "qw")
DEVICE_KEYS = ("dev_tx", "dev_ty", "dev_tz", "dev_qx", "dev_qy", "dev_qz", "dev_qw")


def _arcore_row(frame: dict) -> dict:
    """A frame's ARCore record as one flat row: t_ns, camera_t_ns, tracking, camera pose, device pose, failure."""
    record = frame["arcore"]
    row = {"t_ns": record["t_ns"], "camera_t_ns": frame["camera_t_ns"], "tracking": record["tracking"], "failure": record["failure"]}
    for keys, pose in ((POSE_KEYS, record["pose"]), (DEVICE_KEYS, record["device_pose"])):
        row |= dict(zip(keys, pose if pose is not None else [float("nan")] * 7))
    return row


def load(root: Path) -> Recording:
    root = Path(root)
    meta = json.loads((root / "session.json").read_text(encoding="utf-8"))
    rec = Recording(root, meta, np.zeros(0, np.int64))
    if (root / "imu.csv").exists():
        rows = [line.split(",") for line in (root / "imu.csv").read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
        for name in ("gyro", "accel"):
            mine = [r for r in rows if r[0] == name]
            setattr(rec, f"{name}_times", np.array([int(r[1]) for r in mine], dtype=np.int64))
            setattr(rec, name, np.array([[float(v) for v in r[2:5]] for r in mine]).reshape(-1, 3))
    else:
        rec.missing.append("imu.csv")
    if not rec.is_walk:
        return rec
    if not (root / "frames.jsonl").exists():
        rec.missing.append("frames.jsonl")
        return rec
    frames = [json.loads(line) for line in (root / "frames.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    for frame in frames:
        name = f"{frame['seq']:06d}.png"
        if (root / "cam0" / name).exists():
            rec.image_names[frame["camera_t_ns"]] = name
        if frame["camera"] is not None:
            rec.camera_rows[frame["camera_t_ns"]] = frame["camera"]
        if frame["arcore"] is not None:
            rec.arcore.append(_arcore_row(frame))
    rec.image_times = np.array(sorted(rec.image_names), dtype=np.int64)
    if not len(rec.image_times):
        rec.missing.append("cam0/*.png")
    return rec


def tracking_poses(rec: Recording) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ARCore camera times (ns, the Android camera clock), positions and quaternions (x, y, z, w) while tracking."""
    rows = [r for r in rec.arcore if r["tracking"] == "TRACKING"]
    times = np.array([int(r["camera_t_ns"]) for r in rows], dtype=np.int64)
    positions = np.array([[float(r[k]) for k in POSE_KEYS[:3]] for r in rows]).reshape(-1, 3)
    quats = np.array([[float(r[k]) for k in POSE_KEYS[3:]] for r in rows]).reshape(-1, 4)
    return times, positions, quats


def arcore_match_fraction(rec: Recording) -> float:
    """Share of ARCore's tracked frames whose Android camera timestamp is exactly one of the saved images."""
    times, _, _ = tracking_poses(rec)
    return float(np.isin(times, rec.image_times).mean()) if len(times) else 0.0


def opencv_quaternion(q_gl: np.ndarray) -> np.ndarray:
    """ARCore's OpenGL camera (x right, y up, looking down -z) to OpenCV axes (x right, y down, looking down +z)."""
    return (Rotation.from_quat(q_gl) * _GL_TO_CV).as_quat()


def first_stamps(rec: Recording) -> dict[str, int]:
    streams = {"gyro": rec.gyro_times, "accel": rec.accel_times}
    if rec.is_walk:
        streams["camera"] = rec.image_times
    return {name: int(t[0]) for name, t in streams.items() if len(t)}


def problems(rec: Recording) -> list[str]:
    """Everything that stops the recording being used as it is; empty when it is usable."""
    found = [f"missing {name}" for name in rec.missing]
    if "end" not in rec.meta.get("clock", {}):
        found.append("recording did not stop cleanly (session.json has no end clock stamp)")
    for name, times in (("camera", rec.image_times), ("gyro", rec.gyro_times), ("accel", rec.accel_times)):
        if len(times) > 1 and np.any(np.diff(times) <= 0):
            found.append(f"{name} timestamps are not strictly increasing")
    start = rec.meta["clock"]["start"]["elapsed_realtime_ns"]
    for name, first in first_stamps(rec).items():
        if abs(first - start) > CLOCK_BASE_TOLERANCE_NS:
            found.append(f"{name} clock starts {(first - start) / 1e9:+.3f} s from the app's elapsedRealtime start stamp")
    if rec.is_walk:
        unmatched = [t for t in rec.image_times if int(t) not in rec.camera_rows]
        if unmatched:
            found.append(f"{len(unmatched)} images have no camera settings")
        if rec.arcore and arcore_match_fraction(rec) < ARCORE_MATCH_MINIMUM:
            found.append(f"ARCore camera timestamps match only {100 * arcore_match_fraction(rec):.0f}% of images")
    return found


def to_euroc(rec: Recording, out: Path) -> Path:
    out = Path(out)
    cam = out / "mav0" / "cam0"
    (cam / "data").mkdir(parents=True, exist_ok=True)
    with open(cam / "data.csv", "w", encoding="utf-8") as listing:
        listing.write("#timestamp [ns],filename\n")
        for t in rec.image_times:
            shutil.copyfile(rec.root / "cam0" / rec.image_names[int(t)], cam / "data" / f"{t}.png")
            listing.write(f"{t},{t}.png\n")
    imu = out / "mav0" / "imu0"
    imu.mkdir(parents=True, exist_ok=True)
    inside = (rec.gyro_times >= rec.accel_times[0]) & (rec.gyro_times <= rec.accel_times[-1])
    times = rec.gyro_times[inside]
    accel = np.column_stack([np.interp(times, rec.accel_times, rec.accel[:, k]) for k in range(3)])
    with open(imu / "data.csv", "w", encoding="utf-8") as f:
        f.write("#timestamp [ns],w_RS_S_x [rad s^-1],w_RS_S_y [rad s^-1],w_RS_S_z [rad s^-1],"
                "a_RS_S_x [m s^-2],a_RS_S_y [m s^-2],a_RS_S_z [m s^-2]\n")
        for t, w, a in zip(times, rec.gyro[inside], accel):
            f.write(f"{t}," + ",".join(f"{v:.9g}" for v in (*w, *a)) + "\n")
    if rec.is_walk:
        pose_t, positions, quats = tracking_poses(rec)
        with open(out / "arcore_camera_tum.txt", "w", encoding="utf-8") as f:
            for t, p, q in zip(pose_t, positions, quats):
                f.write(f"{t * 1e-9:.9f} " + " ".join(f"{v:.9g}" for v in (*p, *opencv_quaternion(q))) + "\n")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("recording", type=Path)
    parser.add_argument("--euroc", type=Path, help="write the EuRoC/ASL layout here")
    args = parser.parse_args()
    rec = load(args.recording)
    found = problems(rec)
    print("\n".join(found) if found else "no problems found")
    if args.euroc:
        print(f"written {to_euroc(rec, args.euroc)}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
