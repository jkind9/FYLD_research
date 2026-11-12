"""Write a Kalibr camera-IMU result as the calibration file sitescan reads.

    python research/experiments/open_vio/calibration/to_sitescan.py <data-camchain-imucam.yaml> --out calibration.json

sitescan takes intrinsics and the camera's pose in the IMU frame (imu_from_camera, the inverse of
Kalibr's T_cam_imu) from this file, so it never needs a YAML reader. The distortion model, its
coefficients and Kalibr's time shift (t_imu = t_cam + shift) are kept for the record; sitescan's
stages treat the camera as a pinhole today.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kalibr_files


def sitescan_calibration(camchain: Path, camera: str = "cam0") -> dict:
    """The sitescan calibration record for one camera of a Kalibr camchain-imucam file."""
    chain = kalibr_files.read_camchain(camchain, camera)
    if chain["T_cam_imu"] is None:
        raise ValueError(f"{camchain} has no T_cam_imu: run Kalibr's camera-IMU stage first")
    fx, fy, cx, cy = chain["intrinsics"]
    width, height = chain["resolution"]
    return {
        "camera": {"fx": fx, "fy": fy, "cx": cx, "cy": cy, "width": width, "height": height},
        "distortion_model": chain["model"],
        "distortion": list(chain["distortion"]),
        "imu_from_camera": np.linalg.inv(chain["T_cam_imu"]).tolist(),
        "time_shift_cam_imu_s": chain["timeshift_cam_imu"],
        "source": str(camchain),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("camchain", type=Path)
    parser.add_argument("--camera", default="cam0")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(
        json.dumps(sitescan_calibration(args.camchain, args.camera), indent=1) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
