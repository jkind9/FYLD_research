---
id: "125"
title: Clean-up tuner page: raw room with every clean-up stage on sliders
status: done
files:
  - src/live/clean.py
  - src/live/tests/test_clean.py
  - src/live/denoise_trial.py
  - src/live/cleanup_attributes.py
  - src/live/tests/test_cleanup_attributes.py
  - tools/demos/cleanup_tuner.py
  - tools/demos/tests/test_cleanup_tuner.py
  - tools/demos/web/page_tuner.js
  - research/surface_denoising/README.md
  - src/live/README.md
created: 2026-11-08
---
# Clean-up tuner page: raw room with every clean-up stage on sliders

## Goal

Let the owner tune chain linking (link distance, neighbours, piece size, largest pieces, normal rule) and the other clean-up stages by slider on the raw 15 October room, offline, each slider with a description

## Plan

1. Tests: spot evidence angles, per-point attributes, page data and parameter descriptions. 2. clean.vote_tallies and clean.spot_evidence; fuse returns its views; cleanup_attributes writes raw.ply and attributes.npz. 3. cleanup_tuner page; JS runs DBSCAN-style chain linking and radius outliers on the raw points. 4. Check JS chain result against Open3D cluster_dbscan at the trial's settings. 5. Build the 15 October page, screenshots, notes.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+2 -0, 51 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+48 -0, 162 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+12 -0, 200 lines)
- research/README.md (+3 -1, 241 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+92 -0, 92 lines)
- research/surface_denoising/README.md (+353 -0, 353 lines)
- src/live/README.md (+103 -0, 192 lines)
- src/live/clean.py (+184 -0, 184 lines)
- src/live/cleanup_attributes.py (+51 -0, 51 lines)
- src/live/denoise_trial.py (+308 -0, 308 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+13 -1, 83 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+207 -0, 207 lines)
- src/live/tests/test_clean.py (+117 -0, 117 lines)
- src/live/tests/test_cleanup_attributes.py (+21 -0, 21 lines)
- src/live/tests/test_denoise_trial.py (+46 -0, 46 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+20 -0, 74 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+65 -0, 65 lines)
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

- `python -B -m pytest -q src/live/tests tools/demos/tests -> 98 passed (new: spot evidence angles, per-point attributes, tuner parameter ranges and descriptions, page data); one earlier run had test_processor fail once and pass on 3 reruns (real-time replay under load); ruff -> clean; node --check page_tuner.js -> ok; cleanup_attributes on the 15 October walk, CPU -> 676,853 points; tuner page 17.3 MB; page set to each trial setting in headless Chromium kept within 0.13% of the trial counts (seen_3 exact; chain 5 cm 663,949 vs 663,964; 3 cm 630,272 vs 630,389), no console errors; layout checked by screenshot`
- cost: 11 min from begin to finish; Claude tokens 11,059,869 (fresh input 168,964, cache read 10,818,627, output 72,278; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 31 in 12078 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Owner to tune by eye and report settings from the page's settings box. Door echoes are still expected to need consistent far depth. Not committed.
