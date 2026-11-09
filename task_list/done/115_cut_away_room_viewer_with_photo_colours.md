---
id: "115"
title: Cut-away room viewer with photo colours
status: done
files:
  - src/live/fragments.py
  - src/live/tests/test_fragments.py
  - src/live/room_build.py
  - tools/demos/capture_scene.py
  - tools/demos/tests/test_capture_scene.py
  - tools/demos/web/viewer.js
  - tools/demos/web/page_splats.js
  - src/live/README.md
created: 2026-11-08
---
# Cut-away room viewer with photo colours

## Goal

See the 15 October room from inside: photo colours, near walls and ceiling hidden when seen from behind, ceiling and floor height sliders

## Plan

1. RED tests: fragments keep fused colour; viewer normals face the nearest camera and photo colours are used. 2. Fragments.colours(); room_build writes a coloured surface.ply. 3. capture_scene: photo colours, normals turned to nearest camera, height range. 4. viewer.js: one-way splats and height clip; page_splats.js controls. 5. Rebuild far4.0 at 3 cm display cells with frames; screenshot outside, top and inside views.

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
- src/live/README.md (+95 -0, 184 lines)
- src/live/fragments.py (+9 -1, 79 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+136 -0, 136 lines)
- src/live/tests/test_fragments.py (+9 -0, 63 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+34 -0, 34 lines)
- tools/demos/capture_scene.py (+90 -17, 221 lines)
- tools/demos/tests/test_capture_scene.py (+67 -0, 184 lines)
- tools/demos/web/page_splats.js (+27 -3, 116 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `pytest tools/demos/tests src/live/tests -> 63 passed (3 new: fused colour kept; photo colours and normals facing the nearest camera, 2 cases); ruff on changed Python -> clean; node --check viewer.js and page_splats.js -> ok; room_build far4.0 -> exit 0; capture_scene --voxel 0.03 -> 211,242 splats, 12.62 MB; headless Chromium screenshots of outside, cut-away, top, two bookmarks and timeline -> no console errors, ceiling hidden from above, bookmark views match the photos`
- cost: 6 min from begin to finish; Claude tokens 2,952,670 (fresh input 47,524, cache read 2,882,289, output 22,857; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.15 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 16 in 4898 words: same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items", bold-labels "7 items"

## Left over

Close range (under about 0.5 m) still smears: 3 cm discs and a 2 cm volume. Walls wavy or doubled and the floor band remain from Task113. No walk (WASD) camera yet. Not committed.
