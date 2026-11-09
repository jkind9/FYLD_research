---
id: "116"
title: Measure where each frame puts the red cushion
status: done
files:
  - src/live/landmark_probe.py
  - src/live/tests/test_landmark_probe.py
  - research/dense_surface_fusion/README.md
  - research/README.md
  - learning/05_dense_surfaces.md
  - learning/methods_inputs_and_outputs.md
  - src/live/room_build.py
  - src/live/tests/test_room_build.py
  - tools/demos/capture_scene.py
  - tools/demos/web/page_splats.js
  - tools/demos/tests/test_capture_scene.py
created: 2026-11-08
---
# Measure where each frame puts the red cushion

## Goal

Find whether the doubled sofa comes from learned depth, ARCore depth or poses, by placing the red cushion from each frame that sees it, and collect fixes for floating surfaces

## Plan

1. Test: cushion mask picks the largest saturated red blob; offset splits into along-ray and across-ray parts. 2. landmark_probe: per frame, cushion world position from ARCore depth and from fused learned depth, camera position, fragment. 3. Run on frames 660-730 of the 15 October walk; compare with the fused red clusters. 4. Research floating-surface causes and fixes; research/dense_surface_fusion and learning/05.

## Files

- PROJECT_PLAN.md (+254 -0, 254 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+13 -0, 127 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+3 -0, 191 lines)
- research/README.md (+2 -1, 240 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+59 -0, 59 lines)
- src/live/README.md (+95 -0, 184 lines)
- src/live/fragments.py (+9 -1, 79 lines)
- src/live/landmark_probe.py (+88 -0, 88 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+146 -0, 146 lines)
- src/live/tests/test_fragments.py (+9 -0, 63 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+42 -0, 42 lines)
- tools/demos/capture_scene.py (+95 -17, 226 lines)
- tools/demos/tests/test_capture_scene.py (+68 -0, 185 lines)
- tools/demos/web/page_splats.js (+69 -3, 158 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `pytest tools/demos/tests src/live/tests -> 69 passed (new: cushion mask x2, ray split, stale depth x3, measure controls); ruff on changed Python -> clean; landmark_probe frames 660-727 -> stale-depth copy 0.68 m from fresh copy, almost all along the line of sight; ARCore tracked points -> about 0.2 m from fresh copy, about 0.9 m from stale; room_build far4.0 with MAX_DEPTH_AGE_S 0.1 -> 10 stale skipped, 134 fused; red points within 25 cm of stale copy 121 -> 0, fresh copy 1277 -> 1277; headless Chromium before/after sofa views and a two-click measurement -> no console errors, readout 1.37 m`
- cost: 12 min from begin to finish; Claude tokens 9,375,338 (fresh input 81,587, cache read 9,244,691, output 49,060; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.21 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 18 in 5680 words: same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items", bold-labels "7 items"

## Left over

Live processor.py still uses depth of any age. Cause of the 4.4 s depth lag on the phone unknown (frames 669-691). 66% of grid cells per frame use the frame-median fallback; test with fallback cells left out. Fresh copy still 0.2 m nearer than tracked points. Measure clicks pick the front-most splat within 8 px, so a floating surface in front gets picked. Not committed.
