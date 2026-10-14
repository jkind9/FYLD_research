---
id: "79"
title: Prompt Depth Anything fed with SfM points
status: done
priority: HIGH
type: experiment
approval_status: filed 2026-10-14 from the owner's handover prompt (step 2a); settings marked proposed by Claude are not owner-ruled
blocked_by: []
blocks: ["76"]
verification_test: "experiments/sfm/tests/test_prompt.py"
plan_reviewed: null
files:
  - experiments/sfm/**
docs:
  - experiments/sfm/README.md
  - research/depth_estimation/README.md
baseline_metric:
  source: "Task72 and Task78 surface rows (Depth Anything resized per frame to SfM points, sized from 20 metric readings)"
  field: "surface mean distance to the reference, points within 5 cm, frames per second on the CPU"
  baseline_value: "mean distance ICL 93.0 mm, desk 155.8 mm, xyz 166.2 mm; Task71 ceiling (true poses, exact per-frame size) 82 / 129 / 158 mm"
  target: "proposed by Claude 2026-10-14, not owner-ruled: at least 1 frame per second end to end on the CPU (owner floor 2026-10-07), and mean distance at least 20% below the baseline on two of the three recordings"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 79 — Prompt Depth Anything fed with SfM points

## In plain English

Depth Anything gives every pixel a depth, but its shape is wrong by 8-16 cm even when its size is corrected. Prompt Depth Anything is a different model that takes a rough, low-resolution depth map as a second input and fills in detail from the image. It was built for an iPhone's lidar. Here the rough map is built from the few hundred 3D points the image-only reconstruction found in each frame, sized to metres from 20 readings (Task78). The question is whether this model's depth is closer to the true surface than Depth Anything resized to the same points.

## What

1. **Prompt map per frame.** Take the frame's SfM points (track length ≥ 3, reprojection error ≤ 2 px), multiply their depth by the 20-reading size from Task78, and place them on a 192 × 256 grid (the model's lidar prompt size for a 480 × 640 image, scale 0.4). Two ways to fill the grid between points: *linear* (triangulated interpolation, nearest point outside the hull) and *nearest* (each cell takes the nearest point's depth). A zero-filled sparse grid is not used: the model rescales its output by the prompt's smallest and largest value, so zeros would pull the range to 0.
2. **Run** `depth-anything/prompt-depth-anything-vits-hf` (Small, 25.1M parameters, Apache-2.0 code and checkpoint) on the CPU, one frame at a time, and save the depth in metres in the same folder format as `dump_depth.py`.
3. **Fuse and score** with `run_dense --depth model --poses sfm:<run> --sfm-size <the 20-reading size>`, the same path, size, TSDF settings and reference as the Task72 and Task78 rows.
4. **Report** per recording: mean distance, RMSE, points within 5 cm and reference coverage for both fills, against the baseline rows, plus frames per second (prompt build, model, total).

Frames with fewer than 20 usable points are left out (they get no depth); the number is reported.

## Why

Task72 left Depth Anything's shape error as the limit. A model that takes metric points as input might remove it, and it fits the phone design: ARCore supplies tracked points. The owner asked for the licence and the CPU speed to be checked first: both checkpoints are Apache-2.0 (Hugging Face model card, 14 October 2026) and the measured model time is 0.36 s per frame on this CPU (2.8 frames per second), above the 1 fps floor.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Depth dump format read by the fusion step | `dump_depth.py`, `run_dense.depth_maps` | `run_dense --depth-maps` | experiments/sfm/dump_depth.py:41-48; experiments/sfm/run_dense.py:53-61 |
| Per-frame SfM points, filter and camera-space depth | `run_dense.sfm_frame_sizes` | Task72 rows | experiments/sfm/run_dense.py:221-236 |
| 20-reading size per recording | Task78 `sizes.json` | `run_dense --sfm-size` | experiments/sfm/runs/metric_*/\*/output/sizes.json |
| Surface fusion and scoring | `run_dense.run` | `report.py --dense` | experiments/sfm/run_dense.py:256-304 |
| The model is in the installed transformers | `PromptDepthAnythingForDepthEstimation` | `.venv-yolo` | transformers 5.14.1, models/prompt_depth_anything/modeling_prompt_depth_anything.py:393 |
| Model min-max rescales by the prompt's range | same file | — | modeling_prompt_depth_anything.py:457-470 |

### Plan

Files: `experiments/sfm/src/prompt.py` (frame points and prompt map, no model code), `experiments/sfm/dump_prompt_depth.py` (model run, `.venv-yolo`), `experiments/sfm/tests/test_prompt.py`, `experiments/sfm/README.md`, `research/depth_estimation/README.md` (row for the model and licence).

