---
id: "15"
title: Prepare recorded video recognition plan for owner sign off
status: closed
approval_status: approved
priority: MED
type: decision
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/README.md
plan_reviewed: 2026-10-03 PASS
files:
  - README.md
  - experiments/README.md
  - experiments/01_camera_capture_delivery/README.md
  - experiments/03_camera_pose_estimation/README.md
  - experiments/06_object_recognition/README.md
  - research/README.md
  - task_list/**
docs:
  - README.md
  - experiments/06_object_recognition/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Prepare recorded video recognition plan for owner sign off
  baseline_value: "0 consolidated recorded-video inventory proposals"
  target: "1 source-backed proposal with 10 separately owned follow-up tasks"
created: 2026-10-03
last_updated: 2026-10-03
superseded_by: null
---

# Task 15: Prepare recorded video recognition plan for owner sign off

## In plain English

Put the agreed discussion into one reviewable proposal. Show what already works, what must be measured next, and which work can be assigned to separate sessions. Wait for owner sign-off before starting implementation.

## What

Prepare the stage 06 plan, root processing diagram, updated task index and proposed folder ownership. Preserve existing dirty code and successful historical receipts.

## Why

The discussion now defines a recorded-video inventory stream and a parallel mobile-capture stream; they need an explicit dependency and evidence plan.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Stage 06 already owns checked persistence | IdentityStore | future association | experiments/06_object_recognition/src/identity_store.py:34 |
| Existing tasks remain the evidence ledger | task board | session coordination | task_list/README.md:5 |

Read the supplied segmentation sources and trace existing owners. Write the proposal in existing READMEs. Create Tasks 16 to 25 with dependencies, verification and future settings gates. Review this proposal independently; do not start implementation or inference.

All new work is proposed pending owner sign-off. Existing source code is not modified by this planning task. Planned paths need to be created by their implementation owner; missing future docs/tests are not evidence of a completed task. Each delegated session owns its files; shared viewer work in Tasks 22/23 is serialised. Update only the owning README during parallel execution; a coordinator updates root and board summaries.

## Invariants and recovery

invariants n/a: documentation and task planning only; preserve all existing code and run artifacts.

## Hyperparameters

hyperparameters n/a: documentation and task planning only; no numerical runs or new settings. Follow-up tasks retain their protocol and settings approval requirements.

## Verification

Contract test: experiments/06_object_recognition/README.md. Check that every task link resolves, Tasks 16 to 25 are open/proposed, exactly one pre-existing task (13) is active, and the planned folders are clearly distinguished from existing code. Read the root diagram against actual sources and implementations.

Before: 0 consolidated recorded-video inventory proposals. Target: 1 source-backed proposal with 10 separately owned follow-up tasks. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Prepared in working tree; no commit requested and no implementation changed |
| Files changed | Seven existing READMEs; Tasks08/09/13 updated; planning Task15 and proposed Tasks16 to 25 created |
| Test status | Task lint: 26 records, 0 errors/warnings; all 11 new task plans lint clean; 124 README links resolve; exactly Task13 active; all 10 follow-ups open/proposed; independent proposal review PASS |
| Before measurement | 0 consolidated recorded-video inventory proposals |
| After measurement | 1 source-backed proposal with 10 separately owned follow-up tasks, proposed folder tree and root processing diagram |
| Delta | +1 consolidated proposal; +10 proposed follow-ups; 0 new executed comparisons |
| Decision-gate outcome | Owner signed off the plan on 3 October 2026 ("all good"). Numerical choices and implementation reviews belong to their separate follow-up tasks |

Independent review corrected seed-transform ownership, pose-revision production/derived-geometry recovery, APK handoff scope, experiment invariants and worktree source/task-state preparation. The revised proposal passed, including tailored viewer/build recovery; advisory evidence pointers were corrected. Existing dirty source, successful runs and historical receipts were preserved.

tests n/a: documentation-only change; checked task states, links, scope and claims against code instead of adding implementation tests. Owner sign-off is complete; the separate implementation tasks retain their own numerical protocol and review requirements.
