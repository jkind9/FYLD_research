---
id: "90"
title: Calibrate the Redmi camera and motion sensors with Kalibr and an Allan noise fit
status: done
priority: MEDIUM
type: experiment
blocked_by: []
blocks: []
verification_test: "experiments/open_vio/tests/"
plan_reviewed: null
files:
  - experiments/open_vio/**
  - README.md
  - experiments/README.md
  - learning/12_rebuilding_arcore.md
  - learning/00_glossary.md
  - learning/README.md
  - research/visual_inertial_odometry/**
  - data/README.md
docs:
  - experiments/open_vio/README.md
  - learning/12_rebuilding_arcore.md
  - research/visual_inertial_odometry/README.md
baseline_metric:
  source: "Task08 Redmi capability report (experiments/01_camera_capture_delivery/README.md, 'Redmi device result') and Task88 recorder"
  field: "Redmi camera intrinsics and distortion, camera-to-IMU rotation, translation and time offset, IMU noise densities and random walks"
  baseline_value: "only the phone's self-reported intrinsics [2872.36, 2872.36, 2000, 1500] at full sensor size with zero distortion and zero lens translation; no camera-to-IMU calibration; no IMU noise values"
  target: "a pipeline that turns a Redmi recording into Kalibr camchain and imu files, verified first on TUM-VI's published calibration recordings (camera-to-IMU rotation within 1 degree, translation within 2 cm, time offset within 1 ms of TUM-VI's own calibration); then run on the owner's Redmi recordings"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 90 — Calibrate the Redmi camera and motion sensors with Kalibr and an Allan noise fit

## In plain English

An open-source phone tracker needs to know exactly how the phone's camera bends light, where the camera sits relative to the motion sensors, how far apart their clocks are, and how noisy the motion sensors are. Google's tracking library ships these numbers for each phone; we have to measure them ourselves. The standard free tool, Kalibr, measures most of them from a video of a printed pattern of square markers; the noise levels come from a long recording of the phone lying still. This task builds that measurement pipeline, proves it on a public dataset whose correct answers are published, and prepares the printed pattern and the recording steps for the project's phone.

## What

1. Kalibr (BSD-3) running in Docker under WSL (it needs ROS 1, which the WSL Ubuntu 24.04 does not provide).
2. Converters from a recording (or any EuRoC/ASL folder) to Kalibr's bag-creator folder, and writers for Kalibr's target and IMU files.
3. Own Allan-deviation fit (IEEE Std 952 method) giving noise density and random walk from a recording at rest.
4. A cross-check: the camera-to-IMU transform implied by ARCore's camera and device poses in a Task88 recording, to compare with Kalibr's.
5. One driver script that runs bag creation, camera calibration and camera-IMU calibration; verified on TUM-VI's calib-cam1 and calib-imu1 recordings against TUM-VI's published calibration.
6. A printable AprilGrid for A4 and the recording steps for the owner.

## Why

Stream B step 2 (README "What comes next"). Every open visual-inertial system (Basalt, Kimera-VIO, OKVIS2, OpenVINS) reads a camera model, a camera-to-IMU transform, a time offset and IMU noise values. Wrong values make a tracker drift or fail. The Redmi's self-reported calibration is for the full 4000 x 3000 sensor, has zero distortion and no lens position, so it cannot be used as it is.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Recording reader and EuRoC writer | experiments/open_vio/host/recording.py | clock_check.py, this task | recording.py `load`, `to_euroc`, `tracking_poses`, `opencv_quaternion` |
| ARCore device pose (Android sensor frame) per frame | Task88 recorder | this task | arcore.csv columns dev_tx..dev_qw, RecorderActivity.java `onDrawFrame` |
| Docker 28.3.2 available in WSL, 32 CPUs, 30 GB RAM | workstation | — | `docker info` 14 October 2026 |
| TUM-VI is listed as a project dataset source | datasets research | — | research/datasets_and_benchmarks (EuRoC, TUM-VI family) |
| No Kalibr, Allan or calibration code exists | searched for `kalibr`, `allan`, `camchain` | — | none outside research notes |

### Plan

1. Research: Kalibr papers (Furgale, Rehder, Siegwart IROS 2013; Rehder et al. ICRA 2016), the Kalibr wiki (IMU noise model, bag format, camera-IMU calibration), Allan variance (IEEE Std 952-1997; El-Sheimy et al. 2008), TUM-VI paper (Schubert et al. IROS 2018) for the reference calibration; notes into research/visual_inertial_odometry and learning chapter 12.
2. Tests first: Allan fit recovers synthetic white noise density within 10% and random walk within 25%; a short recording reports no random walk; Kalibr folder from an EuRoC folder has `cam0/<t>.png` and `imu0.csv` with Kalibr's header; IMU yaml has the five keys with the inflation applied and the rate; target yaml has the measured tag size; ARCore cross-check recovers a synthetic camera-to-device transform. See them fail.
3. Write `calibration/allan.py`, `calibration/kalibr_files.py`, `calibration/arcore_extrinsics.py`, `calibration/run_kalibr.sh`, `calibration/compare.py`.
4. Background jobs (START/END logs): Kalibr Docker image; TUM-VI calib downloads (MD5 checked); Kalibr on TUM-VI calib-cam1 then calib-imu1; compare with TUM-VI's calibration.
5. Target PDF (A4) and owner steps; when Redmi recordings arrive (calibration video, rest recording), run the same pipeline.
6. Docs; finish; merge; push.

## Hyperparameters

| name | value | source |
|---|---|---|
| Kalibr | ethz-asl/kalibr master, Docker image from its Dockerfile_ros1_20_04; commit recorded in the run log | proposed by Claude 2026-10-14, not owner-ruled |
| camera model | pinhole-radtan (Redmi); pinhole-equi for TUM-VI to match its published fisheye model | Kalibr supported models; TUM-VI paper |
| target for the Redmi | AprilGrid 6 x 8 tags, 24 mm tag, spacing 0.3 (fits A4 at 100% scale); the printed tag size is measured with a ruler and that value used | proposed by Claude 2026-10-14, not owner-ruled |
| target for TUM-VI | AprilGrid 6 x 6, 0.088 m, spacing 0.3 | TUM-VI dataset documentation |
| IMU noise inflation for Kalibr | 10 x the Allan values | Kalibr wiki IMU noise model ("10x or more" for low-cost MEMS) |
| Allan fit | overlapping Allan deviation at 60 log-spaced cluster times; noise density read at tau = 1 s from a slope -1/2 line fitted where the local slope is within 0.15 of -1/2; random walk read at tau = 3 s from a slope +1/2 line fitted where the local slope is within 0.15 of +1/2 | Kalibr wiki and IEEE Std 952 reading rules; tolerances proposed by Claude 2026-10-14, not owner-ruled |
| image rate fed to Kalibr | every image (30 fps Redmi; 20 fps TUM-VI) | Kalibr wiki reports 20 Hz camera, 200 Hz IMU as working |
| ARCore cross-check | median over tracked frames of T_cam_device = inv(T_world_cam, OpenCV axes) * T_world_device | proposed by Claude 2026-10-14, not owner-ruled |
| acceptance on TUM-VI | rotation within 1 degree, translation within 2 cm, time offset within 1 ms of TUM-VI's calibration | proposed by Claude 2026-10-14, not owner-ruled |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Kalibr input folder | `kalibr_files.to_kalibr_folder` | kalibr_bagcreater | `cam0/<t_ns>.png`, `imu0.csv` (ns, rad/s, m/s^2) | regenerated from the recording |
| IMU noise file | `allan.py` + `kalibr_files.imu_yaml` | Kalibr, later the VIO systems | Kalibr imu.yaml keys, continuous-time units | written in the run folder |
| Calibration result | Kalibr | compare.py, the VIO comparison task | camchain-imucam yaml: T_cam_imu (IMU to camera, OpenCV camera axes), timeshift_cam_imu (s, t_imu = t_cam + shift) | run folder under experiments/open_vio/runs |

- **Source of truth:** Kalibr's camchain-imucam yaml for the camera-IMU transform and offset; the Allan fit for noise.
- **Process boundary:** Windows Python writes folders; Kalibr runs in Docker in WSL on the same files through /mnt/c.
- **Failure after each step:** each Kalibr stage writes its own outputs; a failed stage leaves earlier outputs and its log.
- **Fresh-deployment path:** `wsl -- bash experiments/open_vio/calibration/run_kalibr.sh <kalibr folder> <target yaml> <imu yaml> <model> <out>` after the Docker image is built (command in the experiment README).
- **Backward compatibility:** Task88 recordings and tools are unchanged.

## Verification

- `experiments/open_vio/tests/test_calibration.py`: the assertions in Plan step 2 (right result: Allan values; boundary: short recording, no random walk; cross-check: synthetic transform recovered to 1e-6; file formats).
- Red first: run before the modules exist.
- Real check: Kalibr on TUM-VI calib recordings compared with TUM-VI's published calibration (target above).
- Plan review: not required (MEDIUM).

## Receipts

| field | value |
|---|---|
| closing commit | merge of branch experiment/90-calibrate_the_redmi_camera_and_motion_sensors_with into main |
| files changed | experiments/open_vio/calibration/ (allan.py, kalibr_files.py, arcore_extrinsics.py, prepare.py, compare.py, run_kalibr.sh, tumvi_check.sh), tests/test_calibration.py, conftest path, README step 2; research/visual_inertial_odometry/calibration.md; learning chapter 12 calibration section; glossary unchanged; data/README TUM-VI row |
| test | 29 tests pass (10 new; red first: collection failed before the modules existed; read_camchain's test written with its code) |
| before / after | Before: no calibration tools, only the phone's self-reported full-sensor intrinsics. After: on TUM-VI, focal lengths within 0.01 px, image centre within 0.04 px, camera-to-IMU rotation 0.014 degrees and translation 1.0 mm from the published calibration, time shift 0.13 ms |
| result | Target met on TUM-VI (1 degree, 2 cm, 1 ms). Redmi calibration not run: needs the printed target, a waved calibration recording and about 3 hours at rest |

Notes:

- Kalibr: tools run via `rosrun kalibr`; the camera tool has `--dont-show-report`, not `--dont-show-plots`; outputs are named `data-camchain.yaml` / `data-camchain-imucam.yaml`; it exits 0 when it gives up, so the script checks for the result file. The first camera run diverged; `--use-blakezisserman` fixed it.
- Git Bash rewrites `/mnt/c/...` arguments to `wsl` unless `MSYS_NO_PATHCONV=1`; shell scripts edited from Windows Python got CRLF endings and failed (`pipefail`), now LF.
- PyYAML 6.0.2 installed in `.venv-sfm` for reading Kalibr results.
- Inflation changed from the planned 10x for both to TUM-VI's x2 white noise and x10 random walk, because TUM-VI's sensor is a phone-class BMI160 and those values are documented to work with Kalibr.

## Files

- README.md (+1 -1, 399 lines)
- data/README.md (+1 -0, 104 lines)
- experiments/open_vio/README.md (+47 -1, 119 lines)
- experiments/open_vio/calibration/allan.py (+85 -0, 85 lines)
- experiments/open_vio/calibration/arcore_extrinsics.py (+37 -0, 37 lines)
- experiments/open_vio/calibration/compare.py (+58 -0, 58 lines)
- experiments/open_vio/calibration/kalibr_files.py (+71 -0, 71 lines)
- experiments/open_vio/calibration/prepare.py (+61 -0, 61 lines)
- experiments/open_vio/calibration/run_kalibr.sh (+61 -0, 61 lines)
- experiments/open_vio/calibration/tumvi_check.sh (+12 -0, 12 lines)
- experiments/open_vio/tests/conftest.py (+1 -0, 17 lines)
- experiments/open_vio/tests/test_calibration.py (+124 -0, 124 lines)
- learning/12_rebuilding_arcore.md (+16 -1, 89 lines)
- research/visual_inertial_odometry/README.md (+4 -0, 22 lines)
- research/visual_inertial_odometry/calibration.md (+57 -0, 57 lines)

## Checked

- `.venv-sfm python -m pytest experiments/open_vio/tests -> 29 passed; tumvi_check.sh (Kalibr in Docker) + compare.py on TUM-VI calib-cam1/imu1 -> focal 190.985/190.965 vs 190.978/190.973 px, rotation 0.014 deg, translation 1.0 mm, time shift 0.13 ms`
- cost: 16 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0 (was 0)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 3 in 2146 words: bold-labels "5 items", bold-labels "4 items", bold-labels "4 items"

## Left over

Owner: print runs/target/aprilgrid_6x8_24mm.pdf at actual size and measure a tag; record a waved calibration walk and ~3 h at rest with the recorder; then prepare.py, run_kalibr.sh cameras/imu and compare.py with the ARCore cross-check
