---
id: "95"
title: Capture app: one APK that records every method's inputs and delivers one session folder to the PC
status: done
files:
  - experiments/01_camera_capture_delivery/capture/**
  - experiments/01_camera_capture_delivery/phonecheck/**
  - experiments/01_camera_capture_delivery/phone_session_v2.md
  - experiments/01_camera_capture_delivery/phone_session_v1.md
  - experiments/01_camera_capture_delivery/host/**
  - experiments/01_camera_capture_delivery/tests/**
  - experiments/01_camera_capture_delivery/build/build-capture.sh
  - experiments/01_camera_capture_delivery/build/build-phonecheck.sh
  - experiments/01_camera_capture_delivery/README.md
  - experiments/open_vio/recorder/**
  - experiments/open_vio/build/build-recorder.sh
  - experiments/open_vio/host/**
  - experiments/open_vio/tests/**
  - experiments/open_vio/README.md
  - src/live/stream.py
  - src/live/tests/**
  - src/live/README.md
  - README.md
  - learning/08_phone_and_deployment.md
  - learning/12_rebuilding_arcore.md
created: 2026-10-14
---
# Capture app: one APK that records every method's inputs and delivers one session folder to the PC

## Goal

One Redmi app (owner decision 14 October: capture on the phone, store and process on the PC) records a walk with everything the six reconstruction methods read (every camera frame as lossless grey and colour JPEG, uncalibrated gyroscope and accelerometer on the camera clock, per-frame camera settings, every ARCore output including raw depth, points and anchor corrections), writes it to the phone and sends it to the PC as one session folder that src/live, the open trackers and the offline methods all read; the live phone session v1 stream stays as a second mode; the two old apps are retired

## Plan

1. Definition first: phone_session_v2.md = the v1 per-frame ARCore record (plus camera_t_ns, the Camera2 timestamp of the image, and device_pose for the calibration cross-check) written to frames.jsonl for every ARCore frame, plus Stream B's files (cam0/<t_ns>.pgm lossless grey, cam0.csv per-frame exposure/readout/focus/ISO/OIS, gyro.csv, accel.csv uncalibrated with Android bias columns, meta.json clocks and sensors) and frames/<seq>.jpg colour (quality 90) and depth/<seq>.bin; one folder layout on the phone and on the PC. 2. Tests first: a v2 fixture both the Java encoder (JVM test) and host/session_v2.py must match; a synthetic v2 folder read by session_v2.read_session, by src/live replay, and converted by open_vio recording.py --euroc (its 19 tests moved to the new layout); the file-upload receiver (Stream B's, SHA-256 per file) writes the same layout. See them fail. 3. App: git mv phonecheck to capture (package org.fyld.capture), move Stream B's SharedCameraRig, ImuLogger, FrameWriter, CsvLog, RecordingMeta, Uploader into it (moved, not copied); FrameCapture reads ARCore per frame as now; FrameWriter also writes the colour JPEG; buttons: Record walk, Record motion sensors only (calibration rest), Send last recording, Stream live (v1, for src/live), Run all checks, ARCore notice. 4. Host: one receiver for uploads and the live stream; recording.py and clock_check.py read the v2 folder. 5. Build in WSL with JVM tests; retire rawrecorder and phonecheck build scripts once capture builds. 6. Owner: install, record the house walk (upstairs start, down, back up) and a 60 s rest, send; check rates, dropped frames, clock offset, storage and upload time, then run src.live.run --replay and recording.py --euroc on it. 7. README, experiment 01 and open_vio README, learning chapters 8 and 12; finish; commit only these files; push. Settings proposed by Claude, not owner-ruled: 640 x 480 for both grey and colour (ARCore CPU image size; higher colour resolution for reconstruction is a later option once storage and upload are measured), JPEG quality 90, IMU at fastest rate, uploads on port 8766, live stream on 8765.

## Files

- mobile_deployments/.staging-smoke_20261004_b-5ed74fb9cbd244209ffd4e82559bf89e/README.md (+7 -0, 7 lines)
- mobile_deployments/.staging-smoke_20261004_b-5ed74fb9cbd244209ffd4e82559bf89e/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/camera_20261004_camera_redmi_run6/README.md (+7 -0, 7 lines)
- mobile_deployments/camera_20261004_camera_redmi_run6/test1_mobile.apk (+0 -0, 0 lines)
- mobile_deployments/camera_task52_camera_java_review_20261006_02/README.md (+7 -0, 7 lines)
- mobile_deployments/camera_task52_camera_java_review_20261006_02/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_accuracy_20261014/README.md (+9 -0, 9 lines)
- mobile_deployments/phonecheck_accuracy_20261014/fyld-phonecheck-accuracy.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk.bin (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_archcheck/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_archcheck/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_final/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_final/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_reviewed/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_reviewed/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_smoke_20261004_c/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_smoke_20261004_c/unnamed_dist_1-debug.apk (+0 -0, 0 lines)

## Checked

- `no test exists: planning only; the build moves to a new session with a revised design`
- cost: 3 min from begin to finish; Claude tokens 1,295,811 (fresh input 6,837, cache read 1,283,287, output 5,687; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 0 in 1005 words

## Left over

All of the build, in a new session from the handover prompt: the capture app streams during capture through a disk-backed queue on the phone that keeps sending after capture stops (windowed acknowledgements, resume after reconnect); every frame carries sequence number, camera and ARCore timestamps, camera settings; IMU and device telemetry as their own messages; a PC capture receiver writes one session folder; README and learning chapter 8 still say Task95 and need the new task number
