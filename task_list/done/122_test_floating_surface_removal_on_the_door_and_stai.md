---
id: "122"
title: Test floating-surface removal on the door and stair echoes
status: done
files:
  - src/live/clean.py
  - src/live/tests/test_clean.py
  - src/live/denoise_trial.py
  - src/live/tests/test_denoise_trial.py
  - tools/demos/cleanup_scene.py
  - tools/demos/tests/test_cleanup_scene.py
  - research/surface_denoising/README.md
  - learning/05_dense_surfaces.md
  - src/live/README.md
created: 2026-11-08
---
# Test floating-surface removal on the door and stair echoes

## Goal

Measure whether outlier removal, small-cluster removal and a vote with far see-through evidence remove the hallway-door and staircase echoes, scored on sight lines from those views and checked by eye

## Plan

1. Tests: outlier, radius and cluster filters drop an isolated point and a small patch; focus-window blocked share. 2. clean.keep_after; denoise_trial variants with post filters and far-evidence vote; per-view scores for frames near 65 (door) and 420 (stairs). 3. Run on the 15 October walk, CPU only. 4. Screenshots from the door and stair cameras, before and after. 5. Report results plainly.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+2 -0, 51 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+46 -0, 160 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+11 -0, 199 lines)
- research/README.md (+3 -1, 241 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+92 -0, 92 lines)
- research/surface_denoising/README.md (+259 -0, 259 lines)
- src/live/README.md (+99 -0, 188 lines)
- src/live/clean.py (+119 -0, 119 lines)
- src/live/denoise_trial.py (+278 -0, 278 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+13 -1, 83 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+207 -0, 207 lines)
- src/live/tests/test_clean.py (+67 -0, 67 lines)
- src/live/tests/test_denoise_trial.py (+38 -0, 38 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+20 -0, 74 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+65 -0, 65 lines)
- tools/demos/capture_scene.py (+128 -20, 256 lines)
- tools/demos/cleanup_scene.py (+88 -0, 88 lines)
- tools/demos/tests/test_capture_scene.py (+87 -0, 204 lines)
- tools/demos/tests/test_cleanup_scene.py (+19 -0, 19 lines)
- tools/demos/web/page_splats.js (+85 -3, 174 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `python -B -m pytest -q src/live/tests/test_clean.py src/live/tests/test_denoise_trial.py -> 13 passed; this session's research addition: 4 downloaded PDFs start with %PDF-, 2DGS post_process_mesh read from GitHub (keeps 1,000 largest pieces, min 50 triangles), Westenberg 2007 DOI matches its title in Crossref`
- cost: 8 min from begin to finish; Claude tokens 10,559,242 (fresh input 162,110, cache read 10,339,405, output 57,727; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.18 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 29 in 10156 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Trial results in outputs/denoise_trial_093913_v4/results.json (sor, radius, clusters, clusters_3cm, vote variants) are not yet written up in research/surface_denoising/README.md; the v5 run log stops after loading weights, with no results; before/after screenshots from the door (frame 65) and stair (frame 420) cameras not checked; untested idea: drop a whole piece when most of its points are seen through by the visibility vote
