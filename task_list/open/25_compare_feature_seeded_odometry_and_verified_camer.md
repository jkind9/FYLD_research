---
id: "25"
title: Compare feature seeded odometry and verified camera revisits
status: open
approval_status: approved
priority: LOW
type: experiment
blocked_by: [56]
blocks: []
verification_test: experiments/03_camera_pose_estimation/experiments/tests/test_camera_comparisons.py
plan_reviewed: null
files:
  - experiments/03_camera_pose_estimation/experiments/**
  - experiments/03_camera_pose_estimation/src/backend.py
docs:
  - experiments/03_camera_pose_estimation/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Compare feature seeded odometry and verified camera revisits
  baseline_value: "0 feature-seeded or verified-revisit camera comparisons"
  target: "1 same-input comparison reporting drift/failures/runtime and false loop acceptances"
created: 2026-10-03
last_updated: 2026-10-07
superseded_by: null
---

# Task 25: Compare feature seeded odometry and verified camera revisits

## In plain English

Measure whether feature matches help camera tracking and whether revisited views can correct drift. Compare each addition separately against the existing method and an established tracker. Reject look-alike scenes that cannot supply a verified camera relationship.

The comparison-directory README and verification test are future implementation deliverables. The existing stage03 README is the current documentation owner; no empty comparison folder is created by Task30.

## Current priority, 7 October 2026

Lowered to LOW and blocked only on Task56 by Task60. Run this only if Task56 shows camera drift or failed revisits that hurt measurements or counts. Deployment must be on a phone (owner, 7 October 2026). If the phone route uses ARCore camera tracking, ARCore already corrects drift on revisits, so compare against ARCore's poses before building a separate correction. The earlier Task16 blocker is removed: that research note closed without becoming a gate.

## What

Add separately owned stage03 comparison experiments for ORB/SIFT-seeded RGB-D odometry and keyframe candidate verification/pose-graph correction, after Task13 frozen baseline and Task16 research.

## Why

Current Open3D adapter starts pairs at identity and accumulates motion without map recovery or loop closure. Similarity alone cannot relock a metric camera pose.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Underlying Open3D call accepts initial motion, but our adapter currently hard-codes identity | CPUOdometry.estimate | feature-seeded adapter | experiments/03_camera_pose_estimation/src/backend.py:80 |
| Fixed-scale scoring and segment reporting already exist | evaluate | new comparison scorers | experiments/03_camera_pose_estimation/src/evaluation.py:46 |

Keep current baseline immutable. Extend the existing CPU adapter with an explicitly validated optional initial-motion argument whose default preserves identity initialisation; feature-specific wrappers stay in the new comparison folder. Test unchanged existing callers and invalid seed rejection. Compare ORB and SIFT depth-supported PnP/rigid estimates as initialisation before existing Open3D refinement. Compare appearance/ZNCC candidate retrieval separately from geometric loop verification. Choose overlap/viewpoint-based keyframes as well as any approved time interval. Verified revisits become relative-pose constraints; saved estimated keyframes are not ground-truth anchors. Reuse existing graph/backends rather than implement a full SLAM optimiser. Test a mature backend on the same modality/calibration where available. Record pose revisions and downstream recovery requirements; preserve reset segments until a validated relationship joins them.

The plan outline was approved on 3 October 2026. That approval covers no newly selected numerical values, model settings, dataset splits, or GPU runs. Task-specific protocol decisions and execution receipts remain required.

Task17 delivered the pose-revision sidecar schema; this task reuses it. This task owns its producer/serialization adapter in the new stage03 experiments folder. Persist parent revision and the complete corrected camera-to-world sequence with source/frame/world/segment keys in a unique run, validate using the shared sidecar contract, then publish completion through the existing Run owner. Interruption cannot activate a partial correction. Task35 owns the proposed evaluation and publication of corrected object/surface generations, reusing the existing Task21/22 adapters without reopening their historical trials. Task25 does not mutate their databases or old run artifacts.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original source and calibration | adapter/scorer | immutable frame IDs, pixels, times and declared metre scale | hashed manifests | experiments/shared/contracts.py:11 |
| Existing pose records | derived surface/object geometry | camera-to-world and world/segment explicit; revision sidecar contract exists from Task17 | saved records | experiments/shared/contracts.py:39 |
| Existing run owner | review/completion | unique run and SHA256 inventory; incomplete rejected | yes | experiments/shared/runs.py:59 |

Source of truth is original source evidence plus frozen configuration and independent labels. Boundaries are adapter records, saved JSON/arrays and optional database transactions; no hidden shared mutable state. Before publication a crash leaves incomplete work; after verified completion it stays immutable. Restart uses a fresh run or the existing tested identity replay. Fresh deployment follows pinned requirements and explicitly verified data/model availability; no GPU is used without approval. Existing runs/store callers must remain readable; schema/pose-revision changes require an explicit migration and downstream plan. Actor ownership and error paths must be traced at implementation-plan review.

## Hyperparameters

hyperparameters n/a: this is a proposed plan, not an authorised numerical run. Before implementation/inference, run the hyperparameter audit and replace this line with a complete name | value | source table for every relevant selection, model, prompt, seed, image size, threshold, association rule, resource cap and scoring tolerance. Newly chosen values require dated owner confirmation; inherited values require file/receipt evidence. Experiment entry points must mirror the table in HYPERPARAMETERS and published receipts. Research-only and publication-only work must retain a specific no-inference explanation.

## Verification

Contract test: experiments/03_camera_pose_estimation/experiments/tests/test_camera_comparisons.py (proposed where not yet present). Known-motion fixtures preserve source-to-target direction. An invalid feature seed cannot publish tracked success; a visually similar geometrically inconsistent scene produces 0 accepted loops. A verified loop changes earlier pose revisions with downstream correction evidence. Compare trajectories with fixed scale, all failures, continuous tracked durations and per-segment results; independent reference trajectories remain evaluator-only.

Before: 0 feature-seeded or verified-revisit camera comparisons. Target: 1 same-input comparison reporting drift/failures/runtime and false loop acceptances. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; no implementation commit |
| Files changed | Proposed scope only; task file prepared |
| Test status | Not run; planned contract checks above |
| Before measurement | 0 feature-seeded or verified-revisit camera comparisons |
| After measurement | No implementation/experiment measurement yet |
| Delta | 0 executed comparisons or implementation claims |
| Decision-gate outcome | Outline approved 3 October 2026; task-specific protocol, numerical choices and run approvals remain pending |

still open because this task has not completed its task-specific protocol, implementation, verification and review requirements.
