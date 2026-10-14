---
id: "91"
title: Offline comparison of open visual-inertial trackers on TUM-VI and Redmi recordings
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
  - research/visual_inertial_odometry/**
  - data/README.md
docs:
  - experiments/open_vio/README.md
  - learning/12_rebuilding_arcore.md
  - research/visual_inertial_odometry/README.md
baseline_metric:
  source: "Task84 live visual-only SLAM (experiments/live_slam/README.md); TUM-VI paper Table IV (published VIO results)"
  field: "camera path error in metres without a scale fit (rigid ATE), 1 s relative error, share of frames tracked, CPU time per frame, for each open VIO system on one camera plus IMU"
  baseline_value: "no VIO system has been run in the project; visual-only stella_vslam 17-28 mm after a scale fit on TUM RGB-D, with no metric scale of its own"
  target: "each of Basalt, Kimera-VIO, OKVIS2 and OpenVINS either scored on TUM-VI room1 (monocular + IMU, rigid ATE against motion capture) with time per frame, or recorded as failing with the reason; published room1 ATE (OKVIS 0.06 m, VINS-Mono 0.07 m, Basalt 0.09 m, stereo) as the sanity check; the same runner ready for Redmi recordings with ARCore poses as the reference"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 91 — Offline comparison of open visual-inertial trackers on TUM-VI and Redmi recordings

## In plain English

Several free, open-source programs can follow a camera through space using its images together with the phone's motion sensors, which is what Google's tracking library does. This task installs four of them, runs each on the same recordings with one camera, and measures how far each one's path is from the true path and how long each takes per image. The first recordings are from a public benchmark whose true path was measured with motion-capture cameras; the same runner then takes the project's own phone recordings, where Google's library's path is the comparison.

## What

1. One Docker image per system, built in WSL from each project's sources: Basalt (BSD-3, published binary release), Kimera-VIO (BSD-2, its own dependency Dockerfile), OKVIS2 (BSD-3, plain CMake), OpenVINS (GPL-3.0, reference only, ROS 1 Noetic).
2. Config writers: one camera (pinhole or equidistant fisheye), `T_cam_imu`, IMU noise and rate from Kalibr-style inputs into each system's own config format (so a Redmi calibration from Task90 plugs straight in).
3. A runner that feeds a EuRoC/ASL folder (or a ROS bag for OpenVINS) to each system, collects its trajectory and its time per frame.
4. Scoring with experiment 03's evaluation (rigid and scaled ATE, 1 s RPE) against a reference: TUM-VI motion capture (IMU frame), or ARCore's camera path for Redmi recordings (VIO poses moved to the camera frame with `T_cam_imu`).
5. TUM-VI room1 runs, monocular + IMU, with stereo where a system cannot run monocular (labelled).

## Why

Stream B step 3 (README "What comes next"). Choosing which open tracker to port to the phone needs measured accuracy and speed on one camera plus IMU, the phone's sensor set. TUM-VI room1 has a phone-class IMU (BMI160), full motion-capture coverage and published results to check the harness against. The Redmi recordings plug in when the owner records them.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| ATE (rigid and scaled) and 1 s RPE from records and (time, 4x4) references | experiments/03_camera_pose_estimation/src/evaluation.py `evaluate` | experiments/sfm/src/scoring.py | evaluation.py:86-90 |
| Trajectory file reader `time x y z qx qy qz qw` | experiments/live_slam/src/trajectory.py `read_trajectory` | run_live.py | trajectory.py:43-51 |
| EuRoC folder from a Redmi recording; ARCore reference in OpenCV camera axes | experiments/open_vio/host/recording.py `to_euroc` | Task90 prepare.py | recording.py |
| Kalibr camchain reader; ROS bag creation | experiments/open_vio/calibration/kalibr_files.py `read_camchain`; run_kalibr.sh (bag stage) | compare.py | Task90 |
| TUM-VI calibration export and reference calibration | data/tumvi (Task90) | — | data/README.md TUM-VI row |
| No VIO runner exists | searched for `basalt`, `okvis`, `kimera`, `openvins` in code | — | none outside research notes |

### Plan

1. Research: each system's paper and licence (Basalt: Usenko et al. RA-L 2020; Kimera: Rosinol et al. ICRA 2020; OKVIS2: Leutenegger 2022; OpenVINS: Geneva et al. ICRA 2020), monocular support, published TUM-VI and EuRoC numbers; notes and patent caution in research/visual_inertial_odometry; learning chapter 12 section.
2. Tests first: config writers produce each system's fields from a camchain + IMU noise (intrinsics, distortion model, T_cam_imu or its inverse as each system expects, rates, noise); trajectory readers parse each system's output format into (time s, 4x4); scoring a trajectory against itself gives zero, and against a copy scaled by 1.1 gives a non-zero rigid ATE but zero scaled ATE; IMU-to-camera conversion of poses. See them fail.
3. Images, configs, runner, scoring; TUM-VI room1 download (MD5 checked).
4. Background runs with START/END logs: each system on room1 mono (+ stereo where needed); results table.
5. Docs; finish; merge; push.

## Hyperparameters

| name | value | source |
|---|---|---|
| systems and versions | basalt release from install.sh (source commit 0f3b2b5 recorded); okvis2 a2ea006; kimera-vio ce8c59b; open_vins 6948812 | latest commits cloned 14 October 2026 |
| test recording | TUM-VI room1, 512 x 512 EuRoC export, cam0 + IMU | TUM-VI paper: full motion-capture coverage; published results |
| camera mode | monocular + IMU (the phone's sensor set); stereo only where a system cannot run monocular, labelled | owner brief 2026-10-14 (phone deployment) |
| system settings | each project's own TUM-VI config where it has one (Basalt tumvi_512_config, OKVIS2 tumvi_slam_512, OpenVINS tum_vi with max_cameras 1); Kimera's EurocMono params with TUM-VI calibration | project defaults |
| calibration | TUM-VI's published camchain and inflated IMU noise (imu_config.yaml) | TUM-VI dataset |
| loop closure | each system's default | project defaults |
| pacing | as fast as processed, no real-time waits | inherited live_slam hyperparameter |
| score | rigid ATE (no scale fit, VIO is metric) primary; scaled ATE and 1 s RPE also reported; IMU-frame poses against TUM-VI's IMU-frame motion capture | proposed by Claude 2026-10-14, not owner-ruled |
| time match tolerance | 0.01 s | proposed by Claude 2026-10-14 (motion capture at 120 Hz) |
| devices | CPU only, Docker in WSL2 | owner 2026-10-14 (no GPU) |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| System config | `vio/configs.py` | each system | each system's own format | written into the run folder |
| Trajectory | each system | `vio/score.py` | per system format, converted to (time s, 4x4 IMU-to-world) | run folder |
| Scores | `vio/score.py` | README | JSON: rigid/scaled ATE m, RPE, tracked share, ms per frame | run folder |

- **Source of truth:** each run folder (config, log, trajectory, scores).
- **Process boundary:** Windows Python writes configs and scores; systems run in Docker in WSL on /mnt/c paths.
- **Failure after each step:** a crashed system leaves its log; the run is reported as failed with the log's last error.
- **Fresh-deployment path:** clone sources, `bash vio/build_all.sh`, then `python vio/run.py --system <name> --mav0 <folder> --reference <...>` (README).
- **Backward compatibility:** Task88/90 tools unchanged.

## Verification

- `experiments/open_vio/tests/test_vio.py` (Plan step 2).
- Red first.
- Real check: room1 results against TUM-VI's published numbers for the same systems (stereo published; monocular expected worse).
- Plan review: not required (MEDIUM).

## Receipts

| field | value |
|---|---|
| closing commit | merge of branch experiment/91-offline_comparison_of_open_visual_inertial_tracker into main |
| files changed | experiments/open_vio/vio/ (configs.py, trajectories.py, score.py, run.py, vio_report.py, build_images.sh, build_all.sh, run_tumvi.sh, docker/*.Dockerfile), tests/test_vio.py, conftest path, README step 3; research/visual_inertial_odometry/vio_systems.md and papers list; learning chapter 12 tracker section; glossary (factor graph, MSCKF, sliding-window optimiser); root README Stream B |
| test | 40 tests pass (11 new; red first: collection failed before the modules existed; the template-noise and report tests were written with their code) |
| before / after | Before: no VIO system run in the project. After, TUM-VI room1 with one camera + IMU, rigid ATE: Basalt 0.146 m (100% tracked, 44 ms/frame), OKVIS2 0.505 m with its own noise (diverged with TUM-VI's), Kimera-VIO diverged at ~23%, OpenVINS 0.064 m (GPL reference, 12 ms/frame) |
| result | Target met on TUM-VI: every system scored or recorded as failing with the reason. Redmi runs wait for recordings (Task88) and calibration (Task90) |

Notes:

- Three parallel full-core image builds plus a Basalt run filled the 32 GB WSL machine; WSL stopped answering for about 6 minutes and Docker Desktop stopped (the owner's Bambu-P1S OctoEverywhere container with it). Docker Desktop was restarted the same evening and the container came back. Builds now run one at a time at 8 jobs and every run has 12 GB and 30 min limits.
- Kimera's EurocMono settings start from the ground-truth pose (autoInitialize 0); runs set autoInitialize 1 so no reference data reaches the method; its reader needs a ground-truth folder, given two placeholder identity rows it reads no state from.
- Deviation from the plan's hyperparameters: OKVIS2 and Kimera were also run with their templates' own IMU noise (labelled), because OKVIS2 diverged with TUM-VI's values.
- Time per frame includes container start-up and image loading; it is an upper bound, not the processing time per frame.

## Files

- README.md (+1 -1, 399 lines)
- experiments/open_vio/README.md (+38 -1, 156 lines)
- experiments/open_vio/tests/conftest.py (+1 -0, 18 lines)
- experiments/open_vio/tests/test_vio.py (+164 -0, 164 lines)
- experiments/open_vio/vio/build_all.sh (+6 -0, 6 lines)
- experiments/open_vio/vio/build_images.sh (+27 -0, 27 lines)
- experiments/open_vio/vio/configs.py (+122 -0, 122 lines)
- experiments/open_vio/vio/docker/basalt.Dockerfile (+8 -0, 8 lines)
- experiments/open_vio/vio/docker/kimera.Dockerfile (+6 -0, 6 lines)
- experiments/open_vio/vio/docker/okvis2.Dockerfile (+12 -0, 12 lines)
- experiments/open_vio/vio/docker/openvins.Dockerfile (+10 -0, 10 lines)
- experiments/open_vio/vio/run.py (+197 -0, 197 lines)
- experiments/open_vio/vio/run_tumvi.sh (+13 -0, 13 lines)
- experiments/open_vio/vio/score.py (+34 -0, 34 lines)
- experiments/open_vio/vio/trajectories.py (+42 -0, 42 lines)
- experiments/open_vio/vio/vio_report.py (+28 -0, 28 lines)
- learning/00_glossary.md (+3 -0, 49 lines)
- learning/12_rebuilding_arcore.md (+7 -1, 95 lines)
- research/visual_inertial_odometry/README.md (+5 -0, 27 lines)
- research/visual_inertial_odometry/vio_systems.md (+31 -0, 31 lines)

## Checked

- `.venv-sfm python -m pytest experiments/open_vio/tests -> 40 passed; run_tumvi.sh + run.py on TUM-VI room1 (mono + IMU, Docker in WSL) -> rigid ATE Basalt 0.146 m, OKVIS2 0.505 m (own noise; diverged with TUM-VI noise), Kimera diverged at 23%, OpenVINS 0.064 m`
- cost: 298 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0 (was 0)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 1992 words: bold-labels "5 items"

## Left over

Redmi runs of all four on the owner's recordings with ARCore's path as reference (needs Task88 recordings and Task90 calibration); Task 4: port Basalt to Android (NDK) and replace ARCore depth with learned depth; patent check of the chosen architecture
