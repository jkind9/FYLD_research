---
id: "09"
title: Evaluate scene object recognition and persistent counting
status: open
priority: MED
type: experiment
blocked_by: ["03"]
blocks: []
verification_test: experiments/06_object_recognition/README.md
plan_reviewed: null
files:
  - experiments/06_object_recognition/**
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: independently evaluated inventories
  baseline_value: "0 labelled revisit/counting evaluations"
  target: "Independent identity controls and held-out inventory evaluation"
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 09: Evaluate scene object recognition and persistent counting

## In plain English

Recognise objects in a walkthrough and remember which ones have already been seen. Looking away and returning should not automatically count an object twice. Start with checked examples, then measure what changes when recognition and camera positions are estimated.

## What

Add a sixth independent experiment covering labels, persistent identities, supporting views and distinct counts. Begin with stationary objects and checked 2D masks/detections plus reference depth/poses. Integrate reconstructed geometry after task 04 passes its control; detector/data planning can begin earlier.

## Why

The brief includes size and distinct counts after revisits. Detection, segmentation, short-lived video tracks and persistent inventory have different contracts. Acquired geometry datasets do not establish site recognition or long-lived identity.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Size and revisit counting are in the brief | Edge review | This experiment | research/edge_products/README.md:3 |
| Persistent map-based records are proposed | Edge review | Inventory association | research/edge_products/README.md:32 |
| Reconstruction has an independent reference-input plan | Experiment 04 | Later integration | experiments/04_reconstruction/README.md:3 |

1. Define target classes, identity labels and counting policy before collection/tuning. Keep scene/activity classification separate.
2. Write independently specified controls: one returning object stays one identity; distinct identical objects stay distinct; ambiguous matches remain unresolved.
3. Test association with checked detections/masks and known depth/poses. Preserve world/segment identity and valid depth.
4. Compare a lightweight fixed-class model with text-query detection. Use masks when boundaries/overlap justify their cost.
5. Retain location, extent, appearance, views and uncertainty. Test revisits, occlusions, identical neighbours, moved objects and tracking loss.
6. Compare ConceptGraphs/ConceptFusion and offline OpenMask3D as research references; check component and weight terms before use.
7. Connect to task 04; introduce predicted detections, estimated poses and estimated depth separately.
8. Profile the combined workload on phone, local edge and backend. Correct object positions consistently when map poses change.

## Invariants and recovery

Object IDs and original observations are the inventory source of truth. IDs are session-scoped until cross-session identity is established. Store world/segment, metric position, observation IDs and association decisions. Never merge unresolved origins. State updates must be atomic; restart/replay cannot create a second ID for a committed observation. Before implementation, specify producer/consumer paths, persistence schema, map-correction ownership and fresh-install recovery, then request a plan review for stateful work. A finished diff requires fresh-context review before closure.

## Hyperparameters

Not selected. Before runs, audit and stamp vocabulary, scene splits, frame selection, model/checkpoint, image size, thresholds, association gates, features, persistence and scoring tolerances. New/deviating choices need confirmation; inherited choices need provenance. Mirror settings in run receipts. No runs are claimed.

## Verification

Contract targets: repeated checked views of one stationary object produce exactly 1 ID; two distinct objects produce exactly 2; unresolved origins produce no cross-segment merge; replay after restart produces 0 additional IDs. Confirm controls fail for count-every-detection behaviour. Replace the plan verification path with scoped tests before implementation.

Before: 0 labelled revisit/counting evaluations. Report detector quality, identity errors, duplicates, misses, incorrect merges and unresolved associations separately on held-out scenes. Agree numeric product limits before acceptance runs. A correct total cannot conceal compensating mistakes.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan and experiment README only |
| Test status | No recognition or inventory runs |
| Before measurement | 0 labelled revisit/counting evaluations |
| After measurement | Not measured |
| Delta | Not measured |
| Outcome | Open; labels, controls, persistence review and settings remain |
