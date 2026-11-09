---
id: "120"
title: Merge the far-depth note into the denoising report and run first clean-up and sizing trials
status: done
files:
  - research/surface_denoising/README.md
  - research/dense_surface_fusion/other_systems.md
  - research/dense_surface_fusion/README.md
  - learning/05_dense_surfaces.md
  - src/live/clean.py
  - src/live/tests/test_clean.py
  - src/live/denoise_trial.py
  - src/live/tests/test_denoise_trial.py
  - src/live/room_build.py
  - src/live/tests/test_room_build.py
  - src/live/README.md
  - PROJECT_PLAN.md
  - research/README.md
  - src/live/fragments.py
  - src/live/tests/test_fragments.py
created: 2026-11-08
---
# Merge the far-depth note into the denoising report and run first clean-up and sizing trials

## Goal

One report for denoising and far-depth sizing; measured effect of edge and angle masks, near-first weights, a visibility vote and tracked-point sizing on the 15 October walk, scored against held-out ARCore tracked points

## Plan

1. Merge other_systems.md into research/surface_denoising, fixing the Open3D weight claim; relink. 2. Tests first: edge mask, grazing mask, band repeats, visibility vote, sight-line hits, tracked-point fallback. 3. clean.py and denoise_trial.py; grid_size fallback parameter. 4. Run baseline and variants once each on the 15 October walk. 5. Results into the report, learning chapter 5, src/live README and PROJECT_PLAN.

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
- research/surface_denoising/README.md (+224 -0, 224 lines)
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
- tools/demos/capture_scene.py (+95 -17, 226 lines)
- tools/demos/tests/test_capture_scene.py (+68 -0, 185 lines)
- tools/demos/web/page_splats.js (+69 -3, 158 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `CUDA_VISIBLE_DEVICES= pytest src/live/tests -> 48 passed (10 new); ruff on changed files -> clean; denoise_trial on 20261015_093913_walk, CPU only -> 7 variants in 81 s, repeat run identical; vote cut blocked sight lines 9.2%->1.8% (<2.5 m) and 8.6%->4.1% (>=2.5 m), masks and near-first weights raised them; refactored room_build -> 676,855 points, same as Task116's run; links.py -> 0 missing`
- cost: 16 min from begin to finish; Claude tokens 12,987,630 (fresh input 95,386, cache read 12,819,103, output 73,141; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.16 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 29 in 9553 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Vote not yet in the live processor; not checked on ICL ground truth. Far sizing needs a size that varies with distance (one tracked size per frame put 4.4x as many points below the floor). Floor band cause unknown. Walk has 1.2% of pixels beyond 4 m, so 10 m rooms untested. 6 pre-existing ruff errors in processor.py, stream.py, test_sizing.py, test_stream.py. Not committed.
