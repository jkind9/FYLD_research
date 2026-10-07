---
id: "31"
title: Compare provisional object IDs and duplicate relationships
status: stale
priority: HIGH
type: experiment
approval_status: proposed; no execution authorised by Task30
blocked_by: [21, 22, 40, 56]
blocks: []
verification_test: experiments/06_object_recognition/experiments/06_identity_policy/tests/test_identity_policy.py
plan_reviewed: 2026-10-04 PASS
files:
  - experiments/06_object_recognition/experiments/06_identity_policy/**
  - experiments/06_object_recognition/src/identity_store.py
  - experiments/06_object_recognition/tests/test_identity_store.py
docs:
  - experiments/06_object_recognition/README.md
baseline_metric:
  source: experiments/06_object_recognition/pilot/replay.py:283
  field: evidence and comparison gap
  baseline_value: "90 book proposals unresolved outside gate; 0 evaluated provisional-birth comparisons"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-07
superseded_by: null
---

# Task31: Compare provisional object IDs and duplicate relationships

## In plain English

Give every detection its own record and let uncertain new objects remain provisional. Compare ways to retain returning identities and possible duplicates without losing their histories. Uncertainty should remain visible instead of forcing a match.

## What

Owner update, 5 October 2026: Task46 implements the explicitly requested late-birth bug fix and regenerated demo using the full 60-frame cached baseline. It is a bounded first slice of the policy work, with provisional IDs and no new numerical gates. The broader six-frame comparison, duplicate relationships, confirmation and schema migration below remain separate. Historical Task22 results remain intact. The earlier 5 October order put Task32 next. The 6 October board supersedes that queue: Task56 first establishes the complete baseline, then a measured identity/duplicate failure can justify this refinement.

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
| Observation records accept an ID but do not generate one for each proposal | ObjectObservation and the planned policy runner | persistent source history | experiments/06_object_recognition/shared/observations.py:12-18,67-69 |
| Accepted Task22 automatic input is present only as an ignored local run artifact | Task22 replay publication; Task31 must own a tracked fixture copy | first cached policy comparison in a fresh checkout | experiments/06_object_recognition/experiments/05_replay/README.md:5,19; .gitignore:20 |

Proposed first comparison: copy the accepted Task22 files documented in the reuse table into tracked Task31 inputs: the 917 KB automatic proposal JSON (SHA-256 `135eaf6dd153bc8ecd7a1002c4d1faebad2e6eecfc34f749abcda9c087c4991d`), its source pins (SHA-256 `1564f3c0ecadacfc1b4da11dbeedd893a0d67fadbc4a0e75abb7379d7efa3fad`), and the parent selection file (SHA-256 `8a5f0585acdc38ec237ce7a674be4b34a7a7254b6bbffead386bc82d3baac643`). The parent selection covers 60 frames; it is lineage evidence, not the six-frame policy input. The automatic proposal JSON itself contains six frame groups and 17 boxes. Preserve the parent manifest SHA-256 `fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f`. Before creating the copies, verify the source run's manifest and every file pin; record source paths, source hashes and fixture hashes in a receipt. The Task31 runner consumes only this checked fixture, so a fresh checkout does not depend on ignored run output. Do not rerun detection, depth, pose or appearance. This input supports cached policy accounting only. The historical 95-book/90-unresolved count is context from the restrictive policy evidence row; do not claim to reproduce it with the six-frame input. Reproducing that count requires locating and pinning its exact cached proposal artifact before the experiment starts.

Run two deterministic policies over the same proposals. The baseline preserves the existing restrictive birth rule. The proposed policy creates one provisional ID for each unmatched proposal, records possible-duplicate relationships as separate reviewable records, and never auto-confirms, rejects or unifies from an unapproved threshold. A checked human decision can move an ID from provisional to confirmed or rejected. Keep source proposals and decisions immutable; a human correction appends a revision. Use a deterministic opaque observation ID derived from the frozen input hash, frame ID and proposal index, and reject any collision or repeated ID with different source bytes. Keep one-to-one within-frame assignment and unmatched choices fixed. The first cached run reports policy counts only. False merges/splits, return recovery, inventory precision/recall and claims about physical identity stay blocked until Task40's independent cases are acquired and authorized.

Additive persistence contract: migrate a disposable copy of the version-1 IdentityStore schema to version 2 in one SQLite transaction without deleting or rewriting existing object/observation rows. Build the migration test source as a temporary database using the exact current version-1 schema and representative legacy rows; hash it before migration, copy it to a separate target, and migrate only that copy. Never open a receipt-checked Task21/22 run database as the migration target. If a real pending-review run database is later used as a source, verify its run receipt and database hash before and after the read-only copy. Snapshot every existing observation's decision and object ID into the revision ledger with state `legacy`; do not infer that an old assignment is confirmed. Add append-only candidate-state events, append-only observation-to-object decision revisions, explicit unordered duplicate-pair decisions, union events and aliases from retired IDs to a canonical ID. A union inserts aliases and a union event but never rewrites prior observation assignments; readers resolve canonical IDs through aliases while retaining every original decision and source history. Detect alias cycles and reject conflicting replays. Interruption before commit rolls back every table change; after commit a reopen returns the complete event history and aliases. Exact replay is idempotent; replay with changed proposal bytes or a conflicting decision fails atomically. Keep the accepted Task22 viewer unchanged; Task31 publishes a separate report from its own immutable input and does not claim that the viewer reads the identity store.

Necessary data/reference: Task40 must provide independently checked identities, duplicate boxes, co-visible distinct supports, new same-class objects in later views and genuinely identical disjoint-view cases before identity-accuracy scoring or acquisition. If physical identity is unknowable, reference the ambiguity rather than assigning a false gold answer. A Task40 plan review alone does not satisfy this data dependency.

Measurements: Count unique observation IDs; confirmed/provisional/rejected states; false merges/splits, duplicate candidates, unresolved pairs, return recovery and inventory precision/recall against independent labels. Measure transaction/replay consistency and assignment/runtime/storage costs.

Dependencies: Task21 and Task22 remain in `pending_review`; neither state is treated as owner acceptance. Task40's plan review passed, but its acquisition/reference decision is still proposed and supplies no new cases yet. Task16 remains in `pending_review`. Before implementation, obtain owner approval for this bounded comparison and its schema migration. Before numerical scoring, acquire and authorize Task40's independent references and record every new policy threshold/setting with user-confirmed provenance. Completed controls remain historical evidence, not reopened work. Do not change or close Task16/21/22 as part of Task31.

Cost questions: Assignment scaling, provisional-candidate growth, manual-review burden, aliases/history storage and persistence migration.

Decision informed: Choose a birth/confirmation/merge policy that retains evidence and exposes ambiguous identity. Numeric operating rules remain unselected.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/pilot/replay.py:283 | Isolated comparison/evaluator | Immutable evidence; metres/grid/frame/revision/lineage where applicable | Verified sources retained |
| Proposed runner | Isolated report and version-2 store | Cached proposal bytes plus deterministic per-proposal observation IDs; missing depth is null position | Complete verified runs only; a failed run stays unpublished |
| Version-1 IdentityStore | Version-2 migration and policy readers | Existing rows retained; candidate-state events, observation decision revisions, duplicate links, union events and aliases in SQLite | One transaction rolls back on interruption; after commit reopen reads the complete version |

Immutable tracked Task31 fixture → source-hash/frame/proposal-index observation IDs → policy decisions and duplicate links → isolated version-2 store and Task31 report. Positions retain metres/world/segment/revision; null remains unknown. The accepted Task22 viewer continues to consume its existing `automatic.json`; it is not a reader of the identity store. Migration tests preserve the source version-1 database byte-for-byte and change only its disposable copy. Task31 never migrates a receipt-checked Task21/22 run database in place, and existing run receipts and databases remain readable. A fresh run verifies the tracked Task31 fixture receipt before opening a new isolated store; it never mutates accepted Task22 output.

Fresh-checkout setup and reproduction command after implementation: create an isolated environment with `python -m venv .venv-task31`, install the pinned shared dependencies with `.venv-task31/Scripts/python.exe -m pip install -r experiments/shared/requirements.txt`, then run `.venv-task31/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.06_identity_policy.run --input experiments/06_object_recognition/experiments/06_identity_policy/inputs/task22_automatic.json --output experiments/06_object_recognition/experiments/06_identity_policy/runs/<new-unique-run>`. This follows the existing package entry point and provides the NumPy/SciPy dependencies used by the reused association code. The runner rejects an existing output directory and publishes only after its fixture, decisions and report validate. The local environment is created by these commands and is not expected in a fresh checkout.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| Cached proposal input and six-frame groups | Accepted Task22 `automatic.json`; six frame groups and 17 automatic boxes; parent `selection.json` has 60 frames and is lineage only; manifest SHA-256 `fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f` | inherited experiments/06_object_recognition/experiments/05_replay/README.md:19 |
| Geometry gate | distance ≤0.35 m against anchor and current estimate | inherited task_list/closed/22_build_recorded_video_camera_surface_and_inventory_.md:139 |
| Appearance gate and combined cost | cosine ≥0.80; geometry/appearance weights 0.5/0.5 | inherited task_list/closed/22_build_recorded_video_camera_surface_and_inventory_.md:139 |
| Assignment and ambiguity | max-cardinality then min-cost; alternate mean-cost gap ≤0.05 abstains; float comparison tolerance 1e-12 | inherited task_list/closed/22_build_recorded_video_camera_surface_and_inventory_.md:140,154 |
| Duplicate control and existing birth rule | same-class box IoU ≥0.90 and world distance ≤0.02 m; both unresolved and zero votes; initial-class seeds, later unmatched births pending | inherited task_list/closed/22_build_recorded_video_camera_surface_and_inventory_.md:141 |
| View grouping and position summary | translation ≤0.05 m and rotation ≤10°; one vote per source frame; earliest representative; coordinate median versus last | inherited task_list/closed/22_build_recorded_video_camera_surface_and_inventory_.md:142 |
| Provisional birth and reviewable duplicate-link policy | one provisional ID per unmatched proposal; no automatic confirmation, rejection or union | n/a owner approval pending; do not run before decision |
| Confirmation/rejection criteria and new score thresholds | not selected | n/a no new numerical setting is authorized |
| Independent scoring cases and split | Task40 acquisition, separate sessions/views | n/a cases not yet acquired or authorized |

The repository-wide hyperparameter audit reports divergent values across unrelated historical runs. Before implementation, reconcile only settings consumed by this comparison against the cited Task21/22 records and accepted input hashes. The first cached policy-accounting run can use the inherited settings above; no physical-accuracy threshold is inferred from provisional labels. Any additional tunable setting requires a dated owner decision before numerical scoring.

## Verification

Contract test `experiments/06_object_recognition/experiments/06_identity_policy/tests/test_identity_policy.py` must assert that the tracked fixture receipt validates copied input bytes, deterministic unique proposal IDs, null position for missing depth, two checked co-visible objects staying distinct, a checked return retaining its ID, ID union preserving every history and alias without rewriting prior decisions, version-1 migration snapshotting prior decisions as `legacy`, process-failure rollback at each migration/union write boundary, exact replay idempotency and changed-payload replay rejection. `experiments/06_object_recognition/tests/test_identity_store.py` must cover migration compatibility.

Before: 90 book proposals unresolved outside gate; 0 evaluated provisional-birth comparisons. After: no new measurement yet. Report paired measurements, unavailable cases and costs; decision thresholds remain unselected. Name a concrete verification test within declared scope before start.

Task30 checks plan completeness and board consistency only. This HIGH/stateful plan requires PASS from fresh-context review before start, then finished-diff review before closure. Initial cached results can only report policy-accounting counts for the pinned six-frame input. Accuracy measurements remain unavailable until Task40's cases exist and are authorized. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | Task-plan lint passed; fresh-context plan review recorded PASS on 2026-10-04. No implementation tests or experiment executed. |
| Before measurement | 90 book proposals unresolved outside gate; 0 evaluated provisional-birth comparisons |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Plan review passed; comparison not authorised. Tasks16, 21 and 22 remain pending review; Task40 has no approved independent reference acquisition or scoring cases. Owner approval for the bounded comparison and schema migration is still required. Confirm any new thresholds or settings before numerical scoring. |

still open because the comparison has no owner authorisation or independent scoring cases, and Tasks16, 21 and 22 remain in pending review.

## Board decision, 2026-10-07

Parked under Task60 with owner approval. This is an optional object-identity or review refinement that does not lead directly to the accuracy, latency or phone-deployment goals. It returns to `open/` only if Task56's complete walkthrough benchmark shows a measured failure it would fix; refresh its blockers and plan review then. Earlier receipts and authorisations remain as written. Its motivating defect (90 unresolved books) was fixed by Task46 (5 unresolved).
