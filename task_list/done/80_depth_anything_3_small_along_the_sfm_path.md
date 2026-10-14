---
id: "80"
title: Depth Anything 3 Small along the SfM path
status: done
priority: HIGH
type: experiment
approval_status: filed 2026-10-14 from the owner's handover prompt (step 2b, Task74's Small model); settings marked proposed by Claude are not owner-ruled
blocked_by: []
blocks: ["76"]
verification_test: "experiments/sfm/tests/test_posed.py"
plan_reviewed: null
files:
  - experiments/sfm/**
docs:
  - experiments/sfm/README.md
  - research/depth_estimation/README.md
baseline_metric:
  source: "Task78 and Task79 surface rows (Depth Anything V2 resized per frame to SfM points, sized from 20 metric readings)"
  field: "surface mean distance to the reference, points within 5 cm, frames per second on the CPU"
  baseline_value: "mean distance ICL 93.0 mm, desk 155.8 mm, xyz 166.2 mm; Task71 ceiling 82 / 129 / 158 mm"
  target: "proposed by Claude 2026-10-14, not owner-ruled: at least 1 frame per second end to end on the CPU (owner floor 2026-10-07), and mean distance at least 20% below the baseline on two of the three recordings"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 80 — Depth Anything 3 Small along the SfM path

## In plain English

Depth Anything 3 is a newer depth model that can look at several photos at once. When it is also told where the camera was for each photo, it returns depth that agrees across the photos, in the same units as the camera positions. Here it gets the image-only camera path (sized to metres from 20 readings, Task78). The question is whether its depth is closer to the true surface than the older Depth Anything resized to the same path. The Small version (80 million parameters) is the one that might fit a phone later.

## What

1. **Setup.** Clone the model code at a fixed commit into `third_party/` (ignored by Git), run it from its source folder with a few small extra packages, and download the Small checkpoint `depth-anything/da3-small` (both Apache-2.0).
2. **Two modes**, same frames, same SfM path, same size:
   - *single*: one photo at a time, no camera path. Its depth is resized per frame to the SfM points exactly as Task72 does (`run_dense --depth model-sfm-size`). This compares the models alone.
   - *posed*: windows of 5 consecutive photos with the sized camera path and camera intrinsics given to the model; the depth comes back in metres and is fused as it is (`run_dense --depth model`). This tests whether pose input removes the per-frame size problem.
3. **Score** both against the same references and fusion as Tasks 72, 78 and 79, on TUM xyz, TUM desk and ICL.
4. **Report** mean distance, RMSE, points within 5 cm, coverage, and frames per second (model time and end to end).

## Why

Task79 showed that a depth map prompted with sparse points does not help. The remaining way to a better dense surface on the CPU is a stronger depth model, or one that uses the camera path. Depth Anything 3 does both in one model, and its Small checkpoint is Apache-2.0 (checked 14 October 2026 on the model card). Its measured speed on this CPU with a 5-photo window is 0.9 s (5.5 photos per second).

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Depth dump format read by fusion | `dump_depth.py`, `run_dense.depth_maps` | `run_dense --depth-maps` | experiments/sfm/dump_depth.py:41-48; experiments/sfm/run_dense.py:53-61 |
| Per-frame size to SfM points for single-view depth | `run_dense --depth model-sfm-size` | Task72 rows | experiments/sfm/run_dense.py:207-212, 221-253 |
| SfM poses and sizes, camera of the recording | `Sequence`, Task67 `frames.json`, Task78 `sizes.json` | `dump_prompt_depth.py` | experiments/sfm/src/sequences.py:27-44; experiments/sfm/dump_prompt_depth.py |
| Largest model and sized poses | `prompt.largest_model` | `dump_prompt_depth.py` | experiments/sfm/src/prompt.py |
| Model API accepts extrinsics (world to camera, N × 4 × 4) and intrinsics (N × 3 × 3) | Depth Anything 3 `DepthAnything3.inference` | this task | third_party/depth-anything-3/src/depth_anything_3/api.py:133-158 |
| xformers is optional | DINOv2 layer fallback | this task | third_party/depth-anything-3/src/depth_anything_3/model/dinov2/layers/swiglu_ffn.py:35-40 |

### Plan

Files: `experiments/sfm/src/posed.py` (windows and sized extrinsics, numpy only), `experiments/sfm/dump_da3_depth.py` (model run, `.venv-yolo` with `PYTHONPATH` set to the cloned source and the extra-packages folder), `experiments/sfm/tests/test_posed.py`, `experiments/sfm/README.md`, `research/depth_estimation/README.md`.

1. Tests first for `src/posed.py`; see them fail.
2. Implement; run xyz in both modes and score; then desk and ICL.
3. One background queue with START/END lines; write the next step into the README handover.

## Hyperparameters

| name | value | source |
|---|---|---|
| model | `depth-anything/da3-small` (80M, Apache-2.0), code at commit 3d835ec1a5802d64a8b8b15f817a1ab54809bfe4 | owner handover 2026-10-14 (step 2b) |
| window | 5 consecutive placed frames, no overlap; a short last window is moved back to hold 5 frames and keeps only its new frames | proposed by Claude 2026-10-14, not owner-ruled |
| processing resolution | 504 (model default), depth resized back to 480 × 640 by bilinear interpolation | model default; resize proposed by Claude 2026-10-14 |
| pose input | SfM camera-to-world poses of the largest model times the 20-reading size, inverted to world-to-camera | Task78 size; convention from the model's API |
| intrinsics | the recording's pinhole camera (`Sequence.camera_params`), scaled by the model to its processing size | inherited Task67 |
| scale handling | model default `align_to_input_ext_scale=True` | model default |
| single mode sizing | Task72's per-frame size to SfM points (median ratio, ≥ 20 points, track ≥ 3, error ≤ 2 px) | inherited Task72 |
| SfM run per recording | same as Task72 | inherited Task72 |
| fusion and scoring | Task71 values | inherited Task71 |
| extra packages | moviepy 1.0.3, trimesh, plyfile, pillow_heif, decorator, proglog, imageio_ffmpeg, pycolmap 4.2.1, evo, natsort, argcomplete, installed with `pip --no-deps --target third_party/da3-deps`; the model code imports them but this task does not use them | proposed by Claude 2026-10-14 |
| devices | CPU only | owner 2026-10-14 handover |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Model code and extra packages | `third_party/` (ignored by Git) | `dump_da3_depth.py` | fixed commit; nothing installed into any environment | on disk; the README records the commands |
| Depth dumps | `dump_da3_depth.py` | `run_dense --depth-maps` | `index.json` + one `.npz` per frame (single: relative depth; posed: metres); refuses an existing folder | folder on disk |
| Surface rows | `run_dense.py` | `report.py --dense` | as Task72 | sealed |

- **Source of truth:** the SfM run and the recording; the reference enters only scoring.
- **Failure after each state transition:** a killed dump leaves a folder without `index.json`; delete and rerun. A killed fusion run leaves an incomplete run folder the report skips.
- **Fresh-deployment path:** the README lists the clone, checkout, extra-package install and the `PYTHONPATH` command.
- **Backward compatibility:** no existing file changes.

## Verification

- `experiments/sfm/tests/test_posed.py`:
  - 10 frames, window 5: two windows, every frame kept once; 12 frames: the last window starts at frame 7 and keeps only frames 10 and 11; fewer than 5 frames: one window of all of them; none: no windows;
  - sized extrinsics: a camera at (1, 2, 3) with size 0.5 gives a world-to-camera translation of (-0.5, -1, -1.5) for identity rotation, and `extrinsics @ sized pose = identity` for a rotated camera.
- Red first: run the tests before the module exists.
- Before/after: baseline rows in the front matter; the README holds the measured after.
- Plan review: no independent reviewer (the owner has not asked for agents); started with `task.js start 80 --force`.

## Receipts

| field | value |
|---|---|
| closing commit | not committed at finish; pushed with the follow-up commit the owner asked for (repo kept up to date) |
| files changed | experiments/sfm/src/posed.py, dump_da3_depth.py, tests/test_posed.py (new); experiments/sfm/README.md; research/depth_estimation/README.md |
| test | experiments/sfm/tests 40 passed in .venv-sfm; ruff clean |
| before / after | Mean distance baseline (Depth Anything V2 sized to SfM points, 20 readings) ICL 93.0, desk 155.8, xyz 166.2 mm; best DA3 Small mode per recording: ICL 78.6 mm (posed, sized), desk 237.8 mm (posed stride 10), xyz 298.5 mm (single, sized) |
| result | Accuracy target not met (only ICL improves, by 15%); TUM much worse. Speed target met: 4.4-5.6 fps on the CPU |

Notes / caveats / follow-ups:

- Added during the task (not in the original plan): posed depth also scored after per-frame sizing to SfM points, and a `--stride 10` window variant. Reason: the first posed rows were 546-814 mm on TUM because the model sizes depth from a pose fit that 5 consecutive frames (about 0.3 s) cannot constrain (api.py `_align_to_input_extrinsics_intrinsics`).
- Not tried: masking by the model's confidence map; the Base model; GPU.
- Owner ruled on 14 October that deployment must be live; this used the offline SfM path as a stand-in.
- Plan review: no independent reviewer (the owner has not asked for agents); started with `task.js start 80 --force`.

## Files

- experiments/sfm/README.md (+35 -3, 263 lines)
- research/depth_estimation/README.md (+1 -0, 32 lines)

## Checked

- `.venv-sfm pytest experiments/sfm/tests -> 40 passed; ruff clean; DA3 Small mean distance ICL 78.6 mm (posed, sized) vs 93.0 baseline; desk 237.8 vs 155.8; xyz 298.5 vs 166.2; 4.4-5.6 fps CPU`
- cost: 57 min from begin to finish; Claude tokens 23,226,812 (fresh input 400,716, cache read 22,741,106, output 84,990; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 1 in 1135 words: bold-labels "4 items"

## Left over

TUM gap unexplained (confidence masking untried); live SLAM stand-in to replace SfM per owner's live requirement; GPLv3 reference question pending; multi-view stereo needs GPU permission; Task76
