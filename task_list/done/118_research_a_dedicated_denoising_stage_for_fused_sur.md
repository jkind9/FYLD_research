---
id: "118"
title: Research a dedicated denoising stage for fused surfaces
status: done
files:
  - research/surface_denoising/README.md
  - research/README.md
  - research/dense_surface_fusion/README.md
  - learning/05_dense_surfaces.md
  - learning/00_glossary.md
  - learning/methods_inputs_and_outputs.md
  - src/live/README.md
  - PROJECT_PLAN.md
  - experiments/04_surface_reconstruction/README.md
created: 2026-11-08
---
# Research a dedicated denoising stage for fused surfaces

## Goal

Collect sources on depth-map filtering, fusion weighting, point-cloud outlier removal, plane priors and splat floater removal, and propose where a clean-up stage sits in the live pipeline

## Plan

1. Search and verify sources against arXiv abstracts and paper text. 2. Store open PDFs in research/surface_denoising/papers (local only). 3. Topic README: symptoms, close-range causes, methods by pipeline stage with CPU and live fit, scoring, order to try. 4. Link from research index, dense_surface_fusion, learning chapter 5, glossary, methods list, src/live README, surface layer README and PROJECT_PLAN.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+2 -0, 51 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+33 -0, 147 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+10 -0, 198 lines)
- research/README.md (+3 -1, 241 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+88 -0, 88 lines)
- research/surface_denoising/README.md (+159 -0, 159 lines)
- src/live/README.md (+97 -0, 186 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+9 -1, 79 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+171 -0, 171 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+9 -0, 63 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+55 -0, 55 lines)
- tools/demos/capture_scene.py (+95 -17, 226 lines)
- tools/demos/tests/test_capture_scene.py (+68 -0, 185 lines)
- tools/demos/web/page_splats.js (+69 -3, 158 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `python -I links.py on the 9 edited markdown files -> 0 missing relative links; 21 PDFs present and gitignored (git check-ignore); claims checked against arXiv abstracts and pdftotext of each paper; Open3D 0.19 signatures read from .venv-yolo`
- cost: 0 min from begin to finish; Claude tokens 228,596 (fresh input 1,482, cache read 226,730, output 384; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 27 in 7704 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Nothing run on project data. Next: measure where floaters come from (depth jumps, grazing angles, within 0.5 m of camera) on the 15 October walk and ICL; then per-frame masks, observation-count threshold (needs VoxelBlockGrid), consistency check. Owner to confirm 'low depth distance' means surfaces within about 1-1.5 m. No task filed for the trials yet. Not committed.
