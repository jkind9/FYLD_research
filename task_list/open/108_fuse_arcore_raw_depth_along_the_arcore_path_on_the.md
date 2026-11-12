---
id: "108"
title: Fuse ARCore raw depth along the ARCore path on the 15 October walk
status: open
priority: LOW
type: experiment
blocked_by: []
blocks: []
verification_test: "src/live/tests/test_arcore_depth_fusion.py"
plan_reviewed: null
files:
  - src/live/**
  - outputs/**
docs:
  - src/live/README.md
baseline_metric:
  source: "Task106 probe, 7 November 2026"
  field: "surface built from the phone's own depth and path"
  baseline_value: "never built; 144 of 147 depth maps on the 15 October walk pass the sizing rule"
  target: "A surface from ARCore depth and poses alone, with floor orientation, wall angles and room size reported, to separate pose/axis faults from learned-depth faults"
created: 2026-11-07
last_updated: 2026-11-12
superseded_by: null
---

# Task 108: Fuse ARCore raw depth along the ARCore path on the 15 October walk

## Amendment, 12 November 2026

Deferred. After owner decision 10 ([plan](../../PROJECT_PLAN.md#owner-decisions-in-force)), a surface from ARCore depth and poses alone serves only as a comparison, and Task113 already built the 15 October room from ARCore depth. It no longer blocks Task102. Move it to `stale/` with the board tool when that is next run.


## In plain English

Build a 3D model from the phone's own depth and the phone's own camera path, with no learned depth model at all. If this model looks right, the camera path and the coordinate handling are sound, and the distortion comes from the learned depth. If it is also distorted, the fault is in the path or the coordinate handling.

## Verified inputs, 7 November 2026

- Session `20261015_093913_walk`: 147 raw-depth maps of 160 x 90 pixels with their own intrinsics (about fx 116.9, fy 117.6, cx 79.6, cy 44.1), confidence 0-255, depth in millimetres. 144 maps have at least 50 pixels with confidence 128 or more.
- Depth intrinsics are scaled from ARCore's texture intrinsics (16:9), not the 640 x 480 CPU image (4:3). `src/live/sizing.py:21-34` already maps depth pixels into the image through both intrinsics.
- Fusion owner: `src/live/fragments.py` (Open3D `ScalableTSDFVolume`, anchored fragments). Pose conversion owner: `session_v1.world_from_camera_cv` (ARCore's OpenGL camera axes to OpenCV).
- ARCore depth is another estimate, not ground truth.

## Plan

1. Write a test first with asymmetric known values: a depth pixel at a known (u, v, z) on the 160 x 90 grid, with a known pose, must land at the expected world point. It covers the OpenGL-to-OpenCV flip and the depth-grid intrinsics.
2. Add a small module under `src/live/` that reads the session, keeps confident raw-depth pixels, and fuses them with the existing `fragments.py` TSDF along `world_from_camera_cv` of the frame that carried the map. Record the depth-to-frame time gap per map; skip maps more than 100 ms older than their frame and count them.
3. Run it on the 15 October walk and save `surface.ply` under `outputs/capture_task108_093913/`.
4. Report:
   - fused maps and skipped maps;
   - dominant plane normal against ARCore's up axis (y), and the angle between the two largest near-vertical planes (walls should be about 90 degrees apart);
   - bounding-box length, width and height of the largest room-sized cluster;
   - distance between this surface and the Task107 surface where both have data (no alignment, same world frame).
5. Build the viewer for a visual check. File a follow-up for any confirmed convention fault; do not change the live processor here.

## Settings

| name | value | source |
|---|---|---|
| confidence cut-off | 128 | `src/live/sizing.py:16` (Google's suggested cut-off) |
| voxel | 0.02 m | inherited: Task99 summary `voxel_m` |
| depth range | the live processor's `DEPTH_RANGE_M` | `src/live/processor.py` |
| maximum depth-to-frame age | 100 ms | proposed by Claude 7 November 2026; needs owner confirmation before running |
| pose | ARCore camera pose of the frame carrying the depth map | proposed by Claude; the depth image's own timestamp has no separate pose |

## Finish when

The test passes, the surface exists, the figures are reported and the result says which side of the split it supports: pose and axes, or learned depth.
