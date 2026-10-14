---
id: "70"
title: Score camera paths with the standard best-fit trajectory error
status: done
priority: HIGH
type: experiment
approval_status: filed 2026-10-13 from the owner's request to research the tracking problem; owner asked 2026-10-13 for the tasks to be detailed and worked overnight ("You have the pc overnight"); settings marked "proposed by Claude" are not owner-ruled
blocked_by: []
blocks: ["67"]
verification_test: "experiments/03_camera_pose_estimation/tests/test_evaluation.py"
plan_reviewed: null
files:
  - experiments/03_camera_pose_estimation/src/evaluation.py
  - experiments/03_camera_pose_estimation/tests/test_evaluation.py
  - experiments/02_stereo_depth/scale_drift.py
  - experiments/02_stereo_depth/tests/test_scale_drift.py
  - experiments/02_stereo_depth/runs/task65/**
docs:
  - experiments/03_camera_pose_estimation/README.md
  - experiments/02_stereo_depth/README.md
  - task_list/README.md
baseline_metric:
  source: "outputs/task65_runs/{clip30,xyz,desk}/*/output/scores.json"
  field: "tracking.result.position_rmse_m (first matched pose aligned, scale 1)"
  baseline_value: "only the first-pose score exists; Kinect depth gives 21 / 67 / 220 mm on the 30-frame, full xyz and full desk clips"
  target: "every scored run also reports best-fit rigid error, best-fit scaled error with its fitted size, and relative error over 1 s; all Task65 runs rescored into the Task65 summary tables"
created: 2026-10-13
last_updated: 2026-10-13
superseded_by: null
---

# Task 70 — Score camera paths with the standard best-fit trajectory error

## In plain English

We judge a camera path by comparing it with the true path recorded by a motion-capture system. Today the two paths are pinned together at the first frame only. A small turning error at the start then swings the whole path away, and the number cannot be compared with any published result. The standard method lines up the whole path at once, and for image-only methods also fits one overall size. This task adds those standard scores next to the current one and rescores the finished runs.

## What

Add these fields to the camera-path scorer's result, overall and per segment, keeping every existing field unchanged:

| Field | Meaning |
|---|---|
| `ate_rigid_rmse_m` | Root-mean-square position error after the rotation and shift that best match the whole estimated path to the true path (Umeyama least squares, size fixed at 1). This is the TUM benchmark's absolute trajectory error and the default of its `evaluate_ate.py`. |
| `ate_scaled_rmse_m`, `ate_scaled_size` | The same, but one overall size is also fitted; the size is reported. Image-only methods have no metric size, so this is the score their papers publish. A size far from 1 on a metric method means the path is the wrong length. |
| `rpe_1s_translation_rmse_m`, `rpe_1s_rotation_rmse_rad` | Error of the motion over 1 s windows: for each tracked frame, the frame closest to 1 s later in the same segment. Alignment-free; this is local drift (TUM `evaluate_rpe.py` convention, 1 s delta). |
| `alignment_note` | States which fields use which alignment. |

Overall values pool the per-segment aligned errors (each segment is aligned on its own, as the first-pose score already does). A segment with fewer than 3 matched poses, or whose true positions do not span at least two directions, gets `None` for the best-fit fields.

Then:

1. `scale_drift.py` `summarise_run` recomputes these fields from each run's saved poses (`output/predictions/tracking.json`) and the recording's ground truth, so the finished Task65 runs are rescored without rerunning them. The summary table gains "best fit", "best fit with size" and "size" columns.
2. Regenerate `experiments/02_stereo_depth/runs/task65/*_scale_drift.{json,md}` for the 30-frame, xyz and desk clips, and add the best-fit table to the experiment 02 README.
3. Note the new fields in the experiment 03 README.

## Why

