---
id: "111"
title: Find why the 14 October walk saved empty ARCore depth
status: open
priority: LOW
type: bug
blocked_by: []
blocks: []
verification_test: "research/experiments/01_camera_capture_delivery/tests/test_capture_receiver.py"
plan_reviewed: null
files:
  - research/experiments/01_camera_capture_delivery/**
docs:
  - research/experiments/01_camera_capture_delivery/README.md
baseline_metric:
  source: "Task106 probe, 7 November 2026"
  field: "raw-depth content and timing, 20261014_220756_walk"
  baseline_value: "44 depth messages, all zero bytes; their timestamps span 0.4 s and are 4.3-38.7 s older than the frames carrying them (median 21.5 s)"
  target: "A stated cause, and a capture or receiver check that flags stale or empty depth during recording"
created: 2026-11-07
last_updated: 2026-11-12
superseded_by: null
---

# Task 111: Find why the 14 October walk saved empty ARCore depth

## Amendment, 12 November 2026

Deferred. After owner decision 10 ([plan](../../PROJECT_PLAN.md#owner-decisions-in-force)), ARCore depth is not a product input, so why it was empty on 14 October matters only for comparison recordings. It no longer blocks Task52. The general lesson moves to Task52: capture checks should flag stale or empty measured data of any kind. Move it to `stale/` with the board tool when that is next run.


## In plain English

The main house walk sent 44 depth images from the phone, and every one is blank. They also all date from the first half-second of the session, so the phone kept resending old, empty images for the whole walk. Find out why, and make the capture app or the PC warn when it happens, so a bad recording is caught on the day.

## Verified facts, 7 November 2026

- **14 October walk (`20261014_220756_walk`, capture 1.2):** 44 depth messages; 0 non-zero bytes in depth and confidence; depth timestamps within a 0.4 s window, 4.3-38.7 s older than their frames.
- **15 October walk (`20261015_093913_walk`, capture 1.2):** 147 depth maps with data; depth trails its frame by a median of 8 ms, maximum 4.4 s; timestamps span 25.3 s.
- **Session settings are identical** apart from clocks and counts (`session.json` compared field by field). Both use `RAW_DEPTH_ONLY` and `FIXED` focus.
- **Earlier runs had real depth:** the check app at 47.6% valid pixels (Task85) and a capture-app tracking report at 60.4% valid over 889 depth frames (`runs/capture_redmi_20261014/reports/20261014T212149_627_2201116TG.json`).
- **App code:** `FrameCapture.addDepth` (`capture/app/src/main/java/org/fyld/capture/FrameCapture.java:91-108`) sends a depth image whenever its timestamp differs from the previous one sent. Two stale images that alternate would both pass this check.

## Plan

1. List the 44 depth timestamps in order and show whether they alternate or repeat. Compare with ARCore's tracking state and the first frames' timing.
2. Check telemetry (`telemetry.jsonl`) for temperature, CPU or memory differences between the two walks.
3. State the most likely cause with its evidence: ARCore depth never starting on that run, stale images passing the duplicate check, or another cause found in steps 1-2. Say what remains unproven.
4. Tests first, then fixes for any confirmed app or receiver defect:
   - the app sends a depth map only if its timestamp is newer than every map already sent;
   - the receiver's `summary.json` counts depth maps with no valid pixels and maps older than their frame by more than 1 s, and marks the session as a warning when either is non-zero.
5. Update the capture README and the Task99 table note. A rebuilt APK needs a new deployment entry and the owner's handset run; that run belongs to Task52.

## Settings

settings n/a: a diagnosis and defect fix with no tunable experiment values, apart from the 1 s staleness warning, proposed by Claude 7 November 2026 and needing owner confirmation.

## Finish when

The cause is stated with evidence, and confirmed defects have RED and GREEN tests. A rebuilt APK, if any, is listed for the owner to install.
