---
id: "46"
title: Fix late object births and regenerate the object demo
status: in_progress
priority: HIGH
type: bug
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/pilot/tests/test_replay.py
plan_reviewed: 2026-10-05 PASS
files:
  - experiments/06_object_recognition/pilot/replay.py
  - experiments/06_object_recognition/pilot/tests/test_replay.py
  - experiments/06_object_recognition/experiments/06_identity_policy/cached_replay.py
  - experiments/06_object_recognition/experiments/06_identity_policy/tests/test_cached_replay.py
  - tools/demos/sources.py
  - tools/demos/build.py
  - tools/demos/pages_results.py
  - tools/demos/web/page_objects.js
  - tools/demos/tests/test_demos.py
docs:
  - README.md
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/06_identity_policy/README.md
  - demo_outputs/README.md
  - task_list/README.md
baseline_metric:
  source: tools/demos/sources.py:24
  field: late same-class births suppressed
  baseline_value: "90/95 book detections outside-gate unresolved; 18 IDs; 226/457 unresolved total"
  target: "0 unresolved_outside_gate decisions; retain all 60 frames and 457 proposals"
created: 2026-10-05
last_updated: 2026-10-05
superseded_by: null
---

# Task46: Fix late object births and regenerate the object demo

## In plain English

New objects can enter the camera view at any time. Remove the rule that blocks a new object just because another of its class was seen earlier. Replay saved detections and rebuild the demo, keeping uncertain matches visible and new identities provisional.

## What

Owner requested the core birth fix and regenerated demo on 5 October. Remove the same-class birth veto in the pilot owner. Valid observations with no feasible existing-track match can start provisional identities at any frame. Preserve ambiguous, missing-position and already-claimed outcomes; the latter can be duplicate boxes. Task32 owns geometric integration. Task31 retains broader duplicate relationships, confirmation and SQLite migration; this bounded fix does not approve that migration or physical-accuracy claims.

## Why

The 60-frame demo has 95 books: 1 birth, 4 matches and 90 outside-gate unresolved. New same-class objects cannot appear after initial enrollment. A new ID is still a candidate: noisy medians can split one physical object into several IDs.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Birth veto and one-to-one association exist | associate_frame | replay and cached publisher | experiments/06_object_recognition/pilot/replay.py:127; experiments/06_object_recognition/pilot/replay.py:283 |
| Regression expects defective policy | pilot tests | pytest | experiments/06_object_recognition/pilot/tests/test_replay.py:119 |
| Demo loads full baseline, not six-frame automatic results | demo loader | builder/page 06 | tools/demos/sources.py:54; tools/demos/build.py:79 |
| Immutable completion and hash verification exist | shared Run | publisher and overlay loader | experiments/shared/runs.py:68; experiments/shared/runs.py:135 |
| Narrative describes birth veto | objects_in_3d | HTML | tools/demos/pages_results.py:228 |
| Running count is overwritten in browser code | page_objects.js update | page 06 heading/chips | tools/demos/web/page_objects.js:88 |

1. Change regression and add late birth, return, gate boundary and immutability tests. Run red first.
2. Remove veto; add provisional identity state. Preserve other matching rules.
3. Add CPU cached publisher under the existing Task31 experiment directory, reusing associate_frame and Run. Verify source run; snapshot baseline ledger and pin manifest/ledger hashes. Recompute decisions, snapshots, failures and counts in a fresh output. Add immutable observation IDs from source-ledger hash/frame/proposal index. Persist timing and policy counts, not accuracy.
4. Demo retains historical RGB/depth/cloud assets but accepts verified identity-run overlay. Verify source hashes, frame order and immutable proposal content; replace association fields only. Pin new run as default after verification, retaining explicit CLI override. Footer identifies both sources. Historical run stays unchanged.
5. Rebuild all seven pages. Pass identity state through the page payload and update provisional-count language in static and browser-rendered headings, box labels and chip tooltips, plus the question-mark explanation. Check offline pages and timeline controls with installed Playwright/Chromium. No inference/download.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/06_object_recognition/pilot/replay.py:127 | cached publisher | Same-class positions in metres; one assignment per existing track/frame | Deterministic replay |
| tools/demos/sources.py:54 | publisher/demo | Baseline world/segment/pose/frame lineage | Source stays byte-identical |
| experiments/shared/runs.py:68 | overlay loader | Completed run and copied ledger/source hash receipt | Changed/incomplete runs rejected |

