---
id: "33"
title: Compare object appearance, context and spatial association
status: open
priority: MED
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: [31, 32, 40, 16, 56]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/08_association_comparison/**
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/03_appearance/README.md:56
  field: evidence and comparison gap
  baseline_value: "1 incorrect YOLO monitor ranking; 0 ResNet50/context comparisons"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task33: Compare object appearance, context and spatial association

## In plain English

Compare object appearance with nearby context and measured position on the same views. Include similar neighbours and identical objects that never appear together. Record wrong matches and unresolved cases as well as correct returns.

## Current priority, 6 October 2026

Run this refinement after Task56 identifies mistakes that appearance/context could address. Reuse Task53 independent references. Compare added feature cost with the complete accuracy and latency baseline. Earlier model options remain proposals, not required steps before that baseline.

## What

Question: Which appearance/context evidence and spatial trade-off reduce false merges/splits at acceptable full processing cost?

Proposed isolated experiment, not a run authorised in Task30. Its directory is future scope, not scaffolded now. Before implementation, refine exact files/tests, complete settings/references and perform required plan review.

## Why

Existing evidence: Task20 tested ZNCC and existing YOLO26x features; YOLO made one wrong monitor ranking. Task21 geometry-only and combined rules both resolved eleven provisional observations. ResNet50/contextual embeddings and independent operating thresholds remain untested.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing descriptors/crop adapters are reusable | Task20 adapter | fixed-crop methods | experiments/06_object_recognition/experiments/03_appearance/README.md:37 |
| Recorded monitor failure already exists | Task20 result | hard pair analysis | experiments/06_object_recognition/experiments/03_appearance/README.md:56 |
| Current position/appearance trials exist | Task21 | matched-input baseline | experiments/06_object_recognition/experiments/04_geometry_identity/README.md:3 |

Proposed comparison: Fix crop/support/resizing/gallery/session splits. Compare ZNCC and recorded YOLO features before any authorised ResNet50 or contextual encoder extraction. Separate masked object-only, surrounding-context and context-only controls. Then compare spatial-only, appearance-only and combined costs on exactly matching observations across distance/similarity settings. Include similar co-visible neighbours, identical disjoint-view objects, depth holes, viewpoint/lighting and new sessions. Freeze rules on validation before held-out evaluation.

Necessary data/reference: Task40 independent identity/pair labels, hard negatives and held-out sessions; Task32 fixed support/uncertainty definitions; Task31 ambiguity/birth outputs. New model code/weight terms, hardware and acquisition authorisation are prerequisites, not assumed. Existing inspected pairs remain development evidence.

Measurements: Pair precision/recall and ranking, false accepts/rejects, mistaken merges/splits, unresolved and return counts, inventory errors and runtime including model load/warmup/crops/extraction/matching. Report distance/similarity response curves and context leakage by session.

Dependencies: Task31, Task32, Task40, Task16. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: New embeddings require weights/licence/runtime/memory approval; compare cache reuse, extraction cost, gallery growth and context acquisition/annotation.

Decision informed: Choose whether added appearance/context evidence is useful over geometry on required hard cases; select operating rules only after independent validation, without assuming both cues always necessary.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

invariants n/a: planned read-only descriptor/association comparison with immutable cached inputs; any persistent policy implementation remains Task31. Publish isolated runs, reject incomplete caches and keep evaluator labels out of extraction.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Method inputs never include evaluator identities; all methods score matching crops/queries; ties/unavailable features preserve unresolved status; session-disjoint validation cannot leak nearby test derivatives.

Before: 1 incorrect YOLO monitor ranking; 0 ResNet50/context comparisons. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 1 incorrect YOLO monitor ranking; 0 ResNet50/context comparisons |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
