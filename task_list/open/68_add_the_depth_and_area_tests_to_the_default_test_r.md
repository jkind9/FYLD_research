---
id: "68"
title: Include all maintained test suites in the default check
status: open
priority: HIGH
type: bug
blocked_by: []
blocks: []
verification_test: "tools/tests/test_suite_inventory.py"
plan_reviewed: null
files:
  - pytest.ini
  - tools/check.py
  - tools/tests/**
docs:
  - README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Include all maintained test suites in the default check"
  baseline_value: "28 maintained tests directories; pytest omits 10, runner omits 11; src/live is pytest-only"
  target: "No maintained test directory omitted or inconsistent; one tested inventory rule prevents regression"
created: 2026-10-08
last_updated: 2026-10-15
superseded_by: null
---

# Task 68: Include all maintained test suites in the default check

## In plain English

The default check skips several working parts of the project, including phone capture and the open trackers. Bring its test list into line with the maintained tests and make future omissions fail visibly. Keep test scratch outside the repository.

## Verified gap, 15 October 2026

The original count of 77 missed depth/area tests is obsolete. Directory and configuration inspection finds 28 maintained `tests/` directories. Both lists omit:

- `experiments/01_camera_capture_delivery/tests`
- `experiments/02_stereo_depth/tests`
- `experiments/05_birds_eye_mapping/tests`
- `experiments/06_object_recognition/experiments/06_identity_policy/tests`
- `experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests`
- `experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/tests`
- `experiments/06_object_recognition/pilot/tests`
- `experiments/live_slam/tests`
- `experiments/open_vio/tests`
- `experiments/sfm/tests`

`pytest.ini` includes `src/live/tests`; `tools/check.py` omits it. These are directory counts, not test-case counts. Collect the current case count at execution rather than retaining 907/984 targets.

## Plan

1. Test first: inventory every maintained tests directory under src, experiments and tools, with explicit skips for external dependencies, ignored run/output and scratch trees. Assert agreement with both default lists; show failures against today's configuration.
2. Add the missing suites to `pytest.ini` and `tools/check.py`, or use one existing configuration list if that is the least code. Avoid a new registry competing with both.
3. Use the documented interpreter and OS temporary directories through `tools/check.py`. Run default collection, then the default check in one background queue if long. Report dependencies, skips and pre-existing failures explicitly; do not make an omitted suite disappear behind a broad exclusion.
4. Prove inventory detects a deliberately omitted maintained folder and does not scan third-party/run folders. Preserve task-board hygiene checks and test scratch cleanup on success/failure.

## Completion boundary

Both entry points collect the same maintained suites, the inventory control fails for omissions, and actual test results are recorded. Task99 already fixed acceptance of `task_list/done`, scratch paths and Ruff cache location; do not redo that work. No model trials or GPU use.
