---
id: "74"
title: Compare remaining CPU 3D models on the recorded Redmi walk
status: open
priority: MED
type: experiment
blocked_by: [102]
blocks: []
verification_test: "experiments/sfm/tests/test_posed.py"
plan_reviewed: null
files:
  - experiments/sfm/**
  - src/live/tests/**
docs:
  - experiments/sfm/README.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Compare remaining CPU 3D models on the recorded Redmi walk"
  baseline_value: "DA3 Small already scored on TUM/ICL; no same-walk Redmi batch-model comparison"
  target: "One controlled Redmi comparison with coverage, scale source, runtime and honest unavailable metrics"
created: 2026-10-13
last_updated: 2026-10-15
superseded_by: null
---

# Task 74: Compare remaining CPU 3D models on the recorded Redmi walk

## In plain English

Compare another way of estimating scene depth and camera motion using the same phone recording. Keep the images, image orientation and scoring rules fixed so a different result can be traced to the method. Do not repeat completed benchmark trials as if they were new work.

## Current evidence

Task80 already ran Depth Anything 3 Small in single-image and pose-conditioned modes on TUM xyz, desk and ICL, at 4.4-5.6 fps on CPU. It failed its accuracy-improvement target on TUM and improved ICL by 15%. Task79 found no gain from Prompt Depth Anything. Task67 provides a COLMAP baseline; Tasks71/72/78 isolate depth, camera path and scale. None establishes Redmi accuracy.

The missing experiment is the same Redmi walk, after Task102 resolves orientation/convention errors and publishes a reproducible baseline. A CPU batch trial is diagnostic; using future frames cannot establish live deployment.

## Plan

1. Reuse `experiments/sfm/dump_da3_depth.py`, `src/posed.py`, `run_dense.py` and the existing scorers. Tighten the exact files before execution. Add v2 input adaptation tests first rather than a second session parser.
2. Begin with the already installed Small checkpoint: single-image depth and pose-conditioned depth on the same frame IDs and calibration as the corrected Task102 baseline. If testing jointly estimated cameras, declare that separate row; Task80's supplied-pose mode did not test that claim.
3. Carry orientation preprocessing, depth rotation back to the source grid, scale inputs, window overlap and live/offline availability into saved metadata. Reference poses never enter an image-only prediction row.
4. Compare raw ARCore depth, the current learned-depth baseline and candidate depth on shared valid pixels/frames; retain complete-coverage rows separately so methods with fewer placed frames are not rewarded. A COLMAP path is an offline method comparison, not ground truth. Tasks75/53 own physical accuracy.
5. Report scale source, placed/lost frames, depth/surface coverage, disagreements, cold/steady/end-to-end CPU speed, longest update gaps and peak memory. Accept a negative result. Do not claim a geometric improvement from a nicer render.

## Deferred candidates

The old task mixed feed-forward models, learned SLAM and GPU SfM. MapAnything, VGGT, DROID/DPV, FastMap and GPU multi-view stereo are deferred under the CPU-only rule. No download, licence claim or expected speed is accepted from the 13 October table without rechecking primary sources at execution. New sources go in research and the matching learning chapter. No GPU run is scheduled by this task.

## Settings and completion

Inherit pinned Task80 code/checkpoint and Task102's input/geometry conventions. Window sizes, selected frames and confidence masks must be recorded as proposed by Claude, not owner-ruled, unless inherited unchanged. Finish with a reproducible same-input table and saved outputs; no promise that a new model will improve the house reconstruction. This replaces the obsolete dependency on completed Task67 and its unimplemented first-Small-trial plan.