1. Tests first for `src/prompt.py` (below); see them fail.
2. Implement; run on TUM xyz (fastest) with both fills and score; then desk and ICL.
3. One background queue with START/END lines; write the next step into the README handover.

## Hyperparameters

| name | value | source |
|---|---|---|
| model | depth-anything/prompt-depth-anything-vits-hf (Small) | owner handover 2026-10-14 (step 2a) |
| prompt grid | 192 × 256 for a 480 × 640 image | the model's published example uses a 192 × 256 lidar prompt; scale proposed by Claude 2026-10-14, not owner-ruled |
| fills | linear (headline), nearest | proposed by Claude 2026-10-14, not owner-ruled |
| point filter | track length ≥ 3, reprojection error ≤ 2 px | inherited experiments/sfm/run_dense.py:228 |
| minimum points per frame | 20 | inherited experiments/sfm/run_dense.py HYPERPARAMETERS sfm_frame_size |
| metric size | Task78's draw for 20 readings in total, per recording | Task78 |
| image preprocessing | the model's own image processor defaults (resized to 560 × 756) | model default |
| prompt units | metres (processor scale not used) | proposed by Claude 2026-10-14, not owner-ruled |
| SfM run per recording | same as Task72 | inherited Task72 |
| fusion and scoring | Task71 values | inherited Task71 |
| devices | CPU only; 16 torch threads (library default on this machine) | owner 2026-10-14 handover |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| SfM points and poses | Task67 run folders | `prompt.py` | SfM units until multiplied by the size | read-only, sealed |
| Prompt depth dump | `dump_prompt_depth.py` | `run_dense --depth-maps` | `index.json` + one `.npz` per frame (metres, valid mask); refuses an existing folder | folder on disk |
| Surface rows | `run_dense.py` | `report.py --dense` | as Task72 | sealed |

- **Source of truth:** the SfM run and the recording; the reference enters only scoring.
- **Failure after each state transition:** a killed dump leaves a folder without `index.json`; delete it and rerun. A killed fusion run leaves an incomplete run folder that the report skips.
- **Backward compatibility:** no existing file changes.

## Verification

- `experiments/sfm/tests/test_prompt.py`:
  - a plane of known depth sampled at 100 random points: the linear map matches the plane within 1% inside the hull; the nearest map equals each point's depth at its own cell;
  - fewer than 4 points returns None; the map has the requested shape and no NaN;
  - frame points keep only points passing the filter and give depth in camera space times the size (a point 4 SfM units away at size 0.5 reads 2 m);
  - a point seen at the image edge lands inside the grid.
- Red first: run the tests before the module exists.
- Before/after: baseline rows in the front matter; the README holds the measured after.
- Plan review: no independent reviewer (the owner has not asked for agents); started with `task.js start 79 --force`.

## Receipts

| field | value |
|---|---|
| closing commit | not committed; the owner commits (no commit was requested) |
| files changed | experiments/sfm/src/prompt.py, dump_prompt_depth.py, tests/test_prompt.py (new); README.md; research/depth_estimation/README.md |
| test | experiments/sfm/tests 34 passed in .venv-sfm |
| before / after | Mean distance baseline (Depth Anything resized to the points, 20 readings) xyz 166.2, desk 155.8, ICL 93.0 mm; Prompt Depth Anything linear fill 167.9, 216.7, 146.5 mm |
| result | Target not met: no recording is 20% better (xyz equal, desk 39% worse, ICL 58% worse). Speed target met: 2.2-2.6 fps end to end on the CPU |

Notes / caveats / follow-ups:

-

## Files

