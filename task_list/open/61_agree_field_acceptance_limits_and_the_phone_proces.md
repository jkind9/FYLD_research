---
id: "61"
title: Agree field acceptance limits and the phone processing split
status: open
priority: MED
type: decision
approval_status: created by Task60 on 2026-10-07; owner answers pending
blocked_by: []
blocks: [53, 57]
verification_test: ""
plan_reviewed: null
files:
  - task_list/open/61_agree_field_acceptance_limits_and_the_phone_proces.md
  - task_list/README.md
  - README.md
docs:
  - task_list/README.md
  - README.md
baseline_metric:
  source: task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md, "Earlier field recommendations" table
  field: owner-recorded field acceptance decisions
  baseline_value: "0 of 8 field decisions recorded; phone processing split undecided"
  target: "8 of 8 field decisions recorded with date and units, or explicitly marked pending with the task each one blocks"
created: 2026-10-07
last_updated: 2026-10-07
superseded_by: null
---

# Task61: Agree field acceptance limits and the phone processing split

## In plain English

Before anyone films and measures a real site, the owner needs to decide what a good enough result looks like and where the processing happens. This task records those choices in one place: which site and objects to test, how the site is measured by hand, where recordings are kept, how accurate and how fast the answers must be, and whether the phone only records or also does the calculations. Nothing is guessed; an unanswered choice stays marked as pending.

## What

Own the field decisions that Task51 held before it was rescoped on 6 October 2026 to the first prerecorded pipeline:

1. First use case: the site or room, and its region/boundary definition for area (consumed by Task55's field use and Task56).
2. Target objects and revisit conditions (Task53, Task56).
3. Independent survey method, instruments and reviewers (Task53).
4. Raw-data storage location and offline retrieval steps for phone and survey bundles (Task53).
5. Numeric limits: measurement and count error, coverage, maximum wait for a full result, live-update rate (Task56).
6. Phone processing split: the phone only records and processing is hosted, or the phone also processes; plus whether results must be available offline (Task54 route choice, Task57).
7. Sustained-use limits on the phone: session length, memory, battery and heat (Task57).
8. Session roles for the held-out test: which recordings are used for tuning and which only for the final score (Task53).

Fixed inputs already decided: deployment must be on a phone (owner, 7 October 2026); the Redmi Note 11 Pro (model 2201116TG) is the selected handset; development stays on existing recorded data until phone work resumes.

## Why

Tasks53, 54, 55 and 57 were blocked by "Task51 decisions" that Task51 no longer owns, so the field work had no decision owner. The recommendations, evidence and pending states for items 1-5 and 8 are already written in Task51's "Earlier field recommendations" table; this task makes them the owner's record.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Field recommendations and evidence already drafted | Task51 | this decision record | task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md:69-79 (table "Earlier field recommendations, still pending for later field acceptance"; lines 49-60 under "Recommendations submitted 2026-10-06" in the committed version) |
| Owner asked to leave numeric limits pending on 2026-10-06 | Task51 clarifications | Task56/57 acceptance | task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md:52 (line 45 in the committed version) |
| Survey and reference requirements | Task40 (closed) | Task53 | task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:67-73 |

1. Present the owner one table covering items 1-8. Carry over Task51's recommendations and evidence; add the phone processing split with the measured facts available at the time (model sizes and speeds from Task54 if run).
2. Record each answer with its date and units. Mark any unanswered item pending and name the task it blocks.
3. Update the board README and project README with the agreed first field use case.
4. Do not start Task53 acquisition or Task57 sustained runs until the items they need are recorded.

hyperparameters n/a: decision record; numeric limits recorded here are acceptance limits, not method settings.

invariants n/a: decision record only; no code, data or run artifacts.

## Verification

Each of the 8 items has an owner answer with date (and units where numeric), or an explicit pending state naming the blocked task. 0 values are assumed. tests n/a: decision record.

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
