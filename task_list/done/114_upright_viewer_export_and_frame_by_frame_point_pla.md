---
id: "114"
title: Upright viewer export and frame-by-frame point placement
status: done
files:
  - src/live/orientation_control.py
  - src/live/tests/test_orientation_control.py
  - src/live/room_build.py
  - tools/demos/capture_scene.py
  - tools/demos/web/page_splats.js
  - tools/demos/web/page_timeline.js
  - tools/demos/tests/test_capture_scene.py
  - src/live/README.md
created: 2026-11-07
---
# Upright viewer export and frame-by-frame point placement

## Goal

Viewer photos and camera views upright per frame; a timeline that shows each ARCore-depth frame's points, camera and photo

## Plan

1. Tests: per-frame quarter turns and turned camera projection equivalence; upright bookmarks; timeline embedded. 2. orientation_control: quarter_turns, turned_camera. 3. room_build: per-frame turns, save frames.npz. 4. capture_scene + page_timeline.js. 5. Rebuild 2.5 m room and viewer; check in browser.

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
- src/live/README.md (+89 -0, 178 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+134 -0, 134 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+34 -0, 34 lines)
- tools/demos/capture_scene.py (+53 -11, 190 lines)
- tools/demos/tests/test_capture_scene.py (+46 -0, 163 lines)
- tools/demos/web/page_splats.js (+1 -0, 93 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)

## Checked

- `pytest tools/demos/tests src/live/tests -> 60 passed (6 new: 4 quarter-turn cases + 4 turned-camera projection cases counted as parametrised, 2 viewer); ruff on changed files -> clean; node --check page_timeline.js -> ok; room_build --far 2.5 -> exit 0, 144 fused, all turns_1; capture_scene --frames -> 8.33 MB; tools.demos.screenshot bookmark and timeline clicks -> ok, no console errors or requests, upright photos seen in screenshots`
- cost: 6 min from begin to finish; Claude tokens 4,424,396 (fresh input 44,417, cache read 4,354,841, output 25,138; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.28 (was 0.35)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 16 in 4731 words: same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items", bold-labels "7 items"

## Left over

Splat mode from a bookmark camera renders close-up blobs (points mode clearer); timeline points are pre-anchor-correction. Floor band and doubled walls from Task113 remain. Ruff errors in untouched files (processor.py, stream.py, test_sizing.py, test_stream.py) pre-exist. Not committed.
