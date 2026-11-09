---
id: "128"
title: Run LingBot-Map on the 15 October walk on the GPU and compare it with ARCore and the room build
status: done
files:
  - experiments/lingbot_map/README.md
  - experiments/lingbot_map/prepare.py
  - experiments/lingbot_map/compare.py
  - experiments/lingbot_map/tests/test_compare.py
  - research/feed_forward_3d/lingbot_map.md
  - research/gaussian_splatting/lumina_open_source_parts.md
  - research/repositories.json
  - learning/03_camera_tracking_and_slam.md
  - learning/methods_inputs_and_outputs.md
  - experiments/lingbot_map/run.py
  - PROJECT_PLAN.md
  - experiments/lingbot_map/kv_cache_bf16.patch
created: 2026-11-08
---
# Run LingBot-Map on the 15 October walk on the GPU and compare it with ARCore and the room build

## Goal

Measure LingBot-Map's camera path, size and depth on our own walk against ARCore, so the owner can judge it as the core of the pipeline

## Plan

1. Clone at a pinned commit; conda env with torch cu128 on the RTX 5070 Ti; download weights. 2. Turn the 822 frames upright. 3. Run with saved predictions; time it. 4. Fit one size to ARCore camera centres; report path agreement. 5. Depth vs ARCore tracked points by distance band, as Task117. 6. Point cloud PLY and viewer for the owner. 7. Notes in research and learning.

## Files

- PROJECT_PLAN.md (+288 -0, 288 lines)
- README.md (+7 -5, 423 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/02_stereo_depth/README.md (+2 -1, 312 lines)
- experiments/04_surface_reconstruction/README.md (+2 -0, 234 lines)
- experiments/lingbot_map/README.md (+87 -0, 87 lines)
- experiments/lingbot_map/compare.py (+176 -0, 176 lines)
- experiments/lingbot_map/run.py (+117 -0, 117 lines)
- experiments/lingbot_map/tests/test_compare.py (+39 -0, 39 lines)
- experiments/sfm/README.md (+7 -2, 268 lines)
- learning/00_glossary.md (+7 -0, 56 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+14 -0, 109 lines)
- learning/04_structure_from_motion.md (+12 -0, 97 lines)
- learning/05_dense_surfaces.md (+83 -0, 197 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+33 -1, 220 lines)
- research/README.md (+4 -1, 242 lines)
- research/camera_tracking_and_slam/README.md (+6 -0, 48 lines)
- research/camera_tracking_and_slam/colmap_based_slam.md (+89 -0, 89 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+108 -0, 108 lines)
- research/dense_surface_fusion/live_dense_reconstruction_2010.md (+52 -0, 52 lines)
- research/dense_surface_fusion/mobile3drecon.md (+61 -0, 61 lines)
- research/dense_surface_fusion/mobile_object_reconstruction_2015.md (+51 -0, 51 lines)
- research/dense_surface_fusion/triangulation_and_learned_depth.md (+74 -0, 74 lines)
- research/feed_forward_3d/README.md (+4 -0, 34 lines)
- research/feed_forward_3d/lingbot_map.md (+53 -0, 53 lines)
- research/feed_forward_3d/slam3r.md (+35 -0, 35 lines)
- research/gaussian_splatting/README.md (+36 -0, 36 lines)
- research/gaussian_splatting/generative_repair.md (+48 -0, 48 lines)
- research/gaussian_splatting/lumina_open_source_parts.md (+219 -0, 219 lines)
- research/papers.csv (+14 -0, 31 lines)
- research/products/e2e_product_research/09_lumina/README.md (+60 -0, 60 lines)
- research/products/e2e_product_research/README.md (+1 -0, 279 lines)
- research/repositories.json (+18 -0, 75 lines)
- research/structure_from_motion/colmap.md (+48 -0, 78 lines)
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

- `.venv-sfm pytest experiments/lingbot_map/tests -> 5 passed; run.py on 274 frames of the 15 Oct walk (CPU, bf16, window 16) -> exit 0, 3,026 s, peak RAM 17.8 GB; compare.py -> size 1.353 (depth 1.397), path RMSE 0.118 m over 6.70 m, depth median 0.95 at 3-4 m and 0.60 beyond 4 m; link check on 6 changed docs -> 0 broken`
- cost: 285 min from begin to finish; Claude tokens 75,622,064 (fresh input 1,437,603, cache read 73,858,604, output 325,857; 4 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.23 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 60 in 25073 words: same-opening "it", same-opening "the", same-opening "it", same-opening "the", same-opening "the"

## Left over

Fair test at LingBot-Map's default 64-frame window needs about 24 GB RAM or a GPU: proposed as a laptop (RTX 4060) experiment file synced through git, not yet written, awaiting owner approval. Lumina lessons not yet filed as tasks (coverage view, exposure and white-balance lock, known-pose COLMAP export, RTAB-Map ARCore benchmark). Owner questions open: refinement pass after the walk; splat scene as an output. experiments/lingbot_map/prepare.py and kv_cache_bf16.patch were planned or tried and not kept. Viewer and cloud are local only. Not committed.
