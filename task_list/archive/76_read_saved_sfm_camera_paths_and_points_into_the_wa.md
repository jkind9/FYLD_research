---
id: "76"
title: Read saved SfM camera paths and points into the walkthrough
status: archived
priority: MEDIUM
type: experiment
approval_status: filed 2026-10-13 after the owner asked how to keep the repo's modular structure while testing the image-only design; not yet approved to start
blocked_by: []
blocks: []
verification_test: "src/walkthrough/tests/test_saved_sfm.py"
plan_reviewed: null
files:
  - src/walkthrough/steps/tracking.py
  - src/walkthrough/steps/depth_scale.py
  - src/walkthrough/cli.py
  - src/walkthrough/tests/**
docs:
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: "Task65 walkthrough runs (Depth Anything with Open3D odometry; overlap chain) on TUM xyz and desk every-2nd clips"
  field: "walkthrough camera best fit (Task70), surface gap, plane area, object count stability, processing fps"
  baseline_value: "per Task65 and Task70 summaries"
  target: "the same walkthrough report for a run that reads a Task67 camera path and sizes Depth Anything to its points, with every downstream layer unchanged"
created: 2026-10-13
last_updated: 2026-10-15
superseded_by: 89
---

# Task 76 — Read saved SfM results into the walkthrough

## Board review, 15 October 2026

Absorbed input/pipeline plan. Task89 absorbed Tasks76/77 into src/live; Task96 added v2 replay and Task99 ran it on the Redmi. Do not start a second SfM-input orchestrator. A v2 COLMAP adapter, if needed, belongs to Task102/74; tracked-point export for alternate trackers belongs conditionally to Task104.

The earlier plan and receipts below are historical. This review changes scheduling and ownership, not their recorded results.

## In plain English

The six-layer walkthrough builds a camera path from depth. The standalone SfM experiments produce a better camera path from the images alone, and 3D points that can size the depth. This task adds two small readers so the walkthrough can use those saved files without changing its structure: one tracking choice that reads a saved camera path, and one depth-size choice that reads saved points. Surfaces, the top-down map and object counting then run as usual, so the whole report can be compared with today's runs.

## What

1. **Tracking choice `SavedPath(trajectory, frames)`** in `src/walkthrough/steps/tracking.py`, beside `ReferencePoses` (tracking.py:53). It reads a Task67 `trajectory.txt` and `frames.json`, applies the run's metric size (from the Task67 depth-model size, stored with the path), and returns one `PoseRecord` per frame; unplaced frames are `lost` with the reason. It is an estimate, so `control=None`, and the run records the file paths and SHA-256 hashes so it can never be mistaken for a reference.
2. **Depth-scale source `TrackedPointsScale(run_folder)`** in `src/walkthrough/steps/depth_scale.py`, beside `PoseTriangulatedScale`: per-frame size from the saved SfM points, with Task72's rule and settings.
3. **Command line:** `--tracking saved-path --sfm-run <folder>` and `--depth-scale tracked-points --sfm-run <folder>`; refused without the folder, or when the folder's frame list does not match the capture.
4. **Runs:** TUM xyz and desk every-2nd clips, all six layers, CPU; summarised with `scale_drift.py summarise` beside the Task65 rows.

The walkthrough's layer order is unchanged: depth still runs before tracking, but tracking now reads the saved path, so depth errors cannot move the camera. A run therefore needs two steps: the SfM experiment, then the walkthrough reading its files. Task77 reorders the layers only if this shows clear value.

## Why

The owner asked (2026-10-13) to keep the repo's rough structure and modularity while testing the change. This connects the standalone result to the full pipeline with two method choices, which is the walkthrough's existing extension point (src/walkthrough/README.md, "Each has one method choice with a written input and output contract").

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| A tracking choice that reads poses from a file | `ReferencePoses` | CLI, pipeline | src/walkthrough/steps/tracking.py:52-70 |
| A depth-scale source that reads a file per frame | `PoseTriangulatedScale` | `ScaleCorrected` | src/walkthrough/steps/depth_scale.py |
| Tracking contract and validation | `TrackingMethod`, tracking layer | pipeline | src/walkthrough/steps/tracking.py:37-38; src/walkthrough/pipeline.py:58 |
| Frame matching by timestamp | `nearest_references` | reference adapters | src/walkthrough/steps/contracts.py:166-179 |
| Saved SfM outputs | Task67, Task72 | this task | experiments/sfm/runs/* |

To be planned in full (hyperparameters, invariants, plan review) before `task.js start`.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

-
