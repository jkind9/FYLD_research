---
id: "85"
title: "Redmi check app: ARCore probe and host streaming test"
status: done
priority: MEDIUM
type: experiment
approval_status: owner 2026-10-14 - APK development for the Redmi approved; owner asked for tests of host streaming and of the ARCore module. Settings marked proposed by Claude are not owner-ruled.
blocked_by: []
blocks: ["52", "75"]
verification_test: "experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py"
plan_reviewed: null
files:
  - experiments/01_camera_capture_delivery/phonecheck/**
  - experiments/01_camera_capture_delivery/host/**
  - experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py
  - experiments/01_camera_capture_delivery/build/build-phonecheck.sh
docs:
  - experiments/01_camera_capture_delivery/README.md
baseline_metric:
  source: "Redmi capability report, 5 October 2026 (experiments/01_camera_capture_delivery/README.md, 'Redmi device result'); ARCore feature inventory (research/phone_ar_platforms/arcore/README.md)"
  field: "ARCore availability, depth support, tracking state counts, per-frame update time; host stream frames per second and round-trip delay"
  baseline_value: "ARCore checks SKIPPED (the Camera2 APK has no ARCore SDK); no streaming test exists"
  target: "the app installs on the Redmi and returns a report with every check either passed, failed with a reason, or skipped with a reason; nothing is left unknown"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 85 — Redmi check app: ARCore probe and host streaming test

## In plain English

Before building a full recording app, we need to know two things about the project's phone, a Redmi Note 11 Pro: does Google's ARCore tracking work on it, and can it send camera frames to a computer fast enough. This task makes a small test app for the phone. It runs a list of checks and writes a report saying, for each one, passed, failed (with the reason) or skipped (with the reason). A small program on the computer receives the frames, so the speed of the connection can be measured.

## What

1. **Android app `org.fyld.phonecheck`** (plain Java, Gradle; the native fallback route proposed in the capture README), one screen with a host address box and three buttons:
   - *ARCore check*: device identity; ARCore availability and install state; session creation; raw depth and depth support; the camera configurations ARCore offers.
   - *Tracking run (15 s, move the phone)*: per frame, tracking state and failure reason, camera pose, image intrinsics, tracked point count, raw depth size, share of valid depth pixels and mean confidence, and the time `session.update()` took. Summary: frames, share tracking, path length, update time median and 95th percentile, depth frames.
   - *Stream to host (20 s)*: sends each ARCore camera image as JPEG with its pose and intrinsics over TCP to the host, which acknowledges each frame; measures frames per second, megabytes per second and round-trip delay.
   - The report is saved on the phone and, when a host is set, also sent to it.
2. **Host receiver** (`host/receiver.py`, Python standard library): listens on a port, saves frames and their headers, answers each frame with an acknowledgement, saves reports, prints throughput.
3. **Host tests** (`tests/test_phonecheck_host.py`): message framing round trip, a loopback client streaming to the receiver, acknowledgements, saved files, report schema check.
4. **Build script** `build/build-phonecheck.sh` (WSL, the existing Android SDK and Gradle), and README steps for install and use.

## Why

ARCore is the planned camera tracker and size source on the phone (SLAM review, 14 October 2026), but it has never run on this handset. The existing Camera2 app reported ARCore as skipped. Streaming to a host is the other deployment route the owner asked to test. Both answers decide the recording app's design (Task52) and ARCore's accuracy test (Task75).

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| WSL Android SDK, build tools and Gradle | Task24 build route | build/build-apk.sh | experiments/01_camera_capture_delivery/README.md, "Android package build and offline handoff" |
| A Java activity that writes a JSON check report | Task08 `CameraReport` | capture app | experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraReport.java |
| Report status vocabulary (PASS / SKIPPED with reason) | `capture_report.py` | Redmi result | experiments/01_camera_capture_delivery/app/capture_report.py |
| ARCore outputs needed and their units | ARCore inventory | Task52, Task75 | research/phone_ar_platforms/arcore/README.md |
| No ARCore or streaming code exists | searched the repo for `com.google.ar` and socket streaming | — | none found |

### Plan

1. Host tests first; see them fail; write `host/protocol.py`, `host/receiver.py`, `host/report.py`.
2. Android project and build script; build the debug APK in WSL (Gradle downloads the ARCore library from Google's Maven repository).
3. Install on the Redmi (ADB over Wi-Fi from WSL, or copy the APK) and run the three checks; save the reports under the experiment's `runs/` (not in Git).
4. README section with results.

## Hyperparameters

| name | value | source |
|---|---|---|
| ARCore SDK | com.google.ar:core 1.56.0 | latest on Google Maven, checked 2026-10-14 |
| tracking run length | 15 s | proposed by Claude 2026-10-14, not owner-ruled |
| stream length | 20 s | proposed by Claude 2026-10-14, not owner-ruled |
| depth mode | RAW_DEPTH_ONLY if supported, else AUTOMATIC, else off (reported) | proposed by Claude 2026-10-14 |
| update mode | LATEST_CAMERA_IMAGE | ARCore default for live apps |
| JPEG quality | 80 | proposed by Claude 2026-10-14, not owner-ruled |
| stream image | ARCore CPU image (640 x 480 YUV, converted to JPEG) | ARCore default CPU image size |
| port | 8765 | proposed by Claude 2026-10-14 |
| minimum / target Android API | 24 / 36 | inherited Task24 toolchain |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Check report | phone app | `host/report.py`, README | JSON: schema 1, device, checks with name, status, reason, detail | saved on the phone and on the host |
| Streamed frames | phone app | `host/receiver.py` | framed TCP message: 4-byte length + JSON header, 4-byte length + JPEG | frames and headers saved per session on the host |
| Acknowledgement | host | phone | 4-byte big-endian frame number | not stored; round trip recorded in the phone report |

- **Source of truth:** the phone's report; host files are copies.
- **Process boundary:** phone to Windows host over Wi-Fi TCP; the host must allow the port through its firewall.
- **Failure after each step:** a dropped connection ends the stream check with status fail and the reason; frames already saved stay; the report is still written on the phone.
- **Backward compatibility:** the existing Camera2 app and build route are unchanged.

## Verification

- `tests/test_phonecheck_host.py`: framing round trip for a header and payload; a truncated message raises; a loopback client sends 5 frames and receives 5 acknowledgements in order; the receiver saves 5 JPEGs and 5 header lines; a report with an unknown status or a missing reason on a non-pass check is rejected.
- Red first: run the tests before the host modules exist.
- On the device: the report from the Redmi, checked by `host/report.py`.
- Plan review: not required (MEDIUM); started with `task.js start 85 --take` while Task84's background runs continue.

## Receipts

| field | value |
|---|---|
| closing commit | pushed with the follow-up commit (owner asked to keep the repo current) |
| files changed | experiments/01_camera_capture_delivery/phonecheck/ (Android app), host/ (receiver, protocol, report), tests/test_phonecheck_host.py, build/build-phonecheck.sh, README |
| test | host tests 7 passed; APK builds (aapt checked); device run on the Redmi: report 7 PASS, stream 580 frames in 20 s |
| before / after | Before: ARCore checks SKIPPED (no SDK in the Camera2 app), no streaming test. After: ARCore installed, session, raw and smoothed depth, 3 camera configs, tracking 100% of 891 frames, 4.9 ms per update, raw depth 160 x 90; stream 29 fps, 0.70 MB/s |
| result | Target met: the app installs and every check is passed or explained. Rebuilt UI (portrait, preview, one button) confirmed by the owner; its own stream run did not reach the receiver (address box probably empty) |

Notes / caveats / follow-ups:

- Install route: MIUI blocks installs over debugging without a SIM ("Install via USB" needs a Mi account and SIM); the owner installed the APK from email.
- The first UI was hard to use (landscape, no preview); rebuilt the same day. The first version saved the report before the stream check finished, so that report lacks the stream's round-trip delay.
- The test app does not show the ARCore notice a product must show (research/phone_ar_platforms/arcore_commercial_terms.md).
- Next (new session, owner): extend the stream with points, raw depth and confidence, pose corrections and a shared phone-session definition (README "Next: extend the stream").

## Files

- experiments/01_camera_capture_delivery/README.md (+12 -0, 296 lines)
- learning/08_phone_and_deployment.md (+2 -0, 56 lines)
- learning/11_inside_arcore.md (+114 -0, 114 lines)
- learning/README.md (+1 -0, 57 lines)
- research/phone_ar_platforms/README.md (+5 -0, 25 lines)
- research/phone_ar_platforms/arcore_internals.md (+43 -0, 43 lines)

## Checked

- `.venv-sfm pytest experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py -> 7 passed; device run on the Redmi -> report 7 PASS, 580 frames streamed at 29 fps`
- cost: 82 min from begin to finish; Claude tokens 39,007,592 (fresh input 118,716, cache read 38,808,936, output 79,940; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 6 in 2239 words: bold-labels "4 items", bold-labels "3 items", bold-labels "6 items", bold-labels "3 items", bold-labels "3 items"

## Left over

Confirm the rebuilt app's stream row (nothing reached the receiver on its run); extend the stream (new session)
