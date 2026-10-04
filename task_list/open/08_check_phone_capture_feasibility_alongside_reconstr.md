---
id: "08"
title: Check phone capture feasibility alongside reconstruction
status: in_progress
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/01_camera_capture_delivery/tests/test_capture_report.py
plan_reviewed: null
files:
  - experiments/01_camera_capture_delivery/**
docs:
  - experiments/01_camera_capture_delivery/README.md
  - experiments/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: experiments/README.md
  field: tested target phones
  baseline_value: "0 verified phone camera pairs"
  target: "Capability and capture evidence for both available phones"
created: 2026-10-02
last_updated: 2026-10-04
superseded_by: null
---

# Task 08: Check phone capture feasibility alongside reconstruction

## In plain English

Check whether each available phone can save useful images from two cameras at once. Record what works and what is missing. This check runs alongside reconstruction so camera limitations do not delay benchmark tests.

## Proposed build ownership, 3 October 2026

Task24 recovered the first-party smoke-app build recipe and verified cached WSL packaging. Its clean dependency build and container route remain in pending review because the required JPEG source archive and a compatible local container image are unavailable. That optional follow-up does not block this task: reuse the verified WSL route for the offline camera app, handset handoff, on-device results and phone checks.


Documentation reconciliation: the previously declared mobile deployment directory/README does not exist. The existing stage01 README owns capture/build/handoff instructions; no separate documentation directory is created. Historical WSL/APK receipts remain unchanged.

## Redmi pre-check, 4 October 2026

The owner identified the available phone as Redmi Note 11 Pro, model 2201116TG, Android 13, 6 GB RAM and Helio G96; it is not connected to the workstation yet. The APK may be transferred by email, and USB connection is also acceptable.

Google's current ARCore device list names both “Redmi Note 11 Pro” and “Redmi Note 11 Pro 5G” as supporting the Depth API. The listed non-5G name is consistent with the owner's 2201116TG/Helio G96 description, but Google's public table does not show the product code, so runtime support still needs checking on this handset. This certification does not establish a dedicated depth sensor or usable simultaneous camera pair. Google's Raw Depth guide says its confidence image is available with sparse depth, and image/frame timestamps distinguish new depth from a reprojected image. At runtime, record those timestamps and confidence instead of inferring them from the certification label.

Sources: [Xiaomi Redmi Note 11 Pro specifications](https://www.mi.com/ae-en/product/redmi-note-11-pro/specs/), [Google ARCore supported devices](https://developers.google.com/ar/devices) and [Google Raw Depth API guide](https://developers.google.com/ar/develop/java/depth/raw-depth). No ARCore SDK package has been acquired for this test.

## What

Inspect Samsung S23 and the exact Redmi Note 11 Pro variant. Save capability reports, a single-camera control and an attempted supported camera pair. Establish timing, calibration availability and overlap before choosing stereo deployment.

## Why

Several rear lenses do not establish simultaneous access, synchronization or useful stereo geometry. A negative device result should redirect capture rather than block reconstruction.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Capture already has a plan | Experiment 01 | Stereo and tracking | experiments/01_camera_capture_delivery/README.md:1 |
| APK packaging route is reusable, but currently copies and hash-pins only the smoke app | Task24 stage01 build helpers | This task's separate camera package profile and source provenance | experiments/01_camera_capture_delivery/build/warm.py:198; experiments/01_camera_capture_delivery/build/recipe.py:34 |

1. Reuse the Task24 p4a build and export route with a Task08-owned package profile, source manifest and Java `CameraActivity`. The pinned p4a release supports adding Java source, a custom Activity class and declared permissions; use those built-in options to run native Camera2 directly. Keep the Task24 smoke-app profile, source hashes and receipt intact. Do not add PyJNIus, ARCore or other packages without owner approval; the Camera2 app must remain useful without them.
2. Show each check as PASS, FAIL or SKIPPED with a short reason. Report manufacturer/model/build, permission state, Camera2 IDs, lens facing and level, physical IDs, stream sizes and frame durations, timestamp source, sync type, intrinsics/distortion/pose arrays and fields that are absent.
3. Use Camera2's concurrent-camera sets to select actual supported pairs, configure each advertised combination and save returned capture-result sensor timestamps and original images. Run one rear-camera capture as a control. Record requested and actual dimensions, crop/rotation, frame numbers and per-frame/session errors. Do not claim stereo from a pair existing in the supported-ID list alone.
4. Save an export bundle with the device report, original image samples and integrity hashes. Keep capture time and export/arrival time separate. Give the user a share/export action that works without a live PC connection; verify the received bundle against its hashes.
5. Check the public ARCore device listing against the exact Redmi model and record that listing separately from runtime evidence. The ARCore SDK has not been acquired. Unless separately approved and made available, report runtime depth/camera-pose checks as SKIPPED because the app does not package the ARCore SDK; do not label this as device incompatibility. If later enabled, separately record full and raw depth, raw confidence, camera pose and image/frame timestamps. Label timestamps that show reprojected depth instead of new measurements.
6. Compare single-camera control with simultaneous capture. Assess view overlap and independently check calibration.
7. Report stereo feasible, infeasible or unresolved. Keep capture checks separate from delivery replay and sustained algorithm benchmarks. Do not select performance thresholds or claim physical accuracy from API availability.
8. Put the APK and handoff report in the repository's `mobile deployment/` folder. The existing print-only smoke APK has no camera feature and does not meet this handoff requirement.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence/implementation contract |
|---|---|---|---|---|
| Camera2 `ImageReader` and capture results | App-private capture session | Original image bytes; sensor timestamp in ns with source; dimensions, crop/rotation and request/frame identifiers | Completed frames survive process death in the session directory; an interrupted session stays incomplete | Android build fields and Camera2 APIs are inventoried at runtime; image and arrival times stay distinct |
| App session recorder | On-device status screen and export action | Versioned JSON report with each check's `PASS`/`FAIL`/`SKIPPED`, reason, camera IDs, stream details, metadata availability and file hashes | A finalized report and files are retained; an interrupted session is marked and cannot be exported as complete | Export code validates file paths and hashes before sharing |
| Android share/storage action | Workstation evidence intake | One ZIP/report bundle containing original samples and JSON; no unit conversion or timestamp replacement | Bundle is reusable after transfer; partial transfer fails hash validation | Workstation import rechecks every listed hash before accepting any observation |

The source of truth is the immutable camera image and its sensor metadata. Capture and export/arrival times remain separate. If the process stops during a session, the next launch labels it interrupted and starts a new session; no prior report is silently finalized or overwritten. If permission is denied, a camera disconnects, stream configuration fails or export is interrupted, show the failed/skipped check and preserve any completed evidence as an incomplete session. Fresh deployment installs the arm64 APK, records device build fields and permission outcome, runs a single-camera control, enumerates and attempts only advertised concurrent configurations, then exports and revalidates a versioned bundle. Keep the first report schema backward-readable when fields are added; never reinterpret missing depth or calibration as a valid measurement. Dataset-only controls remain usable without a phone.

## Hyperparameters

hyperparameters n/a: workstation preparation and the packaging smoke build do not select phone capture or performance settings. Before device runs, record stream resolution, frame rate, duration, timing tolerances and calibration procedure with provenance.

## Verification

Contract test: `experiments/01_camera_capture_delivery/tests/test_capture_report.py` must assert that every emitted check has exactly one `PASS`, `FAIL` or `SKIPPED` result; skipped checks carry a non-empty reason; each original capture has a sensor timestamp with clock source, dimensions and crop/orientation; absent calibration/depth is recorded as unavailable rather than replaced with a method estimate; incomplete sessions cannot be exported as complete; and imported bundle hashes match their contents.

On-device contract: confirm model number `2201116TG` in the handset settings and record the app's Android build model/device/product fields plus Android 13. The report lists each Camera2 ID and supported stream size, reports any concurrent pair only after both capture sessions succeed, preserves image and sensor timestamps, and exports a bundle whose hashes revalidate on the workstation. Unsupported combinations are recorded as `FAIL` or `SKIPPED` with the device/API reason. This does not establish camera accuracy or physical-depth accuracy.

Before: 0 verified target-phone camera pairs. Target: capability and capture evidence for both phones, including explicit failure records. Infeasible stereo is a valid feasibility finding. No numerical performance threshold is selected in this task; confirm new settings before any scored comparison.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Existing workstation setup and README preparation; new `app/capture_report.py` and `tests/test_capture_report.py` validate report structure and exported file integrity |
| Test status | NDK arm64 compile passed and prior package smoke APK verified; current report tests: 15 passed, 1 symlink test skipped because Windows denied symlink creation; 100% branch coverage for `capture_report.py`; Python review passed; no phone run |
| Before measurement | 0 verified target-phone camera pairs |
| After measurement | 0 verified target-phone camera pairs; workstation package smoke build verified; report contract covered by 12 passing tests |
| Delta | 0 camera pairs; report/export checks now reject malformed timing or enum values, incomplete sessions, unsafe paths, empty image files and changed bytes |
| Outcome | Report/export foundation is in place. Camera access, APK rebuild and phone feasibility remain untested |

still open because the Redmi is not connected and the camera-test APK is not prepared; Samsung S23 availability is unconfirmed.

### Workstation preparation, 2026-10-02

Neither phone was connected during this work. The Windows host had no Android tools on PATH. Ubuntu 24.04.4 under WSL2 had Python 3.12.3 and Git, but no Java, Android SDK or NDK, gcc, make or unzip. Ubuntu's signed package repositories supplied OpenJDK 17.0.20.1, build-essential, Cython 3.0.8 and the p4a Linux prerequisites.


### Prepared build route

The selected p4a route is installed in an isolated WSL Python environment at version 2026.05.09, release commit 58d21141f17c889bf8585f5665921d72028f8831. Java 17 matches Android Gradle Plugin 8.11.0; its minimum Gradle version is 8.13, and the p4a wrapper uses Gradle 8.14.3. Android SDK platform API 36, build-tools 35.0.0, platform-tools 37.0.1 and NDK r28c (28.2.13676358) are installed. The NDK minimum API is 24. Host Python remains 3.12.3; the bundled Android Python recipe is 3.14.2. These are workstation build settings, not phone capture settings.

Before extraction or installation, the Google command-line tools archive matched publisher SHA-256 `4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583`; the NDK archive matched publisher SHA-1 `a7b54a5de87fecd125a17d54f73c446199e72a64`; the Gradle 8.14.3 binary archive matched SHA-256 `bd71102213493060956ec229d946beee57158dbd89d0e62b91bca0fa2c5f3531`; the Gradle wrapper's 8.14.3 all archive matched SHA-256 `ed1a8d686605fd7c23bdf62c7fc7add1c5b23b2bbc3721e661934ef4a4911d7c`; and the p4a PyPI wheel matched SHA-256 `79a58606a78ed3cec1aba110876a414d4aa988f082385d68393e208d009e1e94`. Ubuntu packages came from signed Ubuntu repositories. The p4a GitHub release marks its commit signature verified.

Checks passed: NDK clang emitted an ELF64 AArch64 Android shared library for API 24; p4a built a minimal arm64 APK with Python 3.14.2; the APK signature verified and its manifest reports min API 24, target API 36 and native code `arm64-v8a`. The build ran in WSL scratch space. No emulator or GPU was used. The current command-line tools warn that `sdkmanager` is deprecated and recommend the new `android sdk` command for future SDK maintenance.

The smoke APK does not include camera access. Neither phone is connected, and no camera IDs, stream pairs, timing, calibration or handset compatibility have been tested. Task 08 remains open for those device checks.
