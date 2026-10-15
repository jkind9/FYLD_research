---
id: "99"
title: Fix Redmi frame JSON crash and publish a timestamped capture update
status: done
files:
  - experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/ArcoreRecord.java
  - experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/SessionMessages.java
  - experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/FrameWriter.java
  - experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CaptureActivity.java
  - experiments/01_camera_capture_delivery/capture/app/build.gradle
  - experiments/01_camera_capture_delivery/capture/app/src/test/java/org/fyld/capture/SessionV2Test.java
  - experiments/01_camera_capture_delivery/capture/app/src/test/java/org/fyld/capture/FrameJsonTest.java
  - experiments/01_camera_capture_delivery/build/export.py
  - experiments/01_camera_capture_delivery/build/deployment.py
  - experiments/01_camera_capture_delivery/build/build-capture.sh
  - experiments/01_camera_capture_delivery/tests/test_deployment.py
  - experiments/01_camera_capture_delivery/tests/test_build_recipe.py
  - mobile_deployments/README.md
  - README.md
  - experiments/01_camera_capture_delivery/README.md
  - experiments/01_camera_capture_delivery/phone_session_v2.md
  - experiments/open_vio/README.md
  - learning/08_phone_and_deployment.md
  - learning/12_rebuilding_arcore.md
  - research/phone_ar_platforms/android_testing_and_crash_reports.md
  - experiments/01_camera_capture_delivery/tests/conftest.py
  - tools/check.py
  - tools/tests/test_check_hygiene.py
  - experiments/shared/tests/test_phone_session.py
  - ruff.toml
  - src/live/processor.py
  - src/live/fragments.py
  - src/live/run.py
  - src/live/tests/test_processor.py
  - src/live/tests/test_fragments.py
  - src/live/README.md
created: 2026-10-14
---
# Fix Redmi frame JSON crash and publish a timestamped capture update

## Goal

Reproduce the Redmi JSON encoding crash, fix its input and provide capture 1.2 with clear version and UTC time in APK and folder names.

## Plan

1. Reproduce non-serializable frame values and timestamp naming in failing tests. 2. Fix encoding inputs and publication names. 3. Build and verify, stage the update, document owner retry, finish and push.

## Files

- README.md (+8 -8, 417 lines)
- experiments/01_camera_capture_delivery/README.md (+41 -8, 400 lines)
- experiments/01_camera_capture_delivery/build/build-capture.sh (+2 -2, 21 lines)
- experiments/01_camera_capture_delivery/build/deployment.py (+12 -1, 29 lines)
- experiments/01_camera_capture_delivery/build/export.py (+24 -15, 276 lines)
- experiments/01_camera_capture_delivery/capture/app/build.gradle (+2 -2, 28 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/ArcoreRecord.java (+5 -3, 113 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CaptureActivity.java (+1 -1, 743 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/SessionMessages.java (+12 -10, 132 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+3 -1, 201 lines)
- experiments/01_camera_capture_delivery/tests/conftest.py (+3 -3, 17 lines)
- experiments/01_camera_capture_delivery/tests/test_build_recipe.py (+2 -2, 638 lines)
- experiments/open_vio/README.md (+7 -5, 163 lines)
- experiments/shared/tests/test_phone_session.py (+3 -9, 296 lines)
- learning/08_phone_and_deployment.md (+5 -3, 99 lines)
- learning/12_rebuilding_arcore.md (+3 -3, 99 lines)
- mobile_deployments/README.md (+5 -3, 20 lines)
- research/phone_ar_platforms/android_testing_and_crash_reports.md (+8 -0, 31 lines)
- ruff.toml (+1 -0, 1 lines)
- src/live/README.md (+11 -3, 81 lines)
- src/live/fragments.py (+8 -3, 71 lines)
- tools/check.py (+1 -1, 108 lines)

## Checked

- `python -B tools/check.py capture/open_vio/live/shared-phone/hygiene suites -> 317 passed, 1 skipped using OS scratch; Ruff changed Python files -> passed; WSL build-capture -> 30 JVM tests passed; real capture 1.2 -> 1194 frames at 29.92 fps, zero reported drops; v2 image validation -> 1194 PNG/JPEG pairs and ordered replay passed; CPU src.live.run replay -> 63 updates, 1.58 per second, no gap over 1s; EuRoC -> 1194 PNGs and 16899 IMU rows written; clock_check/export status1 -> final frame lacks camera settings; estimated clock offset -2.668ms (correlation0.618); scratch audit -> zero generated test/cache paths; APK/email SHA256 matched; git diff --check clean`
- cost: 346 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.34 (was 0.35)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 3 in 2847 words: same-opening "the", same-opening "the", same-opening "the"

## Left over

60 s motion-only rest and calibration recordings not received. Recorded walk has 17 frames without ARCore records, one final frame without Camera2 settings, and no anchor-0 creation record; replay now handles the available anchors, but full metadata coverage still needs work. Clock estimate needs independent calibration; geometric accuracy and object counts remain unvalidated. Longer device runs and AVD setup remain. PC receiver and private recordings/outputs stay local.
