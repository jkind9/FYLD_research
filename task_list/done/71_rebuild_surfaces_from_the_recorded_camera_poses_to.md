---
id: "71"
title: Rebuild surfaces from the recorded camera poses to isolate depth error
status: done
priority: HIGH
type: experiment
approval_status: filed 2026-10-13; rescoped 2026-10-13 to the standalone experiments/sfm folder after the owner asked for standalone SfM experiments and for work on "more accurately produce the structure based on the images"; settings marked "proposed by Claude" are not owner-ruled
blocked_by: []
blocks: ["72"]
verification_test: "experiments/sfm/tests/test_dense.py"
plan_reviewed: null
files:
  - experiments/sfm/**
docs:
  - experiments/sfm/README.md
  - task_list/README.md
baseline_metric:
  source: "experiments/02_stereo_depth/runs/task65/clip30_scale_drift.md (30-frame xyz only); experiment 04's ICL point surface (7.8 mm mean distance, 9 views, supplied depth and poses)"
  field: "surface accuracy (median and mean distance from built surface to reference), completeness (fraction of reference within 5 cm), for each depth source with true poses"
  baseline_value: "no full-length or ICL surface score with learned depth; self-consistency only: Kinect 33 mm, raw Depth Anything 71 mm, per-frame-sized Depth Anything 33 mm at 20 frames apart with motion-capture poses (30-frame clip)"
  target: "a table of accuracy and completeness for every depth source with true poses on TUM xyz, TUM desk and ICL living room 2"
created: 2026-10-13
last_updated: 2026-10-13
superseded_by: null
---

# Task 71 — Rebuild surfaces from the true camera poses

## In plain English

Every surface we build today mixes two errors: wrong depth and a wrong camera path. This task removes the camera error by placing each frame with the true camera position from the recording. Whatever error is left comes from depth alone. It also builds the shared tools that turn many depth images into one surface and score that surface against a reference, which Task72 then reuses with the image-only camera path.

## What

All code lives in the standalone `experiments/sfm/` folder (Task67); the walkthrough is not changed.

1. **Fusion** (`src/dense.py`): combine per-frame depth maps and camera poses into one surface with Open3D's TSDF volume (signed-distance fusion, which averages repeated views), then extract its points. A plain point accumulation (every valid pixel, then a 1 cm voxel filter) is also saved, because it is what the walkthrough builds today.
2. **References** (`src/references.py`):
   - ICL living room 2: the publisher's surface model (`data/icl_nuim/reference_surface/living-room.ply`), moved into the right-handed pose world with the published model-from-world matrix (`data/icl_nuim/conventions.json`, `derived_model_from_compatible_world`) and the y flip F of Task67. Exact.
   - TUM xyz and desk: no surface model exists. The reference is Kinect depth fused along the motion-capture path with the same TSDF settings, labelled "sensor reference" because it carries the Kinect's own error and the motion-capture timing error (about 30 mm, below).
3. **Scoring**: experiment 04's `SurfaceScorer` (experiments/04_surface_reconstruction/src/evaluation.py:82) gives accuracy (built surface to reference) and coverage (reference to built surface) at a 5 cm threshold, plus median and mean distances.
4. **Depth sources**, each fused with the true poses:
   - Kinect depth (TUM) or rendered depth (ICL): the control;
   - raw Depth Anything V2 Metric Small;
   - Depth Anything with one size per frame fitted to the sensor depth (reference control: upper bound for any size correction);
   - Depth Anything with one size for the whole run fitted to the sensor depth (reference control: is the error per-frame or overall?).
   TUM uses the saved Task65 Depth Anything maps; ICL needs a new CPU Depth Anything pass over its 440 frames, saved under the run (`dump_depth.py`, run in `.venv-yolo`, which has the model's libraries).
5. Report the floor: on the 30-frame clip, Kinect with motion-capture poses already shows a 33 mm gap between frames 20 apart, against 14 mm with its own tracked poses. TUM results below about 30 mm cannot be ranked; ICL has no such floor.

## Why

If Depth Anything with a correct per-frame size is close to the sensor control when the camera path is right, then the remaining depth problem is size only, and size can come from the image-only tracker's points (Task72). If it is far worse, its shape is also wrong and Task72 should test multi-view stereo instead.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Surface accuracy and coverage scorer | `SurfaceScorer` | experiment 04, walkthrough validation | experiments/04_surface_reconstruction/src/evaluation.py:82-140; src/walkthrough/validation.py:61-72 |
| ICL reference PLY reader | `read_reference` | experiment 04 run | experiments/04_surface_reconstruction/src/dataset.py:35 |
| ICL model-from-world matrix and depth units (raw / 5000, camera-axis z) | data record | experiment 04 | data/icl_nuim/conventions.json |
| Back-projection and transforms | `backproject`, `transform_points` | surface layer | experiments/shared/geometry.py:28,69 |
| Saved Task65 Depth Anything and Kinect-matched frames | Task65 runs and clips | this task | outputs/task65_runs/{xyz,desk}/depth-anything/*/output/predictions/depth/; outputs/task65_clips/*_every2/depth.txt |
| Depth Anything V2 metric adapter | `DepthAnythingV2Metric` | walkthrough | src/walkthrough/steps/depth.py:82-157 |
| Sequence readers and the ICL y flip | `src/sequences.py` | Task67 | experiments/sfm/src/sequences.py (Task67) |

### Steps

1. Tests first (`tests/test_dense.py`): fusing exact depth of a synthetic box seen from 6 known poses gives a surface within 1 voxel of the box; scaling one frame's depth by 1.3 raises the mean distance; the ICL reference conversion maps a model point and its world twin onto each other to 1e-9; a frame with no valid depth is skipped and counted; inputs are not changed.
2. Implement `dense.py`, `references.py`, `dump_depth.py` and a `run_dense.py` entry with `HYPERPARAMETERS`.
3. Run the four depth sources × three recordings on CPU.
4. Write the table into `experiments/sfm/README.md`.

## Hyperparameters

| name | value | source |
|---|---|---|
| TSDF voxel | 1 cm (ICL), 2 cm (TUM) | n/a: proposed by Claude 2026-10-13 (TUM Kinect noise is several cm at 3 m), not owner-ruled |
| TSDF truncation | 4 voxels | n/a: Open3D tutorial convention; proposed by Claude 2026-10-13, not owner-ruled |
| depth range | 0.1-4.0 m | inherited src/walkthrough/steps/contracts.py RGBD_MAX_DEPTH_M (4 m) |
| score threshold | 5 cm | inherited experiment 04 reporting threshold (README status line: "covered within 5 cm") |
| frames | Task67 frame lists (TUM every-2nd clips; ICL every 2nd posed frame) | inherited Task67 |
| per-frame and whole-run reference size | least squares through zero over pixels valid in both (frame); median over frames of per-frame medians (run) | inherited Task65 `ReferenceFrameScale`, `ReferenceGlobalScale` (src/walkthrough/steps/depth_scale.py) |
| Depth Anything | Metric Indoor Small, CPU, 20 m cap | inherited Task65 |
| devices | CPU only | confirmed 2026-10-08 |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Per-frame depth | sensor files, Task65 saves, `dump_depth.py` | `dense.py` | metres, camera-axis z, NaN or mask for invalid, 640×480 | saved npz per frame |
| Poses | ground truth readers (`sequences.py`) | `dense.py` | camera-to-world, metres, right-handed (ICL flipped by F) | read from the recording each run |
| Fused surface | `dense.py` | scorer, viewers | `output/surface_points.npy` (N×3 metres) and `output/surface.ply` | sealed by the run manifest |
| Scores | `run_dense.py` | README | `output/scores.json` | sealed |

- **Source of truth:** recording files; references only enter scoring and the labelled reference-size controls.
- **Failure after each step:** a failed run keeps its timings and is marked failed by `Run`.
- **Backward compatibility:** no existing file changes.

## Verification

- Contract test `experiments/sfm/tests/test_dense.py`; Ruff clean.
- Before: no surface accuracy for learned depth on full recordings. After: the table in What 4 for three recordings, with the TUM floor stated.
- Plan review: no independent reviewer run (owner has not asked for agents); recorded in Receipts.

## Receipts

| field | value |
|---|---|
| closing commit | not committed; the owner commits (no commit was requested) |
| files changed | experiments/sfm/src/dense.py, src/references.py, run_dense.py, dump_depth.py, tests/test_dense.py, report.py (`--dense` table), README.md section |
| test | experiments/sfm/tests: 20 passed in `.venv-sfm` (test_dense.py 9); Ruff clean. Written alongside the code in a scratch package, not seen failing first |
| before / after | Before: no surface accuracy for learned depth. After (mean distance to reference, true poses): ICL sensor 11.1 mm; Depth Anything raw 167 / 399 / 467 mm (ICL / desk / xyz), per-frame reference size 82 / 129 / 158 mm, one run-wide size 88 / 201 / 152 mm |
| result | Done. Size correction cuts the error 2-3 times, but with exact poses and exact per-frame size Depth Anything still misses by 82-158 mm, with 23-53% of points within 5 cm: shape error remains. Sets the ceiling for Task72 |

Notes / caveats / follow-ups:

- Plan review: no independent plan reviewer was run (the owner has not asked for agents); started with `task.js start 71 --force`.
- TUM has no sensor row: its reference is the sensor fused along the true path, so the row would score itself.
- Rescoped 2026-10-13 from a walkthrough command-line flag (65 GB of walkthrough runs) to standalone fusion in experiments/sfm, which needs only the depth maps and poses.

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
- experiments/sfm/run_dense.py (+311 -0, 311 lines)
- experiments/sfm/run_sfm.py (+135 -0, 135 lines)
- experiments/sfm/src/dense.py (+118 -0, 118 lines)
- experiments/sfm/src/export.py (+101 -0, 101 lines)
- experiments/sfm/src/reconstruct.py (+96 -0, 96 lines)
- experiments/sfm/src/references.py (+32 -0, 32 lines)
- experiments/sfm/src/scoring.py (+101 -0, 101 lines)
- experiments/sfm/src/sequences.py (+133 -0, 133 lines)
- experiments/sfm/tests/test_dense.py (+129 -0, 129 lines)
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

- `.venv-sfm pytest experiments/sfm/tests -> 20 passed; ruff clean; 10 surface runs complete (python -m experiments.sfm.report --dense)`
- cost: 548 min from begin to finish; Claude tokens 13,079,963 (fresh input 553,011, cache read 12,508,979, output 17,973; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.28 (was 0.42)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 20 in 10095 words: bold-labels "3 items", same-opening "the", one-line-closer "[RTAB-Map] records that run's limits.", same-opening "it", same-opening "a"

## Left over

none
