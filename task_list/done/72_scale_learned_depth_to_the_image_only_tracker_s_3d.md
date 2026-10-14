---
id: "72"
title: Scale learned depth to the image-only tracker's 3D points
status: done
priority: HIGH
type: experiment
approval_status: filed 2026-10-13; rescoped 2026-10-13 to the standalone experiments/sfm folder (owner: standalone SfM experiments, "more accurately produce the structure based on the images", speed and edge in mind but not the focus); settings marked "proposed by Claude" are not owner-ruled
blocked_by: ["67", "71"]
blocks: ["76", "77"]
verification_test: "experiments/sfm/tests/test_dense.py"
plan_reviewed: null
files:
  - experiments/sfm/**
docs:
  - experiments/sfm/README.md
  - task_list/README.md
baseline_metric:
  source: "Task71 true-pose rows; Task65 walkthrough runs (Depth Anything with Open3D odometry, overlap chain)"
  field: "surface accuracy and completeness against the reference (Task71 measure); camera best fit; plane area where available; wall time"
  baseline_value: "per Task71 and Task67 results"
  target: "proposed by Claude 2026-10-13, not owner-ruled: on ICL and both TUM clips, Depth Anything sized to SfM points and fused along the SfM path within 1.5 times the surface error of the Task71 true-pose row with per-frame reference size"
created: 2026-10-13
last_updated: 2026-10-14
superseded_by: null
---

# Task 72 — Dense structure from the image-only path and learned depth

## In plain English

An image-only tracker gives a good camera path and a few hundred accurate 3D points per frame, but no dense surface. A depth model gives a dense surface whose size is wrong by a different amount in each frame. This task combines the two: each frame's depth is resized to agree with the tracker's points seen in that frame, then all frames are fused along the tracker's camera path into one surface. The surface is scored against the same references as Task71. This is the structure the phone design would produce, with ARCore in place of the offline tracker.

## What

All code lives in `experiments/sfm/` and reuses Task71's fusion and scoring.

1. **Per-frame size from SfM points** (`src/dense.py`): for each frame, take its observed SfM points (Task67 `observations.npz`), their depth in that camera (from the saved camera path), and Depth Anything's depth at the same pixels. Fit one size per frame (median of ratios; robust to outliers) and, as a variant, a size and shift (least squares after dropping the worst 10%). Frames with fewer than 20 points take the size of the nearest frame in time that has one.
2. **Metric size for the SfM world**, two ways:
   - best-fit size from the camera path against the true path (reference: upper bound);
   - Depth Anything's median over all points (deployable; the Task67 size).
3. **Fuse** along the SfM path with Task71's TSDF settings; align the result to the reference with the camera-path best fit (rigid after the chosen size), and score accuracy and coverage at 5 cm.
4. **Rows per recording** (TUM xyz, TUM desk, ICL):
   - SfM path + Depth Anything sized per frame to SfM points (deployable headline);
   - same, size-and-shift variant;
   - SfM path + raw Depth Anything (no per-frame size);
   - SfM sparse points alone (what SfM gives without any depth model);
   - Task71 true-pose rows for comparison.
   The SfM path used is the best Task67 setting per recording, chosen by camera score before any surface is scored.
5. **Speed and edge view:** time per stage (sizing, fusion, scoring) and frames per second; peak memory of the fusion volume. A note on which steps would run on a phone (ARCore gives the path and points; sizing is a few hundred pixel lookups per frame; fusion is the costly step).
6. **Multi-view stereo**, the standard step after SfM: dense depth for each frame from its neighbours along the SfM path. Its depth agrees with the path by construction, so it has no per-frame size drift. COLMAP's PatchMatch stereo needs CUDA, so it waits for the owner's GPU permission; it is listed here as the comparison to run next, not run on CPU.

## Why

This tests the whole proposed design on recorded data: image-only camera path, learned depth only for density. If it gets close to the true-pose rows, the walkthrough should be rebuilt around it (Tasks 76 and 77). Lectures 8 and 9 of the course in research/3d_vision_fundamentals/ describe the standard chain this follows.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Fusion, references and surface scoring | Task71 `dense.py`, `references.py` | this task | experiments/sfm/src/dense.py, references.py (Task71) |
| SfM camera path, points and observations | Task67 `export.py` | this task | experiments/sfm/runs/*/output/{trajectory.txt,points.npz,observations.npz} |
| Best-fit alignment (size, rotation, shift) | Task70 `_best_fit` | scoring and alignment | experiments/03_camera_pose_estimation/src/evaluation.py (`_best_fit`) |
| Per-frame size from known points | Task62 sparse-point study; Task65 `ReferenceFrameScale` | — | experiments/02_stereo_depth/README.md (50 points per frame reach the every-pixel score); src/walkthrough/steps/depth_scale.py |

### Steps

1. Tests first in `tests/test_dense.py`: a synthetic frame whose depth is 2.5 × the true depth, with 50 exact SfM points, gets size 1/2.5 within 1%; with 20% outlier points the median still lands within 2%; a frame with 5 points borrows its neighbour's size; the size-and-shift fit recovers a known shift of 0.2 m; fusion along a path scaled by a known factor and resized back gives the same surface.
2. Implement, run the rows on CPU, write tables and the edge view into `experiments/sfm/README.md`.

## Hyperparameters

