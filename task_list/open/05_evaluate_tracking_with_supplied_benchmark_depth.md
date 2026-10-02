---
id: "05"
title: Evaluate tracking with supplied benchmark depth
status: open
priority: MED
type: experiment
blocked_by: ["03"]
blocks: []
verification_test: experiments/03_tracking/README.md
plan_reviewed: null
files:
  - experiments/03_tracking/**
docs:
  - experiments/03_tracking/README.md
baseline_metric:
  source: experiments/03_tracking/README.md
  field: fresh independent controls
  baseline_value: "0 active independently evaluated tracking runs"
  target: "Reproducible CPU baseline with held-out trajectory and failure measurements"
created: 2026-10-01
last_updated: 2026-10-01
superseded_by: null
---

# Task 05: Evaluate tracking with supplied benchmark depth

## In plain English

Estimate how a camera moves while giving the tracker known depth. Compare its movement estimates with independently recorded camera positions. Keep failed tracking intervals visible so reconstruction cannot mistake them for reliable poses.

## What

Build a CPU RGB-D motion-estimation baseline using TUM supplied depth. Evaluate camera poses with a separate ground-truth reader. Use Freiburg1 xyz for development and a separately selected sequence for held-out evaluation.

## Why

Supplied depth isolates tracking from stereo errors. Reference-pose reconstruction and estimated tracking can be developed independently after shared contracts are established.

## How

| Claim | Existing owner | Consumers | Evidence |
|---|---|---|---|
| Requirements and references already documented | Existing dataset/source/experiment note | This task and downstream experiments | research/sources/15_tum_rgbd.md:13 |

1. Write known-motion, gap, texture/depth failure and segment-reset tests before the estimator.
2. Implement a documented Open3D RGB-D CPU baseline without ground-truth access; evaluator loads references only after estimation.
3. Report absolute/relative trajectory error using disclosed rigid alignment with scale fixed, tracked fraction, failures and timings.
4. Evaluate held-out sequences chosen in Task02 without retuning against their references. Report whether loop closure/recovery exist.
5. Record poses with segment/world-frame identity. A later same-observation supplied/estimated-pose reconstruction comparison follows when Tasks04 and05 both have controls.

## Invariants and recovery

Reference inputs remain unchanged and outside estimated-method inputs. Record units, frame identities and provenance at each boundary. A partial download or run is not ready data. Publish completed records only after required artifacts validate; interrupted work remains identifiable. Separate origins cannot be fused without a documented transform. No phone, cloud service or GPU is required for the initial control.

## Hyperparameters

Not selected. Before starting this task, agree and record every scene selection, frame limit/stride, association tolerance, depth interval, filtering/voxel/integration setting and scoring threshold with provenance. Add a module-level HYPERPARAMETERS record mirrored in run receipts. Do not silently inherit prototype defaults. This task is a plan, not permission to run with unspecified values.

## Verification

Estimator input cannot expose reference poses. Deliberately scaled/reversed trajectories score worse under fixed-scale evaluation; failed/reset segments remain separate. Record measured trajectory error, tracked fraction and failures on development and held-out data.

Before: 0 active independently evaluated tracking runs. Target: Reproducible CPU baseline with held-out trajectory and failure measurements. The verification_test field points to the current plan; replace it with the actual scoped contract test path before code work.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; no code or data acquired by this task |
| Files changed | Planning record only |
| Test status | Not run; exact contract test path required before code |
| Before measurement | 0 active independently evaluated tracking runs |
| After measurement | Not measured |
| Outcome | Open plan; prerequisites and pre-run configuration must be satisfied |
