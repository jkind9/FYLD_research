"""Read, check and convert a recording made by the raw recorder app (experiments/open_vio/recorder).

    python experiments/open_vio/host/recording.py <recording folder> [--euroc <output folder>]

A recording folder holds meta.json, gyro.csv and accel.csv, and for a walk also cam0.csv, cam0/<t_ns>.pgm
and arcore.csv. Every time is integer nanoseconds on the phone's elapsedRealtime clock. The EuRoC/ASL
output (mav0/cam0, mav0/imu0) is the layout Basalt, Kimera-VIO, OKVIS2 and Kalibr's bag creator read;
arcore_camera_tum.txt is ARCore's camera path in OpenCV camera axes, in the live-SLAM harness's format.
"""

from __future__ import annotations

import argparse
import json
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


def _rows(path: Path) -> tuple[list[str], list[list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[0].split(","), [line.split(",") for line in lines[1:] if line.strip()]


def _imu(path: Path) -> tuple[np.ndarray, np.ndarray]:
    _, rows = _rows(path)
    return np.array([int(r[0]) for r in rows], dtype=np.int64), np.array([[float(v) for v in r[1:4]] for r in rows]).reshape(-1, 3)


def load(root: Path) -> Recording:
    root = Path(root)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    rec = Recording(root, meta, np.zeros(0, np.int64))
    for name in ("gyro", "accel"):
        if (root / f"{name}.csv").exists():
            times, values = _imu(root / f"{name}.csv")
            setattr(rec, f"{name}_times", times)
            setattr(rec, name, values)
        else:
            rec.missing.append(f"{name}.csv")
    if not rec.is_walk:
        return rec
    images = (root / "cam0").glob("*.pgm") if (root / "cam0").is_dir() else []
    rec.image_times = np.array(sorted(int(p.stem) for p in images), dtype=np.int64)
    if not len(rec.image_times):
        rec.missing.append("cam0/*.pgm")
    for name in ("cam0.csv", "arcore.csv"):
        if not (root / name).exists():
            rec.missing.append(name)
            continue
        header, rows = _rows(root / name)
        parsed = [dict(zip(header, row)) for row in rows]
        if name == "cam0.csv":
            rec.camera_rows = {int(r["t_ns"]): {k: float(v) for k, v in r.items() if k != "t_ns"} for r in parsed}
        else:
            rec.arcore = parsed
    return rec


def tracking_poses(rec: Recording) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ARCore camera times (ns, the Android camera clock), positions and quaternions (x, y, z, w) while tracking."""
    rows = [r for r in rec.arcore if r["tracking"] == "TRACKING"]
    times = np.array([int(r["camera_t_ns"]) for r in rows], dtype=np.int64)
    positions = np.array([[float(r[k]) for k in ("tx", "ty", "tz")] for r in rows]).reshape(-1, 3)
    quats = np.array([[float(r[k]) for k in ("qx", "qy", "qz", "qw")] for r in rows]).reshape(-1, 4)
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
        found.append("recording did not stop cleanly (meta.json has no end clock stamp)")
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
            found.append(f"{len(unmatched)} images have no cam0.csv row")
        if rec.arcore and arcore_match_fraction(rec) < ARCORE_MATCH_MINIMUM:
            found.append(f"ARCore camera timestamps match only {100 * arcore_match_fraction(rec):.0f}% of images")
    return found


def to_euroc(rec: Recording, out: Path) -> Path:
    import cv2

    out = Path(out)
    cam = out / "mav0" / "cam0"
    (cam / "data").mkdir(parents=True, exist_ok=True)
    with open(cam / "data.csv", "w", encoding="utf-8") as listing:
        listing.write("#timestamp [ns],filename\n")
        for t in rec.image_times:
            image = cv2.imread(str(rec.root / "cam0" / f"{t}.pgm"), cv2.IMREAD_UNCHANGED)
            cv2.imwrite(str(cam / "data" / f"{t}.png"), image)
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
