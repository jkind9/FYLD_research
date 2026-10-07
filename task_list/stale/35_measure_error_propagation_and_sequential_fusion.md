---
id: "35"
title: Measure error propagation and sequential fusion
status: stale
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: [32, 34, 40, 56]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/10_sequential_fusion/**
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:23
  field: evidence and comparison gap
  baseline_value: "0 independent sequential-error comparisons; cup RMS 72.8 mm on correlated selected views"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-07
superseded_by: null
---

# Task35: Measure error propagation and sequential fusion

## In plain English

Find out when more views improve an estimate and when they repeat a mistake. Change one source of error at a time before combining them. Check how earlier object and surface estimates change when camera positions are corrected.

## Current priority, 6 October 2026

Task13 no longer waits for this investigation. Publish Task56's complete baseline first; use its failures to choose the error/fusion comparison. Task53 owns independent acquisition and Task56 owns complete-report integration. Analytic controls remain useful, but this task does not block the first complete benchmark.

## What

Question: Which errors dominate the pixel-to-fusion chain, and under what conditions do additional independent views reduce or reinforce error?

Proposed isolated experiment, not a run authorised in Task30. Its directory is future scope, not scaffolded now. Before implementation, refine exact files/tests, complete settings/references and perform required plan review.

## Why

Existing evidence: Task29 spread is correlated and association-selected, not independent accuracy. Task21 compares last and independent-view median on a small provisional sample. PoseRevision exists, but Task25 corrected path production and full Task13 validation remain later work.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Observation lineage and revision-qualified positions exist | ObjectObservation | fusion input | experiments/06_object_recognition/shared/observations.py:17 |
| Pose revision contract exists | PoseRevision | correction consumer | experiments/06_object_recognition/shared/pose_revisions.py:17 |
| Correlated spread definition is explicit | Task29 JSON | sequential baseline | experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:23 |

Proposed comparison: Trace pixels/masks, depth, camera coordinates, calibration/poses, world coordinates, association and fusion. Apply separate known perturbations, then combined perturbations. Compare individual/last/equal-weight/robust estimates as independently translated views arrive. Isolate nearby correlated frames, reused/reprojected depth, bias, outliers, wrong association and pose drift. Compare replay after corrected poses against fresh reconstruction; Task25-produced corrections are an optional later condition after Task13, not a reason to run it now.

Necessary data/reference: Task40 analytic and surveyed references with uncertainty; distinct captures/measurement lineage; Task32 anchor/support model and Task34 fixed support comparisons. Real correction trials require reviewed Task25 outputs and frame/world/revision mapping. References used in correction cannot independently score that same correction.

Measurements: Absolute error/coverage and repeatability versus independent views/time; bias/outlier response, wrong-identity contamination, surface distance/coverage, rebuild consistency and full correction/runtime/storage costs. Report cases where extra frames worsen error; no assumed square-root frame-count gain.

Dependencies: Task32, Task34, Task40. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Per-view lineage/correlation tracking, fusion-state storage, global rebuild versus incremental updates, reference capture and pose-correction availability.

Decision informed: Choose evidence weighting/fusion and correction recovery rules justified by independent measurements, and state when additional views should be rejected or treated as redundant.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/shared/observations.py:17 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | New publication/readers | Versioned derived records; unavailable outcomes explicit | Complete verified runs only |

Immutable source pixels/depth and pose revisions → derived observations → association → object/surface generation. Source-of-truth observations never change. Corrected poses invalidate/rebuild every affected estimate before one atomic generation activation; process death before activation leaves old generation, after activation exposes complete new records. Original identities/history survive recomputation. Fresh-deploy path verifies inputs/configuration then publishes a new run; old generations remain readable.

## Per-stage log, 5 October 2026

The shared per-stage report from Task44 carries this task's results. Each stage section records whether its inputs came from the reference (`isolated`) or from earlier predictions (`chained`), so the inherited error at each stage is the chained minus isolated difference on the same frames. This task fills the 3D-position and fusion rows and uses Task45's detection bias and wobble as the measured detection-stage error, instead of a synthetic guess. Task44's `compare` gives the before/after per stage when a fusion rule changes.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Repeated/reprojected measurements retain lineage; biased repeats cannot be scored as new independent references; corrected generations contain consistent pose revisions; rebuilt outputs match a fresh corrected replay under recorded tolerances.

Before: 0 independent sequential-error comparisons; cup RMS 72.8 mm on correlated selected views. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 0 independent sequential-error comparisons; cup RMS 72.8 mm on correlated selected views |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.

## Board decision, 2026-10-07

Parked under Task60 with owner approval. This is an optional object-identity or review refinement that does not lead directly to the accuracy, latency or phone-deployment goals. It returns to `open/` only if Task56's complete walkthrough benchmark shows a measured failure it would fix; refresh its blockers and plan review then. Earlier receipts and authorisations remain as written. Task56's per-stage report already separates errors that come from earlier stages.
