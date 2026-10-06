---
id: "52"
title: Build and verify a usable phone recording
status: open
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; code engineering may start with the existing camera profile; physical capture and acceptance require device access and Task51 decisions
blocked_by: []
blocks: []
verification_test: "experiments/shared/tests/test_phone_session.py"
plan_reviewed: 2026-10-06 PASS
files:
  - experiments/01_camera_capture_delivery/**
  - experiments/shared/phone_session.py
  - experiments/shared/tests/test_phone_session.py
  - tools/check.py
  - tools/tests/test_check_hygiene.py
  - pytest.ini
  - .gitignore
docs:
  - experiments/01_camera_capture_delivery/README.md
  - experiments/shared/README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: build and verify a usable phone recording
  baseline_value: "0 received phone image sessions with usable calibration and synchronized stream lineage"
  target: "1 verified recording bundle on the Task51 target with actual images and explicit stream availability"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task52: Build and verify a usable phone recording

## In plain English

Record real images from the selected phone, with the information needed to interpret them correctly. Save distance and camera-motion data when the phone supplies them. Make missing data and capture failures visible so later tests cannot mistake a capability report for a usable recording.

## What

Own the minimum recorder and shared phone-session reader/contract. Extend the existing native camera app and export validation rather than inventing another app/build route. Check runtime ARCore capability if selected in Task51, capture images, matching calibration, timestamps/clock relations, depth freshness/confidence, pose/tracking/world resets, selected camera configuration and source hashes. Publish a valid RGB session even if depth/pose are unavailable, with explicit absence. Task54 then owns depth resolution; Task56 owns estimator integration.

## Why

Task08's capability session has 0 captured images. The current APK contains no ARCore SDK. A usable phone recording is the missing input to all physical trials.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Native camera capture, detailed export validation and the shared reader exist; physical handset image export remains unverified | CameraCapture.java, CameraActivity.java, capture report validator and phone-session reader | offline session consumers and geometry adapters | experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraCapture.java:148; experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraActivity.java:344; experiments/01_camera_capture_delivery/app/capture_report.py:132; experiments/shared/phone_session.py:164; experiments/01_camera_capture_delivery/README.md:86 |
| Native reports already record active and pre-correction array rectangles; each captured frame records the actual distortion-correction mode | CameraReport.java and CameraCapture.java | calibration-grid selection in the phone-session reader | experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraReport.java:101; experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraCapture.java:187; experiments/shared/phone_session.py:194 |
| The isolated Camera2 package has a pinned offline warm-build route and APK verifier | warm build helper and source profile | reproducible APK package for a physical capture check | experiments/01_camera_capture_delivery/build/warm.py:327; experiments/01_camera_capture_delivery/build/camera-profile.json:1; experiments/01_camera_capture_delivery/build/verify.py:1 |
| Fixture tests already cover capability-report compatibility, image decoding, frame-detail matching and calibration readiness | phone-session contract tests | future recorder and export checks | experiments/shared/tests/test_phone_session.py:86; experiments/shared/tests/test_phone_session.py:154; experiments/shared/tests/test_phone_session.py:239; task_list/README.md:23 |
| Portable calibration/pose/observation records exist | Shared contracts | downstream geometry | experiments/shared/contracts.py:11; experiments/shared/contracts.py:39; experiments/shared/contracts.py:73 |
| Sensor/API inventory is research, not runtime proof | ARCore inventory | minimum recording choices | research/arcore/README.md:3; research/arcore/README.md:7 |
| Existing Observation requires a concrete pose | Observation contract and supplied-pose adapter | geometry consumers | experiments/shared/contracts.py:72; experiments/geometry_validation/src/icl.py:83 |
| The project check now rejects unexpected task-board files before pytest and removes its temporary test directory on exit | `tools/check.py` | project test execution and repository hygiene | tools/check.py:41; tools/check.py:53; tools/check.py:83 |
| Root pytest discovery names the project test paths, includes `task_list` in `norecursedirs`, and the default runner lists those paths plus the hygiene tests | `pytest.ini` and `tools/check.py` | root pytest collection and the default project check | pytest.ini:1; pytest.ini:2; pytest.ini:5; tools/check.py:65 |
| Git already ignores Python and common pytest artifacts under `task_list`, but these are defense in depth and do not remove leaked files | `.gitignore` | Git status and accidental staging | .gitignore:13; .gitignore:15; .gitignore:21 |

1. Reuse the implemented shared reader, strict export validator and Android capture metadata. Preserve the existing package, version, permissions, camera settings, dependencies and pinned source hashes. No new capture settings are authorized.
2. The reader preserves legacy capability-export validation while requiring readable images and matching passing frame details for a usable phone session. It fully decodes images, checks dimensions and hashes, retains raw sensor-grid calibration, maps crop coordinates, and marks corrected or unknown distortion modes not ready for metric geometry. RGB-only frames remain available as `PhoneFrame`; convert to shared `Observation` only when a valid pose exists. The code and fixture tests are already present.
3. Native report writes use Android `AtomicFile`; interrupted session recovery marks the session incomplete. The cached WSL warm build now compiles and verifies the current pinned Camera2 sources. Device installation, crash recovery and physical capture behavior remain unverified.
4. Keep test scratch outside the repository and stop pytest from collecting task records. Make `tools/check.py` fail before running pytest if it finds Python files, bytecode, pytest caches, or job-allocation probe folders in `task_list/`. Use a temporary directory that is removed when the check exits. Add `tools/tests` to both the default check paths and `pytest.ini` test paths. Keep all test paths from `pytest.ini` in the runner's default list. Keep the existing `norecursedirs` exclusion for `task_list`; verify root discovery and an explicit `task_list/` argument do not collect task records. Keep ignore patterns as a second line of defence.
5. Before physical capture, require the confirmed Redmi identity and a usable connected-device path. Site and survey decisions gate the scored walkthrough under Task53; capture references before reviewing predictions.
6. Export and re-open a real phone bundle offline. Report capture duration, dropped frames, data volume and runtime support. A refused capability or unavailable stream is a recorded negative result, not an invented replacement.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Native recorder | sealed phone session | original images, sensor-clock nanoseconds, crop/rotation, active and pre-correction active rectangles, intrinsic-calibration grid and per-frame distortion mode; depth/pose are optional with explicit unavailable reasons | sealed export survives; partial sessions remain incomplete | experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraCapture.java:181; experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraReport.java:101 |
| Phone-session reader | shared geometry/depth adapters | `PhoneFrame` retains RGB bytes, raw calibration and distortion values with their sensor grid, crop/resize mapping, rotation and timestamp. Metric readiness is false unless correction mode and grid support a known mapping. Only a frame with a valid pose becomes shared `Observation` | original bundle remains source of truth | experiments/shared/contracts.py:72; experiments/geometry_validation/src/icl.py:83 |

Source of truth is the sealed original session. Device restart/tracking loss begins a new world/segment; it cannot silently join coordinates. A valid RGB frame with no pose is preserved as `PhoneFrame`, never converted to shared `Observation`; geometry consumers receive only pose-bearing observations. Each report has one writer and uses `AtomicFile`; a crash before `finishWrite` keeps the prior valid report. On restart, an earlier `recording` state becomes an explicit incomplete state, and corrupt/absent report data cannot be mistaken for a complete export. Failed recording/export leaves partial images intact under a fresh or recoverable incomplete session; retry uses a new identifier. Fresh deployment must document the native build, installed package/version, permissions, runtime capabilities and first successful export. Existing Camera2 exports stay readable; any schema change is versioned.

## Hyperparameters

| name | value | source |
|---|---|---|
| device, camera, image grid, capture duration, sensor/depth rates and synchronization policy | pending Task51 decisions and exact runtime capability | n/a planning only; freeze owner-confirmed values before device capture |
| output codec if video is written | H.264 in MP4, with encoder-open check | inherited user AGENTS.md video-output instruction |

## Verification

`experiments/shared/tests/test_phone_session.py` asserts that legacy `validate_export` accepts a complete zero-image capability-shaped report, while `validate_phone_session_export` rejects it, a failed or unlinked single-camera check, and any report with no images. It asserts `read_phone_session` fully decodes each image, checks its dimensions and hash, rejects absent or out-of-bounds sensor calibration metadata, and preserves RGB bytes, raw sensor-grid intrinsics, crop mapping, timestamp and explicit missing depth/pose. Parameterized controls for OFF, corrected and unavailable distortion modes assert that only OFF is marked ready for metric geometry until a correction transform is implemented. Focused capture/export/build-recipe checks assert the current profile hash and preserve existing capability-report behavior. The 6 October warm build receipt reports `status: verified`, packaging exit code 0 and the expected Camera2 manifest. These checks do not prove Android `AtomicFile` recovery or that a handset can install and capture with this APK. Device evidence must contain actual image bytes, calibration with the correct active-array basis, declared clocks, package/device identity and source hashes. Offline re-open must reproduce every input hash. Before 0 usable phone sessions; target 1 completed integrity-verified session, with failures and unsupported streams explicit.

`tools/tests/test_check_hygiene.py` asserts the preflight reports Python files, bytecode, pytest cache paths and job-allocation probe paths, accepts a clean task board, and returns before invoking pytest when a leak exists. The standard check and `pytest.ini` test path list include this test. The check runner's temporary directory must be removed on success and failure. Verify root pytest discovery and `python -m pytest --collect-only task_list/` collect no task-board records.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources. The early software phase uses fixtures only and changes no camera settings. Physical capture remains separately gated by the Task51 choices and access to the handset.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Task remains open; no commit made |
| Files changed | Native capture/report sources, source-hash profile, phone-session validator/reader/tests, related READMEs, this plan, `.gitignore`, `pytest.ini`, `tools/check.py`, and `tools/tests/test_check_hygiene.py` |
| Test status | Focused phone-session, export and build-recipe checks: 132 passed, 1 skipped. Hygiene checks: 8 passed. Android warm build verified; first attempt exposed a duplicate `rect(Rect)` declaration, which was removed before the passing build. Root pytest collected 628 tests and explicit `task_list/` collection collected 0. Full test suite, device installation and recovery not verified. |
| Before measurement | 0 received phone image sessions with usable calibration and synchronized stream lineage |
| After measurement | 0 physical sessions received; fixture reader/export checks pass; current Camera2 APK builds and verifies; hygiene preflight and scratch cleanup pass through the scoped check command |
| Delta | Physical-session count unchanged; duplicate Java method fixed; the APK is ready for a handset install/capture check; task-board leakage is detected before pytest starts |
| Decision-gate outcome | Software reader, hygiene guard and cached package build pass their scoped checks; handset capture, Android recovery verification and acceptance remain gated by Task51 and device access |

still open because no Redmi image session or on-device recovery/build evidence has been received.
