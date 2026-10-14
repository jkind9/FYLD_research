# Open visual-inertial tracking: replacing ARCore with open parts (Stream B)

This experiment rebuilds what ARCore gives the project (the camera's path in metres with gravity, calibration, depth) from open-source or hand-built parts, so the product does not depend on Google. The plan and checked licences are in [research/phone_ar_platforms/arcore_open_replacement.md](../../research/phone_ar_platforms/arcore_open_replacement.md); the plain-language explanation is [learning/12_rebuilding_arcore.md](../../learning/12_rebuilding_arcore.md).

Visual-inertial odometry (VIO) is the core part: it fuses camera images with gyroscope and accelerometer readings, which give scale in metres and the direction of gravity. Every open VIO system needs camera frames and motion-sensor readings stamped on one clock, plus a calibration of the phone. ARCore keeps all of this inside. The steps, in order:

| Step | What | Status (14 October 2026) |
|---|---|---|
| 1. Raw recorder (Task88) | Phone app records camera frames, gyroscope, accelerometer and ARCore's poses on one clock; the computer receives, checks and converts the recording | App and host tools built and tested on synthetic recordings; first Redmi recording waits for the owner to install the app |
| 2. Calibration (Task90) | Kalibr: camera intrinsics, camera-to-IMU rotation, offset and time shift (printed target); IMU noise from a long recording at rest | Pipeline built; reproduces TUM-VI's published calibration (0.014 degrees, 1.0 mm, 0.13 ms); A4 target ready; Redmi calibration waits for its recordings |
| 3. Offline comparison | Basalt (BSD-3), Kimera-VIO (BSD-2), OKVIS2 (BSD-style), with OpenVINS (GPL-3.0, reference only), run in WSL on the recordings and scored against ARCore's poses and tape-measured distances, with time per frame | Not started |
| 4. Port to the phone | Best system built for Android (NDK); learned depth resized to its tracked points replaces ARCore's depth | Not started |

Rules for this stream: build only from published methods (never take ARCore apart); note any design that might touch Google's patents US 10,802,147 or US 11,145,075 for a later patent check; CPU only; live or at least one update per second for anything deployable; permissive licences for anything that ships, GPL only as reference.

## Step 1: the raw recorder (Task88)

### What it records

The app (`recorder/`, package `org.fyld.rawrecorder`) opens the rear camera through ARCore's shared-camera mode: ARCore tracks as usual while a second 640 x 480 stream from the same capture session goes to the app. One button records a walk; a second records the motion sensors alone with the camera closed (for the IMU noise measurement in step 2, which needs hours at rest). A third sends the last recording to the computer over Wi-Fi.

| File | Contents | Units and clock |
|---|---|---|
| `meta.json` | Phone, Android and ARCore versions; camera id, timestamp source (REALTIME or UNKNOWN), reported calibration and lens pose; ARCore camera configuration and CPU-image intrinsics; each motion sensor's type, name, vendor, resolution and minimum delay; both Android clocks (`elapsedRealtimeNanos`, `nanoTime`) at start and end; counts of frames saved and dropped | — |
| `cam0/<t_ns>.pgm` | Luminance (grey) plane of every camera image, lossless 8-bit PGM, 640 x 480, sensor orientation (landscape) | file name = Camera2 sensor timestamp, ns |
| `cam0.csv` | Per capture: `t_ns, exposure_ns, frame_duration_ns, rolling_shutter_skew_ns, focus_distance_dpt, iso, ois_mode` (-1 when the phone does not report a value) | ns; focus in dioptres |
| `gyro.csv`, `accel.csv` | `t_ns, x, y, z, bx, by, bz`: the uncalibrated sensor (no Android bias correction) and Android's own bias estimate; the calibrated sensor with zero bias columns if the phone has no uncalibrated one | rad/s, m/s^2; Android sensor axes |
| `arcore.csv` | Per new ARCore frame: `t_ns` (ARCore's timestamp), `camera_t_ns` (the Android camera timestamp of that image), tracking state, camera pose `tx..qw`, device pose `dev_tx..dev_qw` (ARCore's pose of the Android sensor frame), failure reason | metres; camera pose in OpenGL camera axes (x right, y up, looking down -z), camera-to-world |

Camera, gyroscope and accelerometer stamps are all on Android's `elapsedRealtimeNanos` clock when the camera reports a REALTIME timestamp source, as the Redmi does. The sources and wording are in [research/visual_inertial_odometry/phone_recording_and_clocks.md](../../research/visual_inertial_odometry/phone_recording_and_clocks.md).

### Settings

| Setting | Value | Why |
|---|---|---|
| Image | 640 x 480 YUV, grey plane only | ARCore's own CPU image size; close to the 752 x 480 the VIO systems were tuned on; colour is not used by VIO |
| Frame rate | ARCore's camera configuration (30 fps on the Redmi) | ARCore issues the capture requests while it runs |
| Focus | ARCore's FIXED focus mode; the focus distance of every frame is recorded | Calibration assumes fixed intrinsics; ARCore owns the request in shared mode, so the app cannot set focus itself |
| Stabilisation, exposure | Whatever ARCore requests; per-frame optical stabilisation mode, exposure and readout recorded | As above; they are checked rather than forced |
| Motion sensors | Uncalibrated gyroscope and accelerometer, fastest rate (`SENSOR_DELAY_FASTEST`, `HIGH_SAMPLING_RATE_SENSORS` permission) | Android's bias correction can jump mid-recording |
| Writer | 60-frame buffer pool; a full pool drops the frame and counts it | Memory stays bounded; drops are visible |
| Upload | TCP port 8766, one message per file with SHA-256, each acknowledged | The check app uses 8765 |

All settings are proposals by Claude of 14 October 2026, not owner rulings.

### Host tools

| Command | What it does |
|---|---|
| `python experiments/open_vio/host/receive_recording.py --out experiments/open_vio/runs/recordings` | Listens for the app's upload; saves each file after checking its size and SHA-256; refuses paths outside the recording; writes `received.json` |
| `python experiments/open_vio/host/recording.py <recording> [--euroc <out>]` | Lists problems (missing files, timestamps not increasing, a stream on another clock, images without metadata, ARCore frames matching no image, a recording that did not stop cleanly); writes the EuRoC/ASL layout (`mav0/cam0/data/*.png`, `mav0/imu0/data.csv` at gyroscope times with the accelerometer interpolated) read by Basalt, Kimera-VIO, OKVIS2 and Kalibr's bag creator, and `arcore_camera_tum.txt` (ARCore's path in OpenCV camera axes, `time x y z qx qy qz qw`, the live-SLAM harness format) |
| `python experiments/open_vio/host/clock_check.py <recording>` | Writes `clock_check.json`: rates and gaps per stream, whether all streams start on the same clock, the share of ARCore frames that match a saved image, and the camera-to-gyroscope offset |

