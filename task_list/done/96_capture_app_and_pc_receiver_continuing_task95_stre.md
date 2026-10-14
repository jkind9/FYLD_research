---
id: "96"
title: Capture app and PC receiver, continuing Task95: stream every frame through a phone-side queue, one session folder on the PC
status: done
files:
  - experiments/01_camera_capture_delivery/capture/**
  - experiments/01_camera_capture_delivery/phonecheck/**
  - experiments/01_camera_capture_delivery/phone_session_v2.md
  - experiments/01_camera_capture_delivery/phone_session_v1.md
  - experiments/01_camera_capture_delivery/host/**
  - experiments/01_camera_capture_delivery/tests/**
  - experiments/01_camera_capture_delivery/build/**
  - experiments/01_camera_capture_delivery/README.md
  - experiments/open_vio/recorder/**
  - experiments/open_vio/build/**
  - experiments/open_vio/host/**
  - experiments/open_vio/tests/**
  - experiments/open_vio/README.md
  - src/live/**
  - README.md
  - learning/08_phone_and_deployment.md
  - learning/12_rebuilding_arcore.md
  - research/**
created: 2026-10-14
---
# Capture app and PC receiver, continuing Task95: stream every frame through a phone-side queue, one session folder on the PC

## Goal

Continues Task95 (closed as a hand-over 14 Oct 2026): one Redmi capture app (ARCore shared camera) that queues every Camera2 frame on the phone's storage and streams it to the PC with windowed cumulative acknowledgements and resume after reconnect, plus a PC receiver (port 8766) that writes one phone session v2 folder that src/live, open_vio and the offline methods read

## Plan

1. phone_session_v2.md (messages, fields, units, clocks, payload, ack and resume rules, PC folder layout) and a v2 fixture. 2. Tests first: fixture on JVM and in host/session_v2.py; loopback fake phone with a deliberate disconnect and resume; synthetic v2 folder read by session_v2, src/live replay and recording.py --euroc; clock_check on v2. 3. git mv phonecheck to capture (org.fyld.capture); git mv Stream B's recorder classes in; add disk queue, windowed sender, IMU batches, telemetry, storage guard, link-speed and Deflater checks. 4. host/capture_receiver.py with on_frame, PNG grey, summary.json; src/live/stream.py replays v2; open_vio recording.py and clock_check.py read v2. 5. build-capture.sh in WSL with JVM tests; retire build-phonecheck.sh and build-recorder.sh; APK to mobile deployment/capture_<date>/. 6. Owner Redmi run (house walk + 60 s rest), report. 7. Docs: README, experiment 01, open_vio README, learning 8 and 12, research; finish, commit only these files, push.

## Files

- README.md (+2 -2, 415 lines)
- experiments/01_camera_capture_delivery/README.md (+42 -3, 351 lines)
- experiments/01_camera_capture_delivery/build/build-capture.sh (+25 -0, 25 lines)
- experiments/01_camera_capture_delivery/build/build-phonecheck.sh (+0 -21, 0 lines)
- experiments/01_camera_capture_delivery/capture/app/build.gradle (+28 -0, 28 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/AndroidManifest.xml (+24 -0, 24 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/ArcoreRecord.java (+111 -0, 111 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CameraPreview.java (+77 -0, 77 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CaptureActivity.java (+740 -0, 740 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/DiskQueue.java (+202 -0, 202 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/FrameAssembler.java (+109 -0, 109 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/FrameCapture.java (+146 -0, 146 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/FrameWriter.java (+174 -0, 174 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/ImuLogger.java (+126 -0, 126 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/RecordingMeta.java (+83 -0, 83 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/Report.java (+59 -0, 59 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/SessionFrame.java (+69 -0, 69 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/SessionMessages.java (+130 -0, 130 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/SharedCameraRig.java (+171 -0, 171 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/TrackingStats.java (+141 -0, 141 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/Uploader.java (+225 -0, 225 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/res/values/strings.xml (+4 -0, 4 lines)
- experiments/01_camera_capture_delivery/capture/app/src/test/java/org/fyld/capture/SendingTest.java (+269 -0, 269 lines)
- experiments/01_camera_capture_delivery/capture/app/src/test/java/org/fyld/capture/SessionV2Test.java (+200 -0, 200 lines)
- experiments/01_camera_capture_delivery/capture/app/src/test/resources/session_v2/frame.bin (+0 -0, 0 lines)
- experiments/01_camera_capture_delivery/capture/app/src/test/resources/session_v2/imu.bin (+0 -0, 0 lines)
- experiments/01_camera_capture_delivery/capture/build.gradle (+3 -0, 3 lines)
- experiments/01_camera_capture_delivery/capture/gradle.properties (+2 -0, 2 lines)
- experiments/01_camera_capture_delivery/capture/settings.gradle (+8 -0, 8 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+377 -0, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+4 -3, 47 lines)
- experiments/01_camera_capture_delivery/host/receiver.py (+3 -1, 96 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+27 -21, 158 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+184 -0, 184 lines)
- experiments/01_camera_capture_delivery/phone_session_v1.md (+1 -1, 79 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+199 -0, 199 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/build.gradle (+0 -28, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/AndroidManifest.xml (+0 -22, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CameraPreview.java (+0 -77, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CheckActivity.java (+0 -561, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/FrameCapture.java (+0 -142, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/HostStream.java (+0 -161, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/Report.java (+0 -58, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/SessionFrame.java (+0 -123, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/TrackingStats.java (+0 -141, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/res/values/strings.xml (+0 -4, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/test/java/org/fyld/phonecheck/SessionFrameTest.java (+0 -115, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/test/resources/session_v1/frame_header.json (+0 -19, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/test/resources/session_v1/frame_payload.bin (+0 -0, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/build.gradle (+0 -3, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/gradle.properties (+0 -2, 0 lines)
- experiments/01_camera_capture_delivery/phonecheck/settings.gradle (+0 -8, 0 lines)
- experiments/01_camera_capture_delivery/tests/conftest.py (+6 -0, 6 lines)
- experiments/01_camera_capture_delivery/tests/fake_phone.py (+149 -0, 149 lines)
- experiments/01_camera_capture_delivery/tests/fixtures/session_v1/frame_payload.bin (+0 -0, 0 lines)
- experiments/01_camera_capture_delivery/tests/test_accuracy.py (+1 -1, 183 lines)
- experiments/01_camera_capture_delivery/tests/test_capture_receiver.py (+232 -0, 232 lines)
- experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py (+1 -1, 124 lines)
- experiments/01_camera_capture_delivery/tests/test_session_v1.py (+1 -1, 130 lines)
- experiments/01_camera_capture_delivery/tests/test_session_v2.py (+121 -0, 121 lines)
- experiments/open_vio/README.md (+28 -23, 161 lines)
- experiments/open_vio/build/build-recorder.sh (+0 -18, 0 lines)
- experiments/open_vio/host/clock_check.py (+17 -16, 128 lines)
- experiments/open_vio/host/receive_recording.py (+0 -95, 0 lines)
- experiments/open_vio/host/recording.py (+44 -39, 181 lines)
- experiments/open_vio/recorder/app/build.gradle (+0 -23, 0 lines)
- experiments/open_vio/recorder/app/src/main/AndroidManifest.xml (+0 -23, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/CsvLog.java (+0 -43, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/FrameWriter.java (+0 -112, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/ImuLogger.java (+0 -89, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/RecorderActivity.java (+0 -417, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/RecordingMeta.java (+0 -88, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/SharedCameraRig.java (+0 -171, 0 lines)
- experiments/open_vio/recorder/app/src/main/java/org/fyld/rawrecorder/Uploader.java (+0 -85, 0 lines)
- experiments/open_vio/recorder/build.gradle (+0 -1, 0 lines)
- experiments/open_vio/recorder/gradle.properties (+0 -2, 0 lines)
- experiments/open_vio/recorder/settings.gradle (+0 -5, 0 lines)
- experiments/open_vio/tests/conftest.py (+1 -0, 19 lines)
- experiments/open_vio/tests/synthetic.py (+28 -29, 57 lines)
- experiments/open_vio/tests/test_clock_check.py (+12 -0, 60 lines)
- experiments/open_vio/tests/test_receive_recording.py (+0 -66, 0 lines)
- experiments/open_vio/tests/test_recording.py (+9 -16, 84 lines)
- learning/08_phone_and_deployment.md (+16 -1, 89 lines)
- learning/12_rebuilding_arcore.md (+7 -5, 97 lines)
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
- research/visual_inertial_odometry/README.md (+1 -1, 27 lines)
- research/visual_inertial_odometry/phone_recording_and_clocks.md (+12 -0, 55 lines)
- src/live/README.md (+4 -3, 73 lines)
- src/live/run.py (+10 -9, 146 lines)
- src/live/stream.py (+16 -4, 48 lines)
- src/live/tests/test_stream.py (+19 -0, 19 lines)

## Checked

- `.venv-sfm/Scripts/python.exe -m pytest experiments/01_camera_capture_delivery/tests experiments/open_vio/tests --basetemp .test_tmp96_host4 -q -> 270 passed, 1 skipped; .venv-yolo/Scripts/python.exe -m pytest src/live/tests --basetemp .test_tmp96_live3 -q -> 12 passed; wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh -> 20 JVM tests passed and APK staged; regression tests failed before fixes; final diff review -> no remaining reproducible blockers; git diff --check -> clean`
- cost: 58 min from begin to finish; Claude tokens 31,931,260 (fresh input 270,591, cache read 31,442,047, output 218,622; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.16 (was 0.25)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 2 in 4491 words: same-opening "the", bold-labels "5 items"

## Left over

Owner must install mobile deployment/capture_20261014/fyld-capture.apk from email, run all checks, record the house walk (upstairs, downstairs, upstairs) and 60 s rest, and measure capture fps, dropped frames, IMU rates, Wi-Fi MB/s, sending time after Stop, storage and clock_check.py offset. Zero dropped frames remains unverified on Redmi; overflow of the 30-frame writer buffer is counted as dropped. Then run src.live.run --replay and recording.py --euroc on the real session. Untracked mobile_deployments belongs to earlier work and is excluded from this task commit.
