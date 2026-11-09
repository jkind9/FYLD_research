---
id: "126"
title: Keep the room's largest pieces after the visibility vote in the room build
status: done
files:
  - src/live/clean.py
  - src/live/tests/test_clean.py
  - src/live/room_build.py
  - src/live/tests/test_room_build.py
  - src/live/denoise_trial.py
  - src/live/README.md
  - research/surface_denoising/README.md
  - learning/05_dense_surfaces.md
created: 2026-11-08
---
# Keep the room's largest pieces after the visibility vote in the room build

## Goal

Room build drops points that views see through (vote 0.5) and keeps only the 50 largest touching-cell pieces of at least 5,000 points (owner, 8 Nov), fast enough to time per stage

## Plan

1. RED tests: largest_pieces keeps big touching pieces, drops small and far ones, honours the cap; room build vote views use corrected poses. 2. clean.largest_pieces on a filled-cell grid; VOTE_FAR_M moves to clean. 3. room_build applies vote then pieces, writes raw_surface.ply, surface.ply and stage times. 4. Run on the 15 October walk; compare with the tuner's 561,317. 5. Notes in src/live README, surface_denoising README, chapter 5.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+2 -0, 51 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+50 -0, 164 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+12 -0, 200 lines)
- research/README.md (+3 -1, 241 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+92 -0, 92 lines)
- research/surface_denoising/README.md (+379 -0, 379 lines)
- src/live/README.md (+110 -0, 199 lines)
- src/live/clean.py (+205 -0, 205 lines)
- src/live/cleanup_attributes.py (+51 -0, 51 lines)
- src/live/denoise_trial.py (+307 -0, 307 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+13 -1, 83 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+243 -0, 243 lines)
- src/live/tests/test_clean.py (+138 -0, 138 lines)
- src/live/tests/test_cleanup_attributes.py (+21 -0, 21 lines)
- src/live/tests/test_denoise_trial.py (+46 -0, 46 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+20 -0, 74 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+77 -0, 77 lines)
- tools/demos/capture_scene.py (+128 -20, 256 lines)
- tools/demos/cleanup_scene.py (+126 -0, 126 lines)
- tools/demos/cleanup_tuner.py (+205 -0, 205 lines)
- tools/demos/tests/test_capture_scene.py (+87 -0, 204 lines)
- tools/demos/tests/test_cleanup_scene.py (+33 -0, 33 lines)
- tools/demos/tests/test_cleanup_tuner.py (+40 -0, 40 lines)
- tools/demos/web/page_splats.js (+85 -3, 174 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/page_tuner.js (+263 -0, 263 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `python -B -m pytest -q src/live/tests tools/demos/tests -> 101 passed (new: largest pieces keep big touching pieces and drop small ones, honour the cap, bigger cells bridge wider gaps; vote views follow anchor corrections); 3 new tests failed before the code; ruff -> clean; room_build on the 15 October walk, CPU -> 676,855 fused, vote -100,086, pieces -22,702, 554,067 kept, vote 2.41 s, pieces 0.15 s, build 82 s; scratch probe on the tuner's raw room -> owner setting keeps 1 piece (561,318; next largest 4,377), 2 cm touching cells keep 554,551 in 0.13 s vs DBSCAN 1.04 s, radius 5 cm/16 removes 14,951 of which 3,764 lie outside the kept piece; capture_scene viewer on the cleaned room -> 38,421 splats, 8.35 MB`
- cost: 11 min from begin to finish; Claude tokens 7,220,638 (fresh input 872,674, cache read 6,198,924, output 149,040; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 34 in 12856 words: same-opening "it", same-opening "the", same-opening "the", same-opening "the", one-line-closer "Local outputs:  ."

## Left over

Live processor has no clean-up yet: the vote needs every fused frame's depth (cost grows with frames x points; 2.41 s for 134 frames), so live use needs per-update voting or fewer, sharper frames (blur-picking trial not filed). Owner to check the cleaned room by eye in outputs/room_build_clean_up_093913/redmi-room-15oct-clean.html; it keeps 7,250 fewer points than the tuner's 5 cm DBSCAN (small fringe pieces 8-25 cm off the room). Map's main plane is still a wall, as before the clean-up. Not committed.
