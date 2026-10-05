---
id: "32"
title: Investigate spatial support and position uncertainty
status: pending_review
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: ["40"]
blocks: []
verification_test: experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_spatial_support.py
plan_reviewed: 2026-10-05 PASS
files:
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/**
  - experiments/06_object_recognition/experiments/04_geometry_identity/spatial_support.py
  - experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_spatial_support.py
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:71
  field: evidence and comparison gap
  baseline_value: "0 independently calibrated spatial models; assigned cup RMS 72.8 mm"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-05
superseded_by: null
---

# Task32: Investigate spatial support and position uncertainty

## In plain English

Find out whether regions of possible position match objects better than a single point. Separate a chosen object reference point from its visible surface and full size. Check uncertainty claims against measurements collected independently.

## What

Question: Which support/distribution representation accounts for position error and improves association without pretending raw depth spread is calibrated uncertainty?

Build the reusable support representation first, without running a comparison. Add `spatial_support.py` beside the existing location estimator and focused tests. The component accepts immutable finite 3D samples plus explicit coordinate-frame/world/segment/pose-revision lineage, returns a mean, regularised covariance, rank and sample count, and computes squared Mahalanobis distance only when the support has enough samples and full 3D rank. Malformed inputs raise a clear validation error; rank-deficient, missing or insufficient support returns an explicit unavailable distance. Do not change the existing association policy or select a threshold in this task.

## Why

Existing evidence: Task29 assigned desk-cup box RMS is 72.8 mm with 291.7 mm maximum pair separation; it has no independent centre reference. Current adapter discards depth >=4 m. Task21 centre/median rules resolve the small reference; broad uncertainty and extent matching are untested.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Spread definitions and measurements are saved | Task29 JSON | uncertainty baseline | experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:21 |
| Depth range policy already exists | TUM adapter | supports | experiments/03_camera_pose_estimation/src/dataset.py:124 |
| World/revision-qualified positions exist | ObjectObservation | derived estimates | experiments/06_object_recognition/shared/observations.py:56 |

The first component is descriptive plumbing for that comparison. Hold masks/depth/poses/appearance fixed while a later evaluator compares single centres, covariance ellipsoids, empirical surface supports and non-Gaussian/multiple hypotheses. Separately vary depth confidence, foreground selection, box boundaries, missing depth, extent, calibration and pose error. Separate anchor uncertainty, observed geometry and possible full dimensions. Missing data is unknown, not zero-probability free space.

Necessary data/reference: Task40 defines independently surveyed anchors/surfaces/extents and their uncertainty, reference transforms and held-out recordings. Use analytic scenes for known multimodal depth/pose perturbations; do not treat them as real sensor calibration. Region calibration and association testing need session-disjoint reference pairs.

Measurements: Absolute anchor/surface residuals by range/view; empirical inclusion versus stated coverage, region volume/sharpness, proper distribution scores where a density is defined; missing/ambiguous support frequency; false merges/splits/unresolved outcomes versus centre baseline. Calibrate pair probabilities separately from position distributions.

Dependencies: Task40. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Sampling versus analytic propagation, multimodal support storage, calibration-data labour and association cost. Detector scores/cosines and raw point spread cannot substitute for validated error likelihood.

Decision informed: Choose the simplest support model justified by independent coverage and association results; keep multiple hypotheses where one region hides competing foreground/background explanations.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:19 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | New publication/readers | Versioned derived records; unavailable outcomes explicit | Complete verified runs only |

Raw pixels/depth and confidence → immutable support samples → declared anchor/extent hypotheses → association/scoring. Units, depth semantics, coordinate frame and world/segment/pose-revision lineage are explicit in the support record. Reference data is evaluator-only except named oracle controls. An interrupted run cannot publish calibrated parameters or partial supports; restart uses a new run. Backward reading preserves point-only records with explicit unavailable uncertainty.

## Per-stage log, 5 October 2026

Report anchor error, coverage and uncertainty measures in the shared per-stage report format from Task44 (3D object position section), stating reference kind and input mode. Task45's per-box background fraction and wobble are inputs worth testing here: they describe how mixed foreground/background a support is before any distribution is fitted.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| Covariance diagonal regularisation | `1e-6 m²` | confirmed 2026-10-05 for numerical stability only; not a measurement uncertainty or acceptance threshold |
| Minimum independent support samples for Mahalanobis distance | `4` | confirmed 2026-10-05 as an API guard; fewer samples return unavailable |
| Covariance estimator | Unbiased sample covariance, denominator `n - 1`; `n=1` uses zero scatter before regularisation | confirmed 2026-10-05 for this descriptive component |
| Rank tolerance | `1e-10` passed to `numpy.linalg.matrix_rank` | confirmed 2026-10-05 as a numerical-degeneracy guard |
| Association distance threshold | not selected | n/a validation session must choose and test it |

## Verification

Contract test `experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_spatial_support.py` must assert immutable finite-sample summaries, symmetric positive-definite regularised covariance, explicit lineage, correct zero-distance and known-distance Mahalanobis values, clear rejection of malformed/non-finite samples, and unavailable output below the minimum support count or below full 3D rank. This is an API contract; it does not establish calibrated uncertainty or a useful matching threshold.

Before: 0 independently calibrated spatial models; assigned cup RMS 72.8 mm. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Pending review; implementation commit not yet created |
| Files changed | `spatial_support.py`, focused API tests, object-recognition README and this task plan/receipt |
| Test status | 18 focused tests passed; Ruff passed; plan review PASS recorded 2026-10-05; no association policy or independent validation run |
| Before measurement | 0 independently calibrated spatial models; assigned cup RMS 72.8 mm |
| After measurement | Component contract verified; no accuracy result |
| Delta | 0 executed comparisons; one reusable support API added |
| Decision-gate outcome | Implementation complete for review. Validation of calibration, usefulness, thresholds and matching benefit remains with the parallel evaluation session; current association policy is unchanged |

still open because independent references and validation are not complete. The component is ready for the parallel evaluator to consume, but Task32 must not be treated as an accuracy result.
