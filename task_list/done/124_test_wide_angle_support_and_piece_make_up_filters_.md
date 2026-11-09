---
id: "124"
title: Test wide-angle support and piece make-up filters on the door and stair echoes
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
  - learning/methods_inputs_and_outputs.md
  - src/live/README.md
created: 2026-11-08
---
# Test wide-angle support and piece make-up filters on the door and stair echoes

## Goal

Remove echo layers that only one standing spot supports, using COLMAP's triangulation-angle rule and PCL-style conditional pieces, CPU only, and show the result in the clean-up viewer

## Plan

1. Tests first: wide-angle support, piece make-up test, focus-window coverage, extra viewer cameras. 2. clean.wide_support and clean.piece_majority; trial variants; door and stair coverage score. 3. Run the trial on the 15 October walk with the GPU hidden. 4. Rebuild the viewer with door and stair cameras; screenshots before and after. 5. Merge results with the Task122 write-up and the chain-linking research.

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
- research/surface_denoising/README.md (+329 -0, 329 lines)
- src/live/README.md (+101 -0, 190 lines)
- src/live/clean.py (+168 -0, 168 lines)
- src/live/denoise_trial.py (+305 -0, 305 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+13 -1, 83 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+207 -0, 207 lines)
- src/live/tests/test_clean.py (+108 -0, 108 lines)
- src/live/tests/test_denoise_trial.py (+46 -0, 46 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+20 -0, 74 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+65 -0, 65 lines)
- tools/demos/capture_scene.py (+128 -20, 256 lines)
- tools/demos/cleanup_scene.py (+126 -0, 126 lines)
- tools/demos/tests/test_capture_scene.py (+87 -0, 204 lines)
- tools/demos/tests/test_cleanup_scene.py (+33 -0, 33 lines)
- tools/demos/web/page_splats.js (+85 -3, 174 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `python -B -m pytest -q src/live/tests tools/demos/tests -> 94 passed (new: spots rule far/near, piece make-up with corner strip, behind score, viewer bookmarks); ruff on changed Python -> clean; denoise_trial on the 15 October walk, CPU with CUDA_VISIBLE_DEVICES='' -> 22 variants in 157 s, the 16 earlier variants identical to the v5 run; spots rule removed 114,011 points (17%) with ARCore coverage 84.9% unchanged, far behind-surface 14.0% to 10.7%, door behind 42.6% to 40.7%; viewer pages loaded in headless Chromium, no console errors or network requests; camera and top views checked by eye; relative links in 4 changed docs -> 81 checked, 0 missing`
- cost: 16 min from begin to finish; Claude tokens 11,952,818 (fresh input 90,224, cache read 11,808,938, output 53,656; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.18 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 31 in 11697 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Door echoes remain: several standing spots agree on wrong far sizes, so the fix is consistent far depth at fusion time (multi-view stereo along ARCore's path; measure CPU cost first). Spots rule not in the live processor. Screenshot and top-slice scripts stay in the session scratchpad, not the repo. Not committed.