Source of truth: immutable proposals plus recorded policy, no database migration. Process boundary: JSON and hashes. Before verification nothing publishes; recomputation failure leaves running/failed Run; completed output requires verify_run. Rebuild failure leaves the verified identity run available for retry; demo pages are local generated artifacts, not historical receipts. Fresh deployment requires existing local assets, installed dependencies and documented cached-publisher/build commands; missing files fail clearly. Old ledgers remain readable without identity-state fields.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| Cached inputs | 60 frames, 457 proposals, exact depths/poses/world medians | inherited tools/demos/sources.py:24 |
| Geometry gate | 0.35 m inclusive | inherited experiments/06_object_recognition/pilot/replay.py:38 |
| Ambiguity margin | 0.05 m alternate full-cardinality assignment | inherited experiments/06_object_recognition/pilot/replay.py:39 |
| Assignment and retention | Same class; max cardinality/min distance; no expiry | inherited experiments/06_object_recognition/pilot/replay.py:106 |
| Birth policy | No-candidate valid position starts provisional ID at any frame | confirmed 2026-10-05 owner fix request |
| Display settings | Existing SETTINGS unchanged | inherited tools/demos/build.py:44 |
| New numeric thresholds | None | n/a isolated policy fix |

Repository hyperparameter audit run before implementation; historical unrelated configurations differ. Retain pilot values unchanged. Publisher mirrors consumed settings in HYPERPARAMETERS and output JSON.

## Verification

Contract: late same-class observation at 1 m gets object-0002; reversed returns retain both IDs; 0.35 m matches and just beyond starts provisional; null/invalid/ambiguous remain unresolved; input dictionaries unchanged. Cached tests check unique deterministic observation IDs, unchanged proposals/geometry, snapshots/counts and hash rejection. Demo tests reject incompatible overlays and verify revised explanation.

Before: 90 books outside-gate unresolved; 18 IDs; 226 unresolved. Target: 0 outside-gate decisions; retain 60 frames/457 proposals. Measure all decision counts and provisional IDs; no inventory accuracy. Focused pilot/cached/demo tests plus offline browser check. Fresh code and diff reviews before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit yet; staging was rejected by automatic approval review after its usage limit was reached. Nothing was staged. |
| Files changed | 21 scoped source, test, documentation, task and demo files; the 172-file cached run is complete and remains locally ignored. |
| Test status | 101 focused tests passed; seven-page offline browser check passed with zero console/page errors or external requests; Ruff, Black and cached-publisher mypy passed; Python, diff, security and JavaScript reviews passed. |
| Before measurement | 90/95 books outside-gate unresolved; 18 IDs; 226/457 unresolved |
| After measurement | All 60 frames/457 proposals retained; 55 provisional identities, 346 matches, 56 unresolved and 0 outside-gate births; books: 6 provisional IDs, 84 matches and 5 unresolved. |
| Delta | 18 to 55 IDs; 226 to 56 unresolved overall; 1 to 6 book IDs and 90 to 5 unresolved books. |
| Decision-gate outcome | Plan review PASS; code and security/diff/browser reviews PASS. No independent physical-identity accuracy claim. Implementation and demo are verified locally. Task remains in progress because automatic approval review rejected Git staging at its usage limit; no commit or push exists. |

still open because the automatic approval service rejected the authorized staging command when its usage limit was reached; retry is required before recording a closing commit.
