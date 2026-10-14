# Calibrating a phone for visual-inertial tracking

Notes of 14 October 2026 for Task90. An open visual-inertial tracker needs, per phone: the camera model (focal lengths, image centre, lens distortion), the transform between the camera and the motion sensors (IMU), the time offset between them, and the IMU's noise levels. ARCore ships these for each supported phone; the open rebuild measures them. The plain-language chapter is [learning/12_rebuilding_arcore.md](../../learning/12_rebuilding_arcore.md).

## Tools

| Tool | What it measures | Licence | Notes |
|---|---|---|---|
| Kalibr ([GitHub](https://github.com/ethz-asl/kalibr), commit 1f60227 of 8 March 2024) | Camera intrinsics and distortion (`kalibr_calibrate_cameras`); camera-to-IMU rotation, translation and time offset (`kalibr_calibrate_imu_camera`); rolling-shutter camera intrinsics (`kalibr_calibrate_rs_cameras`) | BSD-3-Clause | Needs ROS 1; run here from its own `Dockerfile_ros1_20_04`. Method: Furgale, Rehder, Siegwart, "Unified Temporal and Spatial Calibration for Multi-Sensor Systems", IROS 2013, pp. 1280-1286 (continuous-time B-spline trajectory; the time offset is estimated with the transform). Rehder et al., "Extending kalibr", ICRA 2016, adds IMU axis misalignment and scale |
| Basalt calibration (`basalt_calibrate`, `basalt_calibrate_imu`, [GitLab](https://gitlab.com/VladyslavUsenko/basalt)) | Camera intrinsics (including the double-sphere fisheye model) and camera-IMU calibration | BSD-3-Clause | No ROS needed; Basalt is also a tracker candidate for step 3. Double-sphere model: Usenko, Demmel, Cremers, 3DV 2018, saved as [papers/double_sphere_usenko_2018_1807.08957.pdf](papers/double_sphere_usenko_2018_1807.08957.pdf) |
| Allan deviation (own code, `experiments/open_vio/calibration/allan.py`) | IMU white noise (noise density) and bias random walk from a recording at rest | Own code | Method of IEEE Std 952-1997; derivation in the TUM-VI paper's appendix |

## What the Kalibr documentation says

| Topic | Wording or value | Source |
|---|---|---|
| Bag creator input | Folder with `cam0/<timestamp>.png` per camera and `imu0.csv` with header `timestamp,omega_x,omega_y,omega_z,alpha_x,alpha_y,alpha_z`; "timestamps=[ns], omega=[rad/s], alpha=[m/s^2]" | [Kalibr wiki, bag format](https://github.com/ethz-asl/kalibr/wiki/bag-format) |
| IMU noise file | Keys `gyroscope_noise_density`, `accelerometer_noise_density`, `gyroscope_random_walk`, `accelerometer_random_walk`, `update_rate`; continuous-time units (rad/s/sqrt(Hz), m/s^2/sqrt(Hz), and per sqrt(Hz) for the random walks) | [Kalibr wiki, IMU noise model](https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model) |
| Reading the Allan plot | White noise: slope -1/2, read at tau = 1 s. Random walk: slope +1/2, read at tau = 3 s | same |
| Inflation | A rest recording misses motion, temperature and scale effects; for low-cost MEMS "increasing the noise model parameters by a factor of 10x or more may be necessary", otherwise "Kalibr will tend to trust your IMU measurements too much" | same |
| Camera-IMU recording | "try to excite all IMU axes (rotation and translation)"; "avoid shocks, especially at the beginning/end"; keep exposure short and light good; 20 Hz camera and 200 Hz IMU have worked; time calibration is on by default | [Kalibr wiki, camera-IMU calibration](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration) |
| Output | `camchain-imucam-<bag>.yaml` with `T_cam_imu` (IMU to camera) and `timeshift_cam_imu` (t_imu = t_cam + shift), a PDF report and a text summary | same |

## TUM-VI: the reference used to check the pipeline

Schubert, Goll, Demmel, Usenko, Stückler, Cremers, "The TUM VI Benchmark for Evaluating Visual-Inertial Odometry", IROS 2018, arXiv 1804.06120. Saved: [papers/tumvi_schubert_2018_1804.06120.pdf](papers/tumvi_schubert_2018_1804.06120.pdf) (local only).

| Fact | Value |
|---|---|
| Sensors | Two global-shutter IDS uEye cameras, 1024 x 1024 at 20 Hz (512 x 512 exports used here), fisheye lenses; Bosch BMI160 IMU at 200 Hz, a phone-class MEMS part; cameras and IMU triggered by one microcontroller |
| Image timestamp | The centre of the exposure |
| Time offset | 5.3 ms between camera and IMU, estimated once during camera-IMU calibration and corrected in both raw and calibrated data; so Kalibr on the calibrated recordings should find about 0 ms |
| IMU noise (111 hours at rest, Allan fit) | Accelerometer: noise density 1.4e-3 m/s^2/sqrt(Hz), random walk 8.6e-5 m/s^3/sqrt(Hz). Gyroscope: 8.0e-5 rad/s/sqrt(Hz), 2.2e-6 rad/s^2/sqrt(Hz). Fits over tau 0.02-1 s (white noise) and 1000-6000 s (random walk) |
| Values given to Kalibr | White noise x2, random walk x10 (`imu_config.yaml` shipped with each calibration recording) |
| Calibration recordings | calib-cam: slow motion in front of the AprilGrid; calib-imu: rapid motion in all six degrees of freedom with short exposure |
| Target | AprilGrid 6 x 6, 88 mm tags, spacing 0.3 (Basalt's `aprilgrid_6x6.json`) |
| Reference calibration | Kalibr results in `dso/camchain.yaml` of each export: cam0 pinhole-equidistant, intrinsics [190.98, 190.97, 254.93, 256.90] at 512 x 512, `T_cam_imu` given |
| Published tracker results | RMSE ATE on the room sequences (fully covered by motion capture): OKVIS 0.03-0.11 m, VINS-Mono 0.04-0.20 m, Basalt 0.02-0.13 m; used as a check in step 3 |

## Result of the TUM-VI check (Task90)

Kalibr in Docker on calib-cam1 and calib-imu1 (512 x 512 export), with TUM-VI's own noise file: focal lengths 190.985 / 190.965 px against 190.978 / 190.973; camera-to-IMU rotation 0.014 degrees and translation 1.0 mm from TUM-VI's `T_cam_imu`; time shift 0.13 ms. The first camera run diverged without `--use-blakezisserman`.

## What a phone adds

- **Rolling shutter.** Kalibr's camera-IMU model assumes a global shutter. A phone's readout of 10-30 ms smears the target during fast motion; slow, smooth motion and short exposure reduce it. Kalibr's separate rolling-shutter calibration (`kalibr_calibrate_rs_cameras`, after Oth, Furgale, Kneip, Siegwart, CVPR 2013) estimates intrinsics and readout time from camera images only.
- **Timestamp meaning.** Camera2 stamps the start of exposure of the first row (TUM-VI stamps the centre of exposure). Kalibr's estimated time offset therefore includes half the exposure plus half the readout, as the Task88 clock check also expects.
- **Fixed focus.** ARCore's FIXED focus mode keeps the lens still; the per-frame focus distance in the recording checks it.
- **IMU noise needs hours.** TUM-VI used 111 hours; the Kalibr wiki's method needs the +1/2 slope to show, which on phone-class sensors starts after minutes to hours. A 3-hour rest recording is the plan; a shorter one gives white noise only.

## Cross-check from ARCore

ARCore reports both the camera pose and the pose of the Android sensor coordinate system for every frame (`Frame.getAndroidSensorPose()`). Their relation is the camera-to-IMU transform ARCore applies. `calibration/arcore_extrinsics.py` reads it from a Task88 recording, and `compare.py` reports how far Kalibr's result is from it. This uses only ARCore's public outputs.

## Patent note

Kalibr, Basalt and the Allan method are published, open methods predating or independent of ARCore. Calibration is not among the designs claimed in US 10,802,147 or US 11,145,075 as summarised in [../phone_ar_platforms/arcore_internals.md](../phone_ar_platforms/arcore_internals.md); no patent concern noted.
