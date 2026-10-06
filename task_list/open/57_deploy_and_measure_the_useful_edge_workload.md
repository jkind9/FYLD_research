---
id: "57"
title: Deploy and measure the useful edge workload
status: open
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; execution requires task-specific review and frozen settings
blocked_by: [51]
blocks: []
verification_test: "experiments/01_camera_capture_delivery/tests/test_edge_workload.py"
plan_reviewed: null
files:
  - experiments/01_camera_capture_delivery/edge/**
  - experiments/01_camera_capture_delivery/native/**
  - experiments/01_camera_capture_delivery/tests/**
docs:
  - experiments/01_camera_capture_delivery/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: deploy and measure the useful edge workload
  baseline_value: "0 deployed useful measurement/counting workloads with sustained target-device evidence"
  target: "1 actual-device feasibility checkpoint and 1 sustained comparable deployment report"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task57: Deploy and measure the useful edge workload

## In plain English

Run the agreed useful workload on the chosen phone or nearby computer. Check early that it can load and work offline, then measure its behaviour during a real-length session. Compare its answers and resource use with the complete baseline.

## What

Own packaging/runtime/device adapter and sustained execution of Task51's selected edge workload. The workload may be capture-quality checks plus provisional measurements/counts, or fuller processing if explicitly selected. It is not automatically every hosted layer. Device feasibility starts after Task51; the final comparable sustained run requires Task52 capture compatibility and Task56's frozen complete baseline. Do not wait for all desktop refinements before checking runtime compatibility and memory. Tighten native/build/runtime/test scope and licence terms for the chosen hardware before implementation.

## Why

APK packaging and a camera report do not deploy the project's useful workload. Edge constraints can invalidate a promising desktop method, so an early real-device checkpoint is needed.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Native camera app/build path already exists | capture experiment | device packaging | experiments/01_camera_capture_delivery/README.md:165; experiments/01_camera_capture_delivery/native/camera/java/org/fyld/capture/CameraActivity.java:1 |
| Cached smoke build does not run measurement | Task24 | deployment baseline distinction | task_list/pending_review/24_recover_and_reproduce_android_apk_build_inside_cap.md:123 |
| Shared records and lineage exist | shared contracts | device adapter/export | experiments/shared/contracts.py:73; experiments/shared/runs.py:59 |
| ARCore feature inventory is not device proof | ARCore research | runtime feasibility | research/arcore/README.md:3; research/arcore/README.md:7 |

1. After Task51, test actual hardware/runtime/license compatibility with the selected useful workload. Record installed package/build, model precision/backend, cold startup and measured memory; explicitly report unsupported execution. This first checkpoint does not require Task56 to pass.
2. Reuse Task52 recorder/exports and the chosen model/methods. Keep algorithm changes in their owning tasks; device conversion/precision changes get explicit settings and output comparisons, never silent degraded fallback.
3. Add controls for no network, unavailable model/runtime, camera/tracking loss, interrupted export and restart. Document build/install-to-first-use steps and preserve lineage after failure.
4. After Task56 freezes a complete baseline, run Task51's sustained workload on the physical target with the same comparison inputs where possible. Measure end-user update/result delay, dropped frames, peak memory, heat, battery and storage under the agreed duration.
5. Compare accuracy and counts with independent Task53 truth and Task56 outputs. Record which stages stay hosted and the offline output actually available. Publish PASS/FAIL per Task51 limit; an incompatible device or insufficient performance is a completed negative result with a specific next decision.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Physical device/runtime | capture/processing adapter | original observations, package/backend/model identity and world/segment/revision | sealed exports survive; live session restarts separately | experiments/shared/contracts.py:73 |
| Device export | independent comparison | versioned records and resource/timing telemetry, no reference labels fed to method | verified benchmark artifacts survive | experiments/shared/runs.py:59 |

Original sessions and model/build configuration are source of truth. Capture/inference boundaries preserve declared timing, units and world/segment IDs. Process death leaves an incomplete export; relaunch begins a new session and does not duplicate confirmed observations. Fresh deployment covers build artifact, installed identity, permissions, offline model availability and first useful result. Existing capability/smoke packages remain separately labelled; converted models must declare version/precision and retain a measured comparison path.

## Hyperparameters

| name | value | source |
|---|---|---|
| target hardware, useful workload, runtime/model/precision, image grid, rates, duration, repeats and resource limits | pending Task51 and reviewed device plan | n/a planning only; owner-confirmed settings required before run |
| compared method configuration | exact frozen Task56/owning-stage values, unless a documented device conversion is approved | n/a baseline not run yet; inherit its future receipt before comparison |

## Verification

Offline and failure controls report unavailable capability explicitly, preserve source lineage and avoid duplicate committed observations on restart. Before 0 useful deployed workloads; target 1 early compatibility/memory result plus 1 physical-device sustained report with correctness, user delay and measured resource costs. A packaging-only or browser-viewer run cannot satisfy this task.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources. No implementation or acquisition is performed while writing this plan.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan only; implementation not started |
| Test status | Planned contract checks; no run claimed |
| Before measurement | 0 deployed useful measurement/counting workloads with sustained target-device evidence |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Open; execution and verification pending |

still open because this plan has not been implemented or measured.