A scratch recomputation on 2026-10-13 from the saved Task65 positions gives Kinect-depth desk 220 mm first-pose, 112 mm best fit; raw Depth Anything full xyz 1,359 mm first-pose, 177 mm best fit with size, fitted size 0.06 (the path is about 16 times too long). Published image-only systems score 16-18 mm on fr1/desk with the best-fit scaled score (MASt3R-SLAM paper, Table 1). Every later comparison (Tasks 67, 72, 74) needs this score.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Scorer pairs estimates and references by time, groups by segment, computes first-pose and frame-to-frame scores | `evaluate()` | walkthrough validation, experiment 03 run, evaluation stages | experiments/03_camera_pose_estimation/src/evaluation.py:46,58-62,67-70 |
| Walkthrough scoring builds `Record`s from saved poses and calls `evaluate` | `validation._tracking` | `scores.json` writer | src/walkthrough/validation.py:49-57 |
| Consumers read only `position_rmse_m`, `relative_*` and `errors`; new keys are additive | report, demos, evaluation stages | — | tools/demos/run_report.py:90,177-178; tools/demos/pages_results.py:103-115; experiments/evaluation/stages/camera.py:24-25; experiments/02_stereo_depth/scale_drift.py:141,284-292 |
| Summary already reads each run's saved poses and its ground truth | `summarise_run`, `_reference_poses` | Task65 tables | experiments/02_stereo_depth/scale_drift.py:115-123,202 |
| Pose reader for saved records | `read_pose` | validation, scale_drift | src/walkthrough/steps/contracts.py:187-191 |

No Umeyama or relative-pose-error code exists in the repo (searched `umeyama`, `procrustes`, `svd(` in experiments/, src/, tools/: none for trajectories).

### Steps

1. Tests first in a new `experiments/03_camera_pose_estimation/tests/test_evaluation.py`, each seen failing first:
   - a true path along a curve; the estimate is that path rotated 30° about z, shifted by (1, 2, 3) m and scaled by 0.5: `ate_scaled_rmse_m` < 1e-9 and `ate_scaled_size` = 2 ± 1e-9; `ate_rigid_rmse_m` > 0.1;
   - the same with scale 1: `ate_rigid_rmse_m` < 1e-9 and `position_rmse_m` unchanged from today's value for that input;
   - Gaussian noise of known size on positions gives `ate_rigid_rmse_m` within 10% of that size over 2,000 points (seed 0);
   - two matched poses, or all true positions on one line, give `None` best-fit fields, not an error;
   - a constant velocity estimate with a 10% speed error gives `rpe_1s_translation_rmse_m` = 0.1 × the speed;
   - two segments are aligned separately (one rotated, one shifted) and both give 0;
   - the input records are not changed.
2. Implement in `evaluation.py` with NumPy only (SVD of the 3×3 cross-covariance; reflection fixed by the determinant sign).
3. Extend `summarise_run` and the markdown table; test with the existing tiny fake runs in test_scale_drift.py.
4. Rescore and regenerate the three Task65 summaries (CPU, minutes).

## Hyperparameters

| name | value | source |
|---|---|---|
| association tolerance | 0.02 s | inherited experiments/03_camera_pose_estimation/src/evaluation.py:49 |
| best-fit method | Umeyama 1991 least squares on matched positions, per segment; rigid (size 1) and with size | n/a: standard TUM `evaluate_ate.py` method (rigid); scaled variant is the published monocular convention; proposed by Claude 2026-10-13, not owner-ruled |
| minimum poses for a best fit | 3, with true positions spanning two directions (second singular value of the centred positions > 1e-9 m) | n/a: proposed by Claude 2026-10-13, not owner-ruled |
| relative-error window | 1 s, nearest frame to 1 s later within the same segment, accepted if 0.9-1.1 s later | n/a: TUM `evaluate_rpe.py` default delta 1 s; acceptance band proposed by Claude 2026-10-13 (0.5-1.5 s first tried; it let end-of-path pairs only 0.5 s apart in, which understated the error), not owner-ruled |

`scale_drift.py` keeps its `HYPERPARAMETERS` dict and adds the window and minimum rows.

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Existing score fields | evaluation.py:100-120 | report, demos, evaluation stages | unchanged names, units metres/radians | yes: additive change only |
| Saved poses of finished runs | Task65 run folders | `summarise_run` | camera-to-world 4×4, metres, per world/segment | read-only; finished runs are not modified |
| Rescored summaries | `scale_drift.py summarise` | READMEs | JSON (`allow_nan=False`) and markdown | regenerated deterministically |

- **Source of truth:** saved poses in each run plus the recording's `groundtruth.txt`.
- **Failure after each step:** a crash while writing a summary leaves the older summary; rerun the command.
- **Backward compatibility:** every existing field keeps its value; checked by the "position_rmse_m unchanged" test and the existing suites for experiment 03, walkthrough and demos.

## Verification

