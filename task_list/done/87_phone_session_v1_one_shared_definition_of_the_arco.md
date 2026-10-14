---
id: "87"
title: Phone session v1: one shared definition of the ARCore frame stream
status: done
files:
  - experiments/01_camera_capture_delivery/phone_session_v1.md
  - experiments/01_camera_capture_delivery/host/session_v1.py
  - experiments/01_camera_capture_delivery/host/receiver.py
  - experiments/01_camera_capture_delivery/tests/test_session_v1.py
  - experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py
  - experiments/01_camera_capture_delivery/phonecheck/app/src/test/resources/session_v1/frame_header.json
  - experiments/01_camera_capture_delivery/phonecheck/app/src/test/resources/session_v1/frame_payload.bin
  - experiments/01_camera_capture_delivery/phonecheck/app/src/test/java/org/fyld/phonecheck/SessionFrameTest.java
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/SessionFrame.java
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/FrameCapture.java
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/HostStream.java
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CheckActivity.java
  - experiments/01_camera_capture_delivery/phonecheck/app/build.gradle
  - experiments/01_camera_capture_delivery/build/build-phonecheck.sh
  - experiments/01_camera_capture_delivery/README.md
  - README.md
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/Report.java
created: 2026-10-14
---
# Phone session v1: one shared definition of the ARCore frame stream

## Goal

The Redmi app streams, and the host receives and checks, one written per-frame definition (image, timestamp, intrinsics, ARCore pose with tracking state and failure reason, tracked points with 3D position, pixel and id, raw depth with confidence when new, keyframe anchors whose pose updates carry ARCore's corrections), with one test fixture that both the Java encoder and the Python reader must match

## Plan

1. Write phone_session_v1.md: messages (session start, frame, report), header fields and units, payload layout (JPEG, then uint16 little-endian depth in mm, then uint8 confidence), ARCore camera axes (x right, y up, looking down -z) and the conversion to the project's OpenCV axes, point pixel = projection of the 3D point with the frame pose and intrinsics, depth intrinsics = texture intrinsics scaled to the depth size, pose corrections = one ARCore anchor per keyframe (every 1.0 s while tracking) whose later poses are resent when they move over 1 mm or 0.1 degrees. 2. Fixture: one frame header + payload (4x3 depth, rotation quaternion (0.5,0.5,0.5,0.5) so projections are exact) in phonecheck/app/src/test/resources/session_v1/. 3. Tests first: Python test_session_v1.py (fixture parses to the listed values; point pixels match projection within 0.5 px; payload length mismatch, unknown version, missing pose while TRACKING, out-of-range depth size each rejected; OpenCV conversion of the fixture pose); receiver test streams a session-start and v1 frames over loopback and saves depth and confidence beside the JPEG; Java SessionFrameTest (JUnit on the JVM) encodes the fixture's values and must equal the fixture header and payload bytes, and its projection must match the fixture pixels. See them fail. 4. Write host/session_v1.py and update receiver.py (validate every frame, save depth/confidence, keep acks). 5. Java: SessionFrame (pure encoder and projection), FrameCapture (reads an ARCore Frame: pose, state, points, new raw depth, anchors), HostStream sends session start and v1 frames, CheckActivity gains a stream-until-stopped button; skip repeated camera timestamps. 6. Build with unit tests in WSL; owner installs; record a device stream; report the measured rates. 7. README updates; finish; commit only this task's files (Stream B shares the tree) and push.

## Files

- README.md (+1 -1, 399 lines)
- experiments/01_camera_capture_delivery/README.md (+12 -8, 300 lines)
- experiments/01_camera_capture_delivery/build/build-phonecheck.sh (+2 -2, 21 lines)
- experiments/01_camera_capture_delivery/host/receiver.py (+22 -6, 90 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+152 -0, 152 lines)
- experiments/01_camera_capture_delivery/phone_session_v1.md (+79 -0, 79 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/build.gradle (+3 -0, 28 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CheckActivity.java (+74 -35, 542 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/FrameCapture.java (+142 -0, 142 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/HostStream.java (+28 -14, 161 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/Report.java (+9 -5, 58 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/SessionFrame.java (+123 -0, 123 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/test/java/org/fyld/phonecheck/SessionFrameTest.java (+115 -0, 115 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/test/resources/session_v1/frame_payload.bin (+0 -0, 0 lines)
- experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py (+53 -10, 117 lines)
- experiments/01_camera_capture_delivery/tests/test_session_v1.py (+130 -0, 130 lines)

## Checked

- `python -m pytest experiments/01_camera_capture_delivery/tests -> 164 passed, 1 skipped (24 for session v1 and the receiver); WSL build-phonecheck.sh -> 4 of 4 JVM SessionFrameTest passed, APK 29c8240b built`
- cost: 13 min from begin to finish; Claude tokens 16,534,595 (fresh input 249,273, cache read 16,141,814, output 143,508; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.13 (was 0)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 1523 words: bold-labels "4 items"

## Left over

Owner: install mobile deployment/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk and stream once with the receiver running, to measure frame rate with depth, depth frames per second and anchor corrections on the Redmi; tools/check.py board check refuses the task_list/done folder (predates this task)
