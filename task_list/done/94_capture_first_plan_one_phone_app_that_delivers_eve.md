---
id: "94"
title: Capture-first plan: one phone app that delivers every method's inputs to the PC
status: done
files:
  - README.md
  - learning/08_phone_and_deployment.md
  - experiments/01_camera_capture_delivery/README.md
created: 2026-10-14
---
# Capture-first plan: one phone app that delivers every method's inputs to the PC

## Goal

Record the owner's 14 October decision (capture on the phone, store and process on the PC, edge deployment later; 3D reconstruction comparison ahead of dimensions) and the exact inputs each Stream A and Stream B method needs, in the README, experiment 01 and learning chapter 8

## Plan

1. List the reconstruction methods in scope (ARCore route, ARCore raw depth, open VIO Basalt/OKVIS2 with OpenVINS as reference, visual-only stella_vslam with ORB-SLAM3 as reference, offline COLMAP, feed-forward 3D) and the inputs each reads, from experiments/open_vio, live_slam, sfm and src/live. 2. README 'What comes next': the decision, the input table, what the house walk can use today. 3. Chapter 8: a 'Capture first' section in plain words. 4. Experiment 01: pointer to the planned capture app. 5. Finish, commit only these files, push.

## Files

- README.md (+16 -0, 415 lines)
- experiments/01_camera_capture_delivery/README.md (+4 -0, 312 lines)
- learning/08_phone_and_deployment.md (+18 -0, 74 lines)
- mobile_deployments/.staging-smoke_20261004_b-5ed74fb9cbd244209ffd4e82559bf89e/README.md (+7 -0, 7 lines)
- mobile_deployments/.staging-smoke_20261004_b-5ed74fb9cbd244209ffd4e82559bf89e/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/camera_20261004_camera_redmi_run6/README.md (+7 -0, 7 lines)
- mobile_deployments/camera_20261004_camera_redmi_run6/test1_mobile.apk (+0 -0, 0 lines)
- mobile_deployments/camera_task52_camera_java_review_20261006_02/README.md (+7 -0, 7 lines)
- mobile_deployments/camera_task52_camera_java_review_20261006_02/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_accuracy_20261014/README.md (+9 -0, 9 lines)
- mobile_deployments/phonecheck_accuracy_20261014/fyld-phonecheck-accuracy.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk.bin (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_archcheck/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_archcheck/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_final/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_final/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_reviewed/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_reviewed/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_smoke_20261004_c/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_smoke_20261004_c/unnamed_dist_1-debug.apk (+0 -0, 0 lines)

## Checked

- `no test exists: documentation only; method inputs read from experiments/open_vio/README.md, live_slam, sfm and src/live`
- cost: 1 min from begin to finish; Claude tokens 1,254,760 (fresh input 5,289, cache read 1,245,645, output 3,826; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 2 in 1301 words: same-opening "the", bold-labels "5 items"

## Left over

Task95 (merged capture app) to build; owner's house walk
