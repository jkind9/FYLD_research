---
id: "117"
title: Find why doors echo in the fresh-depth room
status: done
files:
  - src/live/depth_check.py
  - src/live/tests/test_depth_check.py
  - src/live/room_build.py
  - src/live/tests/test_room_build.py
  - research/dense_surface_fusion/README.md
  - learning/05_dense_surfaces.md
  - src/live/landmark_probe.py
created: 2026-11-08
---
# Find why doors echo in the fresh-depth room

## Goal

Measure how far fused learned depth is from ARCore tracked points by distance and by ARCore depth support, and test whether dropping unsupported cells removes the door echoes

## Plan

1. Tests: cell index matches grid_size; summary splits by support and distance. 2. depth_check: per fused frame, depth*size at tracked-point pixels against tracked depth. 3. room_build --supported-only drops pixels in cells without ARCore support. 4. Run both on the 15 October walk; screenshot the hallway door before and after. 5. Research note and learning chapter.

## Files

- PROJECT_PLAN.md (+254 -0, 254 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+15 -0, 129 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+3 -0, 191 lines)
- research/README.md (+2 -1, 240 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+88 -0, 88 lines)
- src/live/README.md (+95 -0, 184 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+9 -1, 79 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+171 -0, 171 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+9 -0, 63 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+55 -0, 55 lines)
- tools/demos/capture_scene.py (+95 -17, 226 lines)
- tools/demos/tests/test_capture_scene.py (+68 -0, 185 lines)
- tools/demos/web/page_splats.js (+69 -3, 158 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `pytest src/live/tests tools/demos/tests -> 72 passed (new: summary split, cell index, supported pixels); ruff on changed Python -> clean; depth_check on 134 fused frames -> learned/tracked 0.98-1.04 up to 3 m in supported cells, 0.84-0.86 at 3-4 m, fallback middle half 0.72-0.97 at 3-4 m; confident ARCore depth p95 2.54 m; rebuilds 4.0 m supported-only -> 73,265 splats, door single but stairs/TV/ceiling gone; 2.5 m all cells -> 151,032 splats, doorway still smears; all runs on CPU (run.py device=cpu; last rebuild with CUDA_VISIBLE_DEVICES=-1)`
- cost: 8 min from begin to finish; Claude tokens 8,330,865 (fresh input 159,531, cache read 8,123,635, output 47,699; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 19 in 6091 words: same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items", bold-labels "7 items"

## Left over

No fix yet for sizing beyond ARCore range: try ARCore tracked points as extra sizing targets, or sizing against the built surface. Door echo layers in the 2.5 m build not measured. Live processor.py still takes stale depth. Not committed.
