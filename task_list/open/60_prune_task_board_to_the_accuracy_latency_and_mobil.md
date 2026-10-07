---
id: "60"
title: Prune task board to the accuracy, latency and mobile deployment goals
status: in_progress
priority: MED
type: decision
approval_status: owner approved the board review recommendations on 2026-10-07
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - task_list/**
  - README.md
  - experiments/**/README.md
  - research/**/README.md
docs:
  - task_list/README.md
  - README.md
  - experiments/README.md
baseline_metric:
  source: node ~/.claude/task-system/task.js list / list pending_review, 2026-10-07
  field: live tasks (open + pending review)
  baseline_value: "32 live tasks: 15 open, 17 pending review"
  target: "9 open tasks plus 1 new decision task; 0 pending-review tasks waiting on reviews that will not be run"
created: 2026-10-07
last_updated: 2026-10-07
superseded_by: null
---

# Task 60: Prune the task board to the project goals

## In plain English

The work plan had grown to 32 unfinished items, and about half were waiting for reviews that nobody is going to run. This task keeps the items that lead to accurate measurements, an acceptable wait and a working phone deployment. Finished work gets closed with a note, optional refinements get parked until a full test shows they are needed, and one missing decision gets its own item.

## What

- Close finished pending-review work with its commit receipt and a written waiver of the external validation: 16, 21, 22, 24, 32, 37, 38, 39, 40, 41, 42, 44, 45, 47, 48, 49.
- Archive Task08 (superseded by Task52) and Task09 (superseded by Task56).
- Move optional refinements to `stale/`: 23, 31, 33, 34, 35. Task56's measured failures decide whether any return.
- Lower 25 and 36 to LOW and block them only on Task56.
- Create Task61 for the field acceptance limits and the phone capture-only versus on-phone-processing decision. Repoint the 53/54/55/57 blockers from Task51 to Task61 where they need field decisions.
- Add a phone-runnable requirement to Task54 and move Task24's container-build follow-up into Task57.
- Fix Task51's frontmatter title only. Its file name stays because other task files and READMEs link to that path, and Task51 has uncommitted owner edits.
- Rewrite the board README tables to match.

## Why

The board review on 2026-10-07 found: nine pending-review tasks waiting on fixed-snapshot validation that the board README says will not be relaunched automatically (task_list/README.md:120); receipts for Tasks32/47/48/49 saying "no commit" although the code is in `14957e6`; Tasks53-57 blocked on Task51 decisions that Task51 stopped owning when it was rescoped on 2026-10-06; and HIGH-priority object-identity refinements (31, 34, 35) blocked several layers deep while not serving the three goals. The owner also ruled on 2026-10-07 that deployment must be on a phone.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| External review sessions are not relaunched automatically | Board README | pending-review tasks | task_list/README.md:120 |
| Unrelated research approvals are not a blanket gate; check specific claims when used | Board README | all goal tasks | task_list/README.md:105 |
| Task32/47/48/49 code is committed | git history | receipts | `git log -- task_list/*/49_*` shows `14957e6`; experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/run.py tracked |
| Task44 and Task45 code committed | git history | receipts | commits `c3bd9ef`, `cf68ccc` |
| Task56 owns complete-run integration and missing report measures | Board README | Tasks44/45 follow-ups | task_list/README.md:116 |
| Task52 owns new recording work | Board README | Task08 | task_list/README.md:109 |
| Task46 already fixed the late-birth defect that motivated Task31 | Task46 receipt | Task31 | task_list/README.md:151 |
| Task51 rescoped to a prerecorded pipeline; field limits pending | Task51 | Tasks53-57 | task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md:1-20 |

Use `task.js move` for every state change so the moves are journaled and lint-checked. Append a dated closure note to each moved file; do not rewrite earlier results.

hyperparameters n/a: board maintenance only; no experiment.

invariants n/a: task records only; no code, data or run artifact changes.

## Verification

- `task.js lint` reports 0 errors after the moves.
- `task.js list` shows 10 open tasks (25, 36, 51-57, 61) plus this task; `task.js list pending_review` shows 0.
- Every closed task's receipts name a commit or state that no code was written.
- No open task is blocked by a task in `stale/`, `closed/` or `archive/` except where the blocker is satisfied.
- tests n/a: task records and README only.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

-
