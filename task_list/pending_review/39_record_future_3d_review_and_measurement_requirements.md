---
id: "39"
title: Record future 3D review and measurement requirements
status: pending_review
priority: LOW
type: decision
approval_status: proposed requirements only; no application scope or product acceptance
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/README.md
  - task_list/README.md
docs:
  - experiments/06_object_recognition/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/05_replay/README.md:7
  field: evidence and comparison gap
  baseline_value: "0 reviewed complete 3D-pick-to-source application requirements"
  target: "1 source-traceable proposed requirements matrix; app scope and product approval remain separate"
created: 2026-10-04
last_updated: 2026-10-05
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
| Existing replay/history viewer is reusable | Task22 | source frames, boxes, IDs and unresolved candidates | experiments/06_object_recognition/experiments/05_replay/README.md:5 |
| Portable replay exports preserve original evidence | Task29 | audit and offline review | experiments/06_object_recognition/experiments/05_replay/README.md:29 |
| Provisional states, duplicate links and ID history have a separate owner | Task31 | identity review and count states | task_list/open/31_compare_provisional_object_ids_and_duplicate_relationships.md:62 |
| Spatial support, visible extent and pose lineage have a separate owner | Task32 | position and shape displays | task_list/pending_review/32_investigate_spatial_support_and_position_uncertainty.md:74 |
| Sequential fusion and pose-revision comparisons have a separate owner | Task35 | fused estimate and correction history | task_list/open/35_measure_error_propagation_and_sequential_fusion.md:52 |
| Independent identity, anchor and size references are still planned | Task40 | accuracy labels and measurement comparisons | task_list/pending_review/40_plan_independent_references_and_hard_case_acquisition.md:57 |
| Surface-review interactions retain separate implementation ownership | Task23 | viewport controls and mask explanation | task_list/open/23_embed_interactive_surface_review_and_explain_depth.md:43 |

Requirements review only: pick an object or surface and trace it to source frames/crops and depth/mask evidence; inspect accepted, rejected and unresolved observations; inspect provisional, confirmed and duplicate/alias relationships; compare individual positions with the fused estimate; identify coordinate and pose revisions; and measure only between named endpoints. The README records seven review actions and their display boundaries. No app is implemented here.

Necessary data/reference: Requirements must map to existing artifacts and proposed Task31/32/35 outputs, including missing/unresolved data. Later usability review needs representative review questions and participants; metric displays need Task40 independent references for accuracy claims.

Measurements: A seven-row proposed requirements matrix maps each review action to the evidence it must expose and the task that owns that evidence. A later usability review needs owner-selected participants and review questions. Measurement accuracy belongs to independent experiments, not interface acceptance.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Source/crop storage, portable versus hosted access, rendering large scenes, review time and accessibility.

Decision informed: Define a later application scope and data dependencies without starting implementation or expanding Task22/23.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

invariants n/a: future requirement only, not application implementation. Task31/32/35/36 provide conceptual/data dependencies for a later separately scoped build; no runtime scope is added here.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Contract check: Each of the seven README rows names the user action, required display, and evidence boundary. The matrix separates visible extent from full size, keeps unknown values unavailable, requires compatible coordinate revisions for metric measurements, and states that interface usability does not establish accuracy.

Before: 0 source-traceable proposed requirements rows. After: 7 review-action rows linked to current evidence owners; 0 app implementations, accuracy results, or owner approvals.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; no commit created |
| Files changed | `experiments/06_object_recognition/README.md` and this task record |
| Test status | docs n/a: requirements-only review; no implementation or experiment changed |
| Before measurement | 0 source-traceable proposed requirements rows |
| After measurement | 7 review-action rows mapped to existing or planned evidence owners; 0 app implementations or accuracy results |
| Delta | Requirements proposal is reviewable and traceable; product approval is still outstanding |
| Decision-gate outcome | Awaiting source validation and owner review; any application implementation needs a separate task |

still open because an owner must accept or revise the proposed product requirements before they can guide a separate application task. No thresholds, acquisition, app implementation or accuracy claims were selected.
