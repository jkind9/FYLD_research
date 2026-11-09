---
id: "131"
title: LingBot-Map 100-frame GPU sample: load on CPU, bf16 cache, no streaming mask
status: done
files:
  - experiments/lingbot_map/run.py
  - experiments/lingbot_map/attention_no_mask.patch
  - experiments/lingbot_map/README.md
  - research/feed_forward_3d/lingbot_map.md
  - PROJECT_PLAN.md
created: 2026-11-08
---
# LingBot-Map 100-frame GPU sample: load on CPU, bf16 cache, no streaming mask

## Goal

Get 100 frames of the 15 Oct walk through LingBot-Map at the default window on the GPU without spilling, then compare with ARCore

## Plan

1. run.py loads and casts on the CPU. 2. Patch: bf16 key cache and no all-true mask. 3. GPU run with a VRAM log. 4. compare.py; write up; WSL only if Windows still spills.

## Files

- DESIGN.md (+622 -0, 622 lines)
- PROJECT_PLAN.md (+288 -0, 288 lines)
- README.md (+7 -5, 423 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/02_stereo_depth/README.md (+2 -1, 312 lines)
- experiments/04_surface_reconstruction/README.md (+2 -0, 234 lines)
- experiments/lingbot_map/README.md (+132 -0, 132 lines)
- experiments/lingbot_map/attention_no_mask.patch (+29 -0, 29 lines)
- experiments/lingbot_map/compare.py (+176 -0, 176 lines)
- experiments/lingbot_map/run.py (+130 -0, 130 lines)
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

- `GPU run.py 100 frames (window 48, anchors 4) -> exit 0, 78.8 s, 1.27 frames/s, peak GPU 14.6 GB; compare.py on GPU and on CPU run cut to the same frames -> path RMSE 0.024 vs 0.028 m, depth medians within 5% to 4 m in both; no-mask and bf16-key patches -> bit-identical CPU output; git apply --check -R patch -> ok; pytest experiments/lingbot_map/tests -> 5 passed; links -> 0 broken; nvidia-smi after -> 560 MiB`
- cost: 6 min from begin to finish; Claude tokens 6,329,813 (fresh input 28,038, cache read 6,282,360, output 19,415; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 66 in 29271 words: same-opening "it", same-opening "the", same-opening "the", same-opening "it", same-opening "the"

## Left over

Whole walk on the GPU (about 5 min) or the default 64-frame window with FlashInfer in WSL2 not run. Lumina lessons and two owner questions still open. Another session's task.js finish closed Tasks 129 and 130 while they were open (their Checked lines are that session's). Not committed.
