---
id: "11"
title: Explain geometry control outputs and show supplied camera positions
status: closed
priority: MED
type: refactor
blocked_by: []
blocks: []
verification_test: experiments/03_tracking/tests/test_review.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/03_tracking/src/**
  - experiments/03_tracking/tests/**
  - task_list/README.md
docs:
  - experiments/03_tracking/README.md
baseline_metric:
  source: experiments/03_tracking/src/run.py:112
  field: explained stage review and common-coordinate pose views
  baseline_value: "0 explained validation tables and 0 joint coordinate views"
  target: "1 explicit validation table, 1 scene overview, 1 camera-position view"
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 11: Explain geometry controls and show supplied camera positions

## In plain English

Make the run review explain what the program actually did. Show which inputs were supplied and which checks passed. Put the three saved observations and their supplied camera positions in one coordinate space, without claiming to estimate movement or depth.

## What

Extract review generation into experiments/03_tracking/src/review.py. Add descriptive stages, output/download links, numerical visual scales, explicit validation limits and a common-world scene/pose overview. Preserve original run; produce a fresh CPU run from its copied inputs with the identical selected IDs. Update experiment README and task board.

## Why

The user cannot tell if the current exports estimate depth, estimate movement, or only use supplied inputs. Filename-only captions and separate world-cloud previews do not establish that difference. Tracking inference remains task 05; fused reconstruction and independent surface scoring remain task 04.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Both depth and poses are supplied | control.compute | run._frame | experiments/03_tracking/src/control.py:40 |
| Original review labels images by filename | archived run source _review | execute | experiments/03_tracking/runs/20261002T094131.010017Z_cdf718bae0c8460584d323b1e47ebac6/metadata/source/experiments/03_tracking/src/run.py:115 |
| Full world points and original supplied pose already saved | run._frame | new scene view | experiments/03_tracking/src/run.py:60 |
| Run artifacts validate before completion publication | Run.finish | execute and verify_run | experiments/shared/runs.py:190 |

1. Explain stages: original RGB; supplied axial depth/validity; camera points; world points using supplied pose; reference-basis conversion; arithmetic projection roundtrip.
2. Export debug/scene_world.png with all world points, per-frame colours and supplied camera markers. Export debug/camera_positions.png with positions relative to first selected camera in millimetres. Save debug/scene.json with IDs, exact centre coordinates, deltas, geometry coordinate frame and supplied provenance. Use existing proper-pose validation and same-origin guard.
3. Review table separates integrity/coordinate checks from unmeasured depth accuracy, tracking accuracy and reconstruction accuracy. Do not declare projection roundtrip as a prediction error. Describe one/no-frame behavior and reject mismatched origins.
4. Use original run input/dataset snapshot and IDs [1,2,3] for refreshed review; retain original complete run unchanged. New artifacts join existing Run inventory.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| input observation pose, contracts.py:44 | scene view | T_world_camera, metres; camera centre = translation; same world/segment | copied per-input JSON |
| output world.npy, run.py:60 | scene view | full Nx3 supplied-depth points in compatible world | saved array |
| Run.finish, runs.py:181 | reviewer | inventory verified and completion last | yes; new run, old run unchanged |

Source of truth: saved observations and arrays, no inferred or aligned pose. Single process; no new cross-process state. Kill during plot/review generation leaves existing running/failed run state; completion remains last. Fresh deployment uses existing CPU requirements and module CLI. All current output names stay compatible; additional debug artifacts are additive. No GPU import or workload.

## Hyperparameters

| name | value | source |
|---|---|---|
| input IDs | [1,2,3] | inherited task_list/closed/03_define_observation_and_pose_contracts_with_known_g.md:98 |
| depth conversion/backend | unchanged 5000 and CPU | inherited experiments/03_tracking/src/run.py:20 |
| scene sampling | all valid points | inherited experiments/03_tracking/README.md:18 |
| colours, figure dimensions | fixed display choices only | n/a do not change numerical outputs or scores |
| translation display | 1000 mm per metre, relative first selected pose | n/a exact units conversion, no scale fitting |

Hyperparameter audit ran before the refreshed run. It reports nested declaration/parser-fragment differences; the actual values for depth scale, backend and validity agree across code and saved configuration. No estimator setting changed.

## Verification

Contract tests in experiments/03_tracking/tests/test_review.py: known pose translations [1,2,3] and [1.001,2.002,3.003] produce relative millimetres [0,0,0] and [1,2,3]; rotation does not move a camera centre. Input arrays remain unchanged. Reject empty frames and mixed world/segment IDs; one-frame view yields zero delta. Review contains supplied-input declarations, stage explanations and unmeasured accuracy claims, and every linked artifact exists. Test first fails before module exists.

Before: 0 explained validation tables and 0 joint coordinate views. Target: 1 validation table and 2 coordinate views, all full points preserved. New code coverage >=80%. CPU refresh must verify full inventory, identical original input hashes and no changes to old manifest; inspect generated plots.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Uncommitted working tree based on 80d4927600bb290040d75d99379d93bb46315451; no commit requested |
| Files changed | tracking src/review.py and scene.py added; run.py delegates to review; tests/test_review.py added; tracking README, task board and this task |
| Test status | 62 passed, 94.15% total implementation coverage; new scene/review modules 100%; Ruff, Black and mypy pass; RED observed before module existed |
| Before measurement | 0 explained validation tables and 0 joint coordinate views |
| After measurement | 1 explained validation table, 1 full common-world scene, 1 supplied-camera-position view; 130 artifacts verify |
| Outcome | Clarified supplied inputs and absent inference/scoring; original run preserved and refreshed CPU review inspected |

Run: experiments/03_tracking/runs/20261002T100227.141579Z_93c31b333549447389d2ba8f941e8f74. Used the original copied dataset inputs for IDs [1,2,3]. Processing/export time 50.4530714 seconds before final manifest publication. Both old and new runs verify; all original inputs and numerical arrays/PLY files are byte-identical. All review links resolve. Inspected both coordinate plots. Every frame retains 307200 points; relative supplied camera centres in millimetres are [0,0,0], [-4.73952,-1.07861,-0.09], and [-2.92253,-0.298738,-1.28]. No tracking, depth prediction, fusion or independent accuracy score is claimed.

Reviews: plan PASS; Python approves corrective code; code review's hardcoded small-movement claim fixed; fresh diff review PASS after caption fix. Tests cover rotation-independent centres, exact mm conversion, unchanged arrays, mixed origins, estimated source rejection, wrong units, invalid/empty clouds and explanatory output links. No finding or follow-up remains. CPU only; no GPU workload. Temporary reviewer test folder removed and caches remain external.
