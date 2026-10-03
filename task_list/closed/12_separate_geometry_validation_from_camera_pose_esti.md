---
id: "12"
title: Separate geometry validation from camera pose estimation
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/geometry_validation/tests/test_contracts.py
plan_reviewed: null
files:
  - experiments/geometry_validation/**
  - experiments/03_tracking/**
  - experiments/03_camera_pose_estimation/**
  - experiments/04_reconstruction/**
  - experiments/04_surface_reconstruction/**
  - tools/check.py
  - pytest.ini
  - task_list/open/04*
  - task_list/open/05*
  - task_list/open/09*
docs:
  - README.md
  - experiments/README.md
  - experiments/geometry_validation/README.md
  - experiments/03_camera_pose_estimation/README.md
  - experiments/04_surface_reconstruction/README.md
  - experiments/shared/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/03_tracking/README.md:5
  field: mixed control and estimation experiment owners
  baseline_value: 1 mixed folder
  target: 0 mixed folders
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 12: Separate geometry validation from camera pose estimation

## In plain English

Separate the existing checks using known camera positions from the future camera-motion estimator. Rename the reconstruction folder to state that it builds surfaces. Update commands and explanations so readers can see what each stage receives and produces.

## What

Move current source, tests and complete local runs from experiments/03_tracking to experiments/geometry_validation. Create experiments/03_camera_pose_estimation with the estimation plan; rename experiments/04_reconstruction to experiments/04_surface_reconstruction. Update imports, test discovery, new-run experiment identity, READMEs and open task scopes. Preserve historical closed receipts and all existing run bytes.

## Why

The current experiment name suggests that supplied camera poses were estimated. Geometry validation is shared preparation, while camera pose estimation is tracking itself. Surface reconstruction is a separate consumer of depth and poses.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Control already exports supplied depth and poses | execute | CLI and integration test | experiments/03_tracking/src/run.py:112 |
| Tests import numeric experiment path dynamically | test_contracts | pytest | experiments/03_tracking/tests/test_contracts.py:27 |
| Test discovery names old location | pytest.ini and check.py | CPU checks | tools/check.py:24 |
| Reconstruction accepts depth and poses | experiment README | task 04 | experiments/04_reconstruction/README.md:11 |

Move directories without rewriting run contents. Split existing README at its camera-estimation plan. Describe feature matching, pose solution, surface integration, object identity, backend placement and pose revisions. Update active links and open scopes; closed receipts retain historical evidence paths with a relocation note in the task index.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| experiments/shared/runs.py | verify_run and HTML | relative artifact paths and SHA256 hashes | yes; move whole run directories without changing bytes |
| experiments/03_tracking/src/run.py:112 | control CLI | supplied metric depth and poses, CPU only | source relocates; algorithm unchanged |

Source of truth: existing run inventories remain unchanged. No concurrent process or GPU workload. Move only verified workspace directories into absent destinations. If interrupted, inspect source/destination before continuing. Fresh checkout uses new module command and CPU checks. Old module command is intentionally retired; historical source snapshots retain old paths and can be reproduced from their snapshots.

## Hyperparameters

hyperparameters n/a: path relocation only; existing HYPERPARAMETERS and all scientific settings unchanged. No dataset experiment run requested.

## Verification

Existing integration and CLI tests must pass at their new import locations. Existing two local runs must verify with 124 and 130 artifacts after relocation. Scan active source/docs/open tasks for obsolete folder references and check local README links. Baseline 1 mixed control/estimation owner; target 0. Have relocated imports and tests independently reviewed.

## Receipts

| field | value |
|---|---|
| closing commit | No commit requested; working-tree changes based on 80d4927600bb290040d75d99379d93bb46315451 |
| files changed | Geometry source/tests/runs relocated; estimation README split out; reconstruction folder renamed; root/experiment/shared/task READMEs, check.py, pytest.ini and open task 04/05/09 paths updated |
| test | 62 CPU tests passed via .venv-colmap/Scripts/python.exe -B tools/check.py -q; Ruff and Black pass; new CLI --help works; local README target scan has 0 missing files |
| before / after | 1 mixed control/estimation folder -> 0; 2 saved complete runs still validate with 124 and 130 artifacts |
| result | PASS. Code review found a stale Task03 link; fixed and all active README targets checked. Fresh diff review found no reproducible defects and independently verified both moved runs. No GPU work or new dataset experiment performed. |

Reviewer CPU invocations could not use the sandbox external temporary directory (Windows ACL PermissionError). The parent ran the full suite successfully with the established escalation/environment. Existing source snapshots and closed receipts retain historical paths; old module command is intentionally replaced by experiments.geometry_validation.src.run. No follow-up remains for this relocation. Board audit oversized-file findings concern pre-existing downloaded third-party code outside this scope.
