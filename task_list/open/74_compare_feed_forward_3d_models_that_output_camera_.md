---
id: "74"
title: Compare feed-forward 3D models that output camera poses and surfaces together
status: open
priority: MEDIUM
type: experiment
approval_status: filed 2026-10-13 from the owner's request to research the tracking problem and file tasks for the best path; raised to MEDIUM 2026-10-13 after the owner asked for current methods beyond COLMAP; Depth Anything 3 Small can start on CPU, the rest need GPU permission from the owner; not yet planned or approved to start
blocked_by: ["67"]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/03_camera_pose_estimation/experiments/**
docs:
  - experiments/03_camera_pose_estimation/README.md
  - task_list/README.md
baseline_metric:
  source: "Task67 COLMAP rows and Task71 true-pose surface rows"
  field: "best-fit scaled camera error, surface distance to the Kinect-and-true-pose surface, fitted size, fps, peak GPU and host memory"
  baseline_value: "per Task67 and Task71 results"
  target: "to be set when planned"
created: 2026-10-13
last_updated: 2026-10-13
superseded_by: null
---

# Task 74 — Feed-forward 3D models

## In plain English

A newer family of models takes a batch of video frames and outputs, in one pass, a 3D point for every pixel and the camera position for every frame. Some also estimate real-world size. They have no separate tracking step, which is close to the owner's question of whether we need to estimate the camera at all. Most need a GPU, and their licences are mixed. This task scores the usable ones on the same recordings as Task67.

## What

Candidates, with licences as found on 2026-10-13 (recheck at planning):

| Model | Output | Licence and notes |
|---|---|---|
| Depth Anything 3 Small / Base | Depth and camera poses from any number of views | Apache-2.0 for Small (0.08B parameters) and Base (0.12B); Large and Giant are CC BY-NC. Small is the first candidate: permissive and may run on CPU |
| DROID-SLAM | Learned SLAM on ordered video, with loop closure | BSD-3; 18 mm on TUM fr1/desk; GPU |
| DPVO / DPV-SLAM | Learned visual odometry and SLAM | MIT; 18 mm on TUM fr1/desk; GPU |
| FastMap | Structure from motion from a COLMAP database, GPU first-order optimisation | MIT; authors claim up to 10 times faster than COLMAP and GLOMAP at comparable accuracy; speed matters for thousands of images, not our 400 |
| MapAnything | Metric 3D points, camera poses and calibration from images | Apache-2.0 only for the separate `facebook/map-anything-apache-v1` checkpoint; the default checkpoint is CC BY-NC 4.0 |
| VGGT | Poses, calibration, depth and points for many frames | Only the `VGGT-1B-Commercial` checkpoint allows commercial use, under its own acceptable-use licence, after an application form |
| VGGT-SLAM | VGGT batches joined into a SLAM map | Code BSD-2; needs the VGGT commercial checkpoint |
| MASt3R-SLAM, MASt3R-SfM, VGGSfM | SLAM and structure from motion on learned two-view or multi-view priors | Non-commercial (CC BY-NC-SA 4.0 and CC BY-NC 4.0). Research reference only unless the owner rules the licence acceptable. MASt3R-SLAM: 16 mm on TUM fr1/desk |

Run each usable one on the full xyz and desk clips (in overlapping batches where memory requires) and score as Task67 and Task71 do. Start with Depth Anything 3 Small on CPU; the GPU rows wait for the owner's permission.

## Why

If one of these reaches COLMAP's camera accuracy and Kinect-like surfaces at 1 fps or better, it could replace both the tracker and the depth model on the hosted side. It sits after Task67 because a classic baseline is needed to judge them, and most need GPU permission. The phone route still takes camera motion from ARCore.

## How

To be planned before `task.js start`. GPU use needs the owner's explicit permission (owner, 8 October 2026). The 1 fps floor applies.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

- Sources: [MapAnything Apache checkpoint](https://huggingface.co/facebook/map-anything-apache-v1), [VGGT-SLAM](https://arxiv.org/abs/2505.12549), [MASt3R-SLAM](https://arxiv.org/abs/2412.12392).