The offset is measured by cross-correlating the gyroscope's angular speed with the angular speed of ARCore's camera rotation (the Twist-n-Sync method family). Positive means the gyroscope stamps a motion later than the camera. ARCore places its pose at the centre of exposure of the middle image row, while Camera2 stamps the start of exposure of the first row, so even a perfectly aligned phone shows half the exposure plus half the readout time; `camera_imu_clock_offset_ms` is what remains after removing it. Published phones showed offsets up to 30 ms (MARS logger paper), so the offset is measured, not assumed. Kalibr measures it independently in step 2.

Use the `.venv-sfm` environment (numpy, scipy, OpenCV). The receiver uses only the standard library and experiment 01's `host/protocol.py` framing.

### Build, install, record

1. Build in WSL: `wsl -d Ubuntu -- bash experiments/open_vio/build/build-recorder.sh` (writes `runs/apk/rawrecorder-debug.apk` and its SHA-256).
2. Install: copy the APK to the phone and open it (MIUI blocks installs over USB debugging without a SIM; the check app was installed from email).
3. On the computer: start `receive_recording.py` (it prints the address to type into the app; allow Python through the Windows firewall on private networks).
4. Walk: press "Record walk" once ARCore says tracking, walk slowly for about 60 s pointing at textured things, end where you started, press Stop, then "Send last recording".
5. Rest: put the phone flat on a table, press "Record motion sensors only", leave it (60 s for a first check; about 3 hours for the noise measurement), Stop, Send.
6. Check: `clock_check.py` and `recording.py --euroc` on each received folder.

