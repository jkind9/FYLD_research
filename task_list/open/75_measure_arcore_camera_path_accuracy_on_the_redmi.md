---
id: "75"
title: Measure Redmi ARCore drift and physical distance error
status: open
priority: MED
type: experiment
blocked_by: [52, 102]
blocks: []
verification_test: "experiments/01_camera_capture_delivery/tests/test_accuracy.py"
plan_reviewed: null
files:
  - experiments/01_camera_capture_delivery/**
docs:
  - experiments/01_camera_capture_delivery/README.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Measure Redmi ARCore drift and physical distance error"
  baseline_value: "1177 matched ARCore records, all tracking; zero independently measured Redmi accuracy trials"
  target: "At least three closed-loop trials with surveyed marker distances and an offline same-frame camera comparison"
created: 2026-10-13
last_updated: 2026-10-15
superseded_by: null
---

# Task 75: Measure Redmi ARCore drift and physical distance error

## In plain English

Measure how far the phone's reported camera path differs from a physical walk. Start and finish at marked positions and measure distances independently with a tape. Tracking success alone does not say the path is accurate.

## Current evidence

The installed capture 1.2 app already includes ARCore, its notice and live pose logging. Task99's walk contains 1,177 matched tracking records out of 1,194 images. There is no independent path reference or tape survey. Task92 already built `host/accuracy.py`, its tests and `field_accuracy.md`; reuse them. No alternative logger, new ARCore integration or old phonecheck APK is required.

## Plan

1. Use Task52's checked capture app and the existing field guide. Coordinate at least three marked closed loops with the owner; record route, duration, physical start/end placement uncertainty and tape-measured marker distances before inspecting predictions. Indoor/stair/outdoor conditions are separate labelled trials, not an unsupported claim about the existing walk's route.
2. The existing accuracy scorer imports the v1 reader. Test and add a v2 input adapter using the shared reader; do not create a second accuracy scorer. Preserve frame identity, camera convention and anchor revision history; raw live and final corrected path scores are separate.
3. Report endpoint drift in mm and percent of walked distance, marker-distance error, tracking loss/recovery, missing poses and segment resets. Closure is a partial check, not a full-path accuracy measure.
4. Reuse Task102/74's v2-to-COLMAP input adaptation on the exact same image IDs. Report offline camera-path disagreement and tape-based metrics; neither ARCore nor COLMAP is independent truth for the other.
5. Record uncertainties and negative results. Task61 supplies product acceptance limits if a PASS/FAIL claim is wanted; their absence does not prevent reporting measured error.

## Settings and completion

The three-trial minimum is inherited from this task's 13 October plan, not a new owner acceptance threshold. Freeze image orientation, scale fitting and timestamp selection after Task102; new settings are proposed by Claude, not owner-ruled. CPU only. Finish with measured receipts or an explicit remaining owner capture handover; a scorer passing fixtures does not satisfy the physical trials.
