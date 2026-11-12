---
id: "155"
title: Sliders for the surface piece rule in the lounge viewer
status: done
session: 65cfe5b1-b9b4-4dcd-a2c7-7d657da5e127
files:
  - sitescan/cleanup/pieces.py
  - sitescan/cleanup/__init__.py
  - sitescan/cleanup/README.md
  - sitescan/pipelines/room.py
  - sitescan/pipelines/README.md
  - tests/test_sitescan_cleanup.py
  - tests/test_pipelines.py
  - tools/demos/capture_scene.py
  - tools/demos/web/page_splats.js
  - tools/demos/tests/test_capture_scene.py
  - README.md
created: 2026-11-12
---
# Sliders for the surface piece rule in the lounge viewer

## Goal

Owner wants control of the piece-size minimum and the number of largest pieces on the triangulated lounge page

## Plan

1. piece_ranks shared by largest_pieces and the viewer (identical masks). 2. Room build saves voted_surface.ply. 3. Viewer: per-splat piece rank and piece sizes; two sliders hide pieces live; defaults are the room build's 50 and 5,000. 4. Rebuild both lounge rooms, pages, screenshots.

## Files

- DESIGN.md (+72 -8, 848 lines)
- PROJECT_PLAN.md (+112 -34, 437 lines)
- README.md (+180 -71, 583 lines)
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
- sitescan/cleanup/README.md (+1 -0, 72 lines)
- sitescan/cleanup/__init__.py (+8 -2, 39 lines)
- sitescan/cleanup/pieces.py (+15 -7, 32 lines)
- sitescan/depth/README.md (+4 -0, 75 lines)
- sitescan/fusion/README.md (+3 -0, 72 lines)
- sitescan/objects/README.md (+1 -0, 79 lines)
- sitescan/pipelines/README.md (+48 -19, 124 lines)
- sitescan/pipelines/live.py (+45 -13, 248 lines)
- sitescan/pipelines/room.py (+128 -25, 283 lines)
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
- tests/test_sitescan_cleanup.py (+18 -11, 77 lines)
- tests/test_sitescan_scale.py (+69 -3, 173 lines)
- tests/test_sitescan_session.py (+107 -0, 245 lines)
- tests/test_sitescan_triangulate.py (+221 -0, 221 lines)
- tools/demos/capture_scene.py (+95 -13, 338 lines)
- tools/demos/tests/test_capture_scene.py (+45 -1, 248 lines)
- tools/demos/web/page_splats.js (+25 -6, 193 lines)
- tools/demos/web/page_timeline.js (+1 -1, 72 lines)

## Checked

- `pytest -q -> 126 passed (new piece_ranks test); pytest -c pytest-full.ini tools/demos/tests (capture_scene 19, demos + cleanup_scene + cleanup_tuner 18) -> all pass; ruff -> clean; refactored largest_pieces equals the old mask on the 1.3M-point raw triangulated surface at 4 settings; both lounge rebuilds byte-identical to the previous runs plus voted_surface.ply; headless Chromium: default sliders show 554,065 and 1,137,969 points (each run's cleaned surface), all pieces 576,769 and 1,167,796, no page errors`
- cost: 10 min from begin to finish; Claude tokens 9,698,222 (fresh input 43,073, cache read 9,625,943, output 29,206; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.15 (was 0.14)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 19 in 13725 words: same-opening "the", same-opening "the", same-opening "the", bold-labels "6 items", bold-labels "3 items"

## Left over

The triangulated room's remaining streaks sit inside its one large piece (next piece 1,732 points), so no piece setting removes them; they need better sizing per frame or per cell. Outputs naming proposal awaits the owner's three decisions.
