---
id: "103"
title: Measure Redmi camera and IMU calibration from owner recordings
status: open
priority: MED
type: experiment
blocked_by: [52]
blocks: []
verification_test: "experiments/open_vio/tests/test_calibration.py"
plan_reviewed: null
files:
  - experiments/open_vio/calibration/**
  - experiments/open_vio/tests/**
docs:
  - experiments/open_vio/README.md
  - learning/12_rebuilding_arcore.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Measure Redmi camera and IMU calibration from owner recordings"
  baseline_value: "Kalibr pipeline validated on TUM-VI; no Redmi target video or long rest; clock estimate -2.67 ms correlation 0.62"
  target: "Measured Redmi calibration and noise with uncertainty, convergence evidence and clock cross-check"
created: 2026-10-15
last_updated: 2026-10-15
superseded_by: null
---

# Task 103: Measure Redmi camera and IMU calibration from owner recordings

## In plain English

Measure how the phone camera and motion sensors relate to each other. Film a printed target and record the phone lying still for long enough to estimate sensor noise. Reuse the existing calibration tools, then check their result against the phone's own estimates.

## Current evidence and prerequisites

Task90 built the calibration pipeline and verified it on TUM-VI: rotation difference 0.014 degrees, translation 1.0 mm and time shift 0.13 ms. It did not calibrate the Redmi. Task99's -2.67 ms clock estimate is a correlated estimate from ARCore/gyro data, not a measured camera-to-IMU calibration. No target video, measured printed tag or approximately 3-hour rest has arrived. A 60 s rest in Task52 is a health check and does not replace that noise recording.

## Plan

1. After Task52 capture checks, coordinate owner recordings using `experiments/open_vio/README.md` step 2: existing A4 target printed at actual size, measured tag edge, approximately 60-90 s varied target motion and approximately 3 h motion-only rest. Use FYLD capture, not the retired rawrecorder.
2. Validate v2 input, camera configuration, orientation, clocks, bias columns, gaps and missing settings. Reuse `host/recording.py` and `calibration/prepare.py`; test any v2/calibration adaptation before changing it.
3. Run `calibration/allan.py`, `prepare.py`, `run_kalibr.sh` and `compare.py` in the existing CPU Docker/WSL route. Preserve raw inputs and pin source/runtime/configuration identities. Check convergence and required output files, not just process exit code.
4. Report camera intrinsics/distortion, camera-to-IMU transform and time shift, rates, noise densities/random walks, residuals and estimated uncertainty. Compare against ARCore camera/device pose extrinsics and the clock correlation with their different timestamp semantics stated.
5. Re-run the existing TUM-VI control if converter/configuration changes affect it. Publish a versioned calibration consumed by Task104; a poor or under-excited fit is a valid negative result, not usable calibration.

## Settings and completion

Inherit Task90's target and pinhole-radtan model as proposals, not owner-ratified product limits; use the physically measured tag size, not nominal 24 mm. Record noise inflation, offset search and camera configuration. Keep the raw data private. One background queue with START/END logs and completion notification. This task owns the unperformed Redmi follow-up of completed Task90, not rebuilding its tools or claiming its public-dataset result as handset evidence.
