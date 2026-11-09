---
id: "127"
title: Research Lumina's phone-to-splat pipeline and the open-source parts that match it
status: done
files:
  - research/gaussian_splatting/README.md
  - research/gaussian_splatting/lumina_open_source_parts.md
  - research/gaussian_splatting/artifixer.md
  - research/products/e2e_product_research/09_lumina/README.md
  - research/products/e2e_product_research/README.md
  - research/feed_forward_3d/lingbot_map.md
  - research/feed_forward_3d/slam3r.md
  - research/feed_forward_3d/README.md
  - research/README.md
  - research/papers.csv
  - learning/05_dense_surfaces.md
  - learning/03_camera_tracking_and_slam.md
  - learning/methods_inputs_and_outputs.md
  - learning/00_glossary.md
  - research/gaussian_splatting/generative_repair.md
created: 2026-11-08
---
# Research Lumina's phone-to-splat pipeline and the open-source parts that match it

## Goal

Store Lumina's pipeline, each step's open-source match (licence, hardware, fit to CPU/live/mobile limits), plus LingBot-Map, SLAM3R and ArtiFixer, in research/ and learning/

## Plan

1. Read Lumina's site and App Store pages. 2. Find and check open-source parts per step. 3. Read the three owner links. 4. Save papers locally. 5. Write topic folder, product note, feed-forward notes. 6. Update indexes and learning chapters.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+4 -0, 53 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+10 -0, 105 lines)
- learning/05_dense_surfaces.md (+63 -0, 177 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+27 -0, 215 lines)
- research/README.md (+4 -1, 242 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+92 -0, 92 lines)
- research/feed_forward_3d/README.md (+4 -0, 34 lines)
- research/feed_forward_3d/lingbot_map.md (+35 -0, 35 lines)
- research/feed_forward_3d/slam3r.md (+35 -0, 35 lines)
- research/gaussian_splatting/README.md (+36 -0, 36 lines)
- research/gaussian_splatting/generative_repair.md (+48 -0, 48 lines)
- research/gaussian_splatting/lumina_open_source_parts.md (+194 -0, 194 lines)
- research/papers.csv (+11 -0, 28 lines)
- research/products/e2e_product_research/09_lumina/README.md (+60 -0, 60 lines)
- research/products/e2e_product_research/README.md (+1 -0, 279 lines)
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

- `scratchpad check_links.py over the 13 new or edited markdown files -> 0 broken links; csv.reader on research/papers.csv -> 28 rows, all 15 columns; pdftotext first page of all 16 saved PDFs -> titles match the cited papers`
- cost: 10 min from begin to finish; Claude tokens 6,853,331 (fresh input 227,428, cache read 6,552,456, output 73,447; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 40 in 15535 words: same-opening "it", same-opening "the", same-opening "the", same-opening "the", one-line-closer "Local outputs:  ."

## Left over

Owner decisions: may recorded walks be splat-trained on this PC's RTX 5070 Ti as an offline reference (14 Oct ruling says no GPU); is a splat scene a wanted output. Proposed next task, not filed: known-pose COLMAP export from the 15 October walk. Reddit thread not readable by tools. Code licences of AGS-Mesh, 2DGS, PGSR and Cloud2BIM not verified. research/gaussian_splatting/artifixer.md was planned but merged into generative_repair.md. Not committed.
