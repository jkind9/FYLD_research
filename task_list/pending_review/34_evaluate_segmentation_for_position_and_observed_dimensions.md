---
id: "34"
title: Evaluate segmentation for position and observed dimensions
status: pending_review
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: ["40"]
blocks: []
verification_test: experiments/06_object_recognition/experiments/02_segmentation/tests/test_mask_pipeline.py
plan_reviewed: 2026-10-05 PASS
files:
  - experiments/06_object_recognition/experiments/02_segmentation/mask_pipeline.py
  - experiments/06_object_recognition/experiments/02_segmentation/tests/test_mask_pipeline.py
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/02_segmentation/README.md:5
  field: evidence and comparison gap
  baseline_value: "45 masks compared; 0 independently established position/size improvements"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-05
superseded_by: null
---

# Task34: Evaluate segmentation for position and observed dimensions

## In plain English

Measure whether better foreground masks improve position and visible dimensions. Use the same depth and camera views so the comparison isolates the mask. Full object size needs a separate measured reference and enough visible surfaces.

## What

Question: Does foreground segmentation reduce background-depth contamination and improve repeatability/absolute error or dimensions relative to rectangles?

Build the reusable segmentation block first, without making an accuracy claim. Add `mask_pipeline.py` beside the existing rectangle/GrabCut/Canny controls and focused tests. The block preserves original image grids, carries prompt and frame lineage in its returned value for a future caller, returns explicit empty/failed states, and measures wall-clock cost per mask method. It does not alter the current runner's persisted report, detection, depth or identity code.

## Why

Existing evidence: Task19 compared 45 classical/rectangle masks and measured coordinate changes and costs, with formal real-mask accuracy null. It did not prove improved position/size accuracy. Learned segmentation remains unavailable and untested.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Rectangle, GrabCut and Canny mask generation already exists | `masks.segment` | `run.py` calls it for each prompt | experiments/06_object_recognition/experiments/02_segmentation/masks.py:31; experiments/06_object_recognition/experiments/02_segmentation/run.py:203 |
| Depth support summaries already exist | `support.summarise` | later depth/geometry consumers | experiments/06_object_recognition/experiments/02_segmentation/support.py:11 |
| Existing runner owns persisted timing and method rows | `run.py` | JSON report readers | experiments/06_object_recognition/experiments/02_segmentation/run.py:203; experiments/06_object_recognition/experiments/02_segmentation/run.py:217 |
| Coarse masks cannot supply formal accuracy | reference acquisition task | validation session | experiments/06_object_recognition/datasets/README.md:5 |

The component supplies an execution contract for the later comparison: freeze boxes/depth/poses and compare rectangles, inherited classical masks and independently checked foreground masks as an explicit oracle control. It wraps `masks.segment`; it does not replace the existing runner or write report rows. A future learned adapter can implement the same interface with identical prompts; detector-prompt quality stays separate from mask quality. Assess thin/touching/clipped objects, background mixing, empty masks and absent depth. Do not retune geometry at the same time.

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
| `mask_pipeline.run_methods` | Future validation caller | RGB array on original pixel grid; immutable binary masks; prompt/frame/world lineage strings | Caller must persist its own run record |
| Existing `run.py` | Current report readers | Existing method rows, support and timing schema | Existing reports remain unchanged |

For this task, the broader RGB/depth/calibration-to-evaluator chain is a validation design only. The new component stops after returning mask results; it does not create visible-depth supports, camera/world measurements or evaluator records.

Source of truth: the returned `MaskPipelineResult` for the current call. The only boundary is the Python caller receiving immutable NumPy masks and lineage fields. A process exit discards the in-memory result and leaves existing reports unchanged. Fresh deployment requires the existing segmentation package and OpenCV; no model artifact is required.

invariants n/a: this component has no persisted or cross-process state; recovery leaves prior reports unchanged.

Source RGB/depth/calibration and prompts → masks → visible-depth supports → camera/world measurements → evaluator. Units/grid/world/revision and visible/full semantics are explicit. References withheld except named oracle input. Failure leaves unpublished new run; old masks/measurements never overwritten. Fresh run verifies original manifests; learned branch absent without explicit acquisition.

## Per-stage log and detection placement, 5 October 2026

The validation session may later report every measure in the shared per-stage format from Task44, with input mode stated: `isolated` when masks are prompted from reference boxes, `chained` when prompted from detector boxes. This task does not add that persistence path. The difference between the two is the error segmentation inherits from detection.

Reuse Task45's box placement measures as the rectangle baseline: centre offset, edge error, frame-to-frame wobble and background fraction (share of the box outside the object's reference outline). The core question for this task then becomes measurable on the same frames: does a mask lower the background fraction and the 3D position wobble compared with the box? Task45's COCO val2017 images give hand-drawn outlines for mask overlap and boundary scoring, and its TUM desk wobble measure can be repeated with masks, before Task40's own captures exist; physical position and size claims still need Task40 references.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| Built-in methods | `rectangle`, `grabcut`, `canny` | inherited experiments/06_object_recognition/experiments/02_segmentation/masks.py:10 |
| OpenCV thread count | `1` | inherited masks.py:48; deterministic component cost |
| OpenCV random seed | `0` | inherited masks.py:49; deterministic GrabCut component |
| GrabCut initialisation | `GC_INIT_WITH_RECT` | inherited masks.py:56-64 |
| GrabCut iterations | `5` | inherited masks.py:56-64 |
| Canny thresholds | `50`, `150` | inherited masks.py:76-77 |
| Canny aperture and gradient | aperture `3`; `L2gradient=True` | inherited masks.py:76-77 |
| Canny contour selection | `RETR_EXTERNAL`, `CHAIN_APPROX_SIMPLE`, largest-area contour | inherited masks.py:78-84 |
| Boundary scoring tolerance | `1` pixel | inherited scoring.py:33-36; validation consumer, not changed here |
| Learned model/checkpoint | none | n/a acquisition and validation remain separate |

## Verification

Contract test `experiments/06_object_recognition/experiments/02_segmentation/tests/test_mask_pipeline.py` must assert original-grid binary masks, explicit prompt/frame lineage, deterministic method ordering, explicit empty/failed results, and non-negative per-method wall-clock records. This API contract does not establish mask accuracy or position improvement.

Before: 45 masks compared; 0 independently established position/size improvements. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | `3820a3c` |
| Files changed | `mask_pipeline.py`, focused tests, segmentation README, task plan |
| Test status | `22 passed` in focused segmentation suite; Ruff passed; code review found no defects |
| Before measurement | 45 masks compared; 0 independently established position/size improvements |
| After measurement | Component contract verified; no accuracy measurement run |
| Delta | Reusable in-memory mask execution block added; 0 validation comparisons |
| Decision-gate outcome | Implementation ready for the parallel validation session; accuracy, references and learned-model acquisition remain outside this task |

still open because the investigation and its reference/decision requirements are not complete.