### Tests

`python -m pytest experiments/open_vio/tests` (19 tests, no phone needed): a synthetic recording in the app's format is read and validated; each problem above is detected; the EuRoC conversion writes the expected images, IMU rows and reference path; ARCore poses convert to OpenCV axes and back; the offset search recovers synthetic shifts of +12 ms and -20 ms within 1 ms and reports no peak for a motionless signal; the upload receiver saves and acknowledges files, and refuses a corrupted file or a path outside the recording.

### Results

The app builds (debug APK, package `org.fyld.rawrecorder` 0.1, minimum Android 8.0, ARCore 1.56.0). It has not yet run on the Redmi. The first device recording will report camera frame rate, gyroscope and accelerometer rates, dropped frames, the clock-base check and the measured offset here.

## Step 2: calibration (Task90)

A tracker needs four things about the phone: the camera model (focal lengths, image centre, lens distortion), the rotation and offset from the motion sensors (IMU) to the camera, the time offset between them, and the IMU's noise. Kalibr (BSD-3) measures the first three from a video of a printed grid of AprilTag markers; the noise comes from a long recording at rest, fitted with the Allan deviation. Sources and exact wording: [research/visual_inertial_odometry/calibration.md](../../research/visual_inertial_odometry/calibration.md).

### Tools

| Command | What it does |
|---|---|
| `python experiments/open_vio/calibration/prepare.py --recording <walk> --out <run> --tag-size <measured m> [--rest <rest recording>]` | Kalibr's bag-creator folder (`cam0/<t_ns>.png`, `imu0.csv`), `target.yaml` (AprilGrid 6 x 8, spacing 0.3) and, with a rest recording, `allan.json` and `imu.yaml` (Allan values x2 for white noise, x10 for random walk, as TUM-VI used with Kalibr). `--mav0 <EuRoC mav0>` instead of `--recording` takes any EuRoC/ASL folder |
| `python experiments/open_vio/calibration/allan.py <rest recording>` | Allan deviation of each gyroscope and accelerometer axis; noise density read at tau = 1 s on the slope -1/2 line, random walk at tau = 3 s on the slope +1/2 line; no random walk when the recording is too short to show that line |
| `wsl -- bash experiments/open_vio/calibration/run_kalibr.sh image` | Builds Kalibr's Docker image from its own `Dockerfile_ros1_20_04` (Kalibr needs ROS 1, which WSL's Ubuntu 24.04 does not have) |
| `wsl -- bash .../run_kalibr.sh cameras <kalibr folder> <target.yaml> <model> <out>` | Bag creation and camera calibration (`data-camchain.yaml`) |
| `wsl -- bash .../run_kalibr.sh imu <kalibr folder> <target.yaml> <camchain.yaml> <imu.yaml> <out> [offset search s]` | Camera-IMU calibration (`data-camchain-imucam.yaml`: `T_cam_imu`, `timeshift_cam_imu`) |
| `python experiments/open_vio/calibration/compare.py <data-camchain-imucam.yaml> [--reference <camchain.yaml>] [--recording <walk>]` | Rotation (degrees), translation (m) and time-shift differences against a reference calibration and against the camera-to-IMU transform implied by ARCore's own poses in a recording |

| `wsl -- env RUNS=<runs> DATA=<data/tumvi> bash experiments/open_vio/calibration/tumvi_check.sh` | The TUM-VI check: camera calibration on calib-cam1 (pinhole-equidistant, as TUM-VI published), then camera-IMU calibration on calib-imu1 with that camera result and TUM-VI's own IMU noise file |

