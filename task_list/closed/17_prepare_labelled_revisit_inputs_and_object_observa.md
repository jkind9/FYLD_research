---
id: "17"
title: Prepare labelled revisit inputs and object observation contracts
status: closed
approval_status: approved
priority: MED
type: infra
blocked_by: []
blocks: ["18", "19", "20", "21", "25"]
verification_test: experiments/06_object_recognition/shared/tests/test_observations.py
plan_reviewed: 2026-10-03 PASS
files:
  - experiments/06_object_recognition/shared/**
  - experiments/06_object_recognition/datasets/**
  - data/object_revisits/**
  - pytest.ini
  - tools/check.py
  - experiments/06_object_recognition/README.md
  - data/README.md
  - experiments/06_object_recognition/pilot/README.md
  - task_list/README.md
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/datasets/README.md
  - data/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Prepare labelled revisit inputs and object observation contracts
  baseline_value: "0 independently labelled revisit benchmarks"
  target: "1 validated bounded reference manifest; 13 scenarios explicitly present/absent/unusable"
created: 2026-10-03
last_updated: 2026-10-03
superseded_by: null
---

# Task 17: Prepare labelled revisit inputs and object observation contracts

## In plain English

Choose a recording that actually contains useful object returns and label the expected answers. Keep the original images and depth intact. Define the information each object experiment receives and produces.

## What

Create source manifests, independently checked masks/instances/revisit labels, split/enrollment records and stage-specific observation/label validation. Inspect usability before assuming existing footage covers the cases.

## Why

Raw TUM/ICL data exists, but no labelled inventory benchmark exists. Without separate answers, association scores cannot establish correctness.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Calibration and pose agreement already exists | Calibration/Pose | object localisation | experiments/shared/contracts.py:11 |
| Identity decisions already persist | IdentityStore | association/replay | experiments/06_object_recognition/src/identity_store.py:34 |
| Timestamp association and source decoding already exist | dataset adapter | matched-frame studies | experiments/03_camera_pose_estimation/src/dataset.py:78 |

Implement immutable stage-specific records and a validator, then publish a six-frame RGB-only reference set. The owner delegated completion and settings on 3 October 2026. This initial artifact is a visually agent-reviewed within-sequence smoke benchmark, not human ground truth or an unseen held-out accuracy set. The earlier demand for all recorded scenarios is narrowed to the available footage plus an explicit gap registry; unavailable cases remain acquisition requirements for broader claims. No model inference or downloads are needed here.

Reuse the accepted Task28 selection only to choose original RGB-D source files, never detector boxes, masks or IDs. Manually annotate original RGB cup visible-pixel polygons/boxes at sampled indexes 0,9,37,42,59; index27 is an out-of-view cup negative, not scene absence. Also mark two distinguishable monitor identities at indexes0,37,42 to exercise same-class distinct instances. Cup labels are exhaustive for these six frames; monitors are an explicitly non-exhaustive identity subset. Coarse polygon masks are provisional and excluded from formal segmentation accuracy until boundary review. Agent-created identities have their own namespace, never Task28 detector IDs.

Manifest schema v1 carries source/session/frame, seconds, calibration, registered raw depth scale/validity, original relative paths and SHA256 values, per-frame partition, label coverage, instances with visible support and category/identity, revisit links, annotation/review provenance and scenario gaps. Enrollment indexes0,9; evaluation indexes27,37,42,59; validation empty. All are from one desk session, so claim only same-instance within-session return, no session-independent evaluation, no tuning or generalisation. Derived crops/augmentations must retain their source partition. Separate labels from method inputs via an explicit method-input projection.

Observation records carry source key, pixel support, source hashes, depth availability, optional metric geometry, pose origin/revision and method provenance. Reject nonfinite dimensions/times/geometry, duplicate frame/instance/observation keys, changed hashes, path escape, inconsistent dimensions/units, missing depth with fabricated geometry and split/augmentation leakage. Use existing Calibration/Pose/validate_transform; never alter global contracts or existing identity storage. PoseRevision v1 is keyed by run/world/segment/frame/revision, with camera-to-world matrix, metre units, source hash, parent revision and provenance. Validate roots/parents and prohibit cross-origin or cross-frame parenting. Original revisions remain immutable; downstream Tasks21/22/25 own rebuilding and generation publication.

Store six explicit source rows and hashes in checked annotation JSON; preparation does not depend on the ignored pilot run after selection. Fresh clone uses an explicit offline handoff: copy the named original RGB/depth files, rgb.txt/depth.txt/groundtruth.txt and EXTRACTION.json from already-acquired data/tum/rgbd_dataset_freiburg1_desk; frozen hashes verify images and groundtruth provenance. Fail with a missing-source message, do not download. A datasets builder reads checked annotation JSON and source RGB/depth, checks hashes/dimensions, rasterises polygons, publishes separate method-input and evaluator-label JSON plus mask PNGs and an artifact hash inventory. Mirror fixed selection/policies in module HYPERPARAMETERS and publication metadata. Write to a new staging directory, validate it, then rename to a fresh destination; refuse overwrite and incomplete/tampered publications. No shared Run snapshot is needed for data preparation: avoid rescanning unrelated experiments. Add discovery to pytest.ini/tools/check.py. Preserve Task13 source/settings and all unrelated dirty files.

Planned agents: one fresh plan reviewer, one contract implementation worker, one RGB-only visual reviewer, one combined code/diff reviewer (4 total). Root owns annotation data, publication builder, README updates and receipts; worker owns shared contracts and their focused tests. Run only new contract/fixture modules, with temp outside experiments. Review tests independently or show red-first; measure changed-code coverage >=80%.

Additional reuse evidence: experiments/06_object_recognition/pilot/replay.py:454 owns selected source rows; experiments/datasets/acquisition.py:48 owns streaming SHA256; experiments/shared/geometry.py:60 owns rigid-transform validation; tools/check.py:15 owns external temporary check directories. The constitution is an unratified template, not ratified requirements.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original source and calibration | adapter/scorer | immutable frame IDs, pixels, times and declared metre scale | hashed manifests | experiments/shared/contracts.py:11 |
| Existing pose records | derived surface/object geometry | camera-to-world and world/segment explicit; revision sidecar is proposed in Task17 | saved records | experiments/shared/contracts.py:39 |
| Existing run owner | review/completion | unique run and SHA256 inventory; incomplete rejected | yes | experiments/shared/runs.py:59 |

Source of truth is original source evidence plus frozen configuration and independent labels. Boundaries are adapter records, saved JSON/arrays and optional database transactions; no hidden shared mutable state. Before publication a crash leaves incomplete work; after verified completion it stays immutable. Restart uses a fresh run or the existing tested identity replay. Fresh deployment follows pinned requirements and explicitly verified data/model availability; no GPU is used without approval. Existing runs/store callers must remain readable; schema/pose-revision changes require an explicit migration and downstream plan. Actor ownership and error paths must be traced at implementation-plan review.

## Hyperparameters

Audit run 3 October 2026: existing replay snapshots contain historic divergent selections; this task performs no inference and does not alter them.

| Name | Value | Source |
|---|---|---|
| source | TUM Freiburg1 desk, original source bytes | inherited Task28 accepted selection |
| selected replay indexes | 0,9,27,37,42,59 (6 frames) | confirmed 2026-10-03 under delegated completion; compact before/gap/return reference |
| target coverage | cup exhaustive; two monitors non-exhaustive subset | confirmed 2026-10-03 under delegated completion |
| partition | enrollment 0,9; evaluation 27,37,42,59; validation 0 frames | confirmed 2026-10-03 under delegated completion; no tuning/generalisation claim |
| masks | visible-pixel manual RGB polygons; provisional boundaries | confirmed 2026-10-03 under delegated completion; evaluator only |
| review | fresh agent RGB-only review; no human review claimed | confirmed 2026-10-03 under delegated completion |
| image grid/intrinsics | 640x480; 525,525,319.5,239.5 | inherited experiments/03_camera_pose_estimation/src/dataset.py:14 |
| raw depth | unsigned16; /5000 metres; raw zero missing, downstream processed valid 0<depth_m<4 | inherited experiments/03_camera_pose_estimation/src/dataset.py:123 |
| association of RGB/depth | 0.02 seconds | inherited experiments/03_camera_pose_estimation/src/dataset.py:78 |
| pose revision | camera_to_world, metres, explicit world/segment, schema1 | inherited experiments/shared/contracts.py:39; confirmed 2026-10-03 for sidecar schema |
| rigid-transform tolerances | bottom row atol1e-10; rotation/determinant atol1e-5; rtol0 | inherited experiments/shared/geometry.py:67 |
| inference, model, repeats, seeds, thresholds | n/a no inference or stochastic algorithm in data preparation | n/a deterministic annotation/validation publication |

## Verification

Focused contract tests reject source tamper/path escape, duplicates, dimensions/units mismatch, split leakage, nonfinite geometry, invented missing-depth positions, invalid rigid transforms and cross-origin/missing-parent revisions. A method-input projection contains zero evaluator labels. Publication tests reject overwrite and invalid artifacts; original source hashes remain unchanged. Independently review tests and RGB labels. Contract implementation statement coverage >=80%. Verify exactly six frame records, one cup identity across before/return, two distinct monitor IDs and an explicit 13-case scenario registry. Report mask/review limitations and unavailable scenes rather than claiming complete acquisition. Baseline0 prepared manifests, target1 verified bounded reference publication.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit created; unrelated dirty files preserved |
| Files changed | stage06 shared contracts/tests/README; datasets annotation/builder/tests/README; pytest.ini; tools/check.py; stage06/data/pilot README; Task17/21/28 and board traceability |
| Test status | Shared92focused testsPASS, production348statements/4miss (98.85%); publication20focused testsPASS,145statements/13miss (91%); Ruff/mypyPASS; Black formatting verified in one process; original15source hashes match archive-derived member record |
| Before measurement | 0 prepared independent reference manifests; proposed broad inventory coverage unavailable |
| After measurement | 1 verified bounded RGB-only reference publication:6frames,11instance observations,3reference identities (1cup,2monitors),2enrollment/4evaluation/0validation,32hashed artifacts;13scenario registry:6present,5absent,2unusable |
| Delta | +1 bounded reference/contract publication; no model accuracy or generalisation improvement claimed |
| Decision-gate outcome | Initial preparation complete under delegated owner direction. Fresh planPASS; code review findings fixed; Python review approves; finished diff reviewPASS. Broad unavailable-footage and human/boundary review requirements explicitly excluded from this initial smoke scope |

Publication: data/object_revisits/desk_smoke_v1/review.html. Receipt SHA256 eb30954d32b56778d55ac4a1858dd933ddec7550d2aa4da5bfb9e9ae1b5d57e3; published annotations SHA25627fe047dac254161ea823d6c55aeb28e16bd88cd993f1e4bf8fbdee40d4741d3; original annotation JSON SHA256a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920. The two JSON serializations are semantically identical. CLI preparation and verification both report complete6frames/11observations/3identities. Sources are unchanged; no GPU/model run, downloads or Task13full sequence occurred in Task17.

Fresh RGB-only review initially rejected selectedindex20/sourceframe205 because the cup remained partly visible. Replaced it with selectedindex27/sourceframe268 at1305031463.059810, visually confirmed cup out of view. Original cup positive frames23,104,359,405,560 and distinct black/silver monitors pass identity review. Provisional frame405 cup support and frame23 monitor edge were tightened. No human review or precise mask gold is claimed. The full27-sample YOLO miss interval is not continuous visual absence. Accepted Task28 run artifacts remain immutable; its documentation/receipt records this correction.

Code-review defects reproduced red and fixed green: ambiguous concatenated mask filenames, Windows case collisions, nested unindexed publication.json, reserved Windows device names. Semantic visit labels were removed from method inputs. Copies match original source hashes; receipts check actual counts/settings. All regression cases pass. Diff reviewer independently rechecked44reserved/case inputs plus4ordinary controls and returnedPASS. Formatting-only final edits moved lint comments to their reported lines; Ruff and direct Black checks pass, with no behavior change.

Scope waivers: unavailable scene absence/full-occlusion recovery, controlled rotation/lighting/relocation, origin reset and phone capture are acquisition gaps, not simulated recording evidence. Agent-authored/reviewed within-session references replace the original proposed human-reviewed broad benchmark for this initial preparation only, under delegated completion. Coarse masks must not score formal segmentation accuracy; already inspected evaluation views must not support blind accuracy/generalisation claims. Later experiments require additional recordings and independent boundary/human review before those claims. These are explicit limitations, not unfinished parts of this bounded artifact. Task21's owner clarification adds robust coordinate fusion and similar-neighbour/duplicate controls, without changing Task13 or implementing association in this task.

## Acquired-footage inventory, 3 October 2026

The acquired sources are TUM Freiburg1 xyz (798 colour rows, 792 matched colour/depth pairs), TUM Freiburg1 desk (613 colour rows, 573 matched pairs), synthetic ICL living-room trajectory 2, and static Middlebury stereo pairs. No phone recording exists. Visual inspection covered the recorded TUM sequences for the required revisit cases. ICL and Middlebury are synthetic or static and cannot establish real recorded-object identity recovery.

| Required case | Inventory status | Evidence and limit |
|---|---|---|
| Stationary object visible, camera looks away, then returns | Present candidate in desk; xyz candidate rejected | In desk, the same white cup is visible at RGB timestamp 1305031454.127701, physically out of view at1305031463.059810, and visible again at 1305031466.095840. The desk, pen holder, telephone, keyboard and monitor positions show that the camera returns to the same scene. The earlier xyz candidate was wrong: the cup remains visible in frames 1305031116.143441 and 1305031116.943296. This has an independent RGB-only agent review; labels remain provisional and not human gold. |
| Similar but distinct objects | Present candidates in xyz and desk | Monitors, keyboards and books are separate visible objects. No second physical cup was visually verified. Two monitor identities now have provisional independently agent-reviewed labels; no second cup was verified. |
| Absent enrolled object | Unusable | Out of view does not establish absence from the scene. |
| Changed viewpoint | Present in xyz and desk | The camera sweeps around the desk. The desk cup return spans the timestamps above. |
| In-plane object rotation | Absent | No controlled rotation of an object was found. |
| Lighting change | Absent | The indoor recordings do not show a controlled lighting change. |
| Background change | Present candidate, uncontrolled | Viewpoint changes alter visible background context. No controlled background change was found. |
| Partial occlusion | Present candidate in desk | Desk clutter and monitor overlap can obscure objects; Selected cup/monitor identities are reviewed; coarse supports remain excluded from formal mask scoring. |
| Full occlusion followed by recovery | Unusable | The cup leaves the camera view. Full occlusion by another object was not established. |
| Moved enrolled object | Absent | No object relocation was established in the inspected sequences. |
| Depth holes | Present | Desk acquisition inspection reports 25.44% missing depth pixels. Preserve the raw invalid-depth mask. |
| Tracking-origin reset or restart | Absent | The recordings have continuous supplied poses; reset/restart must be a separate control. |
| Phone colour/depth capture | Absent | No phone recording was collected. |

The bounded desk replay samples 60 paired RGB-D frames across the selected 18.67-second span. It confirms a useful cup revisit example, with separate Task17 labels/splits now supplied under the stated limits. The bounded label/split choices above are recorded; wider dataset acquisition remains unavailable. Preserve desk's Task13 hold-out role and do not run its full sequence as part of this inventory.
