---
id: "123"
title: Write up the Task122 echo and floater results
status: done
files:
  - research/surface_denoising/README.md
created: 2026-11-08
---
# Write up the Task122 echo and floater results

## Goal

Record the finished Task122 results; another session closed Task122 while its trial was still running

## Plan

1. Results table and findings in research/surface_denoising. 2. Camera screenshots checked. 3. Close with the correct left-over.

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
- research/surface_denoising/README.md (+284 -0, 284 lines)
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

- `denoise_trial v5, 16 variants, CPU only -> best combination halves blocked share at the door (6.4%->2.6%) and stairs (8.2%->4.0%); no filter removes the echoes; camera screenshots from frames 65 and 420 with SwiftShader -> haze cleared, staircase mostly deleted, door echoes unchanged; pytest src/live/tests tools/demos/tests -> 89 passed; links.py -> 0 missing`
- cost: 0 min from begin to finish; Claude tokens 506,809 (fresh input 746, cache read 505,049, output 1,014; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.18 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 30 in 10442 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Echoes need consistent far depth: multi-view stereo along ARCore's path for depth beyond 2.5 m (measure CPU cost first). Observation count thins the floor band but cuts 19-39% of points. Combined filters delete the open staircase. Learning chapter 5 not updated (another session editing it). Not committed.
