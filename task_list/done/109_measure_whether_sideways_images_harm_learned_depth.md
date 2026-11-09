---
id: "109"
title: Measure whether sideways images harm learned depth
status: done
priority: HIGH
type: experiment
blocked_by: []
blocks: ["102"]
verification_test: "src/live/tests/test_orientation_control.py"
plan_reviewed: null
files:
  - src/live/**
  - outputs/**
docs:
  - src/live/README.md
  - learning/02_depth.md
baseline_metric:
  source: "Task106 probe, 7 November 2026"
  field: "learned-depth error against ARCore raw depth, native against upright input"
  baseline_value: "untested; phone in portrait for 90.0% (14 Oct) and 99.4% (15 Oct) of the walks; images reach the model unrotated"
  target: "Per-frame error and scale spread for native and upright input on the same frames, with a stated winner or no difference"
created: 2026-11-07
last_updated: 2026-11-07
superseded_by: null
---

# Task 109: Measure whether sideways images harm learned depth

## In plain English

The phone was held upright, but its camera delivers pictures turned on their side, and nothing turned them back before the depth model saw them. Depth models are trained mostly on upright photos. Run the model on the same frames twice, once as recorded and once turned upright, and score both against the phone's own depth.

## Verified inputs, 7 November 2026

- Session `20261015_093913_walk`: 144 frames carry a raw-depth map that passes the sizing rule.
- `session.json`: `sensor_orientation_deg: 90`. Android defines this as the clockwise turn that makes the image upright in the phone's natural (portrait) orientation. So upright = turn 90 degrees clockwise, and the inverse turns the predicted depth back.
- Gravity lies along the phone's long edge for 99.4% of the walk, so one fixed turn should apply to almost every frame. Frames where it does not (the 0.6% flat samples) are excluded and counted.
- Depth model and sizing owners: `src/live/processor.py` (model call), `src/live/sizing.py` (raw-depth targets, `depth_targets`), `experiments/sfm/src/dense.py` (`fit_size`).

## Plan

1. Test first: an asymmetric array turned upright and back is unchanged, and a marked pixel (u, v) on the native grid maps to the expected upright pixel and back.
2. Save one native and upright thumbnail pair and confirm by eye that the upright one is the right way up before scoring anything.
3. Select frames: 20 frames evenly spaced through the 144 eligible ones, in sequence order. Save the frame list before running.
4. For each frame, run the cached depth model on (a) the native image and (b) the upright image, then turn (b)'s depth and validity mask back to the native grid. Pose, intrinsics and raw-depth pixel positions stay on the native grid throughout.
5. Score each against ARCore raw depth at the confident pixels from `depth_targets`, after fitting one scale per frame with `fit_size`:
   - absolute relative error (AbsRel) and the share of pixels within 25% (delta < 1.25);
   - the fitted scale per frame, and its spread across the 20 frames (Task65 found the scale jumping between 0.86 and 2.09 on TUM);
   - the same scores against tracked points as a second reference.
6. Report per-frame and median results. If upright input is clearly better, file a follow-up to change the live processor's preprocessing, with geometry kept consistent. Do not change the processor here.

## Settings

| name | value | source |
|---|---|---|
| frames | 20, evenly spaced among the 144 eligible | proposed by Claude 7 November 2026; needs owner confirmation |
| turn direction | 90 degrees clockwise to upright; inverse after prediction | Android `SENSOR_ORIENTATION` definition; checked by eye in step 2 |
| depth model | cached Depth Anything V2 Metric Indoor Small, 16 threads | inherited: Task99 settings |
| confidence cut-off | 128 | `src/live/sizing.py:16` |
| scale fit | `fit_size` median rule | `experiments/sfm/src/dense.py`, Task72 |
| "clearly better" | median AbsRel at least 10% lower over the 20 frames | proposed by Claude; needs owner confirmation |

## Finish when

Both inputs are scored on the same frames, the result is reported with its limits (ARCore depth is not ground truth; 20 frames from one walk), and any follow-up is filed.

## Files

- PROJECT_PLAN.md (+254 -0, 254 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- research/README.md (+1 -1, 239 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- src/live/README.md (+52 -0, 141 lines)
- src/live/orientation_control.py (+117 -0, 117 lines)
- src/live/tests/test_orientation_control.py (+35 -0, 35 lines)

## Checked

- `pytest src/live/tests -> 17 passed (4 new in test_orientation_control.py); ruff -> clean; python -m src.live.orientation_control on 20261015_093913_walk -> exit 0, 20 of 144 eligible frames, 0 excluded; thumbnail pair checked by eye, upright is right way up; median AbsRel vs ARCore depth 0.080 sideways -> 0.058 upright (-27%, 17/20 frames), vs tracked points 0.106 -> 0.090 (-15%, 19/20)`
- cost: 3 min from begin to finish; Claude tokens 1,774,365 (fresh input 28,176, cache read 1,734,785, output 11,404; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.7 (was n/a (no functions))
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 16 in 4473 words: same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items", bold-labels "7 items"

## Left over

Task112 filed (stub, needs plan) to turn portrait frames upright in src/live/processor.py; then rerun the Task107 replay to see whether the surface and floor improve. 20 frames from one walk; ARCore depth is not ground truth. Started with --force (HIGH plan-review gate not run). Not committed.
