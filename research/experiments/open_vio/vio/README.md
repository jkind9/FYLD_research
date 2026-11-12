# Open visual-inertial systems in Docker

This folder runs four open visual-inertial odometry (VIO) systems on one camera plus IMU, and scores each trajectory. VIO fuses camera images with motion-sensor readings to give a camera path in metres. It belongs to the [open visual-inertial tracking experiment](../README.md).

The systems are Basalt (BSD-3), Kimera-VIO (BSD-2), OKVIS2 (BSD-style) and OpenVINS (GPL-3.0, used as a reference only). Each runs in its own Docker image under WSL. Its config is the system's own shipped TUM-VI or EuRoC template with the camera model, camera-to-IMU transform, time shift and IMU noise replaced from one Kalibr calibration, so a new phone calibration drops in unchanged.

| File | What it does |
|---|---|
| `run.py` | Entry point. Writes the configs, runs one system on a EuRoC/ASL folder in Docker (12 GB memory and 30 minute limits), reads its trajectory and writes `scores.json`, `log.txt` and the trajectory into a run folder. |
| `configs.py` | Writes each system's config from a Kalibr calibration: `basalt_calib`, `okvis2_yaml`, `openvins_files`, `kimera_files`. |
| `trajectories.py` | `read_tum` and `read_csv` read each system's output as `(time in seconds, 4 x 4 IMU-to-world matrix)` rows. |
| `score.py` | `score(estimate, reference, tolerance_s=...)` scores with [experiment 03's evaluation](../../03_camera_pose_estimation/src/README.md): rigid error (the main score, because VIO has real scale), scaled error and one-second relative error. `to_camera` moves IMU poses onto the camera for references that follow the camera, such as ARCore. |
| `vio_report.py` | Prints one table from the `scores.json` files under a runs folder. |
| `build_images.sh` | Builds one Docker image, `vio-<system>`, from sources cloned under `~/open_vio/src`. Logs START and END, or FAILED, to `~/open_vio/build_<system>.log`. |
| `build_all.sh` | Builds the four images one after another. Parallel builds filled the 32 GB WSL machine on 14 October 2026. |
| `run_tumvi.sh` | Runs the named systems on TUM-VI room1, one at a time. |
| [`docker/`](docker/README.md) | One Dockerfile per system. |

## How to run it

This needs WSL, Docker, and the system sources cloned under `~/open_vio/src`. It runs on the CPU. Build the images once, from the repository root:

```text
wsl -- bash research/experiments/open_vio/vio/build_all.sh
```

Run one system on a recording:

```text
.venv/Scripts/python.exe research/experiments/open_vio/vio/run.py --system <basalt|okvis2|kimera|openvins> --dataset <folder containing mav0> --camchain <Kalibr camchain> --imu <Kalibr imu.yaml> --camera-rate <Hz> --reference <file> --reference-format <euroc|tum> --reference-frame <imu|camera> --profile <tumvi|phone> --run <run folder>
```

`--template-noise` keeps OKVIS2's or Kimera's own IMU noise values. The TUM-VI room1 runs go through `bash research/experiments/open_vio/vio/run_tumvi.sh <systems>` from Git Bash, with `REPO` set to the checkout that holds `data/`. Summarise runs with:

```text
.venv/Scripts/python.exe research/experiments/open_vio/vio/vio_report.py <runs folder>
```

## Where results are recorded

Trajectory errors, timings and the TUM-VI room1 comparison are in the [open_vio README](../README.md). Sources and licences are in [`research/visual_inertial_odometry/vio_systems.md`](../../../visual_inertial_odometry/vio_systems.md).
