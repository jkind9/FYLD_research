"""Compare a Kalibr camera-IMU result with a reference calibration and, for a phone recording, with ARCore's.

    python experiments/open_vio/calibration/compare.py <data-camchain-imucam.yaml> \
        [--reference <camchain.yaml>] [--recording <walk recording>] [--out compare.json]

Rotation in degrees, translation in metres, time shift in milliseconds (Kalibr: t_imu = t_cam + shift).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
import arcore_extrinsics  # noqa: E402
import kalibr_files  # noqa: E402
import recording  # noqa: E402


def _difference(ours: dict, transform) -> dict:
    angle, distance = kalibr_files.transform_difference(ours["T_cam_imu"], transform)
    return {"rotation_deg": angle, "translation_m": distance}


def compare(result: Path, reference: Path | None = None, walk: Path | None = None) -> dict:
    ours = kalibr_files.read_camchain(result)
    shift = ours["timeshift_cam_imu"]
    out = {"result": str(result), "model": ours["model"], "intrinsics": ours["intrinsics"],
           "time_shift_ms": None if shift is None else shift * 1e3, "T_cam_imu": ours["T_cam_imu"].tolist()}
    if reference:
        ref = kalibr_files.read_camchain(reference)
        out["reference"] = _difference(ours, ref["T_cam_imu"]) | {
            "file": str(reference), "intrinsics": ref["intrinsics"],
            "intrinsics_difference": [a - b for a, b in zip(ours["intrinsics"], ref["intrinsics"])],
            "reference_time_shift_ms": None if ref["timeshift_cam_imu"] is None else ref["timeshift_cam_imu"] * 1e3}
    if walk:
        arcore, spread = arcore_extrinsics.camera_from_device(recording.load(walk))
        out["arcore"] = _difference(ours, arcore) | {"T_cam_device": arcore.tolist(), "rotation_spread_deg": spread}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("result", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--recording", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = compare(args.result, args.reference, args.recording)
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
