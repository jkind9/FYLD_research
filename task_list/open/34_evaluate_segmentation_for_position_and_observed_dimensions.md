---
id: "34"
title: Evaluate segmentation for position and observed dimensions
status: open
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: ["40"]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/09_mask_geometry/**
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/02_segmentation/README.md:5
  field: evidence and comparison gap
  baseline_value: "45 masks compared; 0 independently established position/size improvements"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task34: Evaluate segmentation for position and observed dimensions

## In plain English

Measure whether better foreground masks improve position and visible dimensions. Use the same depth and camera views so the comparison isolates the mask. Full object size needs a separate measured reference and enough visible surfaces.

## What

Question: Does foreground segmentation reduce background-depth contamination and improve repeatability/absolute error or dimensions relative to rectangles?

Proposed isolated experiment, not a run authorised in Task30. Its directory is future scope, not scaffolded now. Before implementation, refine exact files/tests, complete settings/references and perform required plan review.

## Why

Existing evidence: Task19 compared 45 classical/rectangle masks and measured coordinate changes and costs, with formal real-mask accuracy null. It did not prove improved position/size accuracy. Learned segmentation remains unavailable and untested.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Classical masks and depth summaries already exist | Task19 | matched-input comparison | experiments/06_object_recognition/experiments/02_segmentation/README.md:3 |
| Coarse masks cannot supply formal accuracy | Task17 reference | reference acquisition | experiments/06_object_recognition/datasets/README.md:5 |

Proposed comparison: Freeze boxes/depth/poses and compare rectangles, inherited classical masks and independently checked foreground masks as an explicit oracle control. Then add authorised learned masks with identical prompts; separate detector-prompt quality from mask quality. Assess thin/touching/clipped objects, background mixing, empty masks and absent depth. Do not retune geometry at the same time.

Clarification, 4 October 2026 (owner): this task is the test of whether segmentation is useful at all. The learned-mask branch was assumed to start with the SAM family: SAM 2 and SAM 3 as hosted options, and MobileSAM or EdgeSAM for phone cost. Separately, record SAM 3's own video identities as an end-to-end counting baseline on the same clips, for comparison with the 3D identity rules in tasks 31 and 33. Owner direction is investigation only: no operating thresholds are needed to report the outcome.

Necessary data/reference: Task40 human-checked pixel foreground masks, reference visible surfaces/physical anchors and uncertainty, surveyed dimensions and multiple viewpoint coverage. Foreground control inputs and evaluator masks must be separately labelled; physical centre and box centre are not interchangeable. Whole-size claims require complete coverage or independently assessed completion assumptions.

Measurements: Mask overlap/boundary error, foreground depth contamination, missing/empty supports, positional repeatability, absolute anchor/surface error, observed extent and complete-size error only when referenced; prompt-to-mask/projection cost and failure counts.

Dependencies: Task40. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Annotation labour, learned checkpoint/licence/hardware access, prompts, full encoder/decoder cost, thin-surface capture and storage. Unavailable branches remain explicit.

Decision informed: Decide whether masking improves measurement enough to justify cost and which dimensions can be reported as observed rather than inferred whole size.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/experiments/02_segmentation/README.md:3 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | New publication/readers | Versioned derived records; unavailable outcomes explicit | Complete verified runs only |

Source RGB/depth/calibration and prompts → masks → visible-depth supports → camera/world measurements → evaluator. Units/grid/world/revision and visible/full semantics are explicit. References withheld except named oracle input. Failure leaves unpublished new run; old masks/measurements never overwritten. Fresh run verifies original manifests; learned branch absent without explicit acquisition.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Empty or depthless masks produce null position; fixed box/depth/pose inputs remain identical across methods; real accuracy scores require independent pixel/physical references; observed dimensions never silently become complete dimensions.

Before: 45 masks compared; 0 independently established position/size improvements. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 45 masks compared; 0 independently established position/size improvements |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
