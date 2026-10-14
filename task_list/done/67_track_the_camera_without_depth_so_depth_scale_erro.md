---
id: "67"
title: Track the camera without depth so depth scale errors cannot become camera motion
status: done
priority: HIGH
type: experiment
approval_status: owner asked 2026-10-08 to record this idea; rescoped 2026-10-13 to established image-only structure from motion; owner asked 2026-10-13 for "standalone sfm experiments, under an sfm folder", using existing data, with speed and edge deployment in mind but not the focus, and for the work to run overnight; settings marked "proposed by Claude" are not owner-ruled
blocked_by: ["70"]
blocks: ["71", "72", "74", "76"]
verification_test: "experiments/sfm/tests/test_sfm.py"
plan_reviewed: null
files:
  - experiments/sfm/**
  - experiments/README.md
docs:
  - experiments/sfm/README.md
  - experiments/README.md
  - task_list/README.md
baseline_metric:
  source: "Task65 runs rescored by Task70 (experiments/02_stereo_depth/runs/task65/*_scale_drift.json); TUM fr1 xyz and desk every-2nd-frame clips, CPU"
  field: "best-fit scaled camera error (ate_scaled_rmse_m); also best-fit rigid after a size set from the depth model, relative error over 1 s, frames placed, separate models, wall time and frames per second"
  baseline_value: "scratch best-fit scaled error 2026-10-13: xyz 34 mm Kinect, 128 mm overlap chain, 177 mm raw Depth Anything; desk 112 mm Kinect, 438 mm overlap chain, 710 mm raw Depth Anything"
  target: "proposed by Claude 2026-10-13, not owner-ruled: at least one image-only setting below the Kinect-depth tracker on both TUM clips (34 mm xyz, 112 mm desk best fit with size), with at least 95% of frames placed in one model"
created: 2026-10-08
last_updated: 2026-10-13
superseded_by: null
---

# Task 67 — Track the camera without depth: standalone structure-from-motion experiments

## In plain English

The camera tracker works out where the camera moved by lining up each frame's depth with the next. When the depth model gets a frame's size wrong, the tracker explains the error by moving the camera. Established systems that use only the images avoid this: they follow the same points through many frames and solve all the camera positions and 3D points together. This task builds a standalone experiment folder for that method, runs it on the recordings we already have, and scores its camera path against the true path. It also records how long each step takes, as a first view of whether this could run on a phone or a small server.

## What

### Background

The owner's question (8 October 2026): does Open3D need depth to estimate camera motion? Yes. Open3D RGB-D odometry (the current `CpuOdometry`) lifts frame A's pixels into 3D with A's depth and fits the motion that aligns them with frame B, so depth errors become motion errors. From images alone, rotation is fully recoverable and translation up to one overall size. Structure from motion (SfM) solves camera poses and sparse 3D points together with bundle adjustment.

The Task65 full-length runs (rescored by Task70) show depth is not the only problem: with Kinect depth our tracker still scores 112 mm best fit on desk, while published image-only systems score 16-18 mm on that recording. Our tracker keeps no map, never refines old poses and never closes loops. The research review is in research/camera_tracking_and_slam/tracking_review_2026-10-13.md.

### The new experiment folder: `experiments/sfm/`

The owner asked for standalone SfM experiments in their own folder. `experiments/sfm/` is a support folder like `geometry_validation/`: it does not change the six-layer walkthrough in `src/walkthrough`. Its outputs (camera path, sparse points and their observations) are saved files that later tasks read: Task72 builds dense structure from them inside this folder, and Task76 adds thin walkthrough readers for them.

| File | Responsibility |
|---|---|
| `README.md` | What the folder is for, how to run it, settings, result tables, overnight status |
| `requirements.txt` | Pinned packages of the separate `.venv-sfm` environment (pycolmap 4.2.1, NumPy 2.4.2, SciPy 1.17.1, Open3D 0.19.0, OpenCV headless); the COLMAP binary's download and hash are in the README |
| `src/sequences.py` | Read a recording into one `Sequence`: ordered image paths, frame IDs, timestamps, camera model and parameters, and the ground-truth reader. TUM clips (`rgb.txt`, `groundtruth.txt`) and ICL-NUIM (`associations.txt`, `livingRoom2.gt.freiburg`) |
| `src/reconstruct.py` | One COLMAP run through the official 4.2.1 command-line build: feature extraction, sequential matching, incremental or global mapping; per-stage timing and logs; all models read back with pycolmap |
| `src/export.py` | Reconstruction to saved files: TUM-format camera path (camera-to-world), sparse points (position, colour, reprojection error, track length) and per-image observations (pixel and point index); unplaced frames listed |
| `src/scoring.py` | Camera-path scores through experiment 03's `evaluate` (Task70 fields), one segment per SfM model; size from the depth model; fraction of frames placed |
| `run_sfm.py` | Command-line entry; module-level `HYPERPARAMETERS`; one run folder per setting through the shared `Run` (experiments/shared/runs.py:144) |
| `tests/test_sfm.py` | Contract tests (below) |
| `runs/` | Generated runs; ignored by Git (`.gitignore:30`) |

### Data already on disk

| Recording | Frames used | Reference | Why |
|---|---|---|---|
| TUM fr1/xyz, Task65 every-2nd clip (`outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2`) | 399 | motion-capture path | Same frames as the Task65 rows, so camera scores compare directly |
| TUM fr1/desk, Task65 every-2nd clip (`..._desk_every2`) | 298 | motion-capture path | Same; faster motion, the hard case |
| ICL-NUIM living room 2 (`data/icl_nuim/trajectory2`), every 2nd frame | 440 | exact synthetic path and a reference surface model | Exact poses, no capture timing error; its surface model scores structure in Task72 |

### Settings compared

For each recording: SIFT features with brute-force matching (classic COLMAP) and ALIKED features with LightGlue matching (learned, ONNX on CPU), each with the incremental mapper and the global mapper (GLOMAP inside COLMAP 4.2): four runs per recording, twelve in all, plus one desk run with the published fr1 distortion set (it failed; see Hyperparameters). Camera calibration is fixed to the published values; COLMAP does not refine it.

### Scores and records per run

1. Camera path through Task70: best fit with size (headline, the published monocular score), best fit rigid, relative error over 1 s, frames placed, number of models.
2. Size set once from Depth Anything (deployable): the median over sparse points seen in each frame of (Depth Anything depth at that pixel) / (SfM depth), median over frames; then the best-fit rigid error of the resized path. TUM clips only, from the Task65 saved raw Depth Anything maps (`outputs/task65_runs/{xyz,desk}/depth-anything/*/output/predictions/depth/`). ICL waits for Task72, which runs the depth model on ICL.
3. Wall time per stage (extract, match, map, export), frames per second over the whole run, CPU thread count, peak sparse points; the 1 fps floor is reported, not enforced, because this is an offline diagnostic.

## Why

If an image-only path beats the Kinect-depth tracker, learned depth should stop being used for tracking. If it does not, the problem is in our data or scoring and must be found before more depth work. The saved sparse points are also the size source Task72 needs.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Camera scorer with best-fit fields, per segment | `evaluate()` | walkthrough, scale_drift | experiments/03_camera_pose_estimation/src/evaluation.py:46 (Task70 fields) |
| Score input records and pose contract | `Record`, `Pose` | evaluate | experiments/03_camera_pose_estimation/src/tracking.py:21-27; experiments/shared/contracts.py:39-69 |
| TUM ground-truth reader (8 columns, normalised quaternions) | `read_references` | evaluate callers | experiments/03_camera_pose_estimation/src/evaluation.py:13-34 |
| Run folder lifecycle with timing, source snapshot and hashes | `Run` | experiment runners | experiments/shared/runs.py:144-256 |
| Every-2nd TUM clips with RGB, depth and full ground truth | `scale_drift.make_clip` output | Task65 runs | outputs/task65_clips/*_every2; experiments/02_stereo_depth/scale_drift.py:56 |
| Saved raw Depth Anything maps per frame for those clips | Task65 depth layer | size from depth | outputs/task65_runs/xyz/depth-anything/*/output/predictions/depth.json |
| ICL camera, depth units, pose direction and surface-model alignment | data record | Task72 | data/icl_nuim/conventions.json (fx 481.2, fy -480, cx 319.5, cy 239.5; pose camera-to-world; derived_model_from_compatible_world) |
| Earlier pycolmap run on TUM | archived prototype | none | archive/task00_prototype/README.md:24 (120 images, 0.79 px, 172 s; path never scored) |

No SfM code exists outside the archive (searched `pycolmap`, `incremental_mapping` in experiments/, src/, tools/).

### ICL-NUIM camera handedness

ICL's published calibration has a negative fy: its camera's y axis points up, so its camera frame and pose world are mirror images of COLMAP's (x right, y down, z forward). Camera centres are physical positions, but a mirror cannot be undone by a rotation, so the best fit would fail. The ICL reader therefore converts each true pose T to F·T·F with F = diag(1, -1, 1, 1): this flips the camera's y axis to point down and mirrors the world once, which gives a proper right-handed pose. A test checks that F·T·F has determinant +1 and that camera centres become F·c. COLMAP gets fy = +480 with the image unchanged.

### Steps

1. Tests first (`tests/test_sfm.py`), each seen failing first:
   - TUM and ICL readers: order, frame IDs, timestamps (ICL uses the frame number as its time, as its pose file does), `every` sampling, camera parameters; the ICL true-pose conversion keeps determinant +1 and maps centres through F.
   - Export on a pycolmap synthetic reconstruction (`pycolmap.synthesize_dataset`): the saved camera-to-world of each image inverts COLMAP's `cam_from_world` to 1e-9; unplaced images are listed and absent from the path; points and observations round-trip; each model gets its own segment ID.
   - Scoring: a saved path equal to a known transform of the reference scores best fit with size 0; frames placed counts unplaced frames; the depth-model size of a synthetic case where depth = 2.5 × SfM depth is 2.5.
   - End to end on 12 rendered views of a textured synthetic scene (homography renders of a textured plane plus a box) with known poses: SIFT incremental places all views and best fit with size < 1% of the path length. Marked slow if over 60 s.
2. Implement in the order sequences → export → scoring → reconstruct → run_sfm.
3. Run the twelve settings on CPU, one at a time, from a queue script; free disk is checked before each run (stop below 30 GB, the Task65 guard).
4. Write the result tables, timing and an "edge view" paragraph into `experiments/sfm/README.md`; add the folder to experiments/README.md; update the task board.

## Hyperparameters

| name | value | source |
|---|---|---|
| COLMAP | 4.2.1 official Windows build without CUDA (`third_party/colmap-4.2.1-windows-nocuda/bin/colmap.exe`, zip SHA-256 c493d88cb4a43f21afba42cb55bf786e5434a0420e73db0ba1454c5d8b3686ae) runs extraction, matching and both mappers; pycolmap 4.2.1 in `.venv-sfm` only reads the saved models | n/a: proposed by Claude 2026-10-13, not owner-ruled. The pycolmap 4.2.1 Windows wheel aborts on ALIKED extraction (no ONNX runtime in the wheel; tested 2026-10-13), while the official build ships onnxruntime.dll and ran ALIKED + LightGlue on 6 TUM frames |
| TUM camera | PINHOLE fx = fy = 525, cx 319.5, cy 239.5, no distortion (the TUM page's recommended default set, also used by experiment 03, dataset.py:13). The published fr1 FULL_OPENCV set (517.3, 516.5, 318.6, 255.3, k1 0.2624, k2 -0.9531, p1 -0.0054, p2 0.0026, k3 1.1633) is kept as a comparison (`--calibration fr1`) | inherited experiment 03; deviates from the plan's fr1 set because on desk that set gave 2,171 verified pairs but no initial pair for the incremental mapper and no 3D points for the global mapper, while the default set placed all 298 frames (runs 2026-10-13); not owner-ruled |
| ICL camera | PINHOLE fx 481.2, fy 480 (sign flipped, see above), cx 319.5, cy 239.5 | inherited data/icl_nuim/conventions.json |
| calibration refinement | off (focal length, principal point and distortion fixed) | n/a: proposed by Claude 2026-10-13, not owner-ruled |
| frames | TUM: every Task65 clip frame (every 2nd raw frame); ICL: every 2nd of 880 posed frames (frames 1..880; image 0 has no pose) | inherited Task65 clips; ICL spacing proposed by Claude 2026-10-13, not owner-ruled |
| features | SIFT, at most 8,192 per image; ALIKED_N16ROT, at most 2,048, minimum score 0.2; image size unchanged (640×480) | n/a: COLMAP 4.2.1 defaults (`colmap feature_extractor -h`) |
| matching | sequential, overlap 10, quadratic overlap on, loop detection off (COLMAP 4.2.1 defaults); SIFT_BRUTEFORCE (ratio 0.8, cross check) or ALIKED_LIGHTGLUE (minimum score 0.1); geometric verification defaults. The same matches feed both mappers | n/a: COLMAP 4.2.1 defaults (`colmap sequential_matcher -h`); loop detection off because it needs a downloaded vocabulary tree |
| mapper | `colmap mapper` (incremental) or `colmap global_mapper` (GLOMAP), COLMAP 4.2.1 defaults except random seed 0 and calibration refinement off (`ba_refine_focal_length 0`, `ba_refine_extra_params 0`; principal point is off by default); multiple models kept | n/a: COLMAP defaults; seed and fixed calibration proposed by Claude 2026-10-13, not owner-ruled |
| threads | all 32 logical CPUs (`num_threads` -1) | inherited Task65 (library defaults) |
| depth-model size | median over frames of median over each frame's observed points of Depth Anything / SfM depth; points with SfM depth ≤ 0 or Depth Anything invalid skipped; frames with fewer than 20 points skipped | n/a: proposed by Claude 2026-10-13, not owner-ruled; Task62 found 10-50 points per frame enough |
| scoring | Task70 fields; association tolerance 0.02 s (TUM), exact frame number (ICL) | inherited Task70 |
| disk guard | stop below 30 GB free | inherited Task65 |
| devices | CPU only | confirmed 2026-10-08 (owner: "Dont use GPU without permission") |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Image list and calibration | `src/sequences.py` | reconstruct, export, scoring | ordered names, frame IDs, timestamps; camera model string and parameters | `input/sequence.json` in each run, with image SHA-256 |
| COLMAP database and models | `src/reconstruct.py` | export | SQLite and COLMAP binary model under `debug/colmap/` | kept for inspection; a rerun makes a new run folder |
| Camera path | `src/export.py` | scoring, Task72, Task76 | `output/trajectory.txt`, TUM format, camera-to-world in SfM units (no metric size), one line per placed frame; `output/frames.json` with each frame's model ID or "unplaced" | sealed by the run manifest |
| Sparse points and observations | `src/export.py` | Task72 | `output/points.npz` (xyz, rgb, error_px, track_length, model_id); `output/observations.npz` (frame index, point index, u, v) | sealed |
| Scores | `src/scoring.py` | README tables | `output/scores.json`, `allow_nan=False` | sealed |

- **Source of truth:** the recording files plus the run's `input/sequence.json`; ground truth is read only by scoring.
- **Process boundary:** none; one Python process per run.
- **Failure after each step:** an exception marks the run failed with timings kept (`Run.__exit__`); a reconstruction with no model is saved as an incomplete run with its reason, not as zero error.
- **Fresh-deployment path:** create `.venv-sfm` from `requirements.txt`, then `python -m experiments.sfm.run_sfm --recording tum:<clip> --features sift --mapper incremental --run-root experiments/sfm/runs`.
- **Backward compatibility:** no existing file changes behaviour; `.venv-colmap` (pycolmap 3.12.6) is left as it is.

## Verification

- Contract test `experiments/sfm/tests/test_sfm.py` with the assertions in step 1; Ruff clean.
- Before: our tracker with Kinect depth, best fit with size 34 mm (xyz) and 112 mm (desk); with Depth Anything and the overlap chain 128 and 438 mm. Target above. All twelve settings are reported, including failures and partial models.
- Plan review: no independent plan reviewer was run (the owner has not asked for agents); the task was started with the journaled `--force` override and this is recorded in Receipts.

## Receipts

| field | value |
|---|---|
| closing commit | not committed; the owner commits (no commit was requested) |
| files changed | new experiments/sfm/ (README.md, requirements.txt, run_sfm.py, report.py, src/sequences.py, src/reconstruct.py, src/export.py, src/scoring.py, tests/test_sfm.py); experiments/README.md row; COLMAP 4.2.1 build unpacked to third_party/ (ignored by Git) |
| test | experiments/sfm/tests/test_sfm.py 11 passed in `.venv-sfm` (includes an end-to-end COLMAP run on 12 rendered views); Ruff clean. Tests were written alongside the code in a scratch package, not seen failing first |
| before / after | best fit with size: TUM xyz 34 mm (walkthrough tracker, Kinect depth) / 11.9 mm (SfM SIFT, both mappers); TUM desk 112 mm / 24.0 mm incremental, 23.6 mm global; all TUM frames in one model; ICL 34.1 mm incremental (433/440 placed), 57.2 mm global (429/440) |
| result | Target met for SIFT: below the Kinect-depth tracker on both TUM clips with at least 95% of frames placed. Depth Anything as the size source is 1.3-1.4 times too large (size error alone: 58 mm xyz, 357-361 mm desk). Published fr1 distortion set failed on desk (no initial pair); default calibration used. ALIKED + LightGlue runs were still in the background queue at close |

Notes / caveats / follow-ups:

- Plan review: no independent plan reviewer was run (the owner has not asked for agents); started with the journaled `task.js start 67 --force` override on 2026-10-13.
- Deviations: TUM camera is the default set, not the planned fr1 distortion set (it failed; Hyperparameters); ALIKED keeps COLMAP's default 2,048 features, not the planned 4,096; all COLMAP stages run through the official command-line build because the pycolmap wheel aborts on ALIKED; one run per recording and feature type feeds both mappers from one set of matches.
- Filed 2026-10-08 at the owner's request during Task65. Rescoped 2026-10-13: the original plan was our own OpenCV tracker; replaced by an established system in a standalone `experiments/sfm/` folder (owner, 2026-10-13).
- Learned methods (Depth Anything 3, DROID-SLAM, DPVO, MapAnything, FastMap) are Task74. ORB-SLAM3 is GPLv3 and stays a published reference.
- Sources: [COLMAP](https://colmap.github.io/), [TUM file formats and fr1 calibration](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats), papers in research/structure_from_motion/papers/.

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
- experiments/sfm/README.md (+103 -0, 103 lines)
- experiments/sfm/report.py (+68 -0, 68 lines)
- experiments/sfm/requirements.txt (+10 -0, 10 lines)
- experiments/sfm/run_sfm.py (+135 -0, 135 lines)
- experiments/sfm/src/export.py (+101 -0, 101 lines)
- experiments/sfm/src/reconstruct.py (+96 -0, 96 lines)
- experiments/sfm/src/scoring.py (+101 -0, 101 lines)
- experiments/sfm/src/sequences.py (+133 -0, 133 lines)
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

- `.venv-sfm pytest experiments/sfm/tests -> 11 passed; ruff -> clean; runs: TUM xyz SIFT 11.9 mm, desk 24.0/23.6 mm, ICL 34.1/57.2 mm best fit with size (python -m experiments.sfm.report)`
- cost: 19 min from begin to finish; Claude tokens 16,249,829 (fresh input 42,535, cache read 16,176,341, output 30,953; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.26 (was 0.42)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 20 in 10254 words: bold-labels "5 items", same-opening "the", one-line-closer "[RTAB-Map] records that run's limits.", same-opening "it", same-opening "a"

## Left over

ALIKED+LightGlue runs on desk, xyz and ICL still running in the background queue (%TEMP%/sfm_queue.log); add their rows to experiments/sfm/README.md with the report command
