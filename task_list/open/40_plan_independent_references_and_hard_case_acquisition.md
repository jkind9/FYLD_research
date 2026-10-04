---
id: "40"
title: Plan independent references and hard-case acquisition
status: open
priority: HIGH
type: decision
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/datasets/README.md
docs:
  - experiments/06_object_recognition/datasets/README.md
baseline_metric:
  source: experiments/06_object_recognition/datasets/README.md:5
  field: evidence and comparison gap
  baseline_value: "6 provisional frames; 0 independent desk physical-centre references"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task40: Plan independent references and hard-case acquisition

## In plain English

Plan the independent measurements and additional captures needed to judge the next experiments. Check what existing data can supply before requesting new recordings or hardware. Keep uncertain reference answers explicit.

## What

Question: Which independent identity/mask/anchor/extent/surface references and hard cases are necessary and practical for the proposed comparisons?

Proposed research/decision task. No implementation, execution or acquisition is bundled into it.

## Why

Existing evidence: Task17 has six provisional agent-reviewed frames, complete selected cup coverage and monitor positive subset. Task29 has no independent physical-centre reference; TUM has no acquired dense reference surface. Task17's 13-case registry records missing rotation/lighting/movement/origin-reset/phone scenarios.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Provisional annotation and scenario gaps already exist | Task17 dataset | all new evaluators | experiments/06_object_recognition/datasets/README.md:5 |
| Current desk spread is not absolute error | Task29 JSON | anchor/reference design | experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:19 |
| Independent ICL surface already acquired | stage04 | first surface control | experiments/04_surface_reconstruction/README.md:88 |

Proposed comparison: First inventory existing references, independence and metadata. Design human-checked pixel masks and physical identity review with disagreements; survey explicitly defined anchors, visible surfaces and complete dimensions with recorded instrument uncertainty/frame transforms. Plan a minimal static capture bank with similar co-visible neighbours, duplicate boxes, identical objects only in separate views, look-away/return, occlusion, changed lighting/rotation, moved objects, missing depth and camera reset. Plan independent translated viewpoints/new sessions and source-disjoint enrollment/validation/test; do not invent frame counts, tolerances or thresholds.

Necessary data/reference: Owner access to objects/room, capture permission, calibrated sensors or verified existing recording, timestamps/depth lineage, independent instrument/surface reference, human annotation/review labour. Apple LiDAR or outdoor driving acquisition is optional separate Task37/38 decision. Preserve Task13 hold-out and frozen settings.

Measurements: Reference coverage matrix, identity certainty/disagreement, masks usable for formal scoring, instrument uncertainty, coordinate/time consistency, independent session/view coverage, acquisition costs and exact unavailable cases. No experiment accuracy result is claimed by the plan.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Survey instrument/hardware access, human annotation and repeated independent review, capture labour/storage/permissions and missing depth/visibility. Prefer minimum acquisition that isolates a cause.

Decision informed: Approve or revise the reference/capture plan and authorise only needed acquisition; enable Tasks31-35 with stated reference limitations.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/datasets/README.md:5 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | New publication/readers | Versioned derived records; unavailable outcomes explicit | Complete verified runs only |

Reference owner → immutable versioned annotations/survey calibration → evaluator-only datasets. Visible/full geometry and physical anchor definitions have units/frame/source. Annotator disagreements remain explicit; frozen revisions never overwritten. No acquisition in Task30. A later failed capture/annotation publication remains incomplete and cannot score methods; restart publishes a new verified version. Existing Task17 references remain readable historical evidence.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Every proposed score has a compatible independent reference and declared uncertainty or is explicitly unavailable; co-visible/disjoint identical cases are separately labelled; no derived method estimate is reused as its own truth; Task13 inputs/settings remain untouched.

Before: 6 provisional frames; 0 independent desk physical-centre references. After: no new measurement yet. Provide primary-source traceability, explicit acquisition gaps and a reviewable decision; no runtime result is implied.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 6 provisional frames; 0 independent desk physical-centre references |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
