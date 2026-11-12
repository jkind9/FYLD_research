---
id: "153"
title: Build the ARCore replacement parts: tracker poses, triangulated depth, and a lounge demo sized without ARCore depth
status: done
session: 65cfe5b1-b9b4-4dcd-a2c7-7d657da5e127
files:
  - sitescan/types.py
  - sitescan/session/trajectory.py
  - sitescan/session/read.py
  - sitescan/session/wire_v2.py
  - sitescan/session/__init__.py
  - sitescan/triangulate/__init__.py
  - sitescan/triangulate/geometry.py
  - sitescan/triangulate/sparse.py
  - sitescan/triangulate/sweep.py
  - sitescan/triangulate/window.py
  - sitescan/scale/fit.py
  - sitescan/scale/curve.py
  - sitescan/scale/targets.py
  - sitescan/scale/__init__.py
  - sitescan/pipelines/targets.py
  - sitescan/pipelines/room.py
  - sitescan/pipelines/live.py
  - apps/cli.py
  - tests/test_sitescan_triangulate.py
  - tests/test_sitescan_session.py
  - tests/test_sitescan_scale.py
  - tests/test_pipelines.py
  - tests/fixtures/tum_desk_20_golden.json
  - research/experiments/open_vio/calibration/to_sitescan.py
  - research/experiments/open_vio/tests/test_calibration.py
  - research/experiments/triangulation/run_fixture.py
  - research/experiments/triangulation/compare_rooms.py
  - tools/demos/capture_scene.py
  - tools/demos/web/page_timeline.js
  - tools/demos/tests/test_capture_scene.py
created: 2026-11-12
---
# Build the ARCore replacement parts: tracker poses, triangulated depth, and a lounge demo sized without ARCore depth

## Goal

Decision 10 / DESIGN 7.15: open-tracker poses feed the product, learned depth is sized by sparse and dense triangulation along that path, ARCore only a comparison; then the 15 Oct lounge page built that way

## Plan

1. Read tracker trajectories and calibrations into wire records. 2. Sparse triangulation and a plane sweep in sitescan/triangulate. 3. Weighted and distance-varying scale fits. 4. Scale sources by name in room and live. 5. Score on the TUM desk fixture. 6. Build the 15 Oct room on ARCore's path as a stand-in, sized only by triangulation, and its viewer page labelled from the run summary.

## Files

- DESIGN.md (+72 -8, 848 lines)
- PROJECT_PLAN.md (+112 -34, 437 lines)
- README.md (+175 -68, 581 lines)
- apps/README.md (+12 -2, 53 lines)
- apps/cli.py (+49 -8, 172 lines)
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
- research/experiments/triangulation/README.md (+99 -0, 99 lines)
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
- sitescan/pipelines/README.md (+45 -19, 121 lines)
- sitescan/pipelines/live.py (+45 -13, 248 lines)
- sitescan/pipelines/room.py (+108 -24, 264 lines)
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
- tests/test_pipelines.py (+71 -1, 200 lines)
- tests/test_sitescan_scale.py (+69 -3, 173 lines)
- tests/test_sitescan_session.py (+107 -0, 245 lines)
- tests/test_sitescan_triangulate.py (+221 -0, 221 lines)
- tools/demos/capture_scene.py (+35 -5, 286 lines)
- tools/demos/tests/test_capture_scene.py (+9 -1, 212 lines)
- tools/demos/web/page_timeline.js (+1 -1, 72 lines)

## Checked

- `pytest -q (default lane) -> 119 passed; pytest -c pytest-full.ini tools/demos/tests/test_capture_scene.py research/experiments/open_vio/tests/test_calibration.py -> 28 passed; ARCore-default room and live golden numbers equal to this PC's pre-change run (26/26, 241/241); full lane -> 107 failed, 1564 passed, the failures sampled are Windows 260-char paths in run-snapshot copies, same count as before the change; 15 Oct room sized by plane sweep on ARCore's path: on 134 shared frames scale ratio to ARCore depth median 1.03, 69% within 10%`
- cost: 0 min from begin to finish; Claude tokens 270,461 (fresh input 1,656, cache read 267,473, output 1,332; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.14 (was 0.12)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 19 in 13629 words: same-opening "the", same-opening "the", same-opening "the", bold-labels "6 items", bold-labels "3 items"

## Left over

Run Basalt with a Redmi calibration (Task103, Task104) and rerun the 15 Oct room on its poses; find why about 9% of frames' plane-sweep scale is 20% or more off ARCore's and try the power fit there; undistort features before triangulating; enabling Windows long paths is the owner's admin choice