Each Kalibr stage writes START and END lines (or FAILED) to `<out>/kalibr.log`. From Git Bash, set `MSYS_NO_PATHCONV=1` first, or Git Bash rewrites `/mnt/c/...` arguments into Windows paths before `wsl` sees them. Kalibr's tools run through `rosrun kalibr <tool>`; the display options are `--dont-show-report` (there is no `--dont-show-plots`), with `MPLBACKEND=Agg` set because the container has no screen.

### Check on TUM-VI, 14 October 2026

TUM-VI's own calibration (Kalibr, published in each recording's `dso/camchain.yaml`) is the reference. Same pipeline as for the Redmi: `prepare.py --mav0`, then `tumvi_check.sh`. Kalibr ran on the CPU in 17 s (camera, 436 images) and 42 s (camera-IMU, 1,038 images, 10,346 IMU readings).

| Quantity | This pipeline | TUM-VI published | Difference | Acceptance |
|---|---|---|---|---|
| Focal lengths (px) | 190.985, 190.965 | 190.978, 190.973 | 0.007, -0.008 | — |
| Image centre (px) | 254.972, 256.933 | 254.932, 256.897 | 0.040, 0.036 | — |
| Camera reprojection error (px) | 0.06 (camera stage), 0.10 (camera-IMU stage) | — | — | — |
| Camera-to-IMU rotation | — | — | 0.014 degrees | 1 degree |
| Camera-to-IMU translation | — | — | 1.0 mm | 2 cm |
| Time shift (t_imu = t_cam + shift) | 0.13 ms | about 0 (TUM-VI removed a 5.3 ms offset before publishing) | 0.13 ms | 1 ms |

All three acceptance limits are met. The first camera attempt diverged ("Max. attemps reached... Giving up...") after its intermediate estimate had already reached 191.07 px; adding Kalibr's robust Blake-Zisserman estimator (`--use-blakezisserman`) fixed it. Kalibr exits with code 0 even when it gives up, so `run_kalibr.sh` checks for the result file and logs FAILED when it is missing. Run files: `runs/kalibr_tumvi/{cam1,imu1}/out/` (reports `data-report-cam.pdf`, `data-report-imucam.pdf`, `compare.json`).

This shows the tools and conversion work on a hardware-synchronised, global-shutter rig. The Redmi adds a rolling shutter, software timestamps and a noisier IMU, so its result must still be checked against ARCore's transform and the clock check.

### Printed target for the Redmi

`runs/target/aprilgrid_6x8_24mm.pdf` (made by `rosrun kalibr kalibr_create_target_pdf --type apriltag --nx 6 --ny 8 --tsize 0.024 --tspace 0.3`): 6 x 8 tags of 24 mm with 7.2 mm gaps, 200 x 262 mm, fits A4. Print at actual size (no "fit to page"), glue flat to stiff card, and measure one tag's black square edge with a ruler; pass that value to `prepare.py --tag-size`.

### Recording for calibration (owner, Redmi)

1. **Camera and camera-IMU (one walk recording, about 60-90 s).** Target flat on a wall, well lit. Start "Record walk", hold the phone 30-60 cm from the target, then move slowly: tilt up and down, left and right, roll the phone, move it sideways, up and down, closer and further, keeping the whole grid in view most of the time. Avoid knocks at the start and end. Stop, Send.
2. **Noise (rest recording, about 3 hours).** Phone flat on a table, plugged in, nothing touching the table. "Record motion sensors only", leave it, Stop, Send.
3. On the computer: `prepare.py --recording <walk> --rest <rest> --tag-size <measured> --out experiments/open_vio/runs/kalibr_redmi`, then `run_kalibr.sh cameras ... pinhole-radtan` and `run_kalibr.sh imu ... 0.1` (a 100 ms offset search, since Camera2 stamps the start of exposure), then `compare.py ... --recording <walk>` for the ARCore cross-check.
