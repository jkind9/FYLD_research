---
id: "09"
title: Evaluate scene object recognition and persistent counting
status: open
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/tests/test_identity_store.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/06_object_recognition/**
  - pytest.ini
docs:
  - experiments/06_object_recognition/README.md
  - experiments/README.md
  - task_list/README.md
  - README.md
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

Implement pipeline stage 06 covering labels, persistent identities, supporting views and distinct counts; its experiment folder and plan already exist. This is object identity tracking, distinct from camera pose estimation in stage 03. Begin with stationary objects and checked 2D masks/detections plus reference depth/poses. Integrate reconstructed geometry after task 04 passes its control; detector/data planning can begin earlier.

## Why

The brief includes size and distinct counts after revisits. Detection, segmentation, short-lived video tracks and persistent inventory have different contracts. Acquired geometry datasets do not establish site recognition or long-lived identity.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Size and revisit counting are in the brief | Edge review | This experiment | research/edge_products/README.md:3 |
| Persistent map-based records are proposed | Edge review | Inventory association | research/edge_products/README.md:32 |
| Reconstruction has an independent reference-input plan | Experiment 04 | Later integration | experiments/04_surface_reconstruction/README.md:3 |

1. Define target classes, identity labels and counting policy before collection/tuning. Keep scene/activity classification separate.
2. Write independently specified controls: one returning object stays one identity; distinct identical objects stay distinct; ambiguous matches remain unresolved.
3. Test association with checked detections/masks and known depth/poses. Preserve world/segment identity and valid depth.
4. Compare a lightweight fixed-class model with text-query detection. Use masks when boundaries/overlap justify their cost.
5. Retain location, extent, appearance, views and uncertainty. Test revisits, occlusions, identical neighbours, moved objects and tracking loss.
6. Compare ConceptGraphs/ConceptFusion and offline OpenMask3D as research references; check component and weight terms before use.
7. Connect to task 04 for reconstructed geometry and to task 05 for estimated camera poses; introduce predicted detections, estimated poses and estimated depth separately. Neither estimator is required for the initial checked-input identity controls.
8. Profile the combined workload on phone, local edge and backend. Correct object positions consistently when map poses change. Preserve original observations and pose revision IDs so object geometry can be recomputed; test a pose correction without changing identity or count.

### First implementation slice

Build the checked-input identity store and controls only. Use SQLite from Python's standard library so a single transaction can persist an association and unique source observation key. Store explicit operator decisions; do not add an image model, choose site classes, or tune an automatic association threshold in this slice.

Use `objects(session_id, object_id, label, world_id, segment_id)` and `observations(session_id, source_id, observation_id, source_payload_json, payload_sha256, object_id, decision, pose_revision_id, position_x_m, position_y_m, position_z_m)`. `objects.object_id` is primary and each object belongs to one session, world and segment. `observations(session_id, source_id, observation_id)` is primary and `object_id` is a nullable foreign key. Decision is one of `new`, `matched` or `unresolved`. Store the original observation descriptor as canonical JSON, including immutable evidence paths and file hashes when available. Keep original image/depth bytes in their existing immutable dataset or run files; the database preserves descriptors, and a later consumer must report a missing evidence file rather than invent a replacement. Optional positions are metres and refer to the recorded pose revision. An unresolved observation has no object ID.

Commit each observation and identity decision inside one `BEGIN IMMEDIATE` transaction. Replaying the same session/source/observation key and exact payload returns the existing decision. Reusing that key with a changed payload or decision raises an error. Two distinct objects may share a label. An identity may only be matched within its existing session, world and segment. Use fixture labels in tests; do not interpret them as selected product classes.

Add `experiments/06_object_recognition/src/identity_store.py` and `experiments/06_object_recognition/tests/test_identity_store.py`. Extend `pytest.ini` to collect the new tests and expose the experiment source module. Test first-open schema creation, new/matched/unresolved decisions, identical labels with separate IDs, cross-session/world/segment rejection, exact replay, conflicting replay, database reopen, and transaction rollback after a forced failure. Keep map correction and model inference for a later slice; pose revision and original observation keys let a later geometry adapter recompute positions without changing identities.

## Invariants and recovery

Object IDs and original observations are the inventory source of truth. IDs are session-scoped until cross-session identity is established. SQLite owns committed identities and decisions, including the canonical source observation descriptor; callers own the immutable source images/depth files named in that descriptor. Store session/world/segment, metric position when supplied, pose revision, source observation keys and association decisions. Never merge unresolved origins or identities from another session or segment. SQLite commits each decision atomically. A crash before commit leaves no new decision; after commit, replay of the same session/source/observation key and payload returns the committed result, and a conflicting replay fails. A fresh install creates schema version 1 at the caller-supplied database path. No older database exists to migrate. Missing evidence paths remain visible in the descriptor, and any consumer that resolves them must report missing files without substitution. The stateful plan passed review on 2 October 2026. A finished diff requires fresh-context review before closure.

## Hyperparameters

hyperparameters n/a: the first implementation slice stores explicitly checked identities and runs synthetic controls; it does not run a detector or tune automatic matches. Before model or dataset runs, audit and stamp vocabulary, scene splits, frame selection, model/checkpoint, image size, thresholds, association gates, features, persistence and scoring tolerances. New or changed choices need dated confirmation; inherited choices need provenance. Mirror settings in run receipts. No recognition runs are claimed.

## Verification

Contract test: `experiments/06_object_recognition/tests/test_identity_store.py`. It asserts separate IDs for two same-labelled objects, a matched revisit reuses its ID, unresolved evidence has no ID, invalid cross-session/world/segment matches fail, exact replay adds no rows, conflicting replay fails, reopening preserves committed IDs, and a forced insert failure leaves zero objects and observations.

Before: 0 labelled revisit/counting evaluations. After this first slice: still 0 labelled evaluations; 10 checked-input persistence tests pass with 88% line coverage for the new store. The broader stage remains incomplete until labelled scenes, detector comparisons, held-out inventory scoring, and edge-device measurements are agreed and run. No numeric product limits have been set.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; user requested no commits |
| Files changed | `identity_store.py`, `test_identity_store.py`, `pytest.ini`, Task 09, Experiment 06 README, experiment index README, task board README, project README |
| Test status | 10 persistence tests passed; 88% store line coverage; full repository suite 157 passed; no detector or labelled inventory runs |
| Before measurement | 0 labelled revisit/counting evaluations |
| After measurement | 0 labelled revisit/counting evaluations; 10/10 checked-input tests and 157/157 repository tests pass |
| Delta | No labelled-evaluation change; checked persistence controls are now executable |
| Outcome | Still open because class selection, labelled revisit data, model comparison, held-out evaluation and phone/edge profiling remain |

The store does not inspect images or create visual reports. It retains canonical observation descriptors and identity decisions; an input-to-output viewer belongs with the later recognition and geometry stages.

Still open because recognition evaluation requires agreed site classes, labelled revisits, model and held-out scoring settings. The checked identity-store slice is complete; Task 13 has a separate active scope.
