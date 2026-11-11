---
id: "148"
title: Complete RTAB-Map and surface grouping research digest
status: done
files:
  - research/camera_tracking_and_slam/rtabmap.md
  - research/camera_tracking_and_slam/README.md
  - research/surface_denoising/surface_grouping.md
  - research/surface_denoising/README.md
created: 2026-11-10
---
# Complete RTAB-Map and surface grouping research digest

## Goal

Save verified RTAB-Map findings and surface grouping precedents with a controlled experiment proposal.

## Plan

1. Complete the two sourced digests. 2. Check current sources, local links and scoped differences. 3. Finish this research record; no runtime integration is part of the task.

## Files

- DESIGN.md (+57 -4, 747 lines)
- experiments/01_camera_capture_delivery/README.md (+4 -4, 422 lines)
- experiments/01_camera_capture_delivery/field_accuracy.md (+3 -3, 79 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+3 -3, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+3 -46, 4 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+9 -157, 10 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+4 -183, 5 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+2 -200, 3 lines)
- experiments/02_stereo_depth/README.md (+1 -1, 312 lines)
- experiments/03_camera_pose_estimation/README.md (+4 -5, 225 lines)
- experiments/03_camera_pose_estimation/requirements.txt (+0 -8, 0 lines)
- experiments/03_camera_pose_estimation/src/memory_limits.py (+13 -0, 271 lines)
- experiments/03_camera_pose_estimation/src/supervisor.py (+4 -4, 622 lines)
- experiments/03_camera_pose_estimation/tests/test_supervisor.py (+3 -1, 719 lines)
- experiments/03_camera_pose_estimation/tests/test_worker_memory_guard.py (+4 -1, 125 lines)
- experiments/04_surface_reconstruction/README.md (+2 -2, 234 lines)
- experiments/04_surface_reconstruction/requirements.txt (+0 -2, 0 lines)
- experiments/05_birds_eye_mapping/chunks.py (+93 -0, 93 lines)
- experiments/05_birds_eye_mapping/measure.py (+7 -304, 9 lines)
- experiments/05_birds_eye_mapping/streaming.py (+131 -0, 131 lines)
- experiments/06_object_recognition/datasets/README.md (+1 -1, 49 lines)
- experiments/06_object_recognition/experiments/01_detection/README.md (+3 -3, 103 lines)
- experiments/06_object_recognition/experiments/01_detection/jitter_run.py (+1 -1, 413 lines)
- experiments/06_object_recognition/experiments/01_detection/placement_run.py (+1 -1, 200 lines)
- experiments/06_object_recognition/experiments/01_detection/requirements.txt (+0 -4, 0 lines)
- experiments/06_object_recognition/experiments/02_segmentation/README.md (+3 -3, 53 lines)
- experiments/06_object_recognition/experiments/02_segmentation/requirements.txt (+0 -2, 0 lines)
- experiments/06_object_recognition/experiments/03_appearance/README.md (+1 -1, 72 lines)
- experiments/06_object_recognition/experiments/03_appearance/requirements.txt (+0 -3, 0 lines)
- experiments/06_object_recognition/experiments/04_geometry_identity/README.md (+2 -2, 61 lines)
- experiments/06_object_recognition/pilot/README.md (+4 -5, 88 lines)
- experiments/06_object_recognition/pilot/requirements.txt (+0 -8, 0 lines)
- experiments/geometry_validation/README.md (+2 -2, 98 lines)
- experiments/lingbot_map/README.md (+3 -3, 145 lines)
- experiments/lingbot_map/compare.py (+1 -1, 176 lines)
- experiments/lingbot_map/run.py (+2 -2, 130 lines)
- experiments/live_slam/README.md (+1 -1, 83 lines)
- experiments/live_slam/run_live.py (+1 -1, 111 lines)
- experiments/open_vio/README.md (+1 -1, 165 lines)
- experiments/open_vio/vio/run_tumvi.sh (+2 -2, 13 lines)
- experiments/sfm/README.md (+5 -6, 267 lines)
- experiments/sfm/dump_da3_depth.py (+2 -2, 86 lines)
- experiments/sfm/dump_depth.py (+1 -1, 58 lines)
- experiments/sfm/dump_prompt_depth.py (+1 -1, 83 lines)
- experiments/sfm/requirements.txt (+0 -10, 0 lines)
- experiments/sfm/run_dense.py (+1 -1, 338 lines)
- experiments/sfm/run_metric_points.py (+1 -1, 120 lines)
- experiments/sfm/run_sfm.py (+1 -1, 135 lines)
- experiments/sfm/src/dense.py (+5 -2, 121 lines)
- experiments/shared/README.md (+1 -2, 105 lines)
- experiments/shared/geometry.py (+5 -4, 117 lines)
- experiments/shared/requirements.txt (+0 -7, 0 lines)
- experiments/surface_cleanup/README.md (+25 -0, 25 lines)
- experiments/surface_cleanup/__init__.py (+1 -0, 1 lines)
- experiments/surface_cleanup/filters.py (+55 -0, 55 lines)
- experiments/surface_cleanup/masks.py (+48 -0, 48 lines)
- experiments/surface_cleanup/support.py (+55 -0, 55 lines)
- learning/04_structure_from_motion.md (+3 -3, 97 lines)
- learning/05_dense_surfaces.md (+3 -3, 199 lines)
- models/manifest.toml (+1 -1, 23 lines)
- pyproject.toml (+20 -1, 76 lines)
- pytest.ini (+2 -2, 7 lines)
- research/camera_tracking_and_slam/README.md (+1 -1, 48 lines)
- research/camera_tracking_and_slam/colmap_based_slam.md (+1 -1, 89 lines)
- research/camera_tracking_and_slam/rtabmap.md (+111 -16, 125 lines)
- research/dense_surface_fusion/triangulation_and_learned_depth.md (+1 -1, 74 lines)
- research/gaussian_splatting/README.md (+1 -0, 42 lines)
- research/gaussian_splatting/idol.md (+39 -0, 39 lines)
- research/repositories.json (+1 -1, 151 lines)
- research/surface_denoising/README.md (+2 -0, 381 lines)
- research/surface_denoising/surface_grouping.md (+177 -0, 177 lines)
- sitescan/README.md (+28 -0, 28 lines)
- sitescan/cleanup/README.md (+72 -0, 72 lines)
- sitescan/cleanup/__init__.py (+23 -1, 23 lines)
- sitescan/cleanup/pieces.py (+24 -0, 24 lines)
- sitescan/cleanup/vote.py (+55 -0, 55 lines)
- sitescan/depth/README.md (+71 -0, 71 lines)
- sitescan/depth/__init__.py (+5 -1, 5 lines)
- sitescan/depth/model.py (+72 -0, 72 lines)
- sitescan/depth/orientation.py (+36 -0, 36 lines)
- sitescan/fusion/README.md (+69 -0, 69 lines)
- sitescan/fusion/__init__.py (+5 -1, 5 lines)
- sitescan/fusion/fragments.py (+103 -0, 103 lines)
- sitescan/mapping/README.md (+74 -0, 74 lines)
- sitescan/mapping/__init__.py (+8 -1, 8 lines)
- sitescan/mapping/footprint.py (+78 -0, 78 lines)
- sitescan/mapping/plane.py (+70 -0, 70 lines)
- sitescan/mapping/site.py (+59 -0, 59 lines)
- sitescan/mapping/types.py (+69 -0, 69 lines)
- sitescan/scale/README.md (+77 -0, 77 lines)
- sitescan/scale/__init__.py (+15 -1, 15 lines)
- sitescan/scale/fit.py (+92 -0, 92 lines)
- sitescan/scale/targets.py (+41 -0, 41 lines)
- sitescan/session/FORMAT.md (+201 -0, 201 lines)
- sitescan/session/README.md (+70 -0, 70 lines)
- sitescan/session/__init__.py (+5 -0, 6 lines)
- sitescan/session/protocol.py (+45 -0, 45 lines)
- sitescan/session/read.py (+89 -0, 89 lines)
- sitescan/session/replay.py (+39 -0, 39 lines)
- sitescan/session/wire_v1.py (+195 -0, 195 lines)
- sitescan/session/wire_v2.py (+256 -0, 256 lines)
- sitescan/types.py (+48 -0, 48 lines)
- src/live/README.md (+5 -5, 199 lines)
- src/live/clean.py (+13 -204, 14 lines)
- src/live/fragments.py (+6 -82, 7 lines)
- src/live/orientation_control.py (+7 -27, 116 lines)
- src/live/processor.py (+4 -21, 166 lines)
- src/live/room_build.py (+18 -50, 211 lines)
- src/live/run.py (+3 -16, 133 lines)
- src/live/sizing.py (+14 -36, 43 lines)
- src/live/stream.py (+10 -44, 14 lines)
- src/walkthrough/README.md (+2 -2, 277 lines)
- src/walkthrough/steps/depth.py (+15 -49, 289 lines)
- tests/test_sitescan_cleanup.py (+70 -0, 70 lines)
- tests/test_sitescan_depth.py (+115 -0, 115 lines)
- tests/test_sitescan_fusion.py (+56 -0, 56 lines)
- tests/test_sitescan_mapping.py (+58 -0, 58 lines)
- tests/test_sitescan_scale.py (+83 -0, 83 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)
- uv.lock (+114 -17, 1594 lines)

## Checked

- `python - Markdown audit -> 102 local targets exist, fences paired, no trailing whitespace; git diff --check scoped docs -> passed; primary-source review -> close 2025-2026 prior art verified and S-Graphs wording corrected`
- cost: 2 min from begin to finish; Claude tokens 2,591,443 (fresh input 7,813, cache read 2,581,316, output 2,314; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.24); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 2 in 7868 words: bold-labels "7 items", bold-labels "7 items"

## Left over

None for the research digest. RTAB-Map integration, surface-grouping experiments and a mechanism-specific novelty search remain proposals; no runtime trial was performed.
