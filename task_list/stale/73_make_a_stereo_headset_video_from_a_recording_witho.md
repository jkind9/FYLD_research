---
id: "73"
title: Make a stereo headset video from a recording without reconstruction
status: stale
priority: MEDIUM
type: experiment
approval_status: filed 2026-10-13 from the owner's request to research the tracking problem and file tasks for the best path; not yet planned in detail or approved to start
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/07_vr_review/**
docs:
  - README.md
  - experiments/07_vr_review/README.md
  - task_list/README.md
baseline_metric:
  source: "none: no headset output exists"
  field: "side-by-side video produced; depth-layer and total fps on CPU; frame-to-frame disparity flicker on still parts of the scene; owner viewing check in the phone headset"
  baseline_value: "0 headset videos"
  target: "1 side-by-side video of a TUM recording, viewed by the owner in the phone headset, with its speed and flicker reported"
created: 2026-10-13
last_updated: 2026-10-15
superseded_by: null
---

# Task 73 — Stereo headset video without reconstruction

## Board review, 15 October 2026

Deferred headset output. Side-by-side headset video is not the current capture/reconstruction diagnosis. Task100 is an interactive 3D scene viewer, not stereo video and not completion of this task. Reopen only for a separate owner request or a justified review deliverable; keep the H.264 codec rule and check then-current runtime/licences.

The earlier plan and receipts below are historical. This review changes scheduling and ownership, not their recorded results.

## In plain English

The quickest way to turn a flat video into something that looks 3D in a headset needs no camera path at all. A depth model estimates how far away each pixel is. Each frame is then redrawn twice, once for each eye, with near things shifted more than far things. Played side by side in a phone headset, the video has depth. This task makes one such video from a recording and checks it in the headset. It gives no measurements and no free look-around: the viewer sees what the camera saw, from where the camera was.

## What

1. Try the existing open-source converter first: iw3 (part of nunif, MIT licence). It takes a video, estimates depth per frame (it supports Depth Anything V2 and Video Depth Anything, including flicker reduction) and writes side-by-side video for VR players. Record its speed on CPU.
2. Only if iw3 cannot be used (licence of the chosen weights, CPU speed, or install), write the minimum version here: per-frame depth from an existing walkthrough depth choice, a left and right view made by shifting pixels by an amount proportional to inverse depth, gaps filled from neighbours, H.264 side-by-side output (`avc1`).
3. Make one video from the TUM xyz recording, and one from a phone video when Task52 provides one. View both in the phone headset named in the root README.
4. Report fps, flicker on still parts of the scene, and the owner's comfort check (hand shake is magnified in a headset).

## Why

The owner's goal includes turning 2D video into 3D VR. Per-frame stereo is how current 2D-to-3D video converters do it, and it does not depend on solving camera tracking. It suits the phone headset the root README names, which follows head turning only. It does not replace reconstruction: measurements, object counts and looking around a site from a chosen spot still need a camera path and a fused 3D model (Tasks 67, 71 and 72).

## How

To be planned before `task.js start`. Weight licences must be checked first: several Depth Anything V2 and Video Depth Anything checkpoints are CC BY-NC 4.0 (non-commercial); the Small checkpoints are Apache-2.0. GPU use needs the owner's permission.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

- Sources: [iw3 README](https://github.com/nagadomi/nunif/blob/master/iw3/README.md); [Serrano et al. 2019, motion parallax for 360 video in VR](https://graphics.unizar.es/papers/Serrano_IEEEVR2019_VR-6dof.pdf), for why a single-viewpoint image only supports head turning.
