---
id: "32"
title: Investigate spatial support and position uncertainty
status: open
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: ["40"]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/**
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:71
  field: evidence and comparison gap
  baseline_value: "0 independently calibrated spatial models; assigned cup RMS 72.8 mm"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task32: Investigate spatial support and position uncertainty

## In plain English

Find out whether regions of possible position match objects better than a single point. Separate a chosen object reference point from its visible surface and full size. Check uncertainty claims against measurements collected independently.

## What

Question: Which support/distribution representation accounts for position error and improves association without pretending raw depth spread is calibrated uncertainty?

Proposed isolated experiment, not a run authorised in Task30. Its directory is future scope, not scaffolded now. Before implementation, refine exact files/tests, complete settings/references and perform required plan review.

## Why

Existing evidence: Task29 assigned desk-cup box RMS is 72.8 mm with 291.7 mm maximum pair separation; it has no independent centre reference. Current adapter discards depth >=4 m. Task21 centre/median rules resolve the small reference; broad uncertainty and extent matching are untested.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Spread definitions and measurements are saved | Task29 JSON | uncertainty baseline | experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:19 |
| Depth range policy already exists | TUM adapter | supports | experiments/03_camera_pose_estimation/src/dataset.py:124 |
| World/revision-qualified positions exist | ObjectObservation | derived estimates | experiments/06_object_recognition/shared/observations.py:56 |

Proposed comparison: Hold masks/depth/poses/appearance fixed while comparing single centres, simple bounded regions/ellipsoids, empirical surface supports and non-Gaussian/multiple hypotheses where foreground/background mix. Separately vary depth confidence, foreground selection, box boundaries, missing depth, extent, calibration and pose error. Separate anchor uncertainty, observed geometry and possible full dimensions. Missing data is unknown, not zero-probability free space.

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

Raw pixels/depth and confidence → immutable support samples → declared anchor/extent hypotheses → association/scoring. Units, depth semantics, coordinate frame and lineage are explicit. Reference data is evaluator-only except named oracle controls. An interrupted run cannot publish calibrated parameters or partial supports; restart uses a new run. Backward reading preserves point-only records with explicit unavailable uncertainty.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Known synthetic separate depth modes remain distinguishable; missing depth cannot produce an anchor; uncertainty coverage is scored against independent references with nonzero reference uncertainty; world/segment/revision mismatch prevents metric association.

Before: 0 independently calibrated spatial models; assigned cup RMS 72.8 mm. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 0 independently calibrated spatial models; assigned cup RMS 72.8 mm |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
