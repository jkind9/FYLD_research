# Open visual-inertial tracking: replacing ARCore with open parts (Stream B)

This experiment rebuilds what ARCore gives the project (the camera's path in metres with gravity, calibration, depth) from open-source or hand-built parts, so the product does not depend on Google. The plan and checked licences are in [research/phone_ar_platforms/arcore_open_replacement.md](../../research/phone_ar_platforms/arcore_open_replacement.md); the plain-language explanation is [learning/12_rebuilding_arcore.md](../../learning/12_rebuilding_arcore.md).

Visual-inertial odometry (VIO) is the core part: it fuses camera images with gyroscope and accelerometer readings, which give scale in metres and the direction of gravity. Every open VIO system needs camera frames and motion-sensor readings stamped on one clock, plus a calibration of the phone. ARCore keeps all of this inside. The steps, in order:

| Step | What | Status (14 October 2026) |
|---|---|---|
| 1. Capture app (Task96, continuing Task95 and Task88) | One phone app records the inputs for every reconstruction method; the PC receives one v2 session folder, checks it and converts it for the open trackers | Redmi checks passed at 33.4 MB/s; Record walk crashes; Task97 adds a diagnostic APK; a complete walk and rest are still needed |
| 2. Calibration (Task90) | Kalibr: camera intrinsics, camera-to-IMU rotation, offset and time shift (printed target); IMU noise from a long recording at rest | Pipeline built; reproduces TUM-VI's published calibration (0.014 degrees, 1.0 mm, 0.13 ms); A4 target ready; Redmi calibration waits for its recordings |
| 3. Offline comparison (Task91) | Basalt (BSD-3), Kimera-VIO (BSD-2), OKVIS2 (BSD-style), with OpenVINS (GPL-3.0, reference only), run in WSL on the recordings and scored against ARCore's poses and tape-measured distances, with time per frame | All four built and run on TUM-VI room1 with one camera: Basalt 0.146 m, OKVIS2 0.505 m (own noise settings), Kimera lost track, OpenVINS 0.064 m (reference); Redmi runs wait for recordings |
| 4. Port to the phone | Best system built for Android (NDK); learned depth resized to its tracked points replaces ARCore's depth | Not started |

Rules for this stream: build only from published methods (never take ARCore apart); note any design that might touch Google's patents US 10,802,147 or US 11,145,075 for a later patent check; CPU only; live or at least one update per second for anything deployable; permissive licences for anything that ships, GPL only as reference.

## Step 1: the capture app (Task96)

### What it records

Task96 continues Task95 and moves Task88's recorder classes into experiment 01's [capture app](../01_camera_capture_delivery/README.md#the-capture-app-and-pc-receiver-task96-14-october-2026), package `org.fyld.capture`. It replaces both the raw recorder and the check app. ARCore's shared-camera mode supplies Camera2 images while ARCore tracks. The phone captures; the PC stores and processes. One recording supplies the same walk to every reconstruction method. The [phone session v2 definition](../01_camera_capture_delivery/phone_session_v2.md) lists every message, field, unit and clock.

The app writes numbered messages to a queue on phone storage before sending them. A sender drains the queue during capture and after Stop, with up to 64 messages unacknowledged. Cumulative acknowledgements permit deletion only after the PC stores a message. After reconnecting, the sender resumes from the PC's last message held without a gap. The screen stays on and shows frames, MB and estimated time left. Recording refuses to start, and stops with a message, below 1 GB free. The separate motion-sensors-only button closes the camera and ARCore for the calibration rest recording.

| File | Contents | Units and clock |
|---|---|---|
| `session.json` | Phone, Android and ARCore versions; camera id, timestamp source, calibration and configuration; sensor details; both Android clocks at start and end; final counts and stop reason | clocks in ns; wall clock in ms since 1970 |
| `cam0/<seq>.png`, `frames/<seq>.jpg` | Lossless 8-bit grey and colour JPEG quality 90 from the same Camera2 image, 640 x 480, sensor orientation | zero-padded frame sequence from 0 |
| `frames.jsonl` | One line per frame: sequence, Camera2 and wall timestamps; exposure, frame duration, readout, focus, ISO and OIS; matching ARCore timestamp, tracking and failure reason, camera and device poses, image and texture intrinsics, tracked points, depth references, anchors and corrections | timestamps and exposure/readout in ns; focus in dioptres; poses in metres; intrinsics in pixels; ARCore axes as v1 |
| `depth/<seq>.bin` | New ARCore raw depth followed by confidence | little-endian uint16 millimetres, then uint8 confidence |
| `imu.csv` | `sensor,t_ns,x,y,z,bx,by,bz`: uncalibrated gyro and accel plus Android's bias estimates; calibrated fallback with zero bias columns where necessary | elapsedRealtime ns; rad/s, m/s^2; Android sensor axes |
| `telemetry.jsonl` | Once a second: battery, heat, free storage, queue frames and bytes, captured/sent/acknowledged/dropped counts and ARCore update time | %, Android thermal status, bytes, counts, ms |
| `summary.json` | Frames and missing sequence numbers; IMU rates and gaps; clock-base check; received MB/s; sending time after Stop | Hz, ns, MB/s, seconds |

Camera, gyroscope and accelerometer stamps are all on Android's `elapsedRealtimeNanos` clock when the camera reports a REALTIME timestamp source, as the Redmi does. The sources and wording are in [research/visual_inertial_odometry/phone_recording_and_clocks.md](../../research/visual_inertial_odometry/phone_recording_and_clocks.md).

### Settings

| Setting | Value | Why |
|---|---|---|
| Image | 640 x 480 YUV; lossless grey plus colour JPEG quality 90 | Grey for VIO; colour for depth and detection from the same walk |
| Frame rate | ARCore's camera configuration (30 fps on the Redmi) | ARCore issues the capture requests while it runs |
| Focus | ARCore's FIXED focus mode; the focus distance of every frame is recorded | Calibration assumes fixed intrinsics; ARCore owns the request in shared mode, so the app cannot set focus itself |
| Stabilisation, exposure | Whatever ARCore requests; per-frame optical stabilisation mode, exposure and readout recorded | As above; they are checked rather than forced |
| Motion sensors | Uncalibrated gyroscope and accelerometer, fastest rate (`SENSOR_DELAY_FASTEST`, `HIGH_SAMPLING_RATE_SENSORS` permission) | Android's bias correction can jump mid-recording |
| Writer | Queue on phone storage; 30 frames held in memory before the writer; overflow is counted as dropped | Network delays grow the disk queue; the Redmi run must check that capture and storage keep up |
| Grey compression | Deflater level 1 only when the phone's timed check finds it pays; otherwise raw | The CPU cost and link speed decide; the PC always stores PNG |
| Sending | TCP port 8766, window of 64 messages, cumulative acknowledgements and reconnect/resume | Port 8765 stays free for the old v1 live stream |

All settings are proposals by Claude of 14 October 2026, not owner rulings.

### Host tools

| Command | What it does |
|---|---|
| `python experiments/01_camera_capture_delivery/host/capture_receiver.py --out experiments/open_vio/runs/recordings --port 8766` | Prints the PC address, validates incoming messages, stores a v2 folder per session, acknowledges cumulatively and resumes after reconnect |
| `python experiments/open_vio/host/recording.py <recording> [--euroc <out>]` | Lists problems (missing files, timestamps not increasing, a stream on another clock, images without metadata, ARCore frames matching no image, a recording that did not stop cleanly); writes the EuRoC/ASL layout (`mav0/cam0/data/*.png`, `mav0/imu0/data.csv` at gyroscope times with the accelerometer interpolated) read by Basalt, Kimera-VIO, OKVIS2 and Kalibr's bag creator, and `arcore_camera_tum.txt` (ARCore's path in OpenCV camera axes, `time x y z qx qy qz qw`, the live-SLAM harness format) |
| `python experiments/open_vio/host/clock_check.py <recording>` | Writes `clock_check.json`: rates and gaps per stream, whether all streams start on the same clock, the share of ARCore frames that match a saved image, and the camera-to-gyroscope offset |

The offset is measured by cross-correlating the gyroscope's angular speed with the angular speed of ARCore's camera rotation (the Twist-n-Sync method family). Positive means the gyroscope stamps a motion later than the camera. ARCore places its pose at the centre of exposure of the middle image row, while Camera2 stamps the start of exposure of the first row, so even a perfectly aligned phone shows half the exposure plus half the readout time; `camera_imu_clock_offset_ms` is what remains after removing it. Published phones showed offsets up to 30 ms (MARS logger paper), so the offset is measured, not assumed. Kalibr measures it independently in step 2.

Use the `.venv-sfm` environment (numpy, scipy, OpenCV and Pillow). The receiver reuses experiment 01's `host/protocol.py` framing and offers an `on_frame` callback; `python -m src.live.run --listen 8766 --out <run>` uses it for live processing. Replay reads the same v2 folder. The protocol has no authentication or encryption: LAN only; internet use needs a tunnel and authentication, outside this task.

### Build, install, record

1. Build in WSL: `wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh`. This runs the JVM tests, builds the APK and stages `.apk` and `.apk.bin` in `mobile deployment/capture_<date>/`. The rawrecorder and phonecheck build scripts are retired.
2. Install from email on the Redmi (MIUI blocks adb installs). Start `capture_receiver.py` on the PC; enter `192.168.68.123` and port `8766` in the app. Allow Python through the Windows firewall on private networks.
3. Run all checks: ARCore setup and tracking, a 50 MiB link-speed test and a timed compression check. The ARCore notice remains in the app.
4. First walk: start upstairs, go downstairs, return upstairs, Stop. Leave the app open while the queue drains; sending continues after Stop.
5. Rest: phone flat on a table, "Record motion sensors only", 60 s, Stop; wait until sending finishes. Use about 3 hours for the later calibration noise recording.
6. Check: `clock_check.py <session>` and `recording.py <session> --euroc <out>`; then `python -m src.live.run --replay <walk session> --out <run>`. Report capture fps, dropped frames, IMU rates, Wi-Fi MB/s, sending time after Stop, storage used and `camera_imu_clock_offset_ms`.

### Tests

`python -m pytest experiments/open_vio/tests` needs no phone. Synthetic v2 sessions exercise validation, EuRoC images and IMU rows, ARCore reference paths, coordinate conversion and the clock-offset search. The offset search recovers synthetic shifts of +12 ms and -20 ms within 1 ms and reports no peak for a motionless signal. Experiment 01 tests the shared JVM/Python fixture and a fake phone disconnecting and resuming without missing or duplicate frames. `src/live/tests/test_stream.py` checks v2 replay.

### Results

The capture app builds (debug APK, package `org.fyld.capture`, minimum Android 8.0, ARCore 1.56.0). The v2 readers and reconnect path pass synthetic tests. The Redmi's capture checks passed with 100% tracking over 15 s and a 33.4 MB/s link-speed check, but Record walk crashes: the PC retained incomplete attempts with 0 and 100 frames. Task97's diagnostic APK collects crash information without USB ([experiment 01](../01_camera_capture_delivery/README.md#redmi-trial-and-crash-diagnostics-task97)). A complete walk and rest, zero-drop capture, sustained transfer, storage use, sending time after Stop and the measured clock offset remain unverified.

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

1. **Camera and camera-IMU (one walk recording, about 60-90 s).** Target flat on a wall, well lit. Start "Record walk", hold the phone 30-60 cm from the target, then move slowly: tilt up and down, left and right, roll the phone, move it sideways, up and down, closer and further, keeping the whole grid in view most of the time. Avoid knocks at the start and end. Stop and wait for the sending queue to empty.
2. **Noise (rest recording, about 3 hours).** Phone flat on a table, plugged in, nothing touching the table. "Record motion sensors only", leave it, Stop and wait for sending to finish.
3. On the computer: `prepare.py --recording <walk> --rest <rest> --tag-size <measured> --out experiments/open_vio/runs/kalibr_redmi`, then `run_kalibr.sh cameras ... pinhole-radtan` and `run_kalibr.sh imu ... 0.1` (a 100 ms offset search, since Camera2 stamps the start of exposure), then `compare.py ... --recording <walk>` for the ARCore cross-check.

## Step 3: offline comparison of open trackers (Task91)

Each system runs in its own Docker image under WSL, on one camera plus IMU (the phone's sensors), from a EuRoC/ASL folder. Its config is the project's own shipped TUM-VI (or EuRoC) config with the camera model, camera-to-IMU transform, time shift and IMU noise swapped in from one Kalibr calibration, so a Redmi calibration from step 2 plugs in unchanged. Sources, licences and method summaries: [research/visual_inertial_odometry/vio_systems.md](../../research/visual_inertial_odometry/vio_systems.md).

### Tools

| Command | What it does |
|---|---|
| `wsl -- bash experiments/open_vio/vio/build_all.sh` | Builds the four images one after another from sources cloned under `~/open_vio/src` (commits in the research note): Basalt from its Ubuntu 22.04 binary release; OKVIS2 without RealSense, the neural sky mask or ROS 2; Kimera on its own dependency Dockerfile (GTSAM 4.2 and others); OpenVINS in ROS 1 Noetic with `ov_eval`. Compiles are capped at 8 jobs: parallel full-core builds filled the 32 GB WSL machine and stopped Docker Desktop on 14 October |
| `python experiments/open_vio/vio/run.py --system <basalt, okvis2, kimera or openvins> --dataset <folder with mav0> --camchain <Kalibr camchain> --imu <Kalibr imu.yaml> --camera-rate <Hz> --reference <file> --reference-format <euroc or tum> --reference-frame <imu or camera> --profile <tumvi or phone> --run <folder> [--template-noise]` | Writes the configs, runs the system (12 GB memory and 30 min limits), reads its trajectory and scores it with experiment 03's evaluation; `--reference-frame camera` moves the IMU poses onto the camera with `T_cam_imu` for ARCore's path; `--template-noise` keeps OKVIS2's or Kimera's own IMU noise values |
| `bash experiments/open_vio/vio/run_tumvi.sh <systems>` | The TUM-VI room1 runs below (`REPO` points at the checkout holding `data/`) |
| `python experiments/open_vio/vio/vio_report.py <runs folder>` | A table from each run's `scores.json` |

Details that cost time: Basalt's binary needs `LD_LIBRARY_PATH=/root/.local/lib`. OKVIS2 finds its vocabulary beside the program, so it is called by full path, and it writes trajectories next to the images, so it reads a linked copy of the dataset. OpenVINS reads ROS bags (made with Kalibr's bag creator), and its launch file resolves the `ov_data` package even when `path_gt` is given, so an empty stand-in package is created. Kimera's monocular EuRoC settings start from the ground-truth pose (`autoInitialize: 0`), which would hand it the answer, so runs set `autoInitialize: 1` (start from the IMU); its reader refuses to run without a ground-truth folder, so it gets one with two placeholder rows (identity pose at the first IMU times) that it reads no state from.

### Results on TUM-VI room1, 14 October 2026

One camera (cam0, 512 x 512, 20 Hz) plus the BMI160 IMU at 200 Hz: 2,821 frames over 141 s and a 146 m walk inside the motion-capture room. TUM-VI's published calibration and inflated IMU noise for every system. Errors are against motion capture in the IMU frame; rigid ATE has no scale fit, because these systems report metres. Time per frame is the whole container run (including loading) divided by frames, on the workstation CPU in Docker under WSL.

| Run | Licence | Rigid ATE (m) | Scaled ATE (m) | RPE 1 s (m) | Frames placed | ms per frame |
|---|---|---|---|---|---|---|
| Basalt | BSD-3 | **0.146** | 0.146 (scale 0.993) | 0.024 | 100% | 44 |
| OKVIS2, its own TUM-VI noise values | BSD-3 | 0.505 | 0.444 | 0.078 | 100% | 30 |
| OKVIS2, TUM-VI's noise values | BSD-3 | diverged after 47.7 s (positions to 868 km) | | | 100% | 23 |
| Kimera-VIO, either noise setting | BSD-2 | diverged: optimiser failed after about 23% of frames | | | 23% | 20 |
| OpenVINS (reference only) | GPL-3.0 | 0.064 | 0.064 | 0.013 | 95% | 12 |

Published on the same recording with **two** cameras (TUM-VI paper, Table IV): OKVIS 0.06 m, VINS-Mono 0.07 m, Basalt 0.09 m. One camera is expected to do worse, because depth for new points comes from motion alone.

What this says:

- **Basalt is the strongest permissive candidate on this recording.** Every frame was tracked, its own metric scale is within 0.7%, the error is 0.146 m over 146 m, and it takes 44 ms per frame including start-up, well inside the 1-update-per-second floor. It is the first candidate for the phone port, pending Redmi recordings.
- **OKVIS2 is sensitive to the IMU noise setting.** It diverged with TUM-VI's values (3 to 10 times smaller than its own) and tracked with its own, at 3.5 times Basalt's error.
- **Kimera-VIO's monocular mode did not work here.** Its IMU start-up assumes the device starts at rest, and its optimiser failed about a quarter of the way through. Its stereo mode was not tried, since the phone has one usable camera.
- **OpenVINS (GPL) sets the accuracy target** at 0.064 m with one camera. It cannot ship under the project's licence rule; its MSCKF method is published (2007), so a permissive re-implementation is possible.
- This is one recording from a rig with a global-shutter camera and a hardware-synchronised IMU. The Redmi adds a rolling shutter, software timestamps and a noisier IMU, so the ranking must be repeated on Redmi recordings with ARCore's path as the reference.
