---
id: "68"
title: Add the depth and area tests to the default test run
status: open
priority: MED
type: bug
blocked_by: []
blocks: []
verification_test: tools/tests/test_suite_inventory.py
plan_reviewed: null
files:
  - pytest.ini
  - tools/check.py
  - tools/tests/**
docs:
  - README.md
baseline_metric:
  source: "pytest --collect-only, 2026-10-08 evening"
  field: "maintained tests outside the default run"
  baseline_value: "77 tests (experiments/02_stereo_depth/tests and experiments/05_birds_eye_mapping/tests); default run collects 907"
  target: "0 maintained test folders outside the default run; default collection 984 or more"
created: 2026-10-08
last_updated: 2026-10-08
superseded_by: null
---

# Task 68 — Add the depth and area tests to the default test run

## Current state

- Not started. Task 65 holds the active lock; start this after it closes or in a separate worktree.
- Source: HARNESS_WORKFLOW_AUDIT.md finding F5, still open after the 8 October re-check.
- Task 52 also lists `pytest.ini` and `tools/check.py` for its hygiene checks. Coordinate if both are active; this task changes only the suite lists.

## In plain English

The project's standard test command does not run the tests for depth estimation or for site measurement, so it can pass while those parts are broken. This task adds them to the standard run and adds a check that fails if any future test folder is left out.

## What

- Add `experiments/02_stereo_depth/tests` and `experiments/05_birds_eye_mapping/tests` to `testpaths` in `pytest.ini` and to the suite list in `tools/check.py`.
- Add `tools/tests/test_suite_inventory.py`: find every `tests/` folder under `src/`, `experiments/` and `tools/` (skipping `third_party/`, outputs and temp folders) and assert each appears in both lists, and that the two lists match.

## Why

On 2026-10-08 the default collection was 907 tests and the two omitted folders held 77 more. An earlier collection in the same day also hit four permission errors from temporary folders inside the depth tests; they did not recur this evening, so the inventory test should also make sure collection skips temp folders.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Default pytest folders are listed here | pytest.ini | `python -m pytest` | pytest.ini:2 |
| The project check keeps its own copy of the list | tools/check.py | `python tools/check.py` | tools/check.py:66-75 |
| Hygiene tests for the check already exist | tools/tests | default run | tools/tests/test_check_hygiene.py |

## Hyperparameters

hyperparameters n/a: test configuration change, no experiment.

## Invariants and recovery

invariants n/a: configuration only; no state.

## Verification

- **Contract test:** `tools/tests/test_suite_inventory.py` fails against the current lists (naming both missing folders) and passes after.
- **Before/after:** default `--collect-only` count from 907 to at least 984 with no collection errors; `python tools/check.py` passes with the project's documented interpreter, recorded with its path.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |
