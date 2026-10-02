---
id: "04"
title: Evaluate reconstruction with supplied depth and poses
status: open
priority: MED
type: experiment
blocked_by: ["03"]
blocks: []
verification_test: experiments/04_reconstruction/README.md
plan_reviewed: null
files:
  - experiments/04_reconstruction/**
docs:
  - experiments/04_reconstruction/README.md
baseline_metric:
  source: experiments/04_reconstruction/README.md
  field: fresh independent controls
  baseline_value: "0 independently scored active reconstruction runs"
  target: "Reproducible reference-pose control with surface error, coverage and failure results"
created: 2026-10-01
last_updated: 2026-10-02
superseded_by: null
---

# Task 04: Evaluate reconstruction with supplied depth and poses

## In plain English

Build a surface using known camera positions and measured example depth. Compare it with the published reference shape. This tells us what reconstruction itself gets wrong before adding tracking errors.

## What

Build the reference-pose reconstruction control from verified ICL living-room depth/calibration/poses. Compare direct point accumulation with Open3D surface fusion only after a simple control works. Score against the separate living-room reference surface.

This is the main starting experiment after task 03. Retain original views and frame identifiers so task 09 can associate object observations with measured geometry. Task 08's phone feasibility check runs alongside this control. Replace reference poses and depth one at a time only after independent controls pass.

## Why

This is the critical geometric control for evaluating later tracking/depth changes. Correct camera poses do not imply correct fusion or surface coverage.

## How

| Claim | Existing owner | Consumers | Evidence |
|---|---|---|---|
| Requirements and references already documented | Existing dataset/source/experiment note | This task and downstream experiments | research/sources/18_icl_nuim.md:13 |

1. Write known-surface and invalid-input tests before implementation; use Task03's verified contracts.
2. Start with direct accumulation and explicit validity; keep reference surface out of reconstruction inputs.
3. Add optional CPU Open3D integration as a separate comparison, recording extrinsic direction and all selected settings.
4. Score surface distances in the established shared frame and report reference coverage separately. Avoid fitting scale to hide an error or inferring unseen regions from a closed mesh.
5. Save unique run manifests/results; incomplete runs remain explicitly incomplete. Record failures, timing/memory and visible-reference selection.

## Invariants and recovery

Reference inputs remain unchanged and outside estimated-method inputs. Record units, frame identities and provenance at each boundary. A partial download or run is not ready data. Publish completed records only after required artifacts validate; interrupted work remains identifiable. Separate origins cannot be fused without a documented transform. No phone, cloud service or GPU is required for the initial control.

## Hyperparameters

Not selected. Before starting this task, agree and record every scene selection, frame limit/stride, association tolerance, depth interval, filtering/voxel/integration setting and scoring threshold with provenance. Add a module-level HYPERPARAMETERS record mirrored in run receipts. Do not silently inherit prototype defaults. This task is a plan, not permission to run with unspecified values.

## Verification

An incorrect depth scale or pose direction must worsen the independent geometry score. Removing observations must reduce reported coverage, rather than improve completeness. Produce supplied-pose surface-error/coverage/timing measurements; no product accuracy threshold is selected yet.

Before: 0 independently scored active reconstruction runs. Target: Reproducible reference-pose control with surface error, coverage and failure results. The verification_test field points to the current plan; replace it with the actual scoped contract test path before code work.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; no code or data acquired by this task |
| Files changed | Planning record only |
| Test status | Not run; exact contract test path required before code |
| Before measurement | 0 independently scored active reconstruction runs |
| After measurement | Not measured |
| Outcome | Open plan; prerequisites and pre-run configuration must be satisfied |
