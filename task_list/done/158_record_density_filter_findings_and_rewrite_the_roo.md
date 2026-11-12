---
id: "158"
title: Record density-filter findings and rewrite the root README
status: done
session: 38da4c66-bbcf-4716-a5e5-c540fcdc6b46
files:
  - research/surface_denoising/README.md
  - PROJECT_PLAN.md
  - README.md
  - research/evaluation/README.md
  - sitescan/pipelines/README.md
created: 2026-11-12
---
# Record density-filter findings and rewrite the root README

## Goal

Density-filter search and room measurements in research, noted in the plan; README rewritten with current pipeline, ARCore replacement, plan, refactor status and a code map

## Plan

1. Add a density-filter section to research/surface_denoising/README.md with the measured numbers. 2. Note it in PROJECT_PLAN.md. 3. Rewrite README.md around the generated function index. 4. Regenerate the function index and run the docs tests.

## Files

- DESIGN.md (+75 -9, 850 lines)
- PROJECT_PLAN.md (+115 -35, 439 lines)
- README.md (+457 -113, 818 lines)
- apps/README.md (+23 -7, 59 lines)
- apps/cli.py (+89 -23, 197 lines)
- learning/02_depth.md (+1 -1, 70 lines)
- learning/03_camera_tracking_and_slam.md (+5 -3, 111 lines)
- learning/04_structure_from_motion.md (+6 -4, 99 lines)
- learning/05_dense_surfaces.md (+7 -3, 203 lines)
- learning/06_maps_and_measurement.md (+1 -1, 49 lines)
- learning/08_phone_and_deployment.md (+13 -5, 109 lines)
- learning/10_findings_timeline.md (+22 -3, 76 lines)
- learning/11_inside_arcore.md (+3 -1, 120 lines)
- learning/12_rebuilding_arcore.md (+18 -1, 118 lines)
- learning/README.md (+10 -3, 65 lines)
- learning/methods_inputs_and_outputs.md (+4 -4, 221 lines)
- mobile_deployments/README.md (+1 -1, 20 lines)
- recordings.toml (+28 -0, 28 lines)
- research/README.md (+4 -2, 254 lines)
- research/camera_tracking_and_slam/colmap_based_slam.md (+2 -0, 91 lines)
- research/camera_tracking_and_slam/rtabmap.md (+6 -0, 131 lines)
- research/dense_surface_fusion/README.md (+3 -1, 110 lines)
- research/dense_surface_fusion/mobile3drecon.md (+2 -0, 63 lines)
- research/dense_surface_fusion/triangulation_and_learned_depth.md (+10 -3, 81 lines)
- research/depth_estimation/README.md (+1 -0, 33 lines)
- research/evaluation/README.md (+11 -2, 34 lines)
- research/experiments/01_camera_capture_delivery/README.md (+8 -0, 430 lines)
- research/experiments/01_camera_capture_delivery/capture/README.md (+2 -0, 42 lines)
- research/experiments/02_stereo_depth/README.md (+2 -2, 312 lines)
- research/experiments/README.md (+4 -1, 268 lines)
- research/experiments/lingbot_map/README.md (+2 -0, 147 lines)
- research/experiments/open_vio/README.md (+10 -1, 174 lines)
- research/experiments/open_vio/calibration/README.md (+2 -0, 41 lines)
- research/experiments/open_vio/calibration/to_sitescan.py (+53 -0, 53 lines)
- research/experiments/open_vio/tests/test_calibration.py (+21 -0, 145 lines)
- research/experiments/sfm/README.md (+2 -0, 269 lines)
- research/experiments/surface_cleanup/README.md (+2 -2, 29 lines)
- research/experiments/surface_cleanup/cleanup_attributes.py (+2 -3, 55 lines)
- research/experiments/surface_cleanup/denoise_trial.py (+2 -3, 319 lines)
- research/experiments/triangulation/README.md (+111 -0, 111 lines)
- research/experiments/triangulation/compare_rooms.py (+73 -0, 73 lines)
- research/experiments/triangulation/run_fixture.py (+261 -0, 261 lines)
- research/gaussian_splatting/lumina_open_source_parts.md (+8 -0, 227 lines)
- research/phone_ar_platforms/README.md (+3 -1, 29 lines)
- research/phone_ar_platforms/arcore_commercial_terms.md (+2 -0, 54 lines)
- research/phone_ar_platforms/arcore_open_replacement.md (+3 -1, 50 lines)
- research/phone_ar_platforms/arcore_raw_depth.md (+2 -0, 48 lines)
- research/phone_ar_platforms/sceneview.md (+3 -1, 95 lines)
- research/products/e2e_product_research/05_android_on_phone_kit/README.md (+8 -0, 73 lines)
- research/products/e2e_product_research/README.md (+1 -1, 284 lines)
- research/products/sceneview_open3dmap_review_2026-11-09.md (+2 -0, 84 lines)
- research/structure_from_motion/colmap.md (+2 -0, 80 lines)
- research/surface_denoising/README.md (+61 -2, 440 lines)
- research/visual_inertial_odometry/README.md (+3 -0, 30 lines)
- research/visual_inertial_odometry/depth_without_arcore_2026-11-12.md (+215 -0, 215 lines)
- sitescan/README.md (+16 -4, 64 lines)
- sitescan/cleanup/README.md (+2 -0, 73 lines)
- sitescan/cleanup/__init__.py (+8 -2, 39 lines)
- sitescan/cleanup/pieces.py (+30 -7, 47 lines)
- sitescan/depth/README.md (+4 -0, 75 lines)
- sitescan/fusion/README.md (+3 -0, 72 lines)
- sitescan/objects/README.md (+1 -0, 79 lines)
- sitescan/pipelines/README.md (+49 -20, 124 lines)
- sitescan/pipelines/live.py (+45 -13, 248 lines)
- sitescan/pipelines/room.py (+131 -26, 285 lines)
- sitescan/pipelines/targets.py (+84 -0, 84 lines)
- sitescan/runs.py (+100 -0, 100 lines)
- sitescan/scale/README.md (+27 -5, 100 lines)
- sitescan/scale/__init__.py (+13 -1, 27 lines)
- sitescan/scale/curve.py (+80 -0, 80 lines)
- sitescan/scale/fit.py (+25 -6, 113 lines)
- sitescan/scale/targets.py (+3 -3, 41 lines)
- sitescan/session/README.md (+28 -2, 96 lines)
- sitescan/session/__init__.py (+14 -2, 18 lines)
- sitescan/session/read.py (+21 -9, 105 lines)
- sitescan/session/trajectory.py (+182 -0, 182 lines)
- sitescan/session/wire_v2.py (+1 -0, 260 lines)
- sitescan/triangulate/README.md (+96 -0, 96 lines)
- sitescan/triangulate/__init__.py (+47 -0, 47 lines)
- sitescan/triangulate/geometry.py (+76 -0, 76 lines)
- sitescan/triangulate/sparse.py (+113 -0, 113 lines)
- sitescan/triangulate/sweep.py (+210 -0, 210 lines)
- sitescan/triangulate/window.py (+112 -0, 112 lines)
- sitescan/types.py (+27 -3, 72 lines)
- tests/fixtures/tum_desk_20_golden.json (+10 -0, 417 lines)
- tests/test_pipelines.py (+94 -4, 220 lines)
- tests/test_sitescan_cleanup.py (+28 -11, 87 lines)
- tests/test_sitescan_runs.py (+62 -0, 62 lines)
- tests/test_sitescan_scale.py (+69 -3, 173 lines)
- tests/test_sitescan_session.py (+107 -0, 245 lines)
- tests/test_sitescan_triangulate.py (+221 -0, 221 lines)
- tools/README.md (+1 -0, 14 lines)
- tools/runs.py (+120 -0, 120 lines)
- tools/tests/test_runs.py (+74 -0, 74 lines)

## Checked

- `.venv/Scripts/python.exe -B -m pytest -> 138 passed in 9.4 s (includes the function-index test); python -m tools.function_index --check -> exit 0; link and anchor check over the five changed docs -> 0 broken apart from 62 local-only paper PDFs that were missing before`
- cost: 8 min from begin to finish; Claude tokens 7,903,742 (fresh input 69,212, cache read 7,789,163, output 45,367; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.13 (was 0.11)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 23 in 15645 words: same-opening "the", same-opening "the", same-opening "the", same-opening "the", same-opening "the"

## Left over

View the 3,450 coarse-density and 2,694 line-like points in the room viewer to see if they are the strays; the two measurement scripts are in the session scratchpad, not the repo