- README.md (+2 -2, 360 lines)
- experiments/01_camera_capture_delivery/README.md (+5 -5, 242 lines)
- experiments/02_stereo_depth/README.md (+32 -4, 311 lines)
- experiments/02_stereo_depth/scale_drift.py (+41 -7, 466 lines)
- experiments/02_stereo_depth/tests/test_scale_drift.py (+27 -0, 224 lines)
- experiments/03_camera_pose_estimation/README.md (+6 -4, 226 lines)
- experiments/03_camera_pose_estimation/src/evaluation.py (+71 -0, 201 lines)
- experiments/03_camera_pose_estimation/tests/test_evaluation.py (+116 -0, 116 lines)
- experiments/04_surface_reconstruction/README.md (+3 -3, 232 lines)
- experiments/05_birds_eye_mapping/README.md (+2 -2, 136 lines)
- experiments/06_object_recognition/README.md (+1 -1, 236 lines)
- experiments/README.md (+2 -1, 257 lines)
- experiments/datasets/README.md (+2 -2, 115 lines)
- experiments/sfm/README.md (+231 -0, 231 lines)
- experiments/sfm/dump_depth.py (+58 -0, 58 lines)
- experiments/sfm/dump_prompt_depth.py (+83 -0, 83 lines)
- experiments/sfm/report.py (+100 -0, 100 lines)
- experiments/sfm/requirements.txt (+10 -0, 10 lines)
- experiments/sfm/run_dense.py (+338 -0, 338 lines)
- experiments/sfm/run_metric_points.py (+120 -0, 120 lines)
- experiments/sfm/run_sfm.py (+135 -0, 135 lines)
- experiments/sfm/src/dense.py (+118 -0, 118 lines)
- experiments/sfm/src/export.py (+101 -0, 101 lines)
- experiments/sfm/src/metric_points.py (+58 -0, 58 lines)
- experiments/sfm/src/prompt.py (+48 -0, 48 lines)
- experiments/sfm/src/reconstruct.py (+96 -0, 96 lines)
- experiments/sfm/src/references.py (+32 -0, 32 lines)
- experiments/sfm/src/scoring.py (+101 -0, 101 lines)
- experiments/sfm/src/sequences.py (+133 -0, 133 lines)
- experiments/sfm/tests/test_dense.py (+148 -0, 148 lines)
- experiments/sfm/tests/test_metric_points.py (+91 -0, 91 lines)
- experiments/sfm/tests/test_prompt.py (+59 -0, 59 lines)
- experiments/sfm/tests/test_sfm.py (+231 -0, 231 lines)
- research/3d_vision_fundamentals/README.md (+47 -0, 47 lines)
- research/3d_vision_fundamentals/lectures/01_introduction.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/02_image_formation.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/03_2d_features_and_matching.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/03_2d_features_and_matching_2.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/04_camera_calibration.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/05_epipolar_geometry.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/06_depth_estimation.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/07_recap_and_overview.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/08_structure_from_motion_sfm.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/08_structure_from_motion_sfm_2.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/09_multi-view_stereo_mvs.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/09_multi-view_stereo_mvs_2.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/11_neural_networks.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/12_3d_representations.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/12_3d_representations_2.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/13_3d_gaussian_splatting_3dgs.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/14_applications_of_3d_computer_vision_and_graphics.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/15_deep_generative_models.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/15_deep_generative_models_2.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/16_applications_of_deep_generative_models.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/16_applications_of_deep_generative_models_2.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/17_robot_kinematics.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/18_reinforcement_learning.pdf (+0 -0, 0 lines)
- research/3d_vision_fundamentals/lectures/19_vision-language-action_vla_models.pdf (+0 -0, 0 lines)
- research/README.md (+46 -10, 236 lines)
- research/arcore/README.md (+0 -59, 0 lines)
- research/camera_tracking_and_slam/README.md (+34 -0, 34 lines)
- research/camera_tracking_and_slam/mast3r_slam.md (+32 -0, 32 lines)
- research/camera_tracking_and_slam/open3d_rgbd.md (+30 -0, 30 lines)
- research/camera_tracking_and_slam/orb_slam/README.md (+76 -0, 76 lines)
- research/camera_tracking_and_slam/orb_slam/android/README.md (+37 -0, 37 lines)
- research/camera_tracking_and_slam/orb_slam/user_sources/README.md (+69 -0, 69 lines)
- research/camera_tracking_and_slam/papers/dpv_slam_2408.01654.pdf (+0 -0, 0 lines)
- research/camera_tracking_and_slam/papers/droid_slam_2108.10869.pdf (+0 -0, 0 lines)
- research/camera_tracking_and_slam/papers/mast3r_slam_2412.12392.pdf (+0 -0, 0 lines)
- research/camera_tracking_and_slam/papers/orb_slam3_2007.11898.pdf (+0 -0, 0 lines)
- research/camera_tracking_and_slam/papers/vggt_long_2507.16443.pdf (+0 -0, 0 lines)
- research/camera_tracking_and_slam/papers/vggt_slam_2505.12549.pdf (+0 -0, 0 lines)
- research/camera_tracking_and_slam/rtabmap.md (+30 -0, 30 lines)
- research/camera_tracking_and_slam/tracking_review_2026-10-13.md (+127 -0, 127 lines)
- research/construction_site_context/README.md (+11 -0, 11 lines)
- research/construction_site_context/construction_capture_guidance.md (+31 -0, 31 lines)
- research/construction_site_context/construction_orthographic_progress.md (+35 -0, 35 lines)
- research/construction_site_context/fyld_public_context.md (+30 -0, 30 lines)
- research/dataset_catalog.md (+0 -23, 0 lines)
- research/datasets_and_benchmarks/README.md (+13 -0, 13 lines)
- research/datasets_and_benchmarks/dataset_catalog.md (+23 -0, 23 lines)
- research/datasets_and_benchmarks/eth3d.md (+32 -0, 32 lines)
- research/datasets_and_benchmarks/euroc_mav.md (+32 -0, 32 lines)
- research/datasets_and_benchmarks/icl_nuim.md (+32 -0, 32 lines)
- research/datasets_and_benchmarks/tum_rgbd.md (+32 -0, 32 lines)
- research/depth_estimation/README.md (+31 -0, 31 lines)
- research/depth_estimation/banet.md (+35 -0, 35 lines)
- research/depth_estimation/himodepth.md (+35 -0, 35 lines)
- research/depth_estimation/hypersight.md (+37 -0, 37 lines)
- research/depth_estimation/mobidepth.md (+35 -0, 35 lines)
- research/depth_estimation/mobilestereonet.md (+34 -0, 34 lines)
- research/depth_estimation/papers/consistent_video_depth_2004.15021.pdf (+0 -0, 0 lines)
- research/depth_estimation/papers/prompt_depth_anything_2412.14015.pdf (+0 -0, 0 lines)
- research/depth_estimation/papers/video_depth_anything_2501.12375.pdf (+0 -0, 0 lines)
- research/e2e_product_research/01_iggt/README.md (+0 -65, 0 lines)
- research/e2e_product_research/02_conceptgraphs/README.md (+0 -65, 0 lines)
- research/e2e_product_research/03_countvid/README.md (+0 -57, 0 lines)
- research/e2e_product_research/04_apple_roomplan/README.md (+0 -62, 0 lines)
- research/e2e_product_research/05_android_on_phone_kit/README.md (+0 -65, 0 lines)
- research/e2e_product_research/06_viasight_zonesure/README.md (+0 -54, 0 lines)
- research/e2e_product_research/07_skyebrowse/README.md (+0 -61, 0 lines)
- research/e2e_product_research/08_scaniverse/README.md (+0 -63, 0 lines)
- research/e2e_product_research/README.md (+0 -278, 0 lines)
- research/edge_products/README.md (+0 -73, 0 lines)
- research/feed_forward_3d/README.md (+30 -0, 30 lines)
- research/feed_forward_3d/infinite_vggt.md (+36 -0, 36 lines)
- research/feed_forward_3d/papers/depth_anything_3_2511.10647.pdf (+0 -0, 0 lines)
- research/feed_forward_3d/papers/dust3r_mast3r_vggt_aerial_evaluation_2507.14798.pdf (+0 -0, 0 lines)
- research/feed_forward_3d/papers/mapanything_2509.13414.pdf (+0 -0, 0 lines)
- research/feed_forward_3d/papers/vggt_2503.11651.pdf (+0 -0, 0 lines)
- research/feed_forward_3d/vggt.md (+36 -0, 36 lines)
- research/feed_forward_3d/vggt_omega.md (+37 -0, 37 lines)
- research/literature_review.md (+1 -1, 39 lines)
- research/orb_slam/README.md (+0 -76, 0 lines)
- research/orb_slam/android/README.md (+0 -37, 0 lines)
- research/orb_slam/user_sources/README.md (+0 -69, 0 lines)
- research/phone_ar_platforms/README.md (+19 -0, 19 lines)
- research/phone_ar_platforms/apple_roomplan.md (+37 -0, 37 lines)
- research/phone_ar_platforms/arcore/README.md (+59 -0, 59 lines)
- research/phone_ar_platforms/arcore_raw_depth.md (+37 -0, 37 lines)
- research/phone_ar_platforms/papers/realitycheck_2021_arcore_drift.pdf (+0 -0, 0 lines)
- research/products/README.md (+10 -0, 10 lines)
- research/products/e2e_product_research/01_iggt/README.md (+65 -0, 65 lines)
- research/products/e2e_product_research/02_conceptgraphs/README.md (+65 -0, 65 lines)
- research/products/e2e_product_research/03_countvid/README.md (+57 -0, 57 lines)
- research/products/e2e_product_research/04_apple_roomplan/README.md (+62 -0, 62 lines)
- research/products/e2e_product_research/05_android_on_phone_kit/README.md (+65 -0, 65 lines)
- research/products/e2e_product_research/06_viasight_zonesure/README.md (+54 -0, 54 lines)
- research/products/e2e_product_research/07_skyebrowse/README.md (+61 -0, 61 lines)
- research/products/e2e_product_research/08_scaniverse/README.md (+63 -0, 63 lines)
- research/products/e2e_product_research/README.md (+278 -0, 278 lines)
- research/products/edge_products/README.md (+73 -0, 73 lines)
- research/reading_guide.md (+63 -0, 63 lines)
- research/roadmap.md (+1 -1, 20 lines)
- research/session_recovery/README.md (+1 -1, 150 lines)
- research/sources/00_start_here.md (+0 -33, 0 lines)
- research/sources/01_mobidepth.md (+0 -35, 0 lines)
- research/sources/02_himodepth.md (+0 -35, 0 lines)
- research/sources/03_mobilestereonet.md (+0 -34, 0 lines)
- research/sources/04_banet.md (+0 -35, 0 lines)
- research/sources/05_hypersight.md (+0 -37, 0 lines)
- research/sources/06_arcore_raw_depth.md (+0 -37, 0 lines)
- research/sources/07_apple_roomplan.md (+0 -37, 0 lines)
- research/sources/08_vggt.md (+0 -36, 0 lines)
- research/sources/09_vggt_omega.md (+0 -37, 0 lines)
- research/sources/10_infinite_vggt.md (+0 -36, 0 lines)
- research/sources/11_colmap.md (+0 -30, 0 lines)
- research/sources/12_rtabmap.md (+0 -30, 0 lines)
- research/sources/13_open3d_rgbd.md (+0 -30, 0 lines)
- research/sources/14_mast3r_slam.md (+0 -32, 0 lines)
- research/sources/15_tum_rgbd.md (+0 -32, 0 lines)
- research/sources/16_eth3d.md (+0 -32, 0 lines)
- research/sources/17_euroc_mav.md (+0 -32, 0 lines)
- research/sources/18_icl_nuim.md (+0 -32, 0 lines)
- research/sources/19_construction_capture_guidance.md (+0 -31, 0 lines)
- research/sources/20_construction_orthographic_progress.md (+0 -35, 0 lines)
- research/sources/21_fyld_public_context.md (+0 -30, 0 lines)
- research/sources/README.md (+0 -63, 0 lines)
- research/start_here.md (+33 -0, 33 lines)
- research/structure_from_motion/README.md (+34 -0, 34 lines)
- research/structure_from_motion/colmap.md (+30 -0, 30 lines)
- research/structure_from_motion/papers/fastmap_2505.04612.pdf (+0 -0, 0 lines)
- research/structure_from_motion/papers/g_mast3r_sfm_2606.22856.pdf (+0 -0, 0 lines)
- research/structure_from_motion/papers/glomap_2407.20219.pdf (+0 -0, 0 lines)
- research/structure_from_motion/papers/mast3r_sfm_2409.19152.pdf (+0 -0, 0 lines)
- research/structure_from_motion/papers/orbit_plus_plus_sfm_360_video_2608.22039.pdf (+0 -0, 0 lines)
- research/structure_from_motion/papers/vggsfm_2312.04563.pdf (+0 -0, 0 lines)
- research/vr_and_stereo_viewing/README.md (+21 -0, 21 lines)
- research/vr_and_stereo_viewing/papers/liftproj_panorama_stitching_2512.24276.pdf (+0 -0, 0 lines)
- research/vr_and_stereo_viewing/papers/serrano_2019_vr_6dof_360_video.pdf (+0 -0, 0 lines)

## Checked

- `.venv-sfm pytest experiments/sfm/tests -> 34 passed; ruff clean; Prompt DA mean distance xyz 167.9 / desk 216.7 / ICL 146.5 mm vs baseline 166.2 / 155.8 / 93.0 mm; 2.2-2.6 fps CPU`
- cost: 44 min from begin to finish; Claude tokens 2,796,276 (fresh input 27,365, cache read 2,752,693, output 16,218; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.26 (was 0.42)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 23 in 11094 words: bold-labels "4 items", bold-labels "3 items", same-opening "the", one-line-closer "[RTAB-Map] records that run's limits.", same-opening "it"

## Left over

No gain from Prompt Depth Anything, accuracy target not met (speed target met). Depth Anything 3 Small on CPU and Task76 not started; multi-view stereo needs GPU permission (left blank)
