---
id: "39"
title: Record future 3D review and measurement requirements
status: open
priority: LOW
type: decision
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/README.md
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/05_replay/README.md:7
  field: evidence and comparison gap
  baseline_value: "0 reviewed complete 3D-pick-to-source application requirements"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task39: Record future 3D review and measurement requirements

## In plain English

Record what a later review tool should show when a user selects an object or surface. Every estimate should lead back to its original evidence and uncertain decisions. Display and measurement usability are separate from proving accuracy.

## What

Question: What evidence and measurement interactions are needed for later 3D review without hiding rejected/uncertain observations or overstating accuracy?

Proposed research/decision task. No implementation, execution or acquisition is bundled into it.

## Why

Existing evidence: Task22 viewer already shows selected-ID history and baseline proposals; Task29 portable export preserves source evidence. Task23 retains bounded unfinished surface controls. A pick-to-complete-source application remains future work.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing replay/history viewer is reusable | Task22 | review requirements | experiments/06_object_recognition/experiments/05_replay/README.md:7 |
| Surface controls retain separate owner | Task23 | interaction boundaries | task_list/open/23_embed_interactive_surface_review_and_explain_depth.md:43 |

Proposed comparison: Requirements review only: pick object/surface → source frames/crops and depth/mask evidence; accepted/rejected observations; provisional/confirmed IDs and duplicate/alias links; individual positions versus fused estimate; coordinate/pose revisions. Plan surface endpoints, distances, observed dimensions, uncertainty and unavailable/hidden-region displays. Compare review journey against current viewer before a separate app implementation task.

Necessary data/reference: Requirements must map to existing artifacts and proposed Task31/32/35 outputs, including missing/unresolved data. Later usability review needs representative review questions and participants; metric displays need Task40 independent references for accuracy claims.

Measurements: Requirements coverage and traceability matrix now; proposed later completion of source-retrieval/rejected-case journeys and user comprehension. Measurement accuracy belongs to independent experiments, not interface acceptance.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Source/crop storage, portable versus hosted access, rendering large scenes, review time and accessibility.

Decision informed: Define a later application scope and data dependencies without starting implementation or expanding Task22/23.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

invariants n/a: future requirement only, not application implementation. Task31/32/35/36 provide conceptual/data dependencies for a later separately scoped build; no runtime scope is added here.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Every required display specifies provenance and unavailable behaviour; observed extent differs from complete size; unknown coordinate relationships prohibit distances; application usability never substitutes for independent accuracy scoring.

Before: 0 reviewed complete 3D-pick-to-source application requirements. After: no new measurement yet. Provide primary-source traceability, explicit acquisition gaps and a reviewable decision; no runtime result is implied.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 0 reviewed complete 3D-pick-to-source application requirements |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
