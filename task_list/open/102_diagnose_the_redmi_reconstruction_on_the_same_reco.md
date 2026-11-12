---
id: "102"
title: Diagnose the Redmi reconstruction on the same recorded walk
status: open
priority: HIGH
type: experiment
blocked_by: ["107", "109"]
blocks: []
verification_test: "src/live/tests/test_sizing.py"
plan_reviewed: null
files:
  - src/live/**
  - research/experiments/01_camera_capture_delivery/host/**
  - research/experiments/01_camera_capture_delivery/tests/**
  - research/experiments/sfm/**
  - tools/demos/**
docs:
  - src/live/README.md
  - research/experiments/01_camera_capture_delivery/README.md
  - learning/05_dense_surfaces.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Diagnose the Redmi reconstruction on the same recorded walk"
  baseline_value: "845428-point poor geometry; 33 point-scaled and 30 previous-scale updates, zero raw-depth-scaled updates; photos appear rotated"
  target: "Reproducible causal comparison distinguishing orientation, depth, pose and fusion; fix only confirmed defects"
created: 2026-10-15
last_updated: 2026-11-12
superseded_by: null
---

# Task 102: Diagnose the Redmi reconstruction on the same recorded walk

## Amendment, 12 November 2026

Narrowed by owner decision 10 ([plan](../../PROJECT_PLAN.md#owner-decisions-in-force)). Task108 is deferred and no longer gates this task. The ARCore-specific suspects (empty depth, axis conventions, anchor corrections) matter only for using ARCore recordings as a comparison. The sideways-image finding (Task109) and the scale-hiding motions (Task110) hold for any tracker.


## In plain English

Find why the recorded house looks distorted in the reconstruction. First check whether sideways images reached the depth model, then compare the phone's measured depth and the learned depth on the same views. Change one thing at a time so an improvement has an identifiable cause.

## Verified inputs and limits

Use the immutable v2 session `experiments/01_camera_capture_delivery/runs/capture_redmi_20261014/20261014_220756_walk`, Task99 validation/export and `outputs/capture_task99_220756/live_verified/` baseline. The run received 1,194 images and made 63 CPU updates at 1.58/s. Of those updates, 33 used tracked-point scale and 30 reused previous scale; none used raw-depth scale despite 44 saved new depth maps. There were 83 anchor corrections. These facts do not yet explain the geometry.

On 15 October the owner reported sideways photos in the HTML and proposed orientation-sensitive depth as a cause. Session metadata says `sensor_orientation_deg: 90`. `FrameWriter.java` encodes the Camera2 sensor-grid JPEG without a display rotation; `src/live/processor.py` passes its decoded pixels straight to the depth model; `tools/demos/capture_scene.py` embeds the same photo. This confirms the code path, not the correct upright direction for every image. A sensor mounting angle alone does not supply device orientation throughout a walk.

## Update, 7 November 2026

A read-only probe (Task106) changed the starting point:

- **The 14 October walk has no usable raw depth.** All 44 depth maps are zeros on disk, with stale timestamps. So plan step 3 is answered for that walk: raw-depth scaling had no data. Task111 owns the cause.
- **The 15 October walk (`20261015_093913_walk`, 822 frames) has 144 usable depth maps.** Diagnosis moves to that walk.
- **The phone was in portrait for 90-99% of both walks**, so the depth model saw sideways images. The effect is still untested.

The first steps are now separate tasks: Task107 (replay the 15 October walk), Task108 (ARCore depth fused along ARCore's path, covering step 5's raw-depth surface and the axis checks of step 4) and Task109 (rotation control, step 2). This task stays open to combine their results, finish steps 4 and 6, and state the causes.

## Plan, first checks in order

1. **Orientation audit.** Inspect original JPEG/grey pairs, EXIF, recorded camera/device poses, intrinsics, tracked pixel projections and viewer bookmarks at fixed timestamps. Identify viewer-only presentation versus model input. Use camera/device orientation or a documented manual control; never assume every frame needs the same turn merely from the 90-degree sensor value.
2. **Rotation control.** On identical selected frames run the existing depth model on native pixels and upright candidate pixels. Rotate the predicted depth and validity mask back to the native sensor grid before sizing/fusion, preserving original pose/intrinsics and tracked-point pixel coordinates. This isolates learned-model orientation sensitivity. Add asymmetric pixel/known-point projection tests before changing code. If changing the camera grid itself, transform dimensions, intrinsics, pixel coordinates and camera axes together and prove geometric equivalence; a CSS/photo-only rotation is a separate display correction.
3. **Raw-depth eligibility.** Trace `src/live/sizing.py` confidence threshold, in-view pixels, depth/image intrinsics, timestamp matching, freshness and minimum eligible pixels. Log why all 63 updates rejected or lacked raw-depth scaling. Compare frames with new raw depth against the same frame IDs in the learned-depth run; report the overlap and omitted frames, not an unlabelled different subset.
4. **Geometry conventions.** Test ARCore/OpenGL to OpenCV axes, camera-to-world inversion, depth z/ray conventions, orientation and depth-grid projection using asymmetric known coordinates. Confirm the first-anchor workaround and corrected fragment poses; distinguish original live poses from later corrections and viewer bookmarks.
5. **Controlled surfaces.** Fuse raw ARCore depth along its recorded path; learned depth along that same path with baseline and tested orientation preprocessing; then isolate scale source and anchor corrections. Keep shared frames, depth validity, voxel size and camera path fixed for each paired comparison. Retain full-data coverage rows separately. ARCore depth is a sensor comparison, not independent truth.
6. **Offline camera check.** Reuse the SfM harness for a v2 same-image COLMAP reference if pose error remains plausible. Add a v2 adapter fixture first, preserve source identity and orientation, and record camera placement failures. Offline agreement is not absolute accuracy or live performance.
7. Publish source hashes, exact frame IDs, transforms, scale/fallback histories, coverage, cloud bounds, negative results, CPU timings and visual comparisons. Fix only reproduced implementation defects with RED/GREEN tests. File a focused follow-up for unresolved algorithm changes rather than introducing another tracker or optimiser.

## Reuse and ownership

| Existing owner | Evidence | Use |
|---|---|---|
| v2 reader and validation | `host/session_v2.py`, Task99 validation | Original frames and metadata |
| Depth input and sizing | `src/live/processor.py`, `sizing.py` | Orientation/fallback control |
| Fusion and corrections | `src/live/fragments.py` and regression tests | Keep source frame/anchor lineage |
| Pose conversion | `host/session_v1.py`, `src/live/stream.py` | Shared coordinate conversion |
| Surface and path comparisons | `experiments/sfm/run_dense.py`, Task71-80 scorers | Avoid new fusion/scoring implementations |
| HTML/photo export | `tools/demos/capture_scene.py` | Display-only orientation checked separately |

## Settings and validation

Baseline: 640 x 480, cached Depth Anything V2 Metric Indoor Small, 2 cm fusion voxel and 16 CPU threads from Task99. Diagnostic rotations and selection rules are proposed by Claude, not owner-ruled; save them before running, including which way the inverse rotation acts. Use the same frame IDs for paired runs. No GPU, no overwrite of recordings and no silent interpolation of missing poses/settings. All long runs go in one START/END background queue with completion notification.

Finish when the orientation hypothesis and depth/pose/fusion controls have reproducible outcomes, even if a cause remains unresolved. State what is proven, what only agrees with another estimator, and what needs independent Task75/53 references. Trained photographic splats and cosmetic viewer changes cannot substitute for this diagnosis.
