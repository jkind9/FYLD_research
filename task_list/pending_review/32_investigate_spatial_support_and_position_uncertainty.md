---
id: "32"
title: Investigate spatial support and position uncertainty
status: pending_review
priority: HIGH
type: experiment
approval_status: isolated handoff implementation authorised; accuracy claims remain with parallel validation
blocked_by: ["40"]
blocks: []
verification_test: experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py
plan_reviewed: 2026-10-05 PASS
files:
  - experiments/06_object_recognition/pilot/localisation.py
  - experiments/06_object_recognition/pilot/tests/test_localisation.py
  - experiments/06_object_recognition/experiments/04_geometry_identity/spatial_support.py
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/**
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py
  - experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_spatial_support.py
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/**
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/pilot/README.md
  - experiments/06_object_recognition/experiments/04_geometry_identity/README.md
  - task_list/README.md
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

Owner update, 5 October 2026: the descriptive support component is complete, but it is not connected to association. This reopened slice adds an isolated box-and-depth association variant after Task46's late-birth fix. It does not change `pilot/replay.py`, start segmentation, or claim an accuracy gain.

Question: Which support/distribution representation accounts for position error and improves association without pretending raw depth spread is calibrated uncertainty?

Add a separate sample-export function to `pilot/localisation.py` that preserves the existing median output while exposing the immutable finite camera/world samples, source pixels, camera-depth values and explicit pose-revision lineage needed by the new variant. The Task32 module accepts those records in one world frame. It splits clearly separated depth layers into separate surface candidates, creates a `SupportSummary` for each candidate, and records visible surface extent separately from the unavailable calibrated location uncertainty. Association uses a symmetric nearest-sample support distance and the caller-supplied existing gate; the empirical covariance and Mahalanobis result are diagnostics only and never a probability or calibrated gate. The returned per-detection decisions include candidate details, feasible track scores, explicit reasons, source lineage and processing time. The source detections, tracks and candidate samples are never mutated.

The variant preserves Task46's policy: a valid unmatched single candidate can create a provisional ID at any frame, including after an earlier same-class birth. Missing pose/depth produces an unresolved decision. Multiple plausible surface candidates remain unresolved unless one candidate has a unique feasible track; duplicate boxes cannot create an extra birth when their candidate is already claimed. The existing median-point `associate_frame` function remains the comparison baseline and is not edited in this slice.

## Why

Existing evidence: Task29 assigned desk-cup box RMS is 72.8 mm with 291.7 mm maximum pair separation; it has no independent centre reference. Current adapter discards depth >=4 m. Task21 centre/median rules resolve the small reference; broad uncertainty and extent matching are untested.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Spread definitions and measurements are saved | Task29 JSON | uncertainty baseline | experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:21 |
| Depth range policy already exists | TUM adapter | supports | experiments/03_camera_pose_estimation/src/dataset.py:124 |
| World/revision-qualified positions exist | ObjectObservation | derived estimates | experiments/06_object_recognition/shared/observations.py:56 |
| Valid box pixels and camera points already use the measured-depth mask | Pilot localisation | source support adapter and median baseline | experiments/06_object_recognition/pilot/localisation.py:39-52 |
| Existing localisation keeps the median as the published baseline and returns pose/world metadata | Pilot localisation | unchanged baseline plus the new opt-in sample export | experiments/06_object_recognition/pilot/localisation.py:49-94 |
| Camera points are transformed into the supplied world frame | Shared geometry | world-space support construction | experiments/shared/geometry.py:78-87 |
| The existing median-point association and late-birth policy are the comparison baseline | Pilot replay | baseline evaluator and regression controls | experiments/06_object_recognition/pilot/replay.py:127-302 |
| The descriptive support summary already owns lineage, rank and regularised covariance | Task32 support component | candidate diagnostics | experiments/06_object_recognition/experiments/04_geometry_identity/spatial_support.py:23-148 |
| Task21 already owns the general one-to-one evaluator boundary and session/world/segment checks | Geometry identity association | isolated support variant can reuse the assignment shape while adding its required pose-revision check | experiments/06_object_recognition/experiments/04_geometry_identity/association.py:88-151,272-539 |

1. Add an opt-in sample-export function to `experiments/06_object_recognition/pilot/localisation.py` and regression tests in `experiments/06_object_recognition/pilot/tests/test_localisation.py`. It reuses `box_support` and `backproject`, transforms all valid box samples with the supplied pose, requires a non-empty pose revision when world samples are requested, and leaves `localise_detection` output unchanged.
2. Add `experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py` as an isolated variant. Keep its inputs as immutable records with source observation ID, box, valid world samples, camera-depth samples, pixel locations and `(coordinate_frame, world_id, segment_id, pose_revision_id)` lineage. Reject mixed lineages, malformed arrays and non-finite samples.
3. Split each box's valid samples by an explicit camera-depth gap parameter. Retain every candidate, its source sample indexes, world samples, support summary, depth range and visible extent. A planar book-like candidate remains valid with rank 1 or 2; its Mahalanobis diagnostic is unavailable and the association path still works from support distance.
4. Implement a separate frame association function with the same-class, one-to-one, maximum-cardinality then minimum-cost structure as the baseline. Score each candidate against each compatible track with symmetric median nearest-sample distance, report the anchor distance and the unavailable/calculated Mahalanobis diagnostic, and apply the caller's existing metric gate. Do not derive a probability from point spread.
5. Preserve Task46 outcomes explicitly rather than copying Task21's old birth branch: missing support is `unresolved_no_support`; multiple feasible candidates without a unique assignment are `unresolved_competing_support`; a candidate blocked by a track already assigned is `unresolved_track_already_assigned`; lineage-mismatched tracks cannot match, but one valid unmatched candidate still creates a provisional ID with `association: new` at any frame; a return can match the prior ID. Keep duplicate boxes as separate detection records, allow one representative to match or birth, suppress only the duplicate, and never mutate their source dictionaries or track inputs.
6. Return JSON-ready records plus `DecisionDiagnostic` records and total/per-decision `processing_time_ms` so the parallel evaluator can consume this handoff. Do not wire this variant into the published pilot replay, run an accuracy comparison, or regenerate the demo.
7. Add focused tests in `experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py` before implementation for flat planar support, missing depth/pose, foreground/background layers, neighbouring same-class supports, duplicate boxes, return matching, late same-class births, ambiguous candidates, malformed lineage, input immutability, and diagnostic timing. First run those tests red, then implement the smallest passing variant.

Hold masks/depth/poses/appearance fixed while the parallel evaluator compares median-point matching against this support variant. Separately vary depth confidence, foreground selection, box boundaries, missing depth, extent, calibration and pose error. Calibrate pair probabilities separately from position distributions. Software tests establish API and policy behaviour only; they do not establish accuracy.

Necessary data/reference: Task40 defines independently surveyed anchors/surfaces/extents and their uncertainty, reference transforms and held-out recordings. Use analytic scenes for known multimodal depth/pose perturbations; do not treat them as real sensor calibration. Region calibration and association testing need session-disjoint reference pairs.

Measurements: Absolute anchor/surface residuals by range/view; visible extent; empirical inclusion versus stated coverage only where a calibrated model exists; missing/ambiguous support frequency; false merges/splits/unresolved outcomes versus the median baseline; and association processing time. The component must not report raw spread as a probability or call the software test suite an accuracy result.

Dependencies: Task40. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Sampling versus analytic propagation, multimodal support storage, calibration-data labour and association cost. Detector scores/cosines and raw point spread cannot substitute for validated error likelihood.

Decision informed: Choose the simplest support model justified by independent coverage and association results; keep multiple hypotheses where one region hides competing foreground/background explanations.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:19 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| pilot/localisation.py:39-94 and shared/geometry.py:20-39,78-87 | Box-depth adapter | Valid measured depth samples in metres, camera pixels and world coordinates; no pose means no world candidate | Source input remains unchanged; a rerun reconstructs the same samples |
| New opt-in localisation sample export | Task32 association handoff | Exact valid box samples, source pixels, camera depths, world transform and pose-revision lineage; existing median fields remain unchanged | Caller can reconstruct from immutable RGB-D/pose inputs; no partial sample record is published |
| 07_spatial_uncertainty/association.py | Parallel evaluator | Candidate summaries, visible extent, diagnostic-only covariance/Mahalanobis value, decision reason, source observation ID and pose lineage | JSON-ready decision records can be saved; incomplete evaluation is not a result |
| Task46 pilot/replay.py:283-301 | New birth/return policy variant | Same-class provisional IDs with one-to-one assignment; unmatched valid single candidates may start at any frame | Track inputs are copied; restart begins from the saved immutable prior state |

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
| Surface depth-layer gap | `0.08 m` in synthetic contract fixtures; caller must pass it for evaluation | confirmed 2026-10-05 as a fixture partition value only; not an accuracy threshold |
| Association support-distance gate | inherited `0.35 m` only when the evaluator explicitly supplies it | inherited experiments/06_object_recognition/pilot/replay.py:38; no new Task32 gate selected |
| Support-distance ambiguity margin | inherited `0.05 m` only when the evaluator explicitly supplies it | inherited experiments/06_object_recognition/pilot/replay.py:39; no new Task32 gate selected |
| Support-distance aggregation | symmetric median of bidirectional nearest-sample distances | confirmed 2026-10-05 as an explicit empirical support metric; not a probability or calibrated uncertainty |
| One-to-one assignment | SciPy `linear_sum_assignment`; maximize cardinality then minimize total support distance | inherited experiments/06_object_recognition/pilot/replay.py:15,217 |
| Nearest-sample search | Exact SciPy `cKDTree` query with `k=1`, `workers=1` | inherited SciPy dependency; implementation detail to bound support-search memory |
| Location uncertainty calibration | unavailable | n/a raw support spread is visible extent/diagnostic scatter, not a calibrated probability |

## Verification

Contract tests `pilot/tests/test_localisation.py`, `test_spatial_support.py` and `07_spatial_uncertainty/tests/test_association.py` must assert that opt-in sample export preserves the existing median output, emits exact immutable camera/world samples with pose-revision lineage, and rejects missing lineage; immutable finite-sample summaries; separate visible extent and unavailable calibrated uncertainty; flat planar support; foreground/background candidate separation; missing depth/pose; mixed or invalid lineage never matching; neighbouring same-class one-to-one matching; duplicate boxes; returns; late same-class provisional births; ambiguous candidates; input immutability; preserved confirmed track state; bounded support-distance diagnostics; per-decision diagnostics; and non-negative processing time. They must also assert that the median-point `pilot.replay.associate_frame` behaviour remains unchanged. These are API and policy contracts and an evaluator handoff; they do not establish calibrated uncertainty or an accuracy gain.

Before: 0 independently calibrated spatial models; assigned cup RMS 72.8 mm; median-point association remains the baseline. After: no new measurement in this component task. The parallel evaluator may consume the handoff and report paired measurements later; thresholds and accuracy claims remain outside this task.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No new commit; local stack remains unpublished pending owner decision |
| Files changed | `pilot/localisation.py`, its tests, new `07_spatial_uncertainty` association/tests package, the related READMEs, Task32 receipt, and Task47 follow-up receipt |
| Test status | The original 66-test focused baseline passed before follow-ups. Seven added regressions bring the final suite to 73 passed; Black, Ruff, Python compilation, adapter mypy, task-plan lint, and diff whitespace checks passed. Mypy cannot address the new module because its folder name begins with digits. Final diff review found and cleared seven issues; the last review reported no findings. |
| Before measurement | 0 independently calibrated spatial models; assigned cup RMS 72.8 mm |
| After measurement | No accuracy measurement; the isolated handoff and policy contracts pass |
| Delta | No accuracy delta measured or claimed |
| Decision-gate outcome | Handoff ready for the parallel evaluator. Calibration, usefulness, thresholds, and matching benefit remain undecided; the median baseline and Task46 birth policy remain unchanged |

still open because independent references and validation remain outside this session. Task32 must not be treated as an accuracy result, and publication remains pending the owner's decision.
