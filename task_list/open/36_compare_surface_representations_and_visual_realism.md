---
id: "36"
title: Compare surface representations and visual realism
status: open
priority: MED
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/04_surface_reconstruction/experiments/representations/**
docs:
  - experiments/04_surface_reconstruction/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/05_replay/README.md:21
  field: evidence and comparison gap
  baseline_value: "20000 desk display points; 0 local mesh/splat/NeRF comparisons"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task36: Compare surface representations and visual realism

## In plain English

Compare ways to show and reconstruct the captured surfaces. Measure geometric quality separately from how realistic a scene looks. Uncaptured surfaces must remain identifiable as unknown.

## What

Question: Which representation improves review/navigation at suitable cost without obscuring geometry error or missing coverage?

Proposed isolated experiment, not a run authorised in Task30. Its directory is future scope, not scaffolded now. Before implementation, refine exact files/tests, complete settings/references and perform required plan review.

## Why

Existing evidence: Current desk replay displays 20,000 points; single xyz pilot saves 230,405 points. ICL supplied-input reconstruction has an independent reference and limited coverage; TUM desk has no dense reference. Task23 owns the unfinished existing viewer controls, not this numerical comparison.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing supplied-depth surface control is reusable | stage04 | fixed-input geometry control | experiments/04_surface_reconstruction/README.md:5 |
| Replay point sampling/export already exists | Task22/29 | visual baseline | experiments/06_object_recognition/experiments/05_replay/README.md:21 |

Proposed comparison: First vary only display density on fixed cloud/poses. Then compare oriented patches and depth-fused mesh with fixed depth/poses. Texture a fixed mesh separately. Later compare photogrammetry, Gaussian splatting and NeRF using matching static translated/overlapping RGB capture. Keep held-out novel views separate from independent geometric scoring. Compare stereo video conversion/panorama rotation with metric translated navigation/parallax rather than treating display conversion as reconstruction.

Necessary data/reference: ICL acquired reference for first geometry controls; Task40 independent real surfaces/scale and held-out images for realistic capture. Missing surfaces, textureless/reflective regions and static/dynamic capture need labels. Alpha3D supplied pointer returned only landing shell; article claims remain unverified. RGB-only methods need approved software/model/runtime acquisitions.

Measurements: Surface error/coverage, holes/false bridges, boundary preservation, held-out image measures and independently reviewed visual usability/navigation; rendering/reconstruction time, memory/storage and export compatibility. Treat inferred unseen surfaces as unsupported.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Capture overlap/lighting/static-scene labour, calibration/scale, mesh/texture processing, optimisation/training cost and playback hardware. Assess point PLY, mesh/textured formats, Gaussian scenes and NeRF checkpoints separately.

Decision informed: Choose a measured surface/review representation and a separately validated visual layer; decide capture/export requirements before building an immersive application.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/04_surface_reconstruction/README.md:5 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | New publication/readers | Versioned derived records; unavailable outcomes explicit | Complete verified runs only |

Read-only completed cloud/depth/poses → new display/reconstruction runs → review/scoring. Preserve source point indices, coordinate frame/metres and observed/inferred labels. Failure leaves unpublished run; no source viewer rewrite. Estimated-pose correction analysis depends on Task35/25 later; it is not bundled into initial display controls.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Changing display sampling does not change saved metric measurements; reconstruction scores use independent surfaces; novel-view visual scores cannot be reported as size/location accuracy; missing capture stays explicit.

Before: 20000 desk display points; 0 local mesh/splat/NeRF comparisons. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 20000 desk display points; 0 local mesh/splat/NeRF comparisons |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
