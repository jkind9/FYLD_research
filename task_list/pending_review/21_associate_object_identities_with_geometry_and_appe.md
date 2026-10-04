---
id: "21"
title: Associate object identities with geometry and appearance
status: pending_review
approval_status: approved
priority: MED
type: experiment
blocked_by: ["20"]
blocks: ["22"]
verification_test: experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_association.py
plan_reviewed: 2026-10-04 PASS
files:
  - experiments/06_object_recognition/experiments/04_geometry_identity/**
  - experiments/06_object_recognition/README.md
  - pytest.ini
  - tools/check.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/04_geometry_identity/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Associate object identities with geometry and appearance
  baseline_value: "0 bounded five-condition geometry/appearance comparisons"
  target: "1 bounded within-session comparison, 0 origin merges, complete decisions and separate synthetic neighbour controls"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 21: Associate object identities with geometry and appearance

## In plain English

Combine object appearance and scene position to decide which observations share an identity. Leave uncertain matches unresolved. Preserve every measurement while showing how independent camera views change the stored location. Check that a return, restart or camera-path correction keeps accepted identities stable.

## What

Implement a bounded association experiment in 04_geometry_identity. Preserve the existing IdentityStore schema and API. Compare five fixed conditions: geometry-only with last-observation location; geometry-only with independent-view median; appearance-only with median; combined geometry/appearance with last location; combined with median. Save every observation, candidate, abstention, assignment and location contribution. No new models, weights or training. Task13 stays untouched.

## Why

A returning object must keep its identity. Similar neighbours must remain distinct or unresolved. Appearance can help decide identity but does not measure coordinate precision. Repeated near-identical camera views must not acquire unlimited position votes. The available six-frame reference supports descriptive within-session checks, not blind generalisation or true object-centre error.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Immutable decisions and exact replay already exist | IdentityStore.record_observation | staging persistence adapter | experiments/06_object_recognition/src/identity_store.py:93 |
| Existing transactions cover one observation, not a whole frame/generation | BEGIN IMMEDIATE and commit | publication boundary must remain outside store | experiments/06_object_recognition/src/identity_store.py:138 |
| Origin ownership is enforced on matched IDs | IdentityStore matched owner check | association adapter | experiments/06_object_recognition/src/identity_store.py:165 |
| One-to-one geometry assignment and alternative-solution checks exist | associate_frame | policy implementation can adapt algorithm, not last-position state | experiments/06_object_recognition/pilot/replay.py:127 |
| Surface localisation is camera median then world transform | localise_detection | declared box-support baseline | experiments/06_object_recognition/pilot/localisation.py:54 |
| Pixel backprojection and rigid transforms are shared | backproject / transform_points | oracle-support adapter | experiments/shared/geometry.py:20; experiments/shared/geometry.py:78 |
| Metric observation provenance is immutable | ObjectObservation | method records and geometry sidecar | experiments/06_object_recognition/shared/observations.py:12 |
| Revision parentage cannot cross frame or origin | validate_pose_revisions | generation validator | experiments/06_object_recognition/shared/pose_revisions.py:67 |
| Capture projection excludes independent identity labels | method_inputs | capture adapter before explicit oracle supports | experiments/06_object_recognition/shared/manifest.py:261 |
| Completed runs are hash-verified and incomplete runs rejected | Run / verify_run | Task22 verified generation reader | experiments/shared/runs.py:59; experiments/shared/runs.py:229 |
| JSON replacement flushes before same-directory publication | write_json | derived sidecar output | experiments/shared/runs.py:25 |
| Existing appearance comparison specifies cached descriptors | Task20 fixed oracle-support experiment | appearance adapter | task_list/open/20_compare_object_appearance_matching_across_viewpoin.md:64 |

### Source and effect boundaries

Run the hyperparameter audit before implementation. Audit run on 4 October reported 219 declaration sources, including historical snapshots and unrelated stage settings; do not normalise earlier receipts. Own settings below deliberately differ from pilot last-observation aggregation and add independent-view and appearance policies.

Preflight verifies the Task17 original annotation SHA256 a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920, publication receipt SHA256 eb30954d32b56778d55ac4a1858dd933ddec7550d2aa4da5bfb9e9ae1b5d57e3, published annotation SHA256 27fe047dac254161ea823d6c55aeb28e16bd88cd993f1e4bf8fbdee40d4741d3, all original frame/table hashes and the accepted Task20 completed run `experiments/06_object_recognition/experiments/03_appearance/runs/20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d` (140 artifacts; completion manifest SHA256 `f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4`). Its verified descriptor artifact has 11 opaque-keyed YOLO vectors. Pin the exact signature and verify the artifact inventory before exposing the vectors. Join descriptors only through opaque frame/RGB/bbox keys. Pair scores and truth remain scorer-only and never enter association. Refuse arbitrary replacement expected hashes or a synthetic fixture as production input. Fixture-only helpers are explicit and cannot author accepted production provenance.

Before mkdir, snapshot, copy, database construction or descriptor work, resolve output root, Task17 publication/original source roots, Task20 run, any resume run and existing completed-run ancestors. Reject output equal to, inside, or containing any protected input or previous run; reject symlink/junction/reparse aliases and unsafe traversal. Default output is this experiment's runs directory, with a unique Run child; output outside workspace is rejected. A test basetemp lives in outputs, never inside experiments or a snapshotted input. Verify all sources again before completion. This is serial CPU replay of cached descriptors, with 0 GPU forwards in Task21.

### Method records and localisation

The real condition explicitly receives Task17's 11 provisional oracle RGB supports and their class categories across six selected frames. Oracle support/category is disclosed; instance IDs, revisit answers, partitions used as identity hints, filenames containing IDs and label-bearing paths never reach association. Opaque observation keys link capture geometry to Task20 descriptors. Scorer alone owns the 16 same-instance and 9 different-instance pairs and the physical return/reference answers. Already inspected data remains within-session diagnostics.

Read calibrated depth and supplied poses using checked source tables and timestamp matching. Support-conditioned geometry uses the provisional binary polygon mask, valid 0 < depth < 4 metres, shared backprojection, coordinate-wise camera-point median and then camera-to-world transform. Save raw missing/processed-invalid counts, valid fraction, camera and world surface medians, component IQR, pose matrix/source/revision and hashes. Do not call these object centres. Record box-support localisation via the existing helper as a separate support comparison, not as a replacement or true-error measure. Missing depth or pose yields nullable geometry, never invented coordinates.

### Association policies

Process complete frames chronologically, break timestamp ties by opaque frame key, and sort observations by opaque key. Freeze pre-frame track state; solve all same-class proposals jointly. Same session/world/segment and the active geometry generation are required. Unknown origin cannot create or match metric IDs, even in appearance-only control. Missing metric position may be compared by appearance within an already explicit origin, but never seeds a new metric track or contributes a location.

Use Task20's existing-YOLO pooled cosine only for the combined and appearance-only association conditions. ORB/SIFT/ZNCC remain reported Task20 evidence, not silently blended scores. Gallery similarity is the maximum available cosine against accepted independent-view representatives from that ID; preserve the winning representative key. No identity truth enters the gallery. Geometry edges require distance to BOTH fixed location-generation anchor and current policy estimate <= 0.35 metres. This keeps last-location baselines bounded too; no unlimited last-observation chain. Combined edges additionally require cosine >= 0.80. Missing appearance yields unresolved in combined, not a silent geometry fallback. These are exploratory fixed gates, not calibrated probabilities or selected accuracy thresholds.

Geometry cost is distance-to-current-estimate / 0.35. Appearance cost is (1 - cosine) / 2. Combined cost is 0.5 times each cost. Maximise assignment cardinality, then minimise sum of costs. Compare alternatives that forbid each assigned edge: if another full-cardinality solution is within 0.05 mean cost per matched edge, every row whose assignment differs is unresolved. Equality counts as ambiguous. Do not commit apparently stable rows until ambiguity is resolved against the original complete frame solution; accepted matches remain one-to-one. Record candidates/costs, alternate gap, rejected origin/gate/missing evidence and all unresolved observations.

A class with no prior track may seed all nonduplicate, geometry-valid observations in its first usable frame; independent same-class initial neighbours create distinct IDs. After that class has tracks, an unmatched/outside-gate same-class observation is a pending birth or moved-location candidate, never an automatic new persistent ID. New classes may seed later. This conservative policy can miss genuinely new later objects and must report that limitation. Potential overlapping duplicates are same-class pairs with original-image box IoU >= 0.90 AND world distance <= 0.02 metres. Mark both unresolved for that frame, exclude both from birth/assignment/update, retain both originals; do not pick a winner by confidence. Exact repeated source keys with identical payload are replay only; a conflicting payload fails. Nearby objects outside this duplicate predicate still participate in the global ambiguity checks. These predicates are controls, not proof that a neighbour is physically the same object.

### Position update and moved-location records

Association happens first. Only accepted depth/pose-valid observations update their assigned object's separate derived location. Preserve every original coordinate including unresolved and duplicate proposals. Similarity and detector confidence never weight position. The fixed anchor is the first accepted world surface median of a location generation and never moves inside that generation. Last-observation condition exposes the last accepted surface median. Robust condition exposes component-wise median across independent-view representatives.

Define camera-view groups per object and location generation in chronological order: use the earliest accepted member as fixed group pose; a later accepted observation joins the first existing group whose translation distance is <= 0.05 metres AND relative SO(3) geodesic rotation <= 10 degrees. Otherwise create a group. The earliest accepted observation in each group is the sole position and appearance-gallery representative. A source frame contributes at most once to an object; later duplicates or same-frame aliases cannot add a vote. Keep all member coordinates and reasons; slightly changed views inside these limits do not change the robust estimate. This deliberately favours stable bounded voting over averaging every later measurement. Groups reset on a new location generation/revision.

Record representative count, total accepted count, per-coordinate min/max/IQR and distance spread plus before/after estimate shifts and last-vs-median differences. These are observed-surface spread, not calibrated covariance or centre error. While out of view or ambiguous, estimates and anchor remain unchanged.

Outside-anchor/gate observations with strong appearance get a separate time-labelled pending-location hypothesis containing candidate ID list, coordinates and evidence. Do not fold old and new positions into one median, automatically attach the hypothesis to an ID or treat appearance as proof of movement. The trial never automatically approves relocation. A synthetic explicit relocation-decision fixture tests a new location generation with the same stable ID, fresh anchor/groups and retained old history; its external decision is disclosed, not scored as autonomous success. True moved-object confirmation requires later independent recorded evidence.

### Persistence, revision and downstream reader

Implement pure immutable state transitions in association.py and locations.py; input/provenance in inputs.py; persistence/publication and checked read in persistence.py; scorer.py, report.py, run.py and focused tests under the scoped experiment. Stage README, pytest.ini and tools/check.py wire its focused package checks. Each module stays below 800 lines. Leave IdentityStore production code and all existing database schemas unchanged.

For each condition, build a private database inside the new running Run. Use the existing record_observation API with deterministic IDs derived from schema/condition/session/origin/first-observation key, and immutable source descriptors containing all accepted policy settings and original evidence. Per-observation SQLite transactions remain per-observation; they do NOT claim frame or generation atomicity. Complete frame decisions and derived state are computed/validated before persistence. Stage all records, close SQLite connections with no journal/WAL side files, compare DB decisions/counts to strict JSON ledger, then write generation-v1 sidecar and publish only after Run verification. Partial databases are never exposed as complete generations. Single writer per run; refuse shared writable resume DB paths.

A reader accepts only verify_run success plus matching ledger/database/generation hashes, origin/revision/condition/config IDs and full observation membership. Task22 consumes that checked reader, not a loose latest JSON or an open DB. No mutable active pointer is needed: consumer explicitly names one completed run/generation. Original coordinates/decisions are immutable; derived records key observation plus revision. A supplied-pose revision batch recomputes EVERY accepted location and view group from original camera coordinates under validated per-frame PoseRevision records, preserving stable IDs and original decisions. It creates a new complete generation/run and cannot mix old/new positions. Real camera-path correction remains Task25/Task13 work; Task21 tests synthetic revision correctness only.

Restart/resume verifies an earlier completed generation, configuration and source pins, copies its closed DB into a fresh Run staging directory, replays its immutable ledger exactly, and resumes later frames. Replaying all existing keys adds 0 objects and 0 observations. Changed settings or conflicting old evidence fail instead of silently rewriting IDs. A process death before completion leaves failed/running artifacts rejected; prior completed snapshot remains unchanged. Fresh run rebuild is also supported. Fresh deployment uses scoped requirements importing shared NumPy/SciPy/Pillow pins and cached verified Task20 output; no CUDA/model load is needed. Missing inputs fail before effects. Static offline review shows each observation and object history, all candidates/unresolved rows, raw and derived coordinates, view-group votes, distinct monitor IDs and cup return. Interactive recording/cloud integration remains Task22.

Task22 may separately reuse these pure policies on its fixed six-frame automatic detector proposals. It must extract descriptors from those actual detector supports using Task20's adapter and the already acquired checkpoint, rather than transfer any oracle-support descriptor to a detector box. Task21 publishes no automatic 60-frame appearance claim. Task22's original 60-frame pilot baseline and new six-frame automatic combined condition remain visibly separate, with their own input hashes, inference counts and unavailable cases. The six-frame physical cup gap is source frame268 followed by return359; the original 27-sample detector-miss interval is not continuous physical absence.

Persistence mapping for unknown origins: retain every missing/unknown-origin observation in the immutable unresolved ledger with its source key, nullable geometry and explicit reason. Do not pass null world/segment into IdentityStore, whose API requires nonempty origins even for unresolved rows. Such rows stay outside the private database and cannot birth or match identities; account for them separately when checking ledger-to-database counts. No sentinel origin is invented. Known-origin rows with missing depth remain unresolved store records without coordinates.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Checked RGB-D capture/calibration | support geometry | pixels, z metres; camera axes from Calibration | source hash verified | experiments/shared/contracts.py:11; experiments/shared/geometry.py:20 |
| Validated supplied pose/revision | derived location generation | camera_to_world metres; session/world/segment plus revision | immutable sidecar | experiments/06_object_recognition/shared/pose_revisions.py:25 |
| Pure frame decision ledger | staging IdentityStore | new/matched/unresolved; deterministic ID, original observation key | only completed run is resumable | experiments/06_object_recognition/src/identity_store.py:93 |
| Staging DB plus location sidecar | strict reader / Task22 | generation-v1 JSON and closed SQLite v1, same manifest membership | completed Run only | experiments/shared/runs.py:59 |
| Independent truth/reference | scorer only | oracle categories/support disclosed; identity answers separate | hashed evaluator artifact | experiments/06_object_recognition/shared/manifest.py:261 |

Source of truth: frozen original camera evidence, supplied pose records, fixed condition settings and immutable accepted decisions. One process owns a fresh staging Run; no global service/store mutation. Process death during computation, per-record commits, DB closure or sidecar writing exposes 0 completed new generations. Death after verified completion preserves one complete immutable snapshot. Prior completed run is copied, never changed. Verify source/output ancestry before effects; hashes before/after prevent input drift. No schema migration; old callers/runs continue reading unchanged. Constitution is the unratified draft with a placeholder principle; do not invent ratification.

## Hyperparameters

All new choices are recorded under the owner's overnight delegation to choose trial settings and run GPU/tests. They are exploratory controls, not owner-ratified performance thresholds. Mirror every row in HYPERPARAMETERS and output receipt.

| Name | Value | Source |
|---|---|---|
| reference | Task17 six frames, 11 provisional oracle supports, 1 cup and 2 monitors; partitions 2 enrollment/4 evaluation/0 validation; all chronological frames, no tuning | inherited Task17 frozen publication |
| appearance | Task20 run `20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d`; 140 artifacts; manifest SHA256 `f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4`; 11 cached opaque-keyed YOLO vectors; maximum cosine over independent-view representatives; null unavailable | inherited Task20 accepted run receipt; cache contract verifies manifest and exact source/config signature before returning `output/descriptors.json`; join keys in `input/method_inputs.json`, scorer-only `output/results.json`; experiments/06_object_recognition/experiments/03_appearance/cache.py:34 |
| conditions | geometry-last, geometry-viewmedian, appearance-viewmedian, combined-last, combined-viewmedian; 1 serial pass per condition | confirmed 2026-10-04 owner delegated bounded settings |
| geometry | units_per_metre 5000; raw zero missing; 0 < z < 4 m; original 640x480, fx/fy525,cx319.5,cy239.5; pixel-centre convention | inherited experiments/06_object_recognition/shared/manifest.py:16 and Task17 calibration |
| pose | supplied desk mocap, world tum_freiburg1_desk_mocap/segment continuous_capture; match tolerance 0.02 s; explicit base revision | inherited experiments/06_object_recognition/pilot/replay.py:40 |
| support | oracle polygon-valid median vs separately named box-valid median; camera-coordinate median then world transform; component IQR NumPy linear quantiles | inherited experiments/06_object_recognition/pilot/localisation.py:80; confirmed 2026-10-04 oracle geometry control |
| metric gate | <= 0.35 m to both immutable generation anchor and current estimate; geometry and combined conditions | inherited experiments/06_object_recognition/pilot/replay.py:38; confirmed 2026-10-04 fixed-anchor extension |
| appearance gate | cosine >= 0.80; combined/appearance only; no missing-evidence fallback | confirmed 2026-10-04 fixed exploratory gate, no tuning |
| costs | geometry distance/0.35; appearance (1-cosine)/2; combined weights 0.5/0.5 | confirmed 2026-10-04 dimensionless association costs; not precision weights |
| ambiguity | maximum-cardinality/minimum-sum-cost; alternate full-cardinality mean-cost gap <= 0.05 abstains all changed rows; comparison numerical tolerance 1e-12 | confirmed 2026-10-04 bounded global ambiguity policy |
| duplicate suspect | same category, box IoU >= 0.90 AND world distance <= 0.02 m; both unresolved, 0 votes; no confidence winner | confirmed 2026-10-04 conservative duplicate control |
| birth | first usable frame per class seeds all nonsuspect geometry-valid observations; later unmatched same-class stays pending, new class may seed | inherited pilot conservative outside-gate policy; confirmed 2026-10-04 explicit class seeding |
| view groups | chronological first-compatible fixed representative; translation <= 0.05 m AND rotation <= 10 deg; earliest accepted member only; source frame <= 1 vote | confirmed 2026-10-04 correlated-view cap |
| location | last accepted or coordinate-wise median of group representatives; immutable first anchor; no appearance/confidence weights; no automatic relocation | confirmed 2026-10-04 owner coordinate/duplicate clarification |
| spread | component min/max/IQR linear quantile, representative radial distances and estimate shifts; no covariance/error claim | confirmed 2026-10-04 descriptive coordinate diagnostics |
| revision | full-generation recomputation from immutable camera coordinates; stable ID, no assignment rerun; synthetic explicit relocation only | confirmed 2026-10-04 no real path-correction/full Task13 run |
| ordering/IDs | timestamp then opaque key; UUID5 deterministic schema/condition/session/origin/first-key; repeat payload must match exactly | confirmed 2026-10-04 reproducible replay |
| resource | 6 real frames/11 observations/5 conditions; synthetic controls separate; 0 GPU forwards/no models loaded; no descriptor recomputation | confirmed 2026-10-04 efficiency request |
| execution | 1 writer, fresh Run, no overwrite, CPU serial; runtime pins inherited shared and Task20 cached format | inherited experiments/shared/runs.py:140; confirmed 2026-10-04 immutable publication boundary |
| runtime | NumPy2.4.2, Pillow12.3.0, SciPy1.17.1; no OpenCV/Torch import or GPU inference required for cached-vector association | inherited experiments/shared/requirements.txt:1; experiments/shared/requirements.txt:2; experiments/shared/requirements.txt:3 |

## Verification

Contract files: tests/test_association.py, test_locations.py, test_persistence.py and test_inputs.py under the scoped experiment. Meaningful controls first or independently reviewed tests. Focused changed-module coverage >= 80%, lint/type/format checks, offline review browser check, Python/code and fresh diff review before closure.

Exact assertions: one returned cup fixture has 1 persistent ID before/after gap and unchanged estimate during gap; two identical appearance neighbours at separated coordinates keep 2 IDs with geometry or abstain without it; crossed ordering preserves assignments; equal/full-cardinality alternative costs abstain every changed row and change 0 locations. Duplicate suspect pair stores 2 unresolved observations and contributes 0 births/updates. Replay identical keys adds 0 IDs/observations; conflicting evidence fails. Appending 100 identical-view observations yields exactly 1 view representative and unchanged robust position, while preserving all 100 coordinates. Three independent representatives at x=[0,0.02,0.10] metres yield median x=0.02; last x=0.10. A chain of positions each within 0.35 m of its predecessor cannot cross the fixed anchor's 0.35 m gate. Appearance score change alone does not change a location vote weight. Missing depth/pose creates 0 metric birth/update; different origins merge 0 IDs.

Moved neighbour/background-depth cases cannot silently average a new location into an old generation; pending moved candidates retain nullable ID and candidate list. Explicit synthetic relocation starts a new generation with the same ID, retains old estimate/history and averages 0 old-generation votes. Synthetic +1 m rigid revision shifts all derived positions by exactly +1 m, retains original coordinates/IDs and rejects mixed-revision generation. Crash after a persisted record but before completion yields 0 readable generations; prior completed run remains byte-identical. Resume-copy replay adds 0 records, fresh staging never changes the source DB. An ancestry-guard failure performs 0 mkdir/copy/model/database effects. Labels stripped from method records stay absent even with altered evaluator IDs.

Before: 0 bounded five-condition geometry/appearance comparisons. Target: 1 five-condition bounded within-session comparison with complete 11-observation decisions per condition, coordinate shifts/spread and every failed association reported; 0 origin merges; separate synthetic hard-neighbour cases. Real cup success is measured, not assumed. Oracle input and provisional supports preclude automatic-detector accuracy, blind generalisation and physical-centre error claims. Do not treat unavailable/missing cases as success. Save counts of incorrect merges/splits against provisional identity references and unresolved decisions, not tuned operational gates.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No implementation commit |
| Files changed | Task21 experiment package, focused tests, scoped READMEs, pytest index and `tools/check.py`; existing IdentityStore schema/API and Task13 files unchanged |
| Test status | 21 focused tests pass against the immutable accepted run, including the cross-session boundary regression; Ruff, mypy and scoped Black check pass. The regression failed before the session guard and passed after it. The actual bounded replay exercised the full runner and reported 94% package coverage before a test-only assertion key was corrected. The passing snapshot-validation suite reports 77% because it reuses that run and does not repeat input and report construction. |
| Before measurement | 0 bounded five-condition geometry/appearance comparisons |
| After measurement | Immutable run `20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb`, complete with 172 files; manifest SHA256 `75a1b943ab087d846a87d71289b4e118063fad8bac2010694e1521499046d6f7`. Five conditions processed 11 observations across six source frames, including empty gap frame268. Geometry-last, geometry-viewmedian, combined-last and combined-viewmedian resolved 11/11 with 0 reference-scored wrong merges/splits. Appearance-viewmedian resolved 7/11 and abstained on 4. The same cup ID persisted from frame104 to return frame359 within every condition. Combined-viewmedian ID: `be7211538a005d12bb359ab16ce56c8c`. |
| Delta | +1 bounded comparison; 0 origin merges; 0 wrong merges/splits in the provisional reference; no GPU forwards, model loads or descriptor recomputation. Cup frame104-to-359 observed-surface change: `[-0.01382, 0.00377, -0.01399] m` (20.0mm). Final last-minus-viewmedian: `[0.01481, -0.04726, 0.03162] m` (58.8mm). |
| Decision-gate outcome | Exploratory result supports cup identity survival in this inspected clip and identifies appearance-only abstentions. Box-support medians and box-minus-polygon camera/world coordinate differences are in the method input records. Same-class monitor controls, ambiguous proposals, duplicate suspects, view-vote cap, unknown origins, cross-session boundaries, restarts and revision behavior are covered by synthetic tests. The Python review's cross-session ID defect was fixed with a regression test. The completed HTML viewer and run receipts are under the experiment run. Fresh post-fix Python and blind finished-diff reviews found no remaining reproducible defects. Task21 is ready for owner review; it does not approve Task16's broader protocol. |

Run history: immutable snapshots `20261004T141743.357358Z_5788907929ad42e0be51854ff4642f74`, `20261004T142933.968017Z_baefbf4d59a04d5a86cff8a17ab0ce70`, `20261004T143414.120838Z_ac77f275fe084ebd87a0cf212c2b7510`, and `20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb` remain intact. The last run is the accepted box-versus-polygon and six-frame gap snapshot. Earlier runs are diagnostic snapshots superseded by the added support comparison and gap history. No production replay was created after the last run; corrected assertions reused the latest immutable run.

Owner review remains outstanding. Task16's broader protocol remains pending review.
