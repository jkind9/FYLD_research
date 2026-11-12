---
id: "159"
title: Rebuild the walk viewer as a one-screen app with a frame player
status: done
session: f30c618b-0d6d-4d25-a6be-40eb489c251f
files:
  - tools/demos/capture_scene.py
  - tools/demos/page.py
  - tools/demos/web/page_splats.js
  - tools/demos/web/page_timeline.js
  - tools/demos/web/page_capture.js
  - tools/demos/web/capture.css
  - tools/demos/tests/test_capture_scene.py
  - tools/demos/README.md
created: 2026-11-12
---
# Rebuild the walk viewer as a one-screen app with a frame player

## Goal

The walk viewer fits one screen: photo beside the 3D view, a frame player with filmstrip, settings and help behind buttons

## Plan

1. Add a css argument to build_page. 2. Rewrite scene_page markup: top bar, photo pane, 3D pane, floating settings, player dock, help and report dialogs. 3. Replace page_timeline.js with page_capture.js: one frame cursor for final surface and build-up, play/step/speed, track, filmstrip, layer toggles, keys. 4. Guard page_splats.js compare block. 5. Update tests, add a browser test. 6. Rebuild the sweep-jump125 page and screenshot it.

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
- tools/demos/README.md (+1 -1, 24 lines)
- tools/demos/capture_scene.py (+316 -97, 475 lines)
- tools/demos/page.py (+4 -2, 102 lines)
- tools/demos/tests/test_capture_scene.py (+100 -3, 301 lines)
- tools/demos/web/capture.css (+135 -0, 135 lines)
- tools/demos/web/page_capture.js (+180 -0, 180 lines)
- tools/demos/web/page_splats.js (+36 -11, 199 lines)
- tools/demos/web/page_timeline.js (+0 -72, 0 lines)
- tools/runs.py (+120 -0, 120 lines)
- tools/tests/test_runs.py (+74 -0, 74 lines)

## Checked

- `.venv pytest tools/demos/tests/test_capture_scene.py -> 21 passed, including a new Chromium test that steps frames, switches to frame by frame and finds no page scroll; Playwright run on the real sweep-jump125 page at 1440x900 and 390x844 -> no console errors, page height equals the window, a track click at 90% lands on step 109 of 121`
- cost: 9 min from begin to finish; Claude tokens 5,416,268 (fresh input 55,856, cache read 5,321,724, output 38,688; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.17 (was 0.16)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 23 in 15704 words: same-opening "the", same-opening "the", same-opening "the", same-opening "the", same-opening "the"

## Left over

The desk demo page (pages_scene.py) shares page_splats.js and was not rebuilt here: it needs the TUM replay data. 3 test_run_report tests fail from the known Windows source-copy error in research/experiments/shared/runs.py (task 157 left-over). screens/page/viewer.png in the sweep run still shows the old layout.
