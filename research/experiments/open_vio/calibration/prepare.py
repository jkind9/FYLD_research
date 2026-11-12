"""Prepare Kalibr's inputs from a raw recording (or any EuRoC/ASL folder).

    python experiments/open_vio/calibration/prepare.py --recording <calibration walk> --out <folder> \
        --tag-size 0.024 [--rest <recording at rest>]
    python experiments/open_vio/calibration/prepare.py --mav0 <EuRoC mav0 folder> --out <folder> \
        --cols 6 --rows 6 --tag-size 0.088

Writes <out>/kalibr (the bag-creator folder), <out>/target.yaml and, with --rest, <out>/imu.yaml from an Allan fit
of the rest recording. The printed tag size must be measured with a ruler: printers rescale pages.
"""

import argparse
import json
import sys
from pathlib import Path

import allan
import kalibr_files

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
import recording  # noqa: E402

HYPERPARAMETERS = {
    "target": {"value": "AprilGrid 6 x 8, spacing 0.3, tag size as measured on the print", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "noise_inflation": {"value": "white noise x2, random walk x10", "source": "TUM-VI imu_config.yaml (BMI160, used with Kalibr)"},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--recording", type=Path)
    source.add_argument("--mav0", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rest", type=Path, help="motion-sensor recording at rest, for imu.yaml")
    parser.add_argument("--cols", type=int, default=6)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--tag-size", type=float, required=True, help="measured tag edge in metres")
    parser.add_argument("--spacing", type=float, default=0.3)
    args = parser.parse_args()
    mav0 = args.mav0
    if args.recording:
        rec = recording.load(args.recording)
        problems = recording.problems(rec)
        if problems:
            print("recording problems:\n" + "\n".join(problems))
            return 1
        mav0 = recording.to_euroc(rec, args.out / "euroc") / "mav0"
    kalibr_files.to_kalibr_folder(mav0, args.out / "kalibr")
    (args.out / "target.yaml").write_text(kalibr_files.aprilgrid_yaml(cols=args.cols, rows=args.rows, tag_size_m=args.tag_size,
                                                                      spacing=args.spacing), encoding="utf-8")
    if args.rest:
        noise = allan.imu_noise(recording.load(args.rest))
        (args.out / "allan.json").write_text(json.dumps(noise, indent=2), encoding="utf-8")
        (args.out / "imu.yaml").write_text(kalibr_files.imu_yaml(noise), encoding="utf-8")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
