---
id: "121"
title: Clean-up comparison viewer for the 15 October room
status: done
files:
  - tools/demos/capture_scene.py
  - tools/demos/web/page_splats.js
  - tools/demos/tests/test_capture_scene.py
  - tools/demos/cleanup_scene.py
  - tools/demos/tests/test_cleanup_scene.py
  - research/surface_denoising/README.md
  - src/live/README.md
created: 2026-11-08
---
# Clean-up comparison viewer for the 15 October room

## Goal

One offline HTML of the 15 October room: before clean-up, what the visibility vote removes shown in red, the cleaned room with those hidden, and the Task120 results table beside it

## Plan

1. Tests: kept surface flags removed display cells; results table lists every variant. 2. capture_scene: optional kept surface and side panel; page_splats.js: red and hide switches. 3. cleanup_scene CLI from a denoise_trial folder. 4. Build for the 15 October walk; headless Chromium check with SwiftShader (no GPU). 5. Note in the report and live README.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+2 -0, 51 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+44 -0, 158 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+10 -0, 198 lines)
- research/README.md (+3 -1, 241 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+92 -0, 92 lines)
- research/surface_denoising/README.md (+228 -0, 228 lines)
- src/live/README.md (+99 -0, 188 lines)
- src/live/clean.py (+79 -0, 79 lines)
- src/live/denoise_trial.py (+242 -0, 242 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+13 -1, 83 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+207 -0, 207 lines)
- src/live/tests/test_clean.py (+46 -0, 46 lines)
- src/live/tests/test_denoise_trial.py (+32 -0, 32 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+20 -0, 74 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+65 -0, 65 lines)
- tools/demos/capture_scene.py (+128 -20, 256 lines)
- tools/demos/cleanup_scene.py (+79 -0, 79 lines)
- tools/demos/tests/test_capture_scene.py (+87 -0, 204 lines)
- tools/demos/tests/test_cleanup_scene.py (+18 -0, 18 lines)
- tools/demos/web/page_splats.js (+85 -3, 174 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `pytest tools/demos/tests src/live/tests -> 83 passed, 1 failed: test_processor run test, the intermittent object-count race (0/25 at HEAD, appears with Task115's uncommitted fragments colour change); cleanup_scene on the 15 Oct trial -> 196,914 splats, 4.86 MB; tools.demos.screenshot with SwiftShader (no GPU) in 3 states -> ok, no console errors or requests; screenshots checked by eye; links.py -> 0 missing`
- cost: 4 min from begin to finish; Claude tokens 5,951,951 (fresh input 30,426, cache read 5,902,287, output 19,238; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.16 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 29 in 9704 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Vote may remove some real furniture (19% of points 0.1-0.76 m above floor): check on ICL ground truth. Intermittent test_processor object-count race unfixed. Viewer embeds household photos: local only. Not committed.
