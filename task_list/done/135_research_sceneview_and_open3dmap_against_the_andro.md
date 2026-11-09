---
id: "135"
title: Research SceneView and Open3Dmap against the Android room pipeline
status: done
files:
  - research/phone_ar_platforms/sceneview.md
  - research/products/e2e_product_research/11_open3dmap/README.md
  - research/products/sceneview_open3dmap_review_2026-11-09.md
  - research/phone_ar_platforms/README.md
  - research/products/e2e_product_research/README.md
  - research/README.md
  - research/repositories.json
  - research/products/README.md
created: 2026-11-09
---
# Research SceneView and Open3Dmap against the Android room pipeline

## Goal

Explain both repositories from pinned sources and rank the parts that fit our measured Android room reconstruction and object-counting goals

## Plan

1. Read source at fixed commits and check licences. 2. Compare depth, fusion, capture and object handling with local findings. 3. Save notes, source receipts and index links. 4. Check JSON, links and task completion.

## Files

- DESIGN.md (+662 -0, 662 lines)
- PROJECT_PLAN.md (+300 -0, 300 lines)
- README.md (+7 -5, 423 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/02_stereo_depth/README.md (+2 -1, 312 lines)
- experiments/04_surface_reconstruction/README.md (+2 -0, 234 lines)
- experiments/lingbot_map/README.md (+145 -0, 145 lines)
- experiments/lingbot_map/attention_no_mask.patch (+29 -0, 29 lines)
- experiments/lingbot_map/compare.py (+176 -0, 176 lines)
- experiments/lingbot_map/run.py (+130 -0, 130 lines)
- experiments/lingbot_map/tests/test_compare.py (+39 -0, 39 lines)
- experiments/sfm/README.md (+7 -2, 268 lines)
- learning/00_glossary.md (+7 -0, 56 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+14 -0, 109 lines)
- learning/04_structure_from_motion.md (+12 -0, 97 lines)
- learning/05_dense_surfaces.md (+85 -0, 199 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+34 -1, 221 lines)
- research/README.md (+7 -2, 244 lines)
- research/camera_tracking_and_slam/README.md (+6 -0, 48 lines)
- research/camera_tracking_and_slam/colmap_based_slam.md (+89 -0, 89 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+108 -0, 108 lines)
- research/dense_surface_fusion/live_dense_reconstruction_2010.md (+52 -0, 52 lines)
- research/dense_surface_fusion/mobile3drecon.md (+61 -0, 61 lines)
- research/dense_surface_fusion/mobile_object_reconstruction_2015.md (+51 -0, 51 lines)
- research/dense_surface_fusion/triangulation_and_learned_depth.md (+74 -0, 74 lines)
- research/feed_forward_3d/README.md (+10 -0, 40 lines)
- research/feed_forward_3d/feed_forward_splats.md (+48 -0, 48 lines)
- research/feed_forward_3d/lingbot_map.md (+53 -0, 53 lines)
- research/feed_forward_3d/lingbot_map_how_it_works.md (+59 -0, 59 lines)
- research/feed_forward_3d/slam3r.md (+35 -0, 35 lines)
- research/gaussian_splatting/README.md (+41 -0, 41 lines)
- research/gaussian_splatting/generative_repair.md (+48 -0, 48 lines)
- research/gaussian_splatting/lumina_open_source_parts.md (+219 -0, 219 lines)
- research/papers.csv (+14 -0, 31 lines)
- research/phone_ar_platforms/README.md (+1 -0, 27 lines)
- research/phone_ar_platforms/sceneview.md (+93 -0, 93 lines)
- research/products/README.md (+1 -0, 11 lines)
- research/products/e2e_product_research/09_lumina/README.md (+60 -0, 60 lines)
- research/products/e2e_product_research/10_spaitial_echo3/README.md (+127 -0, 127 lines)
- research/products/e2e_product_research/11_open3dmap/README.md (+70 -0, 70 lines)
- research/products/e2e_product_research/README.md (+7 -1, 284 lines)
- research/products/sceneview_open3dmap_review_2026-11-09.md (+49 -0, 49 lines)
- research/repositories.json (+94 -0, 151 lines)
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

- `Research source/link audit -> 3 notes, 13 local links, 36 pinned source links and 2 reference entries passed; JSON parsed; git diff --check on edited tracked research files passed`
- cost: 6 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 72 in 33551 words: same-opening "it", same-opening "the", same-opening "the", same-opening "it", same-opening "the"

## Left over

No research work left. Suggested post-refactor scale, object-association and Redmi benchmark checks were not run. Changes are local and uncommitted.
