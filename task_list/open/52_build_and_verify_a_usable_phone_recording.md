---
id: "52"
title: Finish capture metadata coverage and sustained Redmi checks
status: open
priority: HIGH
type: infra
blocked_by: []
blocks: []
verification_test: "experiments/01_camera_capture_delivery/tests/test_capture_receiver.py"
plan_reviewed: null
files:
  - experiments/01_camera_capture_delivery/**
  - experiments/open_vio/host/**
  - experiments/open_vio/tests/**
  - mobile_deployments/README.md
docs:
  - experiments/01_camera_capture_delivery/README.md
  - experiments/open_vio/README.md
  - learning/08_phone_and_deployment.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Finish capture metadata coverage and sustained Redmi checks"
  baseline_value: "1194 frames, zero reported drops; 17 without ARCore, final frame without Camera2 settings, anchor 0 absent; no rest or sustained trial"
  target: "Explain or fix metadata gaps, validate a new completed capture and 60 s rest, and report sustained queue behaviour"
created: 2026-10-06
last_updated: 2026-10-15
superseded_by: null
---

# Task 52: Finish capture metadata coverage and sustained Redmi checks

## In plain English

The phone now records and sends real walks. Finish checking that stopping, camera metadata and tracking records remain complete, then check a longer walk and a short recording at rest. Preserve missing information explicitly instead of inventing it.

## Current evidence, 15 October 2026

Capture 1.2 (`org.fyld.capture`) replaces phonecheck and rawrecorder. The completed `20261014_220756_walk` has 1,194 frames over 39.88 s, 29.92 fps, no missing/duplicated frame numbers and zero reported drops. Motion sensors ran at 423.54 Hz; receipt was 10.22 MB/s; the PC stores 225 MB. Tasks96-99 built the v2 receiver, resume, readers, crash reporting and serialization fix. Task99 checked 317 tests with 1 skipped and 30 JVM tests. These are recorded results, not a new test run under this review.

Seventeen frames have no ARCore record, frame 1193 has no Camera2 settings, and the first anchor creation is missing. EuRoC export writes its files, but export and clock validation return status 1 for the settings gap. The 30-frame memory buffer can still overflow; one short zero-drop walk proves no sustained guarantee. Estimated clock offset -2.67 ms is not independent calibration.

## Plan

1. Trace Camera2 result/image matching and Stop flushing in `capture/.../FrameCapture.java`, `FrameWriter.java` and `SharedCameraRig.java`. Write regression tests before changing code for the final-result race, unavailable tracking data and first-anchor delivery.
2. Explain the 17 unmatched ARCore records using timestamps and tracking/update events. Distinguish expected unavailable matches from records discarded by the app. Never synthesize a pose or copy an earlier record as a new observation. Task102 owns raw-depth eligibility, image orientation and geometry diagnosis.
3. Preserve anchor creation/correction lineage even when the associated camera frame is absent. Any protocol change must update `phone_session_v2.md`, the Java/Python fixture and both readers together; do not silently reinterpret existing v2 data.
4. Run host/JVM tests using `tools/check.py` and `build-capture.sh`, publish a timestamped APK under `mobile_deployments/`, and retain the latest Camera2 diagnostic. Email installation is the current route; USB is unavailable.
5. Coordinate a new walk and 60 s motion-only rest with the owner after the software checks. Report duration, fps, drops, IMU rates/gaps, MB/s, queue peaks, drain time after Stop, storage, thermal/battery telemetry and clock findings. Choose sustained duration explicitly as proposed by Claude, not owner-ruled; do not call 39.88 s a sustained test.
6. Verify reconnect/resume and Stop draining without duplicate/missing frames; keep the existing loopback test and obtain physical evidence where possible. Preserve old sessions unchanged. Do not suppress checker failures to make an export pass.

## Completion boundary

One new completed walk and short rest parse, export and replay with no unexplained metadata loss; reports name expected absences and any remaining failure. Software fixes can finish with a documented owner-run handover if handset evidence is still unavailable, but cannot claim those runs happened. Calibration target video and the separate approximately 3-hour rest belong to Task103.

## Settings and validation

Inherit Task99's actual 640 x 480, JPEG 90, raw grey, 30 fps configuration, sender window and storage threshold until a measured reason changes them. New settings are proposed by Claude, not owner-ruled. Use fixture parity, Stop/result ordering controls, disconnect/resume tests, full image decoding, sequence checks, clock/export exit codes and replay. LAN only, port 8766; port 8765 remains reserved for v1. No GPU or new app.

## Historical scope

This replaces the 6-7 October plan to build a minimum Camera2 recorder. Its legacy reader remains compatibility code. Implementation receipts are in Tasks88 and 96-99; this task retains only the unresolved capture checks.
