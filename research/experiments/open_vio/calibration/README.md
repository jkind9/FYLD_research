# Phone calibration with Kalibr

This folder measures what a tracker needs to know about the phone: the camera model, the rotation and offset between the motion sensors (IMU) and the camera, the time offset between them, and the IMU's noise. It belongs to the [open visual-inertial tracking experiment](../README.md).

[Kalibr](https://github.com/ethz-asl/kalibr) (BSD-3) does the estimation from a recording of a printed AprilGrid target (a grid of square tags). These scripts prepare its inputs, run it in Docker, and compare its result with a reference.

| File | What it does |
|---|---|
| `prepare.py` | Converts a calibration recording (`--recording`) or an EuRoC `mav0` folder (`--mav0`) into Kalibr's bag-creator folder and `target.yaml`. With `--rest <rest recording>` it also writes `imu.yaml` from an Allan fit. `--tag-size` is required and must be measured on the print with a ruler, because printers rescale pages. |
| `allan.py` | `imu_noise(rec)` computes the Allan deviation of each gyroscope and accelerometer axis from a recording at rest. White noise is read at tau = 1 s and bias random walk at tau = 3 s. A recording too short to show the random-walk line returns no random walk. Writes `allan.json`. |
| `kalibr_files.py` | Writers and readers for Kalibr's files: `to_kalibr_folder`, `imu_yaml` (noise values inflated by 2 for white noise and 10 for random walk), `aprilgrid_yaml`, `read_camchain` and `transform_difference`. |
| `arcore_extrinsics.py` | `camera_from_device(rec)` gives the camera-to-IMU transform implied by ARCore's own poses in a recording, to compare with Kalibr's. It reads public outputs only. |
| `compare.py` | `compare(result, reference, walk)` reports the rotation (degrees), translation (metres) and time-shift (milliseconds) difference between a Kalibr camera-IMU result and a reference calibration, and against ARCore's transform. |
| `to_sitescan.py` | `sitescan_calibration(camchain)` turns a Kalibr camera-IMU result into the calibration JSON that `sitescan.session.read_calibration` reads: intrinsics, image size, distortion, and `imu_from_camera` (the inverse of Kalibr's `T_cam_imu`). The time shift is kept for the record; sitescan does not apply it. |
| `run_kalibr.sh` | Runs Kalibr in Docker. Stages: `image` (build the image), `cameras` and `imu`. Logs START and END lines, or FAILED, to `<out>/kalibr.log`. |
| `tumvi_check.sh` | Runs the camera and camera-IMU stages on TUM-VI's published calibration recordings, to check the pipeline against TUM-VI's own calibration. |

## How to run it

Python scripts run from the repository root with the project environment, on the CPU:

```text
.venv/Scripts/python.exe research/experiments/open_vio/calibration/prepare.py --recording <calibration walk> --out <folder> --tag-size <measured metres> [--rest <rest recording>]
.venv/Scripts/python.exe research/experiments/open_vio/calibration/allan.py <rest recording>
.venv/Scripts/python.exe research/experiments/open_vio/calibration/compare.py <data-camchain-imucam.yaml> [--reference <camchain.yaml>] [--recording <walk>] [--out compare.json]
.venv/Scripts/python.exe research/experiments/open_vio/calibration/to_sitescan.py <data-camchain-imucam.yaml> --out <calibration.json>
```

The shell scripts need WSL and Docker, because Kalibr needs ROS 1, which WSL's Ubuntu 24.04 does not have. Run them with WSL paths:

```text
wsl -- bash research/experiments/open_vio/calibration/run_kalibr.sh image
wsl -- bash research/experiments/open_vio/calibration/run_kalibr.sh cameras <kalibr folder> <target.yaml> <model> <out>
wsl -- bash research/experiments/open_vio/calibration/run_kalibr.sh imu <kalibr folder> <target.yaml> <camchain.yaml> <imu.yaml> <out> [offset search, s]
```

From Git Bash, set `MSYS_NO_PATHCONV=1` first, or Git Bash rewrites `/mnt/c/...` arguments before `wsl` sees them. `tumvi_check.sh` takes `RUNS` and `DATA` as environment variables. The scripts read recordings through [`../host/recording.py`](../host/README.md).

## Where results are recorded

The TUM-VI check, the printed-target instructions and the Redmi calibration status are in the [open_vio README](../README.md).
