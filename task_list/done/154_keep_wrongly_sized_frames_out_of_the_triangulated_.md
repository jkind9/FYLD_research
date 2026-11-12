---
id: "154"
title: Keep wrongly sized frames out of the triangulated lounge room and show only cleaned points frame by frame
status: done
session: 65cfe5b1-b9b4-4dcd-a2c7-7d657da5e127
files:
  - sitescan/pipelines/room.py
  - apps/cli.py
  - tests/test_pipelines.py
  - sitescan/pipelines/README.md
  - tools/demos/capture_scene.py
  - tools/demos/tests/test_capture_scene.py
  - README.md
  - research/experiments/triangulation/README.md
created: 2026-11-12
---
# Keep wrongly sized frames out of the triangulated lounge room and show only cleaned points frame by frame

## Goal

The triangulated 15 Oct room keeps a 113,716-point false piece from 7 frames sized 2.6x too large, which the 5,000-point size rule cannot remove; skip frames whose scale jumps from recent frames (opt-in), and make the frame-by-frame view drop points the clean-up removed

## Plan

1. RoomSettings.max_scale_jump and a scale_jumps check against the median of the last 15 fused frames, counted as scale_jump; CLI --max-scale-jump; test. 2. Viewer: timeline points whose nearest raw surface point was removed by clean-up are dropped when raw_surface.ply sits beside frames.npz; test. 3. Rebuild the triangulated room with the check, and the ARCore room with it to see how many good frames it drops; pages, screenshots, pieces.

## Files

- DESIGN.md (+72 -8, 848 lines)
- PROJECT_PLAN.md (+112 -34, 437 lines)
- README.md (+176 -68, 582 lines)
- apps/README.md (+12 -2, 53 lines)
- apps/cli.py (+51 -8, 174 lines)
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
- research/README.md (+4 -2, 254 lines)
- research/camera_tracking_and_slam/colmap_based_slam.md (+2 -0, 91 lines)
- research/camera_tracking_and_slam/rtabmap.md (+6 -0, 131 lines)
- research/dense_surface_fusion/README.md (+3 -1, 110 lines)
- research/dense_surface_fusion/mobile3drecon.md (+2 -0, 63 lines)
- research/dense_surface_fusion/triangulation_and_learned_depth.md (+10 -3, 81 lines)
- research/depth_estimation/README.md (+1 -0, 33 lines)
- research/evaluation/README.md (+9 -0, 34 lines)
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
- research/experiments/triangulation/README.md (+111 -0, 111 lines)
- research/experiments/triangulation/compare_rooms.py (+63 -0, 63 lines)
- research/experiments/triangulation/run_fixture.py (+260 -0, 260 lines)
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
- research/surface_denoising/README.md (+2 -0, 383 lines)
- research/visual_inertial_odometry/README.md (+3 -0, 30 lines)
- research/visual_inertial_odometry/depth_without_arcore_2026-11-12.md (+215 -0, 215 lines)
- sitescan/README.md (+16 -4, 64 lines)
- sitescan/depth/README.md (+4 -0, 75 lines)
- sitescan/fusion/README.md (+3 -0, 72 lines)
- sitescan/objects/README.md (+1 -0, 79 lines)
- sitescan/pipelines/README.md (+46 -19, 122 lines)
- sitescan/pipelines/live.py (+45 -13, 248 lines)
- sitescan/pipelines/room.py (+124 -24, 280 lines)
- sitescan/pipelines/targets.py (+84 -0, 84 lines)
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
- tests/test_pipelines.py (+84 -2, 212 lines)
- tests/test_sitescan_scale.py (+69 -3, 173 lines)
- tests/test_sitescan_session.py (+107 -0, 245 lines)
- tests/test_sitescan_triangulate.py (+221 -0, 221 lines)
- tools/demos/capture_scene.py (+58 -11, 303 lines)
- tools/demos/tests/test_capture_scene.py (+25 -1, 228 lines)
- tools/demos/web/page_timeline.js (+1 -1, 72 lines)

## Checked

- `pytest -q -> 125 passed (6 new scale-jump cases); pytest -c pytest-full.ini tools/demos/tests/test_capture_scene.py -> 18 passed (new: frame-by-frame drops points nearest a removed raw point); ruff -> clean; triangulated 15 Oct room with --max-scale-jump 1.25 -> 37 of 762 frames skipped, scale 0.47-0.88 (was 0.39-1.99), second-largest piece 599 points (was 113,716), points over 2.5 m from a camera 42,101 (was 160,637); ARCore room with the check -> 5 of 134 frames skipped; both pages load offline with no errors in headless Chromium`
- cost: 12 min from begin to finish; Claude tokens 4,905,231 (fresh input 35,160, cache read 4,851,650, output 18,421; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.14 (was 0.12)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 19 in 13742 words: same-opening "the", same-opening "the", same-opening "the", bold-labels "6 items", bold-labels "3 items"

## Left over

Streaks and smeared walls joined to the triangulated room remain: frames or grid cells sized 10-25% off; next try a tighter jump, a per-cell check against neighbouring frames, or the power fit. The check is off by default and untested on other walks.
