# Open visual-inertial systems compared for the ARCore replacement

Notes of 14 October 2026 for Task91. Four open systems were cloned, built in Docker under WSL, and run offline on one camera plus IMU. The plain-language chapter is [learning/12_rebuilding_arcore.md](../../learning/12_rebuilding_arcore.md); the code is [experiments/open_vio/vio](../../experiments/open_vio/README.md).

## The systems

| System | Commit built | Licence | Method (from the authors' papers) | One camera + IMU | Paper (saved locally) |
|---|---|---|---|---|---|
| Basalt | source 0f3b2b5 (22 March 2026); Ubuntu 22.04 binary release | BSD-3-Clause | Fixed-lag smoother over keyframes with square-root marginalisation; patch-based optical-flow front end; visual-inertial mapping with non-linear factor recovery | Built around a stereo pair; monocular use checked here | Usenko, Demmel, Schubert, Stückler, Cremers, "Visual-Inertial Mapping with Non-Linear Factor Recovery", RA-L 2020, arXiv 1904.06504: [papers/basalt_usenko_2020_1904.06504.pdf](papers/basalt_usenko_2020_1904.06504.pdf) |
| Kimera-VIO | ce8c59b (10 February 2025) | BSD-2-Clause | GTSAM factor-graph smoother with IMU preintegration and structureless vision factors; part of the Kimera mesh and semantics stack | Yes (`MonoImu` front end, `params/EurocMono`) | Rosinol, Abate, Chang, Carlone, "Kimera: an Open-Source Library for Real-Time Metric-Semantic Localization and Mapping", ICRA 2020, arXiv 1910.02490: [papers/kimera_rosinol_2020_1910.02490.pdf](papers/kimera_rosinol_2020_1910.02490.pdf) |
| OKVIS2 | a2ea006 (11 December 2025) | BSD-3-Clause | Keyframe-based sliding-window optimisation with BRISK features, IMU error terms, pose-graph loop closure; real time | Camera count is set by the config; one camera used here | Leutenegger, "OKVIS2: Realtime Scalable Visual-Inertial SLAM with Loop Closure", arXiv 2202.09199: [papers/okvis2_leutenegger_2022_2202.09199.pdf](papers/okvis2_leutenegger_2022_2202.09199.pdf) |
| OpenVINS (reference only) | 6948812 (30 November 2025) | GPL-3.0 | MSCKF filter (the method ARCore is described as building on) with first-estimate Jacobians and online calibration of camera intrinsics, extrinsics and time offset | Yes (`max_cameras: 1`) | Geneva, Eckenhoff, Lee, Yang, Huang, "OpenVINS: A Research Platform for Visual-Inertial Estimation", ICRA 2020, arXiv 1910.01122: [papers/openvins_geneva_2020_1910.01122.pdf](papers/openvins_geneva_2020_1910.01122.pdf) |

## Published results on the test recording

TUM-VI paper, Table IV, RMSE ATE on room1 (146 m walk, full motion-capture coverage), **stereo** + IMU, 512 x 512 images, default parameters: OKVIS 0.06 m, VINS-Mono 0.07 m, Basalt 0.09 m, ROVIO 0.16 m. One camera is expected to do worse: depth for new points comes from motion alone, and the start needs enough motion.

## How they were run here

- Images: `experiments/open_vio/vio/docker/*.Dockerfile`, built by `build_all.sh`. Basalt from its published binary; OKVIS2 with RealSense, the neural sky mask and ROS 2 switched off; Kimera on its own dependency Dockerfile (GTSAM 4.2, OpenGV, DBoW2, Kimera-RPGO); OpenVINS in ROS 1 Noetic with `ov_eval` for its trajectory file.
- Configs: each project's own TUM-VI (or EuRoC) config as the template, with the camera, `T_cam_imu`, time shift and IMU noise swapped in from one Kalibr calibration (`vio/configs.py`). The same writers take the Redmi calibration from Task90.
- Calibration for TUM-VI: TUM-VI's published camchain (cam0 only) and its inflated IMU noise file.
- Scoring: rigid ATE (no scale fit; visual-inertial systems report metres), scaled ATE and 1 s RPE from experiment 03's evaluation, against TUM-VI's motion capture in the IMU frame.

## Results here (14 October 2026)

TUM-VI room1, one camera plus IMU, TUM-VI's calibration and inflated noise, rigid ATE against motion capture: Basalt 0.146 m (100% of frames, scale 0.993, 44 ms per frame); OKVIS2 0.505 m with its own TUM-VI noise values, diverged after 47.7 s with TUM-VI's; Kimera-VIO diverged after about 23% of frames with either noise setting (its IMU initialisation assumes a device at rest); OpenVINS 0.064 m (95% of frames placed, 12 ms per frame). Full table and run commands: [experiments/open_vio/README.md](../../experiments/open_vio/README.md#step-3-offline-comparison-of-open-trackers-task91).

## Patent caution

Google's patent US 10,802,147 B2 (priority May 2016) describes a front-end motion tracker, a slower back-end mapper and a localisation module that feeds corrected poses back. OKVIS2 and Basalt also pair a real-time sliding window with slower loop closure or mapping, a split published long before (for example PTAM's separate tracking and mapping threads, 2007, and OKVIS, 2015). OpenVINS's MSCKF dates from 2007. None of this is a legal opinion: whichever system is ported, its architecture should be listed for the freedom-to-operate check before launch.
