---
id: "31"
title: Compare provisional object IDs and duplicate relationships
status: open
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: ["21","22","40"]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/06_identity_policy/**
  - experiments/06_object_recognition/src/identity_store.py
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/pilot/replay.py:283
  field: evidence and comparison gap
  baseline_value: "90 book proposals unresolved outside gate; 0 evaluated provisional-birth comparisons"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task31: Compare provisional object IDs and duplicate relationships

## In plain English

Give every detection its own record and let uncertain new objects remain provisional. Compare ways to retain returning identities and possible duplicates without losing their histories. Uncertainty should remain visible instead of forcing a match.

## What

Question: Can provisional births and explicit duplicate relationships retain new/returning objects without inflating confirmed inventory or hiding uncertainty?

Proposed isolated experiment, not a run authorised in Task30. Its directory is future scope, not scaffolded now. Before implementation, refine exact files/tests, complete settings/references and perform required plan review.

## Why

Existing evidence: The baseline's 95 books produce 1 new, 4 matched and 90 unresolved because a later unmatched same-class detection cannot be born. Existing one-to-one assignment and checked persistence can be reused; Task21's eleven observations do not cover all inventory hard cases.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Class birth policy is restrictive | pilot replay | policy comparator | experiments/06_object_recognition/pilot/replay.py:283 |
| One-to-one association already exists | associate_frame | new policy trials | experiments/06_object_recognition/pilot/replay.py:127 |
| Checked persistence already exists | IdentityStore | persistent decisions | experiments/06_object_recognition/src/identity_store.py:34 |
| Observations already have distinct keys | ObjectObservation | source history | experiments/06_object_recognition/shared/observations.py:68 |

Proposed comparison: Hold cached proposals, depth and poses fixed. Compare current restrictive births with provisional births plus separate confirmed/rejected states and explicit possible-duplicate links. Compare frame-global one-to-one assignment with unmatched options; verify co-visible distinct supports and duplicate boxes separately. Include identical objects visible only in separate views, positionless observations, returns, replay/restart and later ID unification. Preserve aliases and all accepted/rejected source histories.

Necessary data/reference: Use existing desk proposals for policy accounting, not blind accuracy. Task40 must supply independently checked identities, duplicate boxes, co-visible distinct supports, new same-class objects in later views and genuinely identical disjoint-view cases. If physical identity is unknowable, reference the ambiguity rather than assigning a false gold answer.

Measurements: Count unique observation IDs; confirmed/provisional/rejected states; false merges/splits, duplicate candidates, unresolved pairs, return recovery and inventory precision/recall against independent labels. Measure transaction/replay consistency and assignment/runtime/storage costs.

Dependencies: Task21, Task22, Task40. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Assignment scaling, provisional-candidate growth, manual-review burden, aliases/history storage and persistence migration.

Decision informed: Choose a birth/confirmation/merge policy that retains evidence and exposes ambiguous identity. Numeric operating rules remain unselected.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/pilot/replay.py:283 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | New publication/readers | Versioned derived records; unavailable outcomes explicit | Complete verified runs only |

Immutable source observations → versioned assignment decisions → existing identity store → viewer. Positions retain metres/world/segment/revision; null remains unknown. Identity union is a transaction with aliases; failure before commit exposes no partial union; after commit readers recover complete histories. Fresh run verifies cached source manifests and uses isolated derived state. Old receipts/databases remain readable; migrations require reviewed contracts.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Every proposal has a unique observation ID; missing depth has null position; a second checked co-visible object cannot share an ID; a verified return retains its ID; unifying provisional IDs retains every history/alias; conflicting replay is rejected atomically.

Before: 90 book proposals unresolved outside gate; 0 evaluated provisional-birth comparisons. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 90 book proposals unresolved outside gate; 0 evaluated provisional-birth comparisons |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
