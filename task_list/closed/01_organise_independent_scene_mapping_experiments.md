---
id: "01"
title: Organise independent scene mapping experiments
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/README.md
plan_reviewed: 2026-10-01 PASS
files:
  - README.md
  - experiments/**/README.md
  - src/README.md
  - src/fyld_scene_mapping/*.py
  - scripts/*.py
  - tests/*.py
  - test.py
  - benchmark.py
  - pyproject.toml
  - .github/**
  - docs/**
  - environments/**
  - .gitignore
  - archive/**
  - task_list/**
  - research/README.md
  - research/roadmap.md
  - research/sources/README.md
  - research/sources/13_open3d_rgbd.md
  - research/sources/15_tum_rgbd.md
  - data/**
docs:
  - README.md
  - experiments/README.md
  - archive/task00_prototype/README.md
baseline_metric:
  source: task_list/archive/00_finish_and_validate_the_phase_1_scene_mapping_prot.md
  field: independent experiment plans
  baseline_value: "0 independent experiment directories"
  target: "5 independent plans; 0 missing active local links"
created: 2026-10-01
last_updated: 2026-10-01
superseded_by: null
supersedes: ["00"]
---

# Task 01: organise the research experiments

## In plain English

Preserve the first prototype and make room for five independent experiments. Explain what each piece takes in, produces and tests. Keep camera capture separate from the choice of where depth processing runs. Remove disposable clutter while retaining results and recovery material.

## What

Archive the first implementation, old deployment proposals, environment snapshot and outputs. Keep research and datasets accessible. Check remaining harness staging material and workspace links without altering the external shared harness. Create five README plans and an index; leave active src with a README and no implementation. Preserve protected recovery copies in the ignored archive.

## Why

The user has changed direction from an integrated prototype to independent experimental pieces. Capture, depth, tracking, 3D fusion and map projection must be testable with recorded inputs and controlled references. No deployment location should become part of a method's required interface.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Earlier prototype owns the combined pipeline | experiments.run_experiment | archived benchmark.py and test.py | archive/task00_prototype/src/fyld_scene_mapping/experiments.py:45 |
| Stereo/mobile evidence is collected already | HiMoDepth source note | new stereo/capture plans | research/sources/02_himodepth.md:1 |
| Original acceptance remains unfinished | Task 00 receipts | archived prototype readers | task_list/archive/00_finish_and_validate_the_phase_1_scene_mapping_prot.md:119 |

- Archive Task 00 as superseded; retain unfinished validation explicitly.
- Preserve first-party files and result files with a before/after SHA256 inventory; move rather than rewrite original code.
- Create five plans: camera capture/delivery, stereo depth, tracking, reconstruction, bird's-eye mapping.
- Record available phones without claiming camera support or assuming the Redmi variant.
- Separate recorded/live input and phone/desktop/backend placement.
- Remove named disposable caches after resolved-path checks within the workspace. Preserve harness backups without following junctions.
- Review plans and final repository layout independently.
- User expanded scope to dataset selection and supplied camera/streaming leads, then selected python-for-android for the future phone test app. Acquire the small Middlebury starter with bounded official downloads, provenance and safe extraction; preserve original TUM data. Record phone packaging as a plan only.

## Invariants and recovery

Source of truth: retained source bytes, result artifacts and research references. No input dataset, result or external harness content is deleted. A move interruption leaves either the original or archive path; inspect both before retry. Inventory maps old relative paths to new paths and hashes. Harness junction removal is nonrecursive and operates only on the link. Environments stay at original paths because moving virtual environments breaks them. No service, deployment or mobile test is introduced.

## Hyperparameters

hyperparameters n/a: documentation and file reorganisation only; no experiment is executed and no tunable value is selected.

## Verification

Contract: exactly 5 experiment directories each with README; all active root/research/experiment/src document links resolve; every inventoried moved first-party and result file retains its hash; external shared harness exists after junction removal.

Before: 0 independent experiment directories. Target: 5 plans, 0 missing active local links, 0 changed inventoried prototype bytes. Fresh review checks independent interfaces and honest prototype status.

tests n/a: no implementation changes; integrity and document contract checks replace runtime tests for the archive operation.

## Receipts

| field | value |
|---|---|
| closing commit | Not applicable: workspace has no project Git repository |
| files changed | Root/research README and roadmap; five experiment plans plus dataset guide; data README and Middlebury acquisition/extraction receipts; src README; archived prototype and Task 00 receipts; ignore rules |
| verification | 5 numbered experiment directories; 42 active documents with 0 broken local links; 93 moved files match bytes and SHA256; src contains 0 Python files; both reference checkouts clean at pinned commits; task lint 0 errors/0 warnings |
| before / after | 0 independent plans to 5; 0 inventoried prototype byte changes; 15 Middlebury labelled stereo pairs acquired plus 15 unlabelled test pairs; 44,493,200 compressed bytes and 50,105,243 extracted bytes |
| review | Independent modular-plan and cleanup reviewers approve after fixes for matched stereo sequences, segment/world-frame boundaries, archived source attribution and roadmap alignment |
| result | Completed reorganisation and planning. Task 00 is archived as superseded, without claiming its unfinished runtime validation passed. New experiment implementation has not started. |

Recovery relocation waiver: a protected partial COLMAP move copy remains under ignored archive/task00_prototype/third_party. Both original root checkouts were restored and verified clean; no unique source or result was lost. Moving the recovery copy was denied by filesystem access even after elevation, so retain it without further mutation. Harness staging files, link and root caches were absent at final inspection; the external harness still exists and was not edited by this task. Existing environments remain at their original paths.

Board audit records 103 oversized files in unchanged third-party reference checkouts and one informational tests waiver. No first-party implementation was added or changed; upstream file-size findings are outside this reorganisation and are not waived for future first-party work.