| name | value | source |
|---|---|---|
| per-frame size | median of (SfM depth / Depth Anything depth) over the frame's observed points with SfM depth 0.1-20 m and Depth Anything valid | n/a: proposed by Claude 2026-10-13, not owner-ruled |
| size and shift variant | least squares on the same points after dropping the 10% largest residuals of a first fit | n/a: proposed by Claude 2026-10-13, not owner-ruled |
| minimum points per frame | 20; fewer borrows the nearest frame in time | n/a: proposed by Claude 2026-10-13 (Task62: 10-50 points enough), not owner-ruled |
| point quality filter | track length ≥ 3 and reprojection error ≤ 2 px | n/a: proposed by Claude 2026-10-13, not owner-ruled |
| fusion and scoring | Task71 values | inherited Task71 |
| SfM setting per recording | best Task67 setting by best-fit-with-size camera error, chosen before surfaces are scored | n/a: proposed by Claude 2026-10-13, not owner-ruled |
| devices | CPU only; multi-view stereo waits for GPU permission | confirmed 2026-10-08 |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| SfM outputs | Task67 run folder | `dense.py` | read-only; SfM units until sized | sealed by Task67's manifest; the Task72 run records the source run path and manifest hash |
| Per-frame sizes | `dense.py` | fusion, README | `output/frame_sizes.json` (size, shift, points used, borrowed flag) | sealed |
| Fused surface and scores | `run_dense.py` | README | as Task71 | sealed |

- **Source of truth:** Task67 run outputs and the recording; references enter only scoring and the labelled upper-bound size.
- **Backward compatibility:** no existing file changes.

## Verification

- Contract test `experiments/sfm/tests/test_dense.py` (Task72 cases); Ruff clean.
- Before/after: rows in What 4 against Task71's true-pose rows and the Task65 runs.
- Plan review: no independent reviewer run (owner has not asked for agents); recorded in Receipts.

## Receipts

| field | value |
|---|---|
| closing commit | not committed; the owner commits (no commit was requested) |
| files changed | experiments/sfm/run_dense.py (depth-model size computed from model depth when the SfM run saved none), experiments/sfm/tests/test_dense.py (1 test), experiments/sfm/README.md status |
| test | experiments/sfm/tests 21 passed in `.venv-sfm`; Ruff clean |
| before / after | Mean distance to reference, TUM: Task71 ceiling (true poses, exact per-frame size) desk 129 mm, xyz 158 mm. Depth Anything sized per frame to SfM points along the SfM path (best-fit metric size): desk 151 mm, xyz 199 mm (size-and-shift 147 mm); raw Depth Anything along the SfM path 394 / 465 mm; sparse SfM points alone 48 / 57 mm with about 20% coverage; with Depth Anything's own metric size 391 / 483 mm |
| result | Target met on TUM (within 1.5 times the per-frame-reference row: 1.17 desk, 1.26 or 0.93 xyz). ICL rows were still running in the background at close. A metric size from Depth Anything is not usable (its overall bias dominates); multi-view stereo along the SfM path is the next comparison and needs GPU permission |

Notes / caveats / follow-ups:

- Plan review: no independent plan reviewer was run (the owner has not asked for agents); started with `task.js start 72 --force`.
- SfM setting per recording, chosen by camera score before surfaces were scored: desk ALIKED incremental (21.5 mm), xyz SIFT incremental (11.9 mm), ICL SIFT incremental (34.1 mm).
- Rescoped 2026-10-13: the walkthrough integration moved to Task76 (thin readers) and Task77 (reorder), so this experiment stays standalone.
- Related published methods: [Prompt Depth Anything](https://arxiv.org/abs/2412.14015), [Consistent Video Depth Estimation](https://arxiv.org/abs/2004.15021); papers in research/depth_estimation/papers/.

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
- experiments/sfm/README.md (+140 -0, 140 lines)
- experiments/sfm/dump_depth.py (+58 -0, 58 lines)
- experiments/sfm/report.py (+98 -0, 98 lines)
- experiments/sfm/requirements.txt (+10 -0, 10 lines)
- experiments/sfm/run_dense.py (+324 -0, 324 lines)
- experiments/sfm/run_sfm.py (+135 -0, 135 lines)
- experiments/sfm/src/dense.py (+118 -0, 118 lines)
- experiments/sfm/src/export.py (+101 -0, 101 lines)
- experiments/sfm/src/reconstruct.py (+96 -0, 96 lines)
- experiments/sfm/src/references.py (+32 -0, 32 lines)
- experiments/sfm/src/scoring.py (+101 -0, 101 lines)
- experiments/sfm/src/sequences.py (+133 -0, 133 lines)
- experiments/sfm/tests/test_dense.py (+148 -0, 148 lines)
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

- `.venv-sfm pytest experiments/sfm/tests -> 21 passed; TUM Task72 surface runs 10/10 exit 0 (python -m experiments.sfm.report --dense)`
- cost: 4 min from begin to finish; Claude tokens 3,402,914 (fresh input 12,746, cache read 3,380,889, output 9,279; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.28 (was 0.42)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 19 in 10189 words: same-opening "the", one-line-closer "[RTAB-Map] records that run's limits.", same-opening "it", same-opening "a", same-opening "a"

## Left over

ICL Task72 rows running in background (%TEMP%/dense72_queue.log); when QUEUE DONE, add the --dense table for dense_icl to experiments/sfm/README.md; multi-view stereo along the SfM path needs GPU permission
