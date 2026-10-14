# Open visual-inertial tracking: replacing ARCore with open parts (Stream B)

This experiment rebuilds what ARCore gives the project (the camera's path in metres with gravity, calibration, depth) from open-source or hand-built parts, so the product does not depend on Google. The plan and checked licences are in [research/phone_ar_platforms/arcore_open_replacement.md](../../research/phone_ar_platforms/arcore_open_replacement.md); the plain-language explanation is [learning/12_rebuilding_arcore.md](../../learning/12_rebuilding_arcore.md).

Visual-inertial odometry (VIO) is the core part: it fuses camera images with gyroscope and accelerometer readings, which give scale in metres and the direction of gravity. Every open VIO system needs camera frames and motion-sensor readings stamped on one clock, plus a calibration of the phone. ARCore keeps all of this inside. The steps, in order:

| Step | What | Status (14 October 2026) |
|---|---|---|
| 1. Raw recorder (Task88) | Phone app records camera frames, gyroscope, accelerometer and ARCore's poses on one clock; the computer receives, checks and converts the recording | App and host tools built and tested on synthetic recordings; first Redmi recording waits for the owner to install the app |
| 2. Calibration | Kalibr: camera intrinsics, camera-to-IMU rotation, offset and time shift (printed target); IMU noise from a long recording at rest | Not started |
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