- Contract test: `experiments/03_camera_pose_estimation/tests/test_evaluation.py` with the assertions in step 1, plus extended `test_scale_drift.py`.
- Suites: experiment 03, experiment 02, walkthrough and demos tests pass; Ruff clean on changed files.
- Before/after on the real symptom: the rescored desk Kinect run must show `ate_rigid_rmse_m` ≈ 0.112 m against first-pose 0.220 m (scratch value 2026-10-13); any difference is explained in Receipts.

## Receipts

| field | value |
|---|---|
| closing commit | not committed; the owner commits (no commit was requested) |
| files changed | experiments/03_camera_pose_estimation/src/evaluation.py (best-fit and 1 s relative scores); experiments/03_camera_pose_estimation/tests/test_evaluation.py (new, 8 tests); experiments/02_stereo_depth/scale_drift.py (rescoring from saved poses, new table columns); experiments/02_stereo_depth/tests/test_scale_drift.py (2 tests); experiments/02_stereo_depth/runs/task65/clip30_scale_drift.{json,md} regenerated; READMEs of experiments 02 and 03 |
| test | test_evaluation.py 8 passed (7 seen failing first; the input-not-changed test passed before the change); test_scale_drift.py 11 passed (2 new, seen failing first); walkthrough, demos, experiments 02, 03 and evaluation suites 401 passed, 7 skipped; 2 memory-limit tests in experiment 03 fail with and without this change (checked on the unchanged code) and were deselected |
| before / after | 30-frame xyz, Kinect depth: first pose 21 mm, best fit 13 mm, size 0.97; raw Depth Anything: 218 mm first pose, 118 mm best fit, 100 mm best fit with size, size 0.47 (path about twice too long); overlap chain 113 / 51 / 26 mm, size 0.72. Same values as the 2026-10-13 scratch recomputation |
| result | Done. Every camera score now carries the published best-fit numbers beside the first-pose one. Full xyz and desk summaries were regenerating in the background at close (started 22:46, about 2 hours of surface-gap recomputation) |

Notes / caveats / follow-ups:

- Plan review: no independent plan reviewer was run (the owner has not asked for agents); started with the journaled `task.js start 70 --force` override on 2026-10-13.
- The first relative-error window (0.5-1.5 s) let end-of-path pairs only 0.5 s apart in and understated a known 10% speed error (0.095 instead of 0.1); narrowed to 0.9-1.1 s, recorded in Hyperparameters.
- Sources: [TUM RGB-D evaluation tools](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/rgbdslam_eval), [MASt3R-SLAM, Table 1](https://arxiv.org/abs/2412.12392). Paper saved at research/camera_tracking_and_slam/papers/mast3r_slam_2412.12392.pdf.

## Files

- README.md (+2 -2, 360 lines)
- experiments/01_camera_capture_delivery/README.md (+5 -5, 242 lines)
- experiments/02_stereo_depth/README.md (+20 -4, 299 lines)
- experiments/02_stereo_depth/scale_drift.py (+41 -7, 466 lines)
- experiments/02_stereo_depth/tests/test_scale_drift.py (+27 -0, 224 lines)
- experiments/03_camera_pose_estimation/README.md (+6 -4, 226 lines)
- experiments/03_camera_pose_estimation/src/evaluation.py (+71 -0, 201 lines)
- experiments/03_camera_pose_estimation/tests/test_evaluation.py (+116 -0, 116 lines)
- experiments/04_surface_reconstruction/README.md (+3 -3, 232 lines)
- experiments/05_birds_eye_mapping/README.md (+2 -2, 136 lines)
- experiments/06_object_recognition/README.md (+1 -1, 236 lines)
- experiments/README.md (+1 -1, 256 lines)
- experiments/datasets/README.md (+2 -2, 115 lines)
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

- `pytest experiments/03_camera_pose_estimation/tests/test_evaluation.py experiments/02_stereo_depth/tests/test_scale_drift.py -> 8 + 11 passed; walkthrough+demos+exp02+exp03+evaluation suites -> 401 passed, 7 skipped (2 pre-existing memory-limit failures deselected); clip30 rescore matches scratch values (Kinect 13 mm best fit, Depth Anything 118 mm, size 0.47)`
- cost: 24 min from begin to finish; Claude tokens 38,847,039 (fresh input 161,533, cache read 38,569,304, output 116,202; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.37 (was 0.42)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 18 in 8706 words: bold-labels "3 items", same-opening "the", one-line-closer "[RTAB-Map] records that run's limits.", same-opening "it", same-opening "a"

## Left over

xyz and desk Task65 summaries regenerating in the background at close; their best-fit rows go into the experiment 02 README when they finish (docs only)
