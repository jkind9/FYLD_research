---
id: "23"
title: Embed interactive surface review and explain depth validity masks
status: open
approval_status: approved
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/04_surface_reconstruction/tests/test_surface.py
plan_reviewed: 2026-10-04 PASS
files:
  - experiments/04_surface_reconstruction/src/review.py
  - experiments/04_surface_reconstruction/src/export.py
  - experiments/04_surface_reconstruction/tests/**
  - experiments/shared/publication.py
  - experiments/shared/viewer.js
  - experiments/shared/viewer.html
  - experiments/shared/visualization.py
  - experiments/shared/tests/**
docs:
  - experiments/04_surface_reconstruction/README.md
  - experiments/shared/README.md
  - README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Embed interactive surface review and explain depth validity masks
  baseline_value: "0 embedded interactive surface reviews"
  target: "1 verified embedded review with rotation/pan/zoom and explicit mask counts"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 23: Embed interactive surface review and explain depth validity masks

## In plain English

Make the surface review interactive where readers already look for it. Explain what a white depth-validity image means. Preserve the original measurements while publishing the improved review.

## What

Embed or make the interactive 3D surface directly accessible within review.html, add panning and visible mask legends/counts, and publish fresh inspection copies rather than rewriting completed runs.

## Why

The requested older run has no viewer; current review uses a static image and a separate viewer link. Frame101 mask is white because all 307200 depth pixels are valid.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Interactive drawing already exists | viewer assets | review/publication | experiments/shared/visualization.py:157 |
| Surface review already links a viewer | build_review | surface publications | experiments/04_surface_reconstruction/src/review.py:13 |
| Displayed validity masks/counts come from retained depth | depth_preview via surface_view | review rows | experiments/shared/visualization.py:109; experiments/shared/inspection.py:206 |
| Immutable numerical copies and current review backend have a single publisher | shared publication.publish | fresh CPU review | experiments/shared/publication.py:18; experiments/shared/publication.py:68 |

Reuse shared viewer assets; improve discoverability and embed the existing view without loading numerical arrays into the browser. Add panning, keyboard equivalents and view-reset controls. Describe white=valid depth and black=missing; distinguish this from an object mask and report valid/missing counts. Preserve historical complete run hashes by creating a new publication. Coordinate shared viewer ownership with Task22; no concurrent edits to the same assets.

The plan outline was approved on 3 October 2026. That approval covers no newly selected numerical values, model settings, dataset splits, or GPU runs. Task-specific protocol decisions and execution receipts remain required.

Concrete continuation: use python -B -m experiments.shared.publication --source experiments/04_surface_reconstruction/runs/20261002T195928.219822Z_55d2d0bfa455453eb2289a5e717490c1 --stage 04 --runs experiments/04_surface_reconstruction/runs. This is a new visual edition of an already publication-only source. Do not use stage04 inspection.republish_review: it rewrites numerical metrics/stages/surface JSON. shared publication.copy_inventory preserves copied numerical bytes and archives source metadata separately. Verify exact source manifest and all numerical arrays, PLY, metrics/stages/surface/configuration bytes before/after; regenerated display artifacts are independently checked, not claimed byte-identical.

Add a small resolved destination guard to experiments/shared/publication.py before Run creation, checking destination and every ancestor for existing Run status markers. Reject source/direct/nested/junction-alias output before any mutation. Default runs root containing prior completed siblings is allowed because the new Run allocates a unique child; nesting inside a prior child is rejected. Add focused regressions in experiments/shared/tests/test_publication.py, including normal sibling success and source re-verification. Do not change generic Run or numerical reconstruction. Temporary fixtures remain under outputs/ or OS temp, never inside experiment source trees.

Actual delivered Edge verification must load the review iframe and its viewer; check orbit/pan/zoom/reset and keyboard equivalents, frame stepping/reference toggle, zero page errors, every local href/src target, and unchanged scene coordinates after display controls. Regenerated displayed depth validity follows finite positive retained metre depth, not an object mask. Cross-check displayed mask/counts against retained depth arrays and separate original mask arrays. Frame101 should report307200valid/0missing. Update the three declared READMEs with the fresh review link. Existing partial UI edits are preserved; Task22 does not edit these shared assets.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original binary validity mask | review legend/counts | white/255 means valid; black/0 means missing; same source pixel dimensions | derived from retained original depth; checked against original mask | experiments/shared/inspection.py:206; experiments/shared/visualization.py:109 |
| Existing surface and camera artifacts | embedded viewer | supplied coordinates and origin labels retained; controls alter display only | original artifact retained | experiments/shared/visualization.py:157 |
| Existing run owner | review/completion | unique run and SHA256 inventory; incomplete rejected | yes | experiments/shared/runs.py:59 |

Source of truth is the completed source run and its verified artifacts. Publication copies/linkages and browser viewer data are the boundaries. Publish into a fresh run; an interruption leaves that copy incomplete and the source untouched. Restart uses another fresh publication. A fresh checkout first acquires data or a verified source publication and uses existing CPU publication tooling. Preserve numeric hashes and existing viewer consumers. This task changes neither poses nor identity storage and has no dependency on the proposed revision sidecar.

## Hyperparameters

hyperparameters n/a: CPU publication only; no new inference or numerical reconstruction; inherit unchanged source and display settings rather than conduct a numerical experiment. Inherited display settings: surface20000totalpoints split across9shards, reference20000points, deterministic sample_points; camera frustum0.3metres (shared/inspection.py:180,262,298,309). Depth preview maximum=max(4.0,finite retained depth maximum) metres, validity finite and>0 (inspection.py:206;visualization.py:109). Preserve source metric/pose/calibration configuration. These settings alter only display and are recorded in publication receipts; no parameter tuning.

## Verification

Contract test: experiments/04_surface_reconstruction/tests/test_surface.py (proposed where not yet present). All-valid fixture renders 100% valid/0 missing; a half-valid fixture renders 50% and correct counts. Browser panning changes view without changing scene coordinates, and keyboard controls work. Original source manifests and arrays remain byte-identical; all new review/viewer links resolve.

Before: 0 embedded interactive surface reviews. Target: 1 verified embedded review with rotation/pan/zoom and explicit mask counts. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit requested; implementation remains unfinished |
| Files changed | stage04 review.py and test_surface.py; shared viewer.js, viewer.html and test_viewer_browser.py |
| Test status | Focused review and offline Edge pan/reset checks passed. The broad 103-case regression run was stopped before a final result; its temporary inputs were placed inside the source-snapshot tree and caused excessive repeated work. Future checks use outputs/ outside experiments/. Ruff, mypy and JavaScript syntax checks passed. |
| Before measurement | 0 embedded interactive surface reviews |
| After measurement | Generated fixture review embeds the viewer and shows valid/missing mask counts; pointer/keyboard pan and reset passed in Edge. No acquired-run publication yet. |
| Delta | Implementation and focused controls added; acquired publication and finished reviews remain |
| Decision-gate outcome | Outline approved 3 October 2026; task-specific protocol, numerical choices and run approvals remain pending |

still open because acquired-run publication, source-hash comparison and finished reviews remain. The owner prioritized completing Tasks16 and 17 in order; preserve these partial changes and resume Task23 afterward.
