---
id: "78"
title: Size the SfM world from a few metric depth readings
status: done
priority: HIGH
type: experiment
approval_status: filed 2026-10-14 from the owner's handover prompt; settings marked proposed by Claude are not owner-ruled
blocked_by: []
blocks: ["76"]
verification_test: "experiments/sfm/tests/test_metric_points.py"
plan_reviewed: null
files:
  - experiments/sfm/**
docs:
  - experiments/sfm/README.md
  - task_list/README.md
baseline_metric:
  source: "Task67 camera scores (best-fit size, Depth Anything size); Task72 surface rows"
  field: "camera-path rigid error after sizing, size error against the best-fit size, surface mean distance to the reference"
  baseline_value: "Depth Anything size: xyz 58 mm path error, desk 339-361 mm; best-fit size: xyz 11.9 mm, desk 21.5-24 mm, ICL 34.1 mm. Task72 surface with best-fit size: ICL 92 mm, desk 151 mm, xyz 199 mm"
  target: "proposed by Claude 2026-10-14, not owner-ruled: with 20 metric readings in total, camera-path rigid error within 1.2 times the best-fit-size error and surface mean distance within 1.2 times the best-fit-size row, on all three recordings"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 78 — Size the SfM world from a few metric depth readings

## In plain English

Photos alone give a 3D model with the right shape but no real-world size. A phone can supply a few real distances, for example ARCore's depth readings at tracked points. This task checks how few such distances are enough. The recorded depth camera stands in for the phone: we take N of its readings at points the image-only reconstruction already found, compute the size from them, and measure how far the camera path and the surface then are from the truth. N runs from 5 to every reading.

## What

1. **Readings.** For each SfM point seen in a frame (track length ≥ 3, reprojection error ≤ 2 px), the reading is the depth camera's depth at that pixel divided by the point's depth in the SfM world. The ratio is the metres per SfM unit that reading implies.
2. **Two ways to use N readings** (my reading of "per run and per frame"):
   - *Per run*: N readings drawn at random from the whole run; the size is their median ratio. N is the total number of readings the phone must take.
   - *Per frame*: N readings drawn in every frame (all of them when the frame has fewer); each frame gets its median ratio and the run size is the median over frames. N is the readings per frame, so the total is about N times the frame count.
3. **N** = 5, 20, 100 and all. 100 random draws per setting (one draw for all).
4. **Camera path.** Multiply the SfM path by the size, align rigidly, report the error (Task70 `ate_rigid`), the size error against the best-fit size, and the spread over the draws (median, 10th and 90th percentile).
5. **Surface.** For the per-run setting at each N, take the draw whose absolute size error is the median of the draws, rerun Task72's row (Depth Anything resized per frame to the SfM points, fused along the SfM path) with that size, and score it against the same reference. Rows go beside the best-fit-size and Depth-Anything-size rows.

Everything runs on the CPU with the recorded data: TUM xyz and desk every-2nd clips, ICL living room 2 every 2nd frame, the same SfM runs as Task72.

## Why

Task72 showed that the remaining unknown for the image-only design is the real-world size: Depth Anything's own size is 1.3-1.4 times too large and unusable, and the best-fit size uses the true path. The phone can give a few metric readings. This sets how many are needed before the size error stops mattering, which decides whether the phone needs a depth sensor at all or only a few ARCore points.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Camera-path error after a given size | `scoring.sized_score` | Task67 report | experiments/sfm/src/scoring.py:97 |
| The median ratio at observed points, per frame then per run | `scoring.depth_model_size` (model depth; this task swaps in sensor depth) | `run_sfm.py` | experiments/sfm/src/scoring.py:59-94 |
| Sensor depth reader and best-fit size and alignment | `run_dense.sensor_depth`, `sfm_poses`, `_align` | `run_dense.run` | experiments/sfm/run_dense.py:64, 111, 148 |
| Point filter (track ≥ 3, error ≤ 2 px) | `sfm_frame_sizes` | Task72 rows | experiments/sfm/run_dense.py:228 |
| Surface rows with a given size | `run_dense --depth model-sfm-size` | `report.py --dense` | experiments/sfm/run_dense.py:207, 269-272 |
| Nothing comparable for drawing N readings | searched `experiments/` and `src/` for "metric points" and "sample" | — | none found |

### Plan

Files: `experiments/sfm/src/metric_points.py` (readings and the two size rules), `experiments/sfm/run_metric_points.py` (draws, camera scores, writes a sealed run with `sizes.json`), `experiments/sfm/tests/test_metric_points.py`, small edits to `run_dense.py` (`--sfm-size` accepts a number) and `report.py` (label "SfM (N metric points)"), `experiments/sfm/README.md`.

1. Tests first (below); see them fail.
2. Implement `metric_points.py`; run `run_metric_points.py` for the three recordings (camera path only, minutes).
3. Queue the surface rows (12 runs: 3 recordings × N = 5, 20, 100, all). ICL runs take 8-17 minutes each, so one background queue with START/END lines.
4. Write results and the handover into `experiments/sfm/README.md`.

## Hyperparameters

| name | value | source |
|---|---|---|
| N | 5, 20, 100, all | owner handover 2026-10-14 |
| draws per setting | 100 (one for all) | proposed by Claude 2026-10-14, not owner-ruled |
| random seed | draw i uses seed i | proposed by Claude 2026-10-14, not owner-ruled |
| point filter | track length ≥ 3, reprojection error ≤ 2 px | inherited experiments/sfm/run_dense.py:228 |
| reading range | depth camera depth 0.1-4 m, SfM depth > 0 | inherited run_dense.py HYPERPARAMETERS depth_range_m |
| size per set of readings | median of ratios | inherited scoring.py:85 |
| surface draw for fusion | the draw with the median absolute size error | proposed by Claude 2026-10-14, not owner-ruled |
| SfM run per recording | same as Task72 (desk ALIKED incremental, xyz and ICL SIFT incremental) | inherited Task72 |
| depth camera noise | none (real Kinect and ICL readings used as recorded); ARCore noise is not simulated | proposed by Claude 2026-10-14, not owner-ruled |
| devices | CPU only | owner 2026-10-14 handover |

The script mirrors this table in a `HYPERPARAMETERS` dict written into its result JSON.

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| SfM run outputs | Task67 run folders | `run_metric_points.py`, `run_dense.py` | read-only; SfM units | sealed by their manifests |
| Sizes per setting and draw | `run_metric_points.py` | `run_dense.py --sfm-size <number>`, README | `output/sizes.json`, metres per SfM unit | sealed run folder |
| Surface rows | `run_dense.py` | `report.py --dense` | as Task72 | sealed |

- **Source of truth:** the SfM run and the recording; the depth camera enters only as the simulated readings and the scoring reference.
- **Failure after each state transition:** a killed queue leaves finished sealed runs and an unfinished folder that `report.py` skips (status not complete); rerunning the missing rows is enough.
- **Backward compatibility:** `--sfm-size best-fit` and `depth-model` keep working (test).

## Verification

- `experiments/sfm/tests/test_metric_points.py`, run with `.venv-sfm/Scripts/python.exe -B -m pytest experiments/sfm/tests -p no:cacheprovider --import-mode=importlib`:
  - noiseless readings with ratio 0.5: every N gives exactly 0.5 in both modes;
  - 20% outlier readings, N = 100: size within 2% of the true ratio;
  - N larger than the readings available uses all readings and equals the median of all;
  - the same seed gives the same draw, a different seed a different one;
  - per-frame mode: a frame with 3 readings and N = 5 uses 3; frames with none are skipped; empty input returns None;
  - readings are only taken from points passing the filter and from pixels with valid depth camera depth;
  - `--sfm-size 0.25` is accepted by the argument parser and `abc` is refused.
- Red first: run the new tests before the module exists.
- Before/after: baseline numbers in the front matter; the README tables hold the measured after.
- Plan review: no independent reviewer (the owner has not asked for agents); started with `task.js start 78 --force`.

## Receipts

| field | value |
|---|---|
| closing commit | not committed; the owner commits (no commit was requested) |
| files changed | experiments/sfm/src/metric_points.py, run_metric_points.py, tests/test_metric_points.py (new); run_dense.py (--sfm-size number, --size-note); report.py (label); README.md |
| test | experiments/sfm/tests 30 passed in .venv-sfm; Ruff clean |
| before / after | Path error best-fit size xyz 11.9, desk 21.5, ICL 34.1 mm; with 20 readings 13.7, 24.2, 34.1 mm. Surface mean distance best-fit size 198.6 / 150.6 / 92.4 mm (xyz / desk / ICL); with 20 readings 166.2 / 155.8 / 93.0 mm |
| result | Target met (within 1.2 times on path and surface, all three recordings). 20 readings in the whole run are enough; more readings and per-frame readings add nothing; the remaining size error is the depth camera's own bias (3.7% xyz, 1.2% desk) |

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
- experiments/sfm/README.md (+208 -0, 208 lines)
- experiments/sfm/dump_depth.py (+58 -0, 58 lines)
- experiments/sfm/report.py (+100 -0, 100 lines)
- experiments/sfm/requirements.txt (+10 -0, 10 lines)
- experiments/sfm/run_dense.py (+338 -0, 338 lines)
- experiments/sfm/run_metric_points.py (+120 -0, 120 lines)
- experiments/sfm/run_sfm.py (+135 -0, 135 lines)
- experiments/sfm/src/dense.py (+118 -0, 118 lines)
- experiments/sfm/src/export.py (+101 -0, 101 lines)
- experiments/sfm/src/metric_points.py (+58 -0, 58 lines)
- experiments/sfm/src/reconstruct.py (+96 -0, 96 lines)
- experiments/sfm/src/references.py (+32 -0, 32 lines)
- experiments/sfm/src/scoring.py (+101 -0, 101 lines)
- experiments/sfm/src/sequences.py (+133 -0, 133 lines)
- experiments/sfm/tests/test_dense.py (+148 -0, 148 lines)
- experiments/sfm/tests/test_metric_points.py (+91 -0, 91 lines)
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

- `.venv-sfm pytest experiments/sfm/tests -> 30 passed; ruff clean; camera path with 20 readings 1.0-1.15x best-fit error, surface 93.0/155.8/166.2 mm (ICL/desk/xyz) vs 92.4/150.6/198.6 mm best-fit size`
- cost: 51 min from begin to finish; Claude tokens 3,632,343 (fresh input 39,982, cache read 3,570,978, output 21,383; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.27 (was 0.42)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 22 in 10885 words: bold-labels "3 items", same-opening "the", one-line-closer "[RTAB-Map] records that run's limits.", same-opening "it", same-opening "a"

## Left over

Dense surface beyond Depth Anything (Prompt Depth Anything, Depth Anything 3 Small on CPU) and Task76 readers not started; multi-view stereo needs GPU permission (left blank); ARCore reading accuracy untested
