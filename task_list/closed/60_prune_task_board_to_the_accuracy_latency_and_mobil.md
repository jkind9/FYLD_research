---
id: "60"
title: Prune task board to the accuracy, latency and mobile deployment goals
status: closed
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
| closing commit | `bf3fdbc` (board changes); receipt and close in the following commit |
| files changed | 47 task files moved or edited, Task60 and Task61 added; `task_list/README.md`, root `README.md`, `experiments/README.md`, object-recognition, surface, dataset, segmentation, appearance, geometry-identity, replay, capture and research READMEs (link and status updates only) |
| test | `task.js lint`: 62 tasks, 0 errors, 0 warnings. `task.js ready`: board health clean. Relative-link check over every changed Markdown file: 0 broken links. tests n/a: task records and READMEs only |
| before / after | 32 live tasks (15 open, 17 pending review) to 11 open (9 goal tasks plus Task60 and Task61) and 0 pending review; 16 closed, 2 archived, 5 stale |
| result | Done. Ready to start: 51, 52 (software only), 54, 55, 61. Blocked: 53 and 57 on Task61; 56 on 52-55; 25 and 36 on 56 |

Notes / caveats / follow-ups:

- `task.js move <id> closed --dry-run` ignored `--dry-run` and performed the 16 closes. Those were the intended moves, so they were kept and annotated; the CLI flag is a harness bug to fix separately.
- Task51 and `experiments/01_camera_capture_delivery/README.md` had uncommitted owner edits. Only the link fixes were committed for those two files; the owner's edits and `data/README.md` remain uncommitted in the working tree.
- Task51's file name still says "agree success criteria"; its title was already corrected in the working copy. The file name stays to keep its links stable.
- The board audit's 445 oversized-file findings are vendored `third_party/` code and source copies inside old run folders. Excluding those paths from the size check is a harness change, not done here.
- Removed the empty untracked folder `walkthrough-references-13o_jh04/` from the repository root.
