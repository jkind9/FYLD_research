---
id: "08"
title: Check phone capture feasibility alongside reconstruction
status: pending_review
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/01_camera_capture_delivery/README.md
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
last_updated: 2026-10-02
superseded_by: null
---

# Task 08: Check phone capture feasibility alongside reconstruction

## In plain English

Check whether each available phone can save useful images from two cameras at once. Record what works and what is missing. This check runs alongside reconstruction so camera limitations do not delay benchmark tests.

## What

Inspect Samsung S23 and the exact Redmi Note 11 Pro variant. Save capability reports, a single-camera control and an attempted supported camera pair. Establish timing, calibration availability and overlap before choosing stereo deployment.

## Why

Several rear lenses do not establish simultaneous access, synchronization or useful stereo geometry. A negative device result should redirect capture rather than block reconstruction.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Capture already has a plan | Experiment 01 | Stereo and tracking | experiments/01_camera_capture_delivery/README.md:1 |

1. Follow the capture plan; verify the build route before selecting versions.
2. Record model/variant, operating system, camera IDs, supported stream combinations and synchronization metadata.
3. Save original observations, capture timestamps, dimensions, crop/orientation and available calibration. Mark missing fields explicitly.
4. Compare single-camera control with simultaneous capture. Assess overlap and independently check calibration.
5. Report stereo feasible, infeasible or unresolved. Compare supported ARCore depth or external stereo if needed, with input differences explicit.
6. Keep capture tests separate from delivery replay and sustained algorithm benchmarks.

## Invariants and recovery

Raw observations remain unchanged. Capture and arrival times stay distinct. Interrupted recordings remain incomplete. Before implementation, document permission denial, camera disconnect and app interruption. Dataset controls remain usable without a phone.

## Hyperparameters

hyperparameters n/a: workstation preparation and the packaging smoke build do not select phone capture or performance settings. Before device runs, record stream resolution, frame rate, duration, timing tolerances and calibration procedure with provenance.

## Verification

Before: 0 verified target-phone camera pairs. Target: capability and capture evidence for both phones, including explicit failure records. Replace the plan-only verification path with scoped tests before implementation. Infeasible stereo is a valid feasibility finding.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | WSL build tools installed; Task 08, experiment 01 and overview READMEs updated |
| Test status | NDK arm64 compile passed; minimal p4a APK built and signature/manifest verified; no phone run |
| Before measurement | 0 verified target-phone camera pairs |
| After measurement | 0 verified target-phone camera pairs; workstation build verified |
| Delta | 0 camera pairs; one arm64 APK smoke build verified |
| Outcome | Workstation preparation complete; open because neither phone is connected and camera feasibility remains untested |

still open because both target phones still need to be connected for camera capability and simultaneous-pair checks.

### Workstation preparation, 2026-10-02

Neither phone was connected during this work. The Windows host had no Android tools on PATH. Ubuntu 24.04.4 under WSL2 had Python 3.12.3 and Git, but no Java, Android SDK or NDK, gcc, make or unzip. Ubuntu's signed package repositories supplied OpenJDK 17.0.20.1, build-essential, Cython 3.0.8 and the p4a Linux prerequisites.


### Prepared build route

The selected p4a route is installed in an isolated WSL Python environment at version 2026.05.09, release commit 58d21141f17c889bf8585f5665921d72028f8831. Java 17 matches Android Gradle Plugin 8.11.0; its minimum Gradle version is 8.13, and the p4a wrapper uses Gradle 8.14.3. Android SDK platform API 36, build-tools 35.0.0, platform-tools 37.0.1 and NDK r28c (28.2.13676358) are installed. The NDK minimum API is 24. Host Python remains 3.12.3; the bundled Android Python recipe is 3.14.2. These are workstation build settings, not phone capture settings.

Before extraction or installation, the Google command-line tools archive matched publisher SHA-256 `4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583`; the NDK archive matched publisher SHA-1 `a7b54a5de87fecd125a17d54f73c446199e72a64`; the Gradle 8.14.3 binary archive matched SHA-256 `bd71102213493060956ec229d946beee57158dbd89d0e62b91bca0fa2c5f3531`; the Gradle wrapper's 8.14.3 all archive matched SHA-256 `ed1a8d686605fd7c23bdf62c7fc7add1c5b23b2bbc3721e661934ef4a4911d7c`; and the p4a PyPI wheel matched SHA-256 `79a58606a78ed3cec1aba110876a414d4aa988f082385d68393e208d009e1e94`. Ubuntu packages came from signed Ubuntu repositories. The p4a GitHub release marks its commit signature verified.

Checks passed: NDK clang emitted an ELF64 AArch64 Android shared library for API 24; p4a built a minimal arm64 APK with Python 3.14.2; the APK signature verified and its manifest reports min API 24, target API 36 and native code `arm64-v8a`. The build ran in WSL scratch space. No emulator or GPU was used. The current command-line tools warn that `sdkmanager` is deprecated and recommend the new `android sdk` command for future SDK maintenance.

The smoke APK does not include camera access. Neither phone is connected, and no camera IDs, stream pairs, timing, calibration or handset compatibility have been tested. Task 08 remains open for those device checks.
