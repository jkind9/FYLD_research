---
id: "47"
title: Fix Task32 association defects found in final review
status: pending_review
priority: MED
type: bug
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py
docs:
  - task_list/README.md
baseline_metric:
  source: Ruff check and Task32 diff review, 2026-10-05
  field: lint findings and reproducible association/resource defects
  baseline_value: "5 lint findings; 7 reproducible cases can confuse identities or exhaust resources"
  target: "0 lint findings; unique observation decisions and bounded assignment/distance memory"
created: 2026-10-05
last_updated: 2026-10-05
superseded_by: null
---

# Task 47: Fix Task32 association defects found in final review

## In plain English

The new spatial matching handoff has style-check failures, identity edge cases, and resource use that can grow too large. I will fix the lint findings, keep duplicate decisions within one coordinate frame, bound matching work, and prevent IDs from being overwritten. Tests will check these behaviors on larger inputs.

## What

Fix five Ruff findings and six association defects in the Task32 implementation and contract tests. Ensure stale counters cannot reuse an existing ID, duplicate suppression respects coordinate lineage and pairwise evidence, suppressed rows cannot consume tracks, assignment work stays bounded, and nearest-sample distance does not allocate a full pairwise point tensor.

## Why

Ruff reported five findings. Diff reviews reproduced stale ID reuse, transitive and cross-lineage duplicate suppression, lost feasible matches, exponential assignment enumeration, and a nearest-sample temporary requiring about 2.45 GB for two 100,000-point supports.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| The association variant owns its implementation and contract tests | Task32 association module and tests | focused pytest and Ruff checks | experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:1; experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py:1 |
| The pilot already uses polynomial one-to-one assignment | `linear_sum_assignment` in pilot replay | Task32 assignment comparison | experiments/06_object_recognition/pilot/replay.py:15,217 |
| Existing geometry input checks enforce unique source IDs | geometry run | evaluator input contract | experiments/06_object_recognition/experiments/04_geometry_identity/run.py:337 |

Reject duplicate observation IDs within a frame before producing decisions. Add tests for this input boundary, the existing identity and duplicate edge cases, a dense 10-detection/10-track assignment, and a 20,000-sample support-distance comparison. Replace assignment enumeration with SciPy's one-to-one solver and detect close alternatives by re-solving with each selected edge removed. Replace the dense pairwise-distance tensor with exact nearest-neighbour queries. Keep source samples, output records, association gates, lineage checks and birth/return rules unchanged. Fix the five Ruff findings. This task changes no median baseline, acceptance gate, calibration claim, or published replay.

## Invariants and recovery

invariants n/a: this local association function returns copied track records and writes no external state

## Hyperparameters

hyperparameters n/a: this task does not run or change an experiment

## Verification

The tests assert duplicate observation IDs raise `ValueError` before decisions are produced, identity and duplicate edge cases remain correct, 10 of 10 dense feasible observations match, and a 20,000-sample support pair returns the expected distance. Ruff must report zero findings. The original 66-test baseline must still pass, with the added regressions included in the final focused suite.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; changes remain unpublished pending owner decision |
| Files changed | `07_spatial_uncertainty/association.py`, `07_spatial_uncertainty/tests/test_association.py`, `task_list/README.md`, and this task receipt |
| Test status | 73 focused tests passed; Ruff, Black, Python compilation, adapter mypy, both task-plan lint checks, and `git diff --check` passed. Mypy cannot map the new module because its package directory begins with digits. |
| Before / after | 5 Ruff findings and 7 reproduced association/resource defects / 0 Ruff findings; all 7 regression tests pass |
| Result | Final diff review passed with no findings; follow-up moved to pending review |

still open because owner review and the publication decision remain outstanding.
