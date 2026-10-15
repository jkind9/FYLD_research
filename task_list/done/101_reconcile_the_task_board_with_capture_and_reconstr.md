---
id: "101"
title: Reconcile the task board with capture and reconstruction evidence
status: done
files:
  - task_list/README.md
  - task_list/open/*.md
  - task_list/stale/*.md
  - README.md
  - task_list/archive/*.md
  - experiments/01_camera_capture_delivery/README.md
  - experiments/open_vio/README.md
  - learning/08_phone_and_deployment.md
  - learning/12_rebuilding_arcore.md
  - HARNESS_WORKFLOW_AUDIT.md
  - experiments/03_camera_pose_estimation/README.md
  - experiments/04_surface_reconstruction/README.md
  - experiments/06_object_recognition/README.md
  - research/README.md
  - experiments/README.md
created: 2026-10-15
---
# Reconcile the task board with capture and reconstruction evidence

## Goal

Make every unfinished task reflect the capture-first decision, current evidence and a justified next action.

## Plan

1. Audit all open and stale tasks against code, receipts and capture results. 2. Amend plans and dependencies, migrate superseded or deferred work and rewrite the board order. 3. Validate task states, dependencies and links, finish the review, commit and push.

## Files

- HARNESS_WORKFLOW_AUDIT.md (+1 -1, 891 lines)
- README.md (+15 -13, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+4 -2, 406 lines)
- experiments/03_camera_pose_estimation/README.md (+1 -1, 226 lines)
- experiments/04_surface_reconstruction/README.md (+1 -1, 232 lines)
- experiments/06_object_recognition/README.md (+3 -3, 236 lines)
- experiments/README.md (+2 -2, 259 lines)
- experiments/open_vio/README.md (+2 -0, 165 lines)
- learning/08_phone_and_deployment.md (+5 -3, 101 lines)
- learning/12_rebuilding_arcore.md (+2 -0, 101 lines)
- research/README.md (+1 -1, 239 lines)

## Checked

- `python -B %TEMP%/fyld_board_review_101.py -> 105 records checked across all folders, open-plan YAML and dependency DAG valid, queue covers all 10 planned tasks, 372 relative links and 43 heading anchors valid; python -B tools/check.py tools/tests -q -> 9 passed with OS-temp access; task.js ready --next -> Task102; task.js lint -> 0 errors, 3 false missing-done warnings documented; git diff --check -> clean; private session, viewer and APK git check-ignore -> ignored`
- cost: 31 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 5 in 1562 words: same-opening "task", same-opening "the", same-opening "task", same-opening "task", same-opening "task"

## Left over

Next is Task102: test the orientation hypothesis and diagnose reconstruction on the existing walk. Tasks52, 103 and 104 own capture fidelity/sustained checks, owner calibration recordings and same-walk open-tracker runs. No experiment or handset trial was run during this board review. Legacy CLI omission of done records and seven historical non-YAML values are documented; historical results remain unchanged.
