---
id: "88"
title: Raw camera and motion-sensor recorder on the Redmi with ARCore reference poses
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
  - learning/README.md
  - learning/00_glossary.md
  - research/visual_inertial_odometry/**
  - research/README.md
  - research/phone_ar_platforms/arcore_open_replacement.md
docs:
  - experiments/open_vio/README.md
  - README.md
  - learning/12_rebuilding_arcore.md
baseline_metric:
  source: "Task85 check app (experiments/01_camera_capture_delivery/README.md, 'First device run'): ARCore CPU images and poses only"
  field: "raw camera frames, motion-sensor readings and ARCore poses saved together on one clock and replayable on the host"
  baseline_value: "none: no project recording has raw motion-sensor readings; the check app streams JPEG frames with ARCore poses but no gyroscope or accelerometer"
  target: "a Redmi recording whose camera, gyroscope, accelerometer and ARCore timestamps share one clock base; camera-to-gyroscope offset measured from the data; converted to the EuRoC folder layout that Basalt, Kimera-VIO, OKVIS2 and Kalibr read"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 88 — Raw camera and motion-sensor recorder on the Redmi with ARCore reference poses

## In plain English

To replace Google's tracking library with open-source parts, we first need recordings from the project's phone that an open tracker can use: every camera frame, every gyroscope and accelerometer reading, all stamped on the same clock, plus Google's own camera path recorded at the same time as the answer to compare against. This task builds a small phone app that records all of this, and a computer program that receives the recording over Wi-Fi, converts it into the standard folder layout that open trackers and calibration tools read, and checks that the clocks agree.

## What

A new Android app (`org.fyld.rawrecorder`) records camera frames through Camera2 while ARCore runs on the same camera (ARCore's shared-camera mode), together with the gyroscope and accelerometer at the fastest rate the phone allows and ARCore's camera and device poses. A second button records the motion sensors alone, for the sensor-noise measurement in the calibration task. The phone sends the finished recording to the computer. Host tools check the recording, measure the clock alignment and convert it to the EuRoC/ASL folder layout, with ARCore's path as a reference trajectory in the format the live-SLAM harness reads.

## Why

Stream B (README "What comes next") rebuilds ARCore's functions from open parts. Every open visual-inertial system and Kalibr needs camera and motion-sensor data on one clock, which no project recording has. ARCore's poses recorded alongside give a reference for every walk without extra equipment. The replacement map names clock alignment on Android as the hardest part, so it is measured here first.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| WSL Android SDK, Gradle 8.14.3, ARCore 1.56.0 dependency | Task85 build route | build-phonecheck.sh | experiments/01_camera_capture_delivery/build/build-phonecheck.sh:7-14; phonecheck/app/build.gradle:24 |
| ARCore install check, session creation, GL texture hand-over | Task85 check app | CheckActivity | experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CheckActivity.java:217-290, 306-334 |
| Length-prefixed JSON + payload framing and 4-byte acks | host/protocol.py | receiver.py, HostStream.java | experiments/01_camera_capture_delivery/host/protocol.py:24-46 (imported, not copied) |
| Trajectory file `time x y z qx qy qz qw`, camera-to-world | live_slam trajectory reader | run_live.py | experiments/live_slam/src/trajectory.py:43-51 |
| Redmi camera timestamp source is REALTIME | Task08 capability report | README | experiments/01_camera_capture_delivery/README.md, "Redmi device result" |
| No motion-sensor recorder or shared-camera code exists | searched for `SensorManager`, `SharedCamera`, `getAndroidCameraTimestamp` | — | none found in the repository |

The check app belongs to Stream A (Task87 edits it), so the recorder is a separate app under `experiments/open_vio/recorder/`; nothing in experiment 01 changes.

### Plan

1. Research: Android camera and sensor timestamp documentation, ARCore shared camera, published phone recorders (MARS logger, OpenCamera Sensors) and gyroscope-based time alignment; notes in `research/visual_inertial_odometry/` and a new `learning/12_rebuilding_arcore.md`.
2. Tests first (`experiments/open_vio/tests/`): a synthetic recording written in the phone format; the reader parses it; validation flags a missing file, a non-increasing timestamp, a camera clock seconds away from the motion-sensor clock, and ARCore camera timestamps that match no frame; the EuRoC conversion writes the expected files and interpolates the accelerometer at gyroscope times; ARCore poses convert to OpenCV camera axes; the offset estimator recovers a known 12 ms shift from a synthetic rotation within 1 ms, and the test fixes its sign; the upload receiver saves files over loopback, checks SHA-256 and rejects a corrupted file. See them fail.
3. Host code: `host/recording.py` (read, validate, convert), `host/clock_check.py` (clock report), `host/receive_recording.py` (Wi-Fi upload receiver).
4. Android app and `build/build-recorder.sh`; build in WSL; owner installs from email (MIUI blocks USB installs without a SIM).
5. Owner records on the Redmi: a 60 s walk and a 60 s motion-sensor-only rest; upload; run the clock check; report rates, drops and the offset.
6. README (experiment, root "What comes next"), learning and research updates; finish; merge to main; push.

## Hyperparameters

| name | value | source |
|---|---|---|
| camera stream | Camera2 YUV_420_888 640 x 480, luminance plane saved as 8-bit PGM (lossless) | proposed by Claude 2026-10-14, not owner-ruled; 640 x 480 is ARCore's CPU image size (Task85) and close to the EuRoC 752 x 480 the VIO systems were tuned on |
| frame rate | ARCore camera configuration's own range (30 fps on the Redmi) | inherited Task85 camera configs |
| focus | ARCore Config.FocusMode.FIXED (ARCore issues the capture requests in shared mode); per-frame focus distance recorded | proposed by Claude 2026-10-14, not owner-ruled; changed during the task from 'autofocus off at hyperfocal' after reading the SharedCamera reference |
| stabilisation | as ARCore requests; per-frame optical stabilisation mode recorded | proposed by Claude 2026-10-14, not owner-ruled; changed during the task for the same reason |
| exposure | automatic; per-frame exposure time and rolling-shutter skew recorded | proposed by Claude 2026-10-14, not owner-ruled |
| motion sensors | uncalibrated gyroscope and accelerometer if present (else calibrated), SENSOR_DELAY_FASTEST with HIGH_SAMPLING_RATE_SENSORS | proposed by Claude 2026-10-14, not owner-ruled; uncalibrated avoids Android's own bias jumps |
| ARCore | shared camera, depth off, LATEST_CAMERA_IMAGE; camera pose and device (Android sensor) pose per new frame | proposed by Claude 2026-10-14, not owner-ruled |
| writer queue | 60 frames; a full queue drops the frame and counts it | proposed by Claude 2026-10-14, not owner-ruled |
| upload | TCP port 8766, one message per file with SHA-256, acknowledged | proposed by Claude 2026-10-14 (8765 is the check app's) |
| clock check: offset search | +-200 ms around zero, 1 ms grid, angular speed magnitude, normalised cross-correlation with parabolic peak refinement | proposed by Claude 2026-10-14, not owner-ruled |
| clock check: same clock base | camera, gyroscope and accelerometer first stamps within 1 s of each other and of the app's elapsedRealtime start stamp | proposed by Claude 2026-10-14, not owner-ruled |
| EuRoC conversion | IMU rows at gyroscope times, accelerometer linearly interpolated; images PNG | EuRoC/ASL layout as read by Basalt, Kimera-VIO, OKVIS2 and Kalibr's bag creator |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Recording folder | recorder app (`Recorder.java`) | `host/recording.py` | `meta.json`, `cam0.csv` + `cam0/<t_ns>.pgm`, `gyro.csv`, `accel.csv`, `arcore.csv`; all times integer nanoseconds on the camera/sensor clock | files flushed and closed on Stop; a killed app leaves files without end stamps, which the reader reports |
| Upload | recorder app (`Uploader.java`) | `host/receive_recording.py` | protocol.py framing; header {type: file, recording, path, size, sha256}; ack = file number | phone copy kept; a re-upload overwrites the host copy |
| ARCore pose | ARCore `Camera.getPose()` | `recording.to_euroc` | OpenGL camera axes (x right, y up, looking down -z), metres, ARCore world; converted to OpenCV axes on the host | in arcore.csv |
| Clock report | `host/clock_check.py` | README, calibration task | JSON: rates, gaps, base check, offset ms with sign t_imu = t_camera + offset | written beside the recording |

- **Source of truth:** the phone's recording; the host copy is verified by SHA-256.
- **Process boundary:** phone to Windows host over Wi-Fi TCP.
- **Failure after each step:** recording stopped by the app being closed: files written so far stay, meta.json lacks the end stamps and validation says so. Upload cut: files already acknowledged stay; the phone shows the error; upload again.
- **Fresh-deployment path:** `wsl -- bash experiments/open_vio/build/build-recorder.sh`, install the APK, `python experiments/open_vio/host/receive_recording.py --out experiments/open_vio/runs/recordings`, record, Send.
- **Backward compatibility:** experiment 01 and the check app are untouched.

## Verification

- `experiments/open_vio/tests/test_recording.py`, `test_clock_check.py`, `test_receive_recording.py` with the assertions in Plan step 2 (right result; boundary: one frame and empty files; inverse: OpenCV conversion round trip; error: corrupt upload, clock mismatch).
- Red first: run before the host modules exist.
- On the device: a Redmi recording passes validation; report camera fps, IMU rates, dropped frames and the offset.
- Plan review: not required (MEDIUM).

## Receipts

| field | value |
|---|---|
| closing commit | merge of branch experiment/88-raw_camera_and_motion_sensor_recorder_on_the_redmi into main |
| files changed | experiments/open_vio/ (recorder app, host tools, tests, build script, README); learning/12_rebuilding_arcore.md; research/visual_inertial_odometry/; index rows in README, experiments/README, learning/README, glossary, research/README, arcore_open_replacement.md |
| test | 19 host tests pass (red first: collection failed before the modules existed); APK builds in WSL in 15 s, aapt2 shows package org.fyld.rawrecorder 0.1 with CAMERA, INTERNET and HIGH_SAMPLING_RATE_SENSORS |
| before / after | Before: no recording with motion-sensor readings. After: recorder and host tools ready; synthetic offset of +15 ms recovered as 15.08 ms through the command line |
| result | Partly met: everything except the device run. The Redmi recording, its rates and its measured offset wait for the owner to install the APK (MIUI blocks USB installs) |

Notes:

- ARCore owns the capture requests while it runs in shared mode (the app "must not" issue its own), so focus is set through ARCore's FIXED focus mode and stabilisation cannot be forced off; both are recorded per frame instead. This changed two rows of the Hyperparameters table from the plan.
- Patent check: nothing here copies an ARCore design; ARCore's output is recorded as a reference only.

## Files

- README.md (+1 -1, 399 lines)
- experiments/README.md (+1 -0, 259 lines)
- experiments/open_vio/README.md (+73 -0, 73 lines)
- experiments/open_vio/host/clock_check.py (+127 -0, 127 lines)
- experiments/open_vio/host/receive_recording.py (+95 -0, 95 lines)
- experiments/open_vio/host/recording.py (+176 -0, 176 lines)
- experiments/open_vio/recorder/app/build.gradle (+23 -0, 23 lines)
- experiments/open_vio/recorder/app/src/main/AndroidManifest.xml (+23 -0, 23 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/CsvLog.java (+43 -0, 43 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/FrameWriter.java (+112 -0, 112 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/ImuLogger.java (+89 -0, 89 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/RecorderActivity.java (+417 -0, 417 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/RecordingMeta.java (+88 -0, 88 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/SharedCameraRig.java (+171 -0, 171 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/Uploader.java (+85 -0, 85 lines)
- experiments/open_vio/recorder/build.gradle (+1 -0, 1 lines)
- experiments/open_vio/recorder/gradle.properties (+2 -0, 2 lines)
- experiments/open_vio/recorder/settings.gradle (+5 -0, 5 lines)
- experiments/open_vio/tests/conftest.py (+16 -0, 16 lines)
- experiments/open_vio/tests/synthetic.py (+58 -0, 58 lines)
- experiments/open_vio/tests/test_clock_check.py (+48 -0, 48 lines)
- experiments/open_vio/tests/test_receive_recording.py (+66 -0, 66 lines)
- experiments/open_vio/tests/test_recording.py (+91 -0, 91 lines)
- learning/00_glossary.md (+4 -0, 46 lines)
- learning/12_rebuilding_arcore.md (+74 -0, 74 lines)
- learning/README.md (+1 -0, 58 lines)
- research/README.md (+1 -0, 239 lines)
- research/phone_ar_platforms/arcore_open_replacement.md (+2 -0, 48 lines)
- research/visual_inertial_odometry/README.md (+18 -0, 18 lines)
- research/visual_inertial_odometry/phone_recording_and_clocks.md (+43 -0, 43 lines)

## Checked

- `.venv-sfm python -m pytest experiments/open_vio/tests -> 19 passed; build-recorder.sh in WSL -> APK built, aapt2 shows org.fyld.rawrecorder 0.1 with CAMERA, INTERNET, HIGH_SAMPLING_RATE_SENSORS; clock_check.py on a synthetic 15 ms shift -> 15.08 ms`
- cost: 15 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.3 (was n/a (no functions))
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 3 in 2559 words: bold-labels "5 items", bold-labels "3 items", bold-labels "3 items"

## Left over

Owner: install runs/apk/rawrecorder-debug.apk on the Redmi, record a 60 s walk and a 60 s rest, send both; then run clock_check.py and recording.py --euroc and add rates, drops and the offset to experiments/open_vio/README.md
