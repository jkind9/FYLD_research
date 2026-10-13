---
id: "65"
title: Diagnose and fix frame to frame depth scale drift
status: in_progress
priority: HIGH
type: experiment
approval_status: owner brief 2026-10-08 ("Diagnose before fixing ... shortlist and test"); GPU use not permitted without asking; settings marked "proposed by Claude" are not owner-ruled
blocked_by: []
blocks: []
verification_test: "src/walkthrough/tests/test_depth_scale.py"
plan_reviewed: 2026-10-08 PASS
files:
  - src/walkthrough/**
  - tools/demos/run_report.py
  - tools/demos/run_pages.py
  - tools/demos/web/page_run.js
  - tools/demos/tests/test_run_report.py
  - experiments/02_stereo_depth/scale_drift.py
  - experiments/02_stereo_depth/tests/test_scale_drift.py
docs:
  - experiments/02_stereo_depth/README.md
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: "outputs/task64_report_runs/depth-anything/20261008T132653.807304Z_bb77fcc1f0db45dab0d2eb7d5c464e2a (30 TUM xyz frames, every 2nd, CPU)"
  field: "camera position RMSE; median depth gap between overlapping surfaces 20 frames apart (own poses, median over 10 pairs); depth-layer fps; processing fps (frames / sum of all prediction_* stage times, tools/demos/run_report.py:76-97)"
  baseline_value: "218 mm; 155 mm; 3.37 fps depth layer (prediction_depth 8.90 s for 30 frames, metadata/timing.json); 0.92 fps processing (raw Depth Anything V2 Metric Small, all CPU)"
  target: "a deployable (RGB-only or phone-sensor) depth choice with camera RMSE below 218 mm and lag-20 surface gap below 155 mm on the 30-frame clip, and both lower than raw Depth Anything on full xyz and desk, with its depth layer at >= 1 fps on CPU; processing fps reported for every run"
created: 2026-10-08
last_updated: 2026-10-08
superseded_by: null
---

# Task 65 — Diagnose and fix frame to frame depth scale drift

## In plain English

A model that guesses distance from a single photo gets the shape of a room right but its size wrong, and wrong by a different amount in each photo. When the photos are combined, the same wall appears several times at different distances, and the camera path goes wrong. This task first measures how much of the damage comes from that changing size, then tries ways to keep the size the same from photo to photo: one that uses only the video, one that uses the camera movement a phone already measures, and a newer model built for video. Each is scored against the recording's measured depth and camera path, with its speed, and compared with the current results.

## What

1. **Measure the duplication.** New `src/walkthrough/consistency.py`: `surface_gap(...)` places frame B's depth points in frame A's camera using the two camera-to-world poses (camera axes x-right, y-down, z-forward; plain pinhole, distortion ignored as in experiments/03_camera_pose_estimation/src/dataset.py:13). It keeps points more than 0.05 m in front of A, rounds them to the nearest pixel, keeps only the nearest B point per A pixel (a z-buffer, so hidden surfaces do not count), and reports the median signed and absolute difference from frame A's own depth along A's view axis over pixels valid in both, plus the overlap fraction. No overlap gives `None` gaps and overlap 0. `gap_by_lag(...)` runs it for each frame against the frame `lag` frames earlier, only inside one tracking world/segment.
2. **Score scale per frame.** `src/walkthrough/validation.py` `_depth`: each per-frame row gains `scale_ratio` (median predicted/reference over pixels valid in both; 1.34 means 34% too far), `fit_scale`, `fit_shift` (least-squares metric scale and shift) and `fitted_abs_rel` (AbsRel after that per-frame fit, via `score_shape_to_metric`). A frame with fewer than 2 overlapping pixels gets `None` for these fields, never NaN, following experiments/02_stereo_depth/scoring.py:137-145. This is a scoring view; the method never sees it.
3. **Report pages.** `tools/demos/run_report.py`, `run_pages.py`, `web/page_run.js`. Every NaN becomes `null` in `run_report.py` before page data is written: page.py:64 writes bare `NaN`, which `JSON.parse` in viewer.js:7 rejects. `chart()` in page_run.js learns to skip nulls and to draw negative values with a zero line. The depth page adds "scale ratio per frame" and "error left after a per-frame fit" charts. The surface page adds per-frame surface-gap charts at lags 1 and 10 and a table of median gap at lags 1, 5, 10, 20 and the longest available up to 29.
4. **Scale corrections as swappable depth choices.** New `src/walkthrough/steps/depth_scale.py`: `ScaleCorrected(base, scale)` is a `DepthMethod` that runs a base depth method and passes all its frames through one scale source:
   - `ReferenceFrameScale` (reference control): per-frame scale only (least squares through zero, experiments/02_stereo_depth/geometry.py:86-87) against all Kinect pixels, so it changes size, not shape. Tests the hypothesis; upper bound only. Task62 already has the every-pixel scale-and-shift numbers.
   - `ReferenceGlobalScale` (reference control): one factor for the whole recording (median over frames of per-frame median reference/predicted). Separates "biased overall" from "inconsistent per frame".
   - `OverlapChainScale` (deployable, RGB only): for frame k, detect corners in each earlier partner frame k-1, k-2, k-4, k-8, track them into frame k with pyramidal Lucas-Kanade optical flow, back-project them with the partner's already-corrected depth (base depth below 4 m only, tracking's range, contracts.py:205), solve PnP with RANSAC, move the inlier points into frame k, and take the median of (PnP depth / base depth) as that partner's estimate; frame k's correction is the median over partners. Frame 0's correction is 1. After all frames, every correction is divided by their median so the overall scale stays the base model's own. A frame with no usable partner keeps the previous correction and a `UserWarning` is raised. This is an offline method (hosted, after capture): normalisation needs the whole run, so all base frames are buffered, and the depth layer's first per-frame timing sample holds the whole computation; only the layer total fps is reported.
   - `PoseTriangulatedScale` (reference control standing in for ARCore or IMU poses): uses the recording's motion-capture poses with added noise as the "phone's" metric camera motion. For frame k it tracks corners to the nearest frame at least 5 cm away, triangulates them with the metric relative pose and takes the median (triangulated depth / base depth) as frame k's scale. Frames without a partner, or without a pose within 0.02 s, take the scale linearly interpolated in time from the nearest frames that have one (the nearest value at the ends); if no frame has one, the layer fails.
   - **Per-frame diagnostics.** `DepthPrediction` (src/walkthrough/steps/contracts.py:57-63) gains an optional `diagnostics: dict | None = None`; the depth layer saves it in that frame's `depth.json` row as `method_diagnostics` (absent stays absent). Scale sources record `scale`, and the chain also `partners_used` (a count) and `fallback` (a bool). Diagnostic values must be plain Python `float`/`int`/`bool` or `None`, and finite; the depth layer converts numpy scalars and refuses NaN with a `ValueError` (depth.json is written with `allow_nan=False`, experiments/shared/runs.py:31). `DepthArtifact` (contracts.py:103-108) marks the new key `NotRequired`. Every scale source rebuilds the valid mask after scaling (finite, > 0, ≤ 20 m), as ScaledZipDepth does at src/walkthrough/steps/depth.py:242-247.
5. **Command line.** `src/walkthrough/cli.py`: `--depth-scale reference-frame|reference-global|overlap-chain|pose-triangulated` on top of `--depth depth-anything` (or `video-depth-anything` if step 9 adds it); reference choices need `--dataset`; `--depth-scale` with any other depth choice is refused before a run folder exists. `DepthAnythingV2Metric` defaults to `cuda` (depth.py:92), so the CLI and every script pass `device="cpu"` explicitly.
6. **Diagnosis and comparison script.** `experiments/02_stereo_depth/scale_drift.py`:
   - Makes full-length clips of TUM xyz and desk. From the RGB rows that have a depth row within 0.02 s, it keeps every 2nd one (a pose is not required: the tracking scorer skips frames without one, experiments/03_camera_pose_estimation/src/evaluation.py:53-56, and requiring one leaves a 0.132 s gap in xyz at rows 201-202), copies the RGB and nearest depth images, writes `rgb.txt`, `depth.txt`, the full `groundtruth.txt` and a `CLIP_SOURCE.txt`, and refuses to write a clip whose largest RGB gap exceeds 0.1 s (the tracker's origin reset). This drops desk's first frames, whose depth starts 0.58 s after its RGB. The nested desk folder is found with experiments/02_stereo_depth/run.py `_resolve_sequence_root`.
   - Reads finished walkthrough runs and writes one JSON and a markdown table: per run the depth AbsRel, fitted AbsRel, scale-ratio range and median frame-to-frame change, Spearman correlation between |frame-to-frame scale change| and |frame-to-frame camera-error change|, surface gap by lag with own poses and with motion-capture poses (pairs that include a frame without a motion-capture pose within 0.02 s are skipped and counted; one xyz frame, full-recording row 202, has none), camera RMSE, plane area, depth-layer fps and processing fps.
   - Declares a module-level `HYPERPARAMETERS` dict written into its JSON, and writes JSON with `allow_nan=False` after turning NaN into null.
7. **Runs (CPU only).** On the 30-frame clip and both full-length clips: raw Depth Anything; + reference frame scale; + reference global scale; + overlap chain; + pose-triangulated; ZipDepth scaled from 50 Kinect pixels; Kinect depth. All six layers run on every clip, so every run can complete (a skipped layer marks the run failed: src/walkthrough/records.py:29-30, pipeline.py:99-100); objects cost only about 14 MB of a 468 MB run. If tracking loses a frame (tracking.py:100-104), that run is recorded as a failure with the frame named; it is not retried with other settings. Disk: about 15.6 MB per frame and 697 frames for both full-length clips (399 xyz, 298 desk), so about 10.9 GB per method; 7 methods about 77 GB, about 88 GB with video depth, against 146 GB free. The script checks free space before each full-length run and stops below 30 GB; nothing is deleted without the owner's say.
8. **Research write-up.** A verified survey of six method families (temporal scale alignment, video depth models, multi-view/SLAM, structure from motion and splatting, ARCore/ARKit scale, TSDF fusion), with input, metric-scale source, published accuracy and speed, size, licence and phone/host feasibility, goes into the experiment 02 README. The survey (2026-10-08) found one permissive video depth model: Metric Video Depth Anything Small (`depth-anything/Metric-Video-Depth-Anything-Small`, Apache-2.0 code and Small weights, 28.4M parameters, 116 MB, arXiv 2501.12375). No CPU speed is published.
9. **Third option: Metric Video Depth Anything Small** (deployable, RGB only). Download the code at a pinned commit and the Small metric weights into `data/models/` (hashes recorded), then run a CPU speed check on the 30-frame clip. If it reaches ≥ 1 fps on CPU, add `MetricVideoDepthAnything` in a new `src/walkthrough/steps/video_depth.py` as a base depth choice (`--depth video-depth-anything`) and run it on the three clips, raw and with the overlap chain. If it is slower than 1 fps, record the measured speed and stop there. Its code is imported from its own folder on `PYTHONPATH`, like ZipDepth; extra Python packages, if any, are pinned in `experiments/02_stereo_depth/requirements-task65-video-depth.txt`. The downloaded repository is kept in its own folder and used only through its documented model class.

## Why

Same 30 frames, only depth changed: raw Depth Anything gives camera RMSE 218 mm and desk-plane area 7.44 m²; Kinect 21 mm and 2.21 m²; ZipDepth scaled per frame from 50 Kinect pixels 72 mm and 3.45 m². A first look (scratch analysis 2026-10-08 on the three saved runs) shows Depth Anything's median predicted/Kinect ratio moves 1.21-1.63 across the clip, and at frame 16 it jumps 1.39 → 1.62 while camera error jumps 147 → 337 mm. With the run's own poses, neighbouring frames' surfaces agree to 16 mm, because odometry turns the scale jump into camera motion. Surfaces 20 frames apart sit 155 mm apart (median of 10 pairs; Kinect 13 mm, scaled ZipDepth 25 mm), and 29 frames apart 195 mm. With motion-capture poses, neighbouring Depth Anything frames disagree by 42 mm. Task62 showed a per-frame scale and shift brings AbsRel 0.345 → 0.066. The hypothesis is that inconsistent per-frame scale, not shape, is the main failure; if so, a cross-frame scale fix should recover most of the gap at ≥ 1 fps.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Back-projection of a depth grid to camera points, and rigid transforms | `backproject`, `project`, `transform_points` | surface layer `metric_points` | experiments/shared/geometry.py:28,42,69; src/walkthrough/steps/surface.py:45-47 |
| Saved poses rebuild through one reader | `read_pose` | validation `_tracking` | src/walkthrough/steps/contracts.py:187-191; src/walkthrough/validation.py:51 |
| Recorded TUM depth reader with timestamp pairing (reference control) | `RecordedSensorDepth` | depth scorer, report, ScaledZipDepth | src/walkthrough/steps/depth.py:43-79 |
| Depth Anything V2 metric adapter (base method), default device cuda | `DepthAnythingV2Metric` | CLI `depth_choice` | src/walkthrough/steps/depth.py:82-157 (device at :92); src/walkthrough/cli.py:43-44,76 |
| Mask rebuild after scaling | `_predict_scaled_zipdepth` | depth layer | src/walkthrough/steps/depth.py:242-247 |
| Metric least-squares scale (and scale-only) fit and per-frame shape alignment | `fit_native_alignment`, `align_shape_to_metric` | sparse study, scoring | experiments/02_stereo_depth/geometry.py:56,86-87,106 |
| Raw metric depth score, aligned score and pooling; None for empty regions | `score_depth`, `score_shape_to_metric`, `aggregate_scores` | validation `_depth` | experiments/02_stereo_depth/scoring.py:19,34,137-145; experiments/02_stereo_depth/evaluate.py:95; src/walkthrough/validation.py:76-99 |
| Motion-capture pose reader (normalises rounded quaternions) | `read_references` | `ReferencePoses`, tracking scorer | experiments/03_camera_pose_estimation/src/evaluation.py:13-34; src/walkthrough/steps/tracking.py:65 |
| Streamed nearest-timestamp matching for reference adapters | `nearest_references` | reference controls | src/walkthrough/steps/contracts.py:166-179 |
| Depth layer checks grid, mask, order and count, and records the control label | `depth.run` | pipeline | src/walkthrough/steps/depth.py:251-303 |
| A run completes only when all six layers complete | `Result.complete`, `stop_incomplete` | pipeline, report | src/walkthrough/records.py:29-34; src/walkthrough/pipeline.py:99-100 |
| Tracking starts a new origin when frames are > 0.1 s apart (why clips are every 2nd frame) | experiment 03 tracker | `CpuOdometry` | experiments/03_camera_pose_estimation/src/tracking.py:70 |
| Nested TUM folder resolution | `_resolve_sequence_root` | experiment 02 runner | experiments/02_stereo_depth/run.py (`_resolve_sequence_root`) |
| Report data reads saved run files; chart helper draws one per-frame series; processing fps definition | `run_report.depth_data`, `surface_data`, `overview_data`; `chart()` | `run_pages._depth`, `_surface`, `_overview` | tools/demos/run_report.py:76-97,103-143,175-204; tools/demos/web/page_run.js:7,59-70 |
| No optical-flow, PnP or triangulation code exists in the repo | — | — | searched `goodFeaturesToTrack`, `calcOpticalFlowPyrLK`, `solvePnP`, `triangulatePoints`, `findEssentialMat`, `recoverPose` across experiments/, src/, tools/, archive/: only ORB in experiments/06_object_recognition/experiments/01_detection/floor.py:41 (floor features, unrelated) |

### Steps

1. Tests first (each seen failing before the code exists):
   - `src/walkthrough/tests/test_consistency.py`: two views of a fronto-parallel plane at 2 m with exact poses give gap 0 ± 1e-9 and overlap > 0.9; scaling frame B's depth by 1.1 gives median signed gap +0.2 m ± 0.01; a sideways camera move of 0.1 m with consistent depth gives gap below 1 mm; a nearer surface hiding a farther one keeps only the nearer point per pixel; frames that see nothing in common return overlap 0 and `None` gaps, not zeros; frames in different tracking origins are skipped by `gap_by_lag`.
   - `src/walkthrough/tests/test_depth_scale.py` on a synthetic textured plane rendered by homography for known poses, with base depth = true depth × a per-frame factor (1.0, 1.3, 0.9, 1.6, ...): `ReferenceFrameScale` output equals true depth within 1e-6; `ReferenceGlobalScale` applies one factor to every frame; `OverlapChainScale` output/true ratio varies by less than 3% across frames (raw base varies 78%); `PoseTriangulatedScale` with noise 0 gives output/true ratio within 3% of 1 on every frame; control labels are `reference`, `reference`, `None`, `reference`; the chain receives no reference path; `ScaleCorrected.name` names both parts; a frame with no partner in the chain raises a `UserWarning` and keeps the previous correction; method diagnostics reach `depth.json` as `method_diagnostics`, a numpy float32 diagnostic is saved as a plain number and a NaN diagnostic fails the layer with a named status; a scaled pixel that becomes ≤ 0 or > 20 m is invalid, not an error; an empty frame list returns nothing; inputs are not mutated.
   - `src/walkthrough/tests/test_depth_score.py`: prediction = 1.3 × reference gives `scale_ratio` 1.3, `fit_scale` ≈ 1/1.3, `fitted_abs_rel` ≈ 0; a frame with no overlap gives `None` scale fields and scores.json still writes.
   - `tools/demos/tests/test_run_report.py`: depth page data carries `scaleRatio` equal to the scorer's per-frame values; surface page data carries a `gapByLag` table and a per-frame lag-1 series of the right length with `null`, not NaN, for frames without a partner; every page's embedded JSON parses with a strict parser that rejects NaN.
   - `src/walkthrough/tests/test_imports_cli.py`: `--depth-scale overlap-chain` with `--depth depth-anything` builds `ScaleCorrected(DepthAnythingV2Metric(device="cpu"), OverlapChainScale)`; `--depth-scale` with `--depth recorded` is refused; `--depth-scale pose-triangulated` without `--dataset` is refused before a run folder exists.
   - `experiments/02_stereo_depth/tests/test_scale_drift.py`: the clip maker drops RGB rows without depth within 0.02 s, keeps every 2nd of the rest, pairs each with the nearest depth row, and refuses a clip with an RGB gap over 0.1 s; the summary reads two tiny fake runs and reports their known numbers; its JSON contains no NaN.
2. Implement in the order consistency → scorer → scale sources → CLI → report → script. Full walkthrough, experiment 02, experiment 05 and demo suites pass; Ruff clean.
3. Diagnose: run the 30-frame clip and both full-length clips with raw Depth Anything, + reference frame scale, + reference global scale, ZipDepth-scaled and Kinect; write the diagnosis table. The hypothesis is confirmed if reference frame scale cuts camera RMSE and the lag-20 surface gap by at least half against raw Depth Anything on each clip, while reference global scale does not (thresholds proposed by Claude 2026-10-08).
4. Fix: run overlap chain and pose-triangulated on the same three clips. On the 30-frame clip also run the chain's smoothing ablation (5-frame median of corrections) and pose-triangulated with σ = 0, so the noise's own effect is visible (5 mm on a 50 mm baseline can move one frame's scale by up to about 14%). Step 9 (video depth) follows. Report pages for every run.
5. Merge the survey (each source used in a recommendation spot-checked by opening it) into the experiment 02 README with the result tables; update the walkthrough README choices table, the task board and this file.

## Hyperparameters

| name | value | source |
|---|---|---|
| base depth model and device | Depth Anything V2 Metric Indoor Small, `data/models/depth_anything_v2_metric_indoor_small`, 20 m cap; device passed explicitly as `cpu` | inherited src/walkthrough/cli.py:29-30,76 (checkpoint, CPU default) and src/walkthrough/steps/depth.py:93 (cap) |
| CPU threads | PyTorch and OpenCV defaults on the 32-thread Ryzen 9 9950X; `torch.get_num_threads()` recorded with each speed number | inherited src/walkthrough/README.md throughput table (same defaults) |
| tracking, surface, mapping | `CpuOdometry`, `MetricPoints`, `GridFootprint` defaults (5 cm cells) | inherited src/walkthrough/steps/tracking.py:42-49; src/walkthrough/README.md mapping row |
| objects (all clips) | YOLO26x CPU, 0.35 m / 0.05 m | inherited src/walkthrough/README.md (pilot/replay.py:46) |
| full-length clip frame spacing | every 2nd of the RGB rows that have depth within 0.02 s (about 15 Hz), nearest depth row each, full groundtruth; largest gap ≤ 0.1 s | deviates from the full 30 Hz recording because a full-rate run is about 12 GB on disk (468 MB per 30 frames); every 2nd is the spacing the 30-frame clip already uses (CLIP_SOURCE.txt); proposed by Claude 2026-10-08, not owner-ruled |
| surface-gap lags | 1, 5, 10, 20 and the longest available up to 29 frames; headline is lag 20 | proposed by Claude 2026-10-08, not owner-ruled; lag 29 on the 30-frame clip is a single pair |
| surface-gap pixel rule | nearest-pixel projection, nearest B point per A pixel (z-buffer), both depths valid, projected depth > 0.05 m, no cap beyond each run's own mask; median over pixels; pairs only within one world/segment | proposed by Claude 2026-10-08, not owner-ruled |
| camera model | plain pinhole, lens distortion ignored | inherited experiments/03_camera_pose_estimation/src/dataset.py:13 |
| per-frame score fit | metric least squares scale and shift over all pixels valid in both | inherited experiments/02_stereo_depth/geometry.py:56,106 |
| reference frame and global scale | frame: least-squares scale through zero over all valid pixels; global: median over frames of per-frame median(reference/predicted) | proposed by Claude 2026-10-08, not owner-ruled |
| scaled-depth validity | finite, > 0, ≤ 20 m after scaling | inherited src/walkthrough/steps/depth.py:242-247 |
| chain partner frames | k-1, k-2, k-4, k-8; corners re-detected in each partner; frame 0 correction 1 before normalisation | proposed by Claude 2026-10-08, not owner-ruled |
| corner detection | `goodFeaturesToTrack` up to 500 corners, quality 0.01, min distance 7 px | proposed by Claude 2026-10-08, not owner-ruled (OpenCV tutorial values) |
| optical flow | pyramidal Lucas-Kanade, 21 px window, 3 levels, stop after 30 iterations or 0.01 px; forward-backward check ≤ 1 px | proposed by Claude 2026-10-08, not owner-ruled |
| PnP | `solvePnPRansac` with `SOLVEPNP_ITERATIVE`, 2 px reprojection threshold, 100 iterations, confidence 0.99, ≥ 30 inliers per partner; partner depth < 4 m only | proposed by Claude 2026-10-08, not owner-ruled |
| chain correction | median of PnP depth / base depth over inliers; median over partners; whole-run median normalised to 1 | proposed by Claude 2026-10-08, not owner-ruled |
| chain smoothing ablation | none (default) vs 5-frame causal median of corrections, 30-frame clip only | proposed by Claude 2026-10-08, not owner-ruled |
| triangulation | partner: nearest frame in time with ≥ 0.05 m camera baseline, searched ±10 frames; same corner and flow settings as the chain; `cv2.triangulatePoints` (linear); keep points with positive depth in both views, reprojection error ≤ 2 px and parallax ≥ 1°; ≥ 20 points; pose time tolerance 0.02 s; missing frames linearly interpolated in time | proposed by Claude 2026-10-08, not owner-ruled |
| simulated phone pose noise | independent Gaussian translation noise σ = 5 mm per frame (σ = 0 also on the 30-frame clip), seed 0, no rotation noise | proposed by Claude 2026-10-08, not owner-ruled; survey: ARCore 1.29 final drift 0.07-0.12 m over indoor walks (Kim et al. 2022, arXiv 2207.06780), which is drift over a walk, not per-frame noise |
| chain anchored to poses (added 2026-10-08) | run-wide factor = median over frames with a measured (not interpolated) triangulated scale of triangulated / chain scale; chain and triangulation settings as above | proposed by Claude 2026-10-08, not owner-ruled |
| ZipDepth-scaled and Kinect runs | as Task63 (50 points, seed 0) | inherited task_list/open/63 hyperparameters |
| video depth model | Metric Video Depth Anything Small, upstream inference defaults (input size, window, FP32 on CPU) read from the pinned commit at download | proposed by Claude 2026-10-08, not owner-ruled; upstream values recorded in Receipts |
| video depth speed gate | ≥ 1 fps on CPU over the 30-frame clip, model loading excluded | confirmed 2026-10-07 (owner 1 fps floor, task_list/README.md) |
| disk guard | stop before a full-length run when free space is below 30 GB | proposed by Claude 2026-10-08, not owner-ruled |
| devices | CPU only for every run | confirmed 2026-10-08 (owner: "Dont use GPU without permission") |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Base depth frames | `DepthAnythingV2Metric` src/walkthrough/steps/depth.py:130-157 | `ScaleCorrected` (new) | camera-axis metres, NaN where invalid, boolean mask, RGB grid | in memory; all frames buffered as float32 so the chain and normalisation can see the whole run (about 1.2 MB per frame, about 0.5 GB for 400 frames) |
| Corrected depth and diagnostics | `ScaleCorrected` | depth layer src/walkthrough/steps/depth.py:251-303, then every later layer | same contract; optional `method_diagnostics` per row; run labelled with the scale source's control | sealed run files |
| Kinect depth and motion-capture poses | `RecordedSensorDepth`, `read_references` | only reference-control scale sources and scorers | metres; camera-to-world 4x4 in metres | original TUM files |
| Surface gap | `consistency.py` (new) | report pages, `scale_drift.py` | metres along the earlier camera's view axis, per frame and lag, within one world/segment; `None` when there is no overlap | recomputed from sealed run files on demand |

- Source of truth: TUM files plus the settings above; every run is reproducible from them (seed 0 for noise).
- Only reference-control choices touch Kinect depth or motion-capture poses; `OverlapChainScale` receives colour frames and the base depth only. A test asserts its control is `None` and that it holds no reference path.
- Process death mid-run leaves an incomplete run folder; rerun into a fresh folder. The report and diagnosis script read only runs whose status is complete, except that a run whose tracking lost a frame is reported as that failure.
- Backward compatibility: existing depth choices, CLI flags and score fields keep their meaning; new score fields and `method_diagnostics` are additions; `DepthPrediction`'s new field has a default, so existing methods are unchanged.

## Verification

- Contract test `src/walkthrough/tests/test_depth_scale.py` with the assertions in Step 1; plus the consistency, scorer, report, CLI and script tests named there. Red first for each.
- Before (30-frame clip, raw Depth Anything): camera RMSE 218 mm, lag-20 surface gap 155 mm, depth layer 3.37 fps (`prediction_depth` stage), processing 0.92 fps. Target: overlap chain, pose-triangulated or video depth below both accuracy numbers with its depth layer at ≥ 1 fps; processing fps reported beside it. The whole CPU pipeline with Depth Anything is already 0.92 fps, so a depth change alone cannot lift it over 1 fps; that is reported, not hidden. The Receipts give the after numbers on all three clips next to the Kinect-scaled ZipDepth and Kinect rows, with reference controls labelled.

## Receipts

| field | value |
|---|---|
| commit | `bfb70f2` contains the implementation; task remains open |
| files changed | Scale scoring and correction, report charts, experiment runner and result notes, tests, and the declared walkthrough and experiment READMEs |
| test | Regression tests are included in the change; tests were not run during this commit request |
| before / after | On the 30-frame xyz clip, raw Depth Anything was 218 mm camera RMSE and 152 mm lag-20 surface gap. The RGB-only overlap chain measured 113 mm and 32 mm, at 3.25 depth-layer fps. Full-length results are not yet summarized. |
| result | The overlap chain is a promising candidate on the short clip. Full xyz and desk queues completed, but their summaries and the final recommendation remain outstanding. |

Notes / caveats / follow-ups:

- Plan review 1, 2026-10-08: FAIL with 4 blocking findings (skipped objects layer marks runs failed; desk's first frames have no depth within 0.02 s; the processing-fps target could not pass and its baseline was 0.92 not 0.97; NaN in page data breaks the browser) and 13 advisory. All applied in this revision.
- Plan review 2, 2026-10-08: FAIL with 1 blocking finding (requiring a pose in the clip maker leaves a 0.132 s gap in xyz) and 2 advisory (depth-layer baseline is 3.37 fps from timing.json, not 3.8; diagnostics must be plain finite numbers). All applied.
- still open because the full-length run results have not been summarized or compared, and the recommendation has not been written. The CPU queues completed on 2026-10-08. Resume by generating the xyz and desk summaries from `outputs/task65_runs/`, adding their tables and the recommendation to the declared READMEs, then completing the remaining review and verification steps.
  Results so far (30-frame xyz clip, camera RMSE / lag-20 surface gap / plane area / depth-layer fps): raw Depth Anything 218 mm / 152 mm / 7.44 m² / 3.48; reference per-frame scale (control) 56 / 33 / 2.63; reference global scale (control) 167 / 49 / 3.04; overlap chain (RGB only) 113 / 32 / 3.86 / 3.25; chain + 5-frame smoothing 145 / 180 / 7.37; triangulated 5 mm noise (control) 4376 / 1346; triangulated exact (control) 242 / 130 / 2.79; Video Depth Anything 93 / 25 / 5.92 / 0.77 fps (fails 1 fps); VDA + chain 63 / 22 / 5.89 / 0.81; ZipDepth 50 Kinect points (control) 72 / 26 / 3.45; Kinect 21 / 14 / 2.21. Full xyz: chain 399 frames, 0 fallbacks; triangulated exact failed at mapping (path drifted, points span 550 m). Owner idea filed as Task67 (track without depth).
- 2026-10-08 addition (Claude, not owner-ruled), decided from the 30-frame results before any full-length result existed: `AnchoredScale(consistent, metric)` and `--depth-scale overlap-chain-pose-anchor`. The chain's frame-to-frame factors are multiplied by one run-wide factor, the median over frames of triangulated/chain scale (frames whose triangulated scale was interpolated are skipped). Reason: on the 30-frame clip the chain was consistent but kept Depth Anything's size (AbsRel 0.359, area 3.86 m²), while exact-pose triangulation had the right size but wobbled (AbsRel 0.113, area 2.79 m², camera RMSE 242 mm). It combines two shortlisted sources and adds no tuned value; 3 tests in test_depth_scale.py and 1 in test_imports_cli.py. Runs: 30-frame clip at 5 mm and 0 noise; full xyz and desk at 0 noise.
- 2026-10-08 caveat: about 20 s of pytest ran on the same CPU at the start of the full xyz Depth Anything run (15:52), which may lower that run's fps slightly.
- 2026-10-08 30-frame finding: smoothing the chain's corrections over 5 frames made it worse (camera RMSE 113 → 145 mm, lag-20 gap 32 → 180 mm), because the correction must follow the model's frame-to-frame jumps. Metric Video Depth Anything Small ran at 0.77 fps (depth layer, CPU, 518 px input), below the 1 fps floor, so per What 9 it was not run on the full-length clips.
- 2026-10-08 deviation (Claude, not owner-ruled): full-length pose-triangulated runs use noise 0 instead of 5 mm. On the 30-frame clip the 5 mm setting gave scale/sensor-fit ratios 0.44-1.76 (camera RMSE 4.4 m), because frame steps are 20-35 mm and independent 5 mm noise per frame swamps them; with exact poses the ratios are 0.64-1.05 (offline check on the saved Depth Anything run). Independent per-frame noise is also unlike phone tracking error, which grows as slow drift. The 30-frame clip keeps both settings. Added CLI flags `--pose-noise-m` and `--chain-smoothing-frames` (tested) so the queue can set them; the first queue was stopped mid-way through the full xyz Depth Anything run and restarted (its partial folder `outputs/task65_runs/xyz/depth-anything/20261008T144321.148301Z_*` is incomplete and not used).
- 2026-10-08 deviation: the planned `requirements-task65-video-depth.txt` was not written; the harness documentation hook refuses creating or editing `.txt` files. The one added package (`easydict==1.13`, LGPL-3.0, installed into `.venv-yolo` from a downloaded wheel) and the code commit and weight hashes are recorded in the experiment 02 README instead.
- Plan review 3, 2026-10-08: PASS; 3 advisory notes applied (697 frames, pose-less frame rule for the motion-capture gap, `partners_used` is a count).
