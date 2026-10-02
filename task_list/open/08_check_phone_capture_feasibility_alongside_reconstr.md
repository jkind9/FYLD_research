---
id: "08"
title: Check phone capture feasibility alongside reconstruction
status: open
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

Before runs, audit and stamp stream resolution, frame rate, duration, timing tolerances and calibration procedure with provenance. No performance threshold or experimental setting is selected here.

## Verification

Before: 0 verified target-phone camera pairs. Target: capability and capture evidence for both phones, including explicit failure records. Replace the plan-only verification path with scoped tests before implementation. Infeasible stereo is a valid feasibility finding.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Planning record only |
| Test status | No app build or device run |
| Before measurement | 0 verified target-phone camera pairs |
| After measurement | Not measured |
| Delta | Not measured |
| Outcome | Open; inspection and pre-run settings remain |
