---
id: "77"
title: Reorder the walkthrough so camera tracking comes before depth
status: stale
priority: LOW
type: experiment
approval_status: filed 2026-10-13; start only if Tasks 72 and 76 show the image-only design is clearly better; not approved to start
blocked_by: ["72", "76"]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - src/walkthrough/**
docs:
  - src/walkthrough/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: "Task76 runs"
  field: "same report as Task76, produced in one walkthrough run instead of two steps"
  baseline_value: "two-step runs (SfM experiment, then walkthrough reading its files)"
  target: "one-step run with identical numbers to the Task76 two-step run on the same clip"
created: 2026-10-13
last_updated: 2026-10-14
superseded_by: null
---

# Task 77 — Camera tracking before depth in the walkthrough

## In plain English

Today the walkthrough estimates depth first and then tracks the camera from that depth. The image-only design needs the reverse: track the camera from the images, then use the tracker's 3D points to size the depth. Task76 tests this by reading saved files. If it proves worth keeping, this task changes the walkthrough's order and contracts so the whole thing runs in one go, on recorded video and later on the phone.

## What

1. Layer order becomes capture → camera position → depth → surface → mapping → objects; the root README diagram's arrow between layers 2 and 3 flips.
2. The tracking contract takes colour frames (no depth) and returns, with each pose, the frame's observed sparse points (pixel, 3D position).
3. The depth contract gains read access to the tracking output, so a depth method can size itself to the tracker's points.
4. On the phone, ARCore supplies pose and tracked points with each frame. They can enter at the capture layer (like `PhoneExport`), with a pass-through tracking choice, so the phone path needs no separate tracker.
5. Existing choices keep working: `CpuOdometry` still needs depth, so it becomes a choice that runs after depth, or is retired with the owner's agreement; every saved run stays readable.

## Why

Only if the evidence from Tasks 72 and 76 supports it. Reordering touches every layer's contract and the runner (src/walkthrough/pipeline.py:48-68), so it is not worth doing on a guess.

## How

To be planned in full (reuse table, hyperparameters, invariants, plan review) before `task.js start`.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

-
