---
id: "67"
title: Track the camera without depth so depth scale errors cannot become camera motion
status: open
priority: HIGH
type: experiment
approval_status: owner asked 2026-10-08 to record this idea; not yet planned in detail or approved to start
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - src/walkthrough/steps/tracking.py
  - src/walkthrough/tests/**
docs:
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: "Task65 runs, outputs/task65_runs/clip30/* (30 TUM xyz frames, CPU)"
  field: "camera position RMSE"
  baseline_value: "218 mm raw Depth Anything with Open3D RGB-D odometry; 113 mm with the Task65 overlap chain; 21 mm with Kinect depth"
  target: "to be set when planned"
created: 2026-10-08
last_updated: 2026-10-08
superseded_by: null
---

# Task 67 — Track the camera without depth

## In plain English

The camera tracker works out where the camera moved by lining up each frame's depth with the next. When the depth model gets a frame's size wrong, the tracker explains the error by moving the camera. A tracker that uses only the images can tell how the camera turned and which way it moved, and keeps one unknown overall size for the whole walk instead of a new error every frame. This task tests such a tracker on the recorded data, with the overall size set once (later from the phone's own motion tracking).

## What

The owner's question (8 October 2026): does Open3D need depth to estimate camera motion? Answer recorded here:

- Open3D RGB-D odometry (the current `CpuOdometry`) lifts frame A's pixels into 3D with A's depth and fits the motion that aligns them with frame B. Depth errors become motion errors. Task65 measured this: Depth Anything's size jumped 1.39 → 1.62 at frame 16 of the 30-frame xyz clip and camera error jumped 147 → 337 mm in the same frame (rank correlation of size jumps with camera-error jumps 0.73).
- From images alone (feature matches, essential matrix, triangulation, PnP) the rotation is fully recoverable and the translation only up to one overall scale. Monocular SLAM and structure from motion (ORB-SLAM3 monocular, DPVO, COLMAP) give a camera path and sparse points with one unknown scale per run that drifts slowly; it cannot read a depth-size jump as motion.
- Still needed from elsewhere: metric size (phone visual-inertial tracking such as ARCore, a known distance, or the depth model's median size) and dense surfaces (per-frame depth scaled to the tracked points, or multi-view stereo).
- Phone design this points to: camera path from ARCore (image plus IMU, metric); the depth model only fills in dense surfaces, scaled per frame to ARCore's points.

Proposed experiment: a new `TrackingMethod` beside `CpuOdometry` that uses images only (OpenCV corner tracking, essential matrix and PnP against triangulated points), with one run-wide scale from the depth model's median, compared on the Task65 clips (30-frame xyz, full-length xyz and desk at every 2nd frame) against `CpuOdometry` with raw Depth Anything, with the Task65 overlap chain and with Kinect depth. Check licences before considering ORB-SLAM3 (GPLv3) or DPVO (GPU).

## Why

Task65 showed depth-based tracking is where per-frame depth size errors do their damage; the triangulated-scale run on full xyz drifted until the points spanned 550 m.

## How

To be planned (reuse table, hyperparameters, invariants, plan review) before `task.js start`.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

- Filed 2026-10-08 at the owner's request during Task65.
