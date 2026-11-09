---
id: "113"
title: Build the 15 October room cloud from ARCore-depth frames
status: done
files:
  - src/live/room_build.py
  - src/live/tests/test_room_build.py
  - src/live/README.md
created: 2026-11-07
---
# Build the 15 October room cloud from ARCore-depth frames

## Goal

One offline room cloud and 3D viewer from the 144 ARCore-depth frames: upright learned depth fitted to ARCore depth on an 8x6 grid

## Plan

1. Test the grid size fit. 2. Module: read session, track anchors, upright depth, grid fit, fuse with Fragments. 3. Run at 4.0 m and 2.5 m range; score against ARCore floor. 4. Build viewers. 5. Document in src/live/README.md.

## Files

- PROJECT_PLAN.md (+254 -0, 254 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- research/README.md (+1 -1, 239 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- src/live/README.md (+74 -0, 163 lines)
- src/live/orientation_control.py (+117 -0, 117 lines)
- src/live/room_build.py (+107 -0, 107 lines)
- src/live/tests/test_orientation_control.py (+35 -0, 35 lines)
- src/live/tests/test_room_build.py (+34 -0, 34 lines)

## Checked

- `pytest src/live/tests -> 20 passed (3 new in test_room_build.py); ruff -> clean; held-out ARCore pixels on 144 frames -> median AbsRel 0.065 one size, 0.044 8x6 grid; room_build --far 4.0 and --far 2.5 -> exit 0, 144 fused, 3 skipped; vs ARCore floor: 5.2% / 5.4% points >10 cm below (one size on same frames 5.1%); 2.5 m dominant plane is the floor; capture_scene viewers -> exit 0, 42,503 and 53,355 splats`
- cost: 4 min from begin to finish; Claude tokens 1,841,469 (fresh input 15,773, cache read 1,816,337, output 9,359; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.45 (was n/a (no functions))
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 16 in 4483 words: same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items", bold-labels "7 items"

## Left over

Grid fit does not improve the fused floor (still a ~30 cm band, some doubled walls); next candidates: fuse ARCore depth directly where present, or offline SfM reference. Viewer photos still sideways (display only). Task112 (upright in live processor) still a stub. Not committed.
