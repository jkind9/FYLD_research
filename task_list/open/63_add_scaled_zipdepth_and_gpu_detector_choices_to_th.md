---
id: "63"
title: Add scaled ZipDepth and GPU detector choices to the walkthrough
status: open
priority: HIGH
type: infra
approval_status: owner asked on 2026-10-07 to progress the swappable pipeline as far as possible; settings chosen under that delegation
blocked_by: []
blocks: []
verification_test: "src/walkthrough/tests/test_scaled_depth.py"
plan_reviewed: 2026-10-08 PASS
files:
  - src/walkthrough/**
docs:
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: "outputs/task55_real_runs/reviewed_xyz60_every2_* (30 TUM xyz frames, CPU)"
  field: "walkthrough depth choices that use the phone-ready ZipDepth model; end-to-end frames per second"
  baseline_value: "0 ZipDepth depth choices; 0.62 fps end to end (Depth Anything, all CPU)"
  target: "1 ZipDepth choice with a labelled scale source; a measured end-to-end fps with GPU depth and detection, compared with the owner's 1 fps floor"
created: 2026-10-07
last_updated: 2026-10-08
superseded_by: null
---

# Task 63 — Add scaled ZipDepth and GPU detector choices to the walkthrough

## In plain English

The depth model best suited to phones gives the shape of a scene but not its size in metres; it needs a few known distances in each picture to set the scale. This task lets the walkthrough use that model, taking the known distances for now from the recorded depth sensor and labelling the run clearly as using recorded answers. It also lets the object detector use the graphics card, then measures whether the whole walkthrough reaches at least one picture per second, the owner's minimum.

## What

1. `src/walkthrough/steps/depth.py`: `ScaledZipDepth` depth choice. For each frame it runs experiment 02's ZipDepth adapter (phone build by default), picks `points_per_frame` random pixels that have valid recorded TUM depth, fits scale and shift in inverse-depth space with experiment 02's tested fit, and returns metres with a validity mask. `control = "reference"` because the scale uses recorded depth. If the ZipDepth package cannot be imported, `load()` raises `Unavailable` naming the folder to put on `PYTHONPATH`.
2. `src/walkthrough/steps/objects.py`: `Yolo26x(checkpoint, device="cpu")`; `"0"` selects GPU 0, which experiment 06's detector already accepts.
3. `src/walkthrough/cli.py`: `--depth zipdepth-scaled` (with `--depth-checkpoint` pointing at the ZipDepth checkpoint and `--device`), `--points-per-frame`, and `--detector-device cpu|0`.
4. Run the 30-frame clip end to end on GPU and CPU; record frames per second against the 1 fps floor.

## Why

Task62 found ZipDepth's phone build plus about 50 known distances per frame matches its every-pixel shape score (AbsRel 0.068–0.070) at 42 fps on CPU and 190 fps on GPU, against Depth Anything's 4.4 fps CPU and 34–45% raw metric error. The walkthrough has no way to use it. The owner ruled that anything under 1 frame per second is not worth using; the all-CPU pipeline runs at 0.62 fps end to end (0.97 fps for processing alone), with tracking (0.49 s per frame), depth (0.26 s) and objects (0.21 s) the largest parts.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| ZipDepth adapter returns raw inverse depth and a validity mask per frame | `experiments/02_stereo_depth/zipdepth.py` `ZipDepth.load` / `_predict_zipdepth` | experiment 02 runner | experiments/02_stereo_depth/zipdepth.py:52-93 |
| Sparse pixel choice, native-space fit and conversion to metres are tested | `sparse_scale.choose_fit_pixels`, `geometry.alignment_fit_pixels`, `fit_native_alignment`, `apply_native_alignment` | sparse study | experiments/02_stereo_depth/sparse_scale.py:67; experiments/02_stereo_depth/geometry.py:33,56,93 |
| Recorded TUM depth reader with timestamp matching is a labelled reference control | `RecordedSensorDepth` | depth layer | src/walkthrough/steps/depth.py:39-74 |
| Depth layer validates grid and mask and records the control label | `depth.run`, `check_depth_grid` | pipeline | src/walkthrough/steps/depth.py:155-207; experiments/shared/geometry.py:20-25 |
| Detector accepts "cpu" or GPU "0" | `YoloDetector.__init__` | `Yolo26x.load` | experiments/06_object_recognition/pilot/detector.py:28-38; src/walkthrough/steps/objects.py:47-55 |
| Command-line method choices are built by small functions | `depth_choice`, `mapping_choice` | `cli.main` | src/walkthrough/cli.py |

### Steps

1. Tests first in `src/walkthrough/tests/test_scaled_depth.py`: with a fake ZipDepth predictor returning `2.5 / depth + 0.7` and a fake recorded reader, the output equals the true metres within 1e-6 on every valid pixel and is scored by `depth.run` validation; exactly `points_per_frame` sensor pixels are used per frame and the choice repeats for the same seed; a frame with fewer valid sensor pixels than `points_per_frame` fails the layer with the frame named; non-positive aligned values are invalid, not negative metres; `control == "reference"`; a missing `zipdepth` package gives an unavailable layer that names `PYTHONPATH`, while another missing package names that package; a pixel where ZipDepth is invalid is never chosen; a fitted depth beyond 20 m is invalid; a non-positive fitted scale fails the frame. CLI tests: `--depth zipdepth-scaled` defaults to the phone checkpoint; `--depth zipdepth-scaled` without `--dataset` is refused before a run folder exists; `--detector-device 0` reaches `Yolo26x.device`.
2. Implement; run the full walkthrough suite.
3. Real runs on `outputs/task51_real_clips/rgbd_dataset_freiburg1_xyz_first60_every2`: ZipDepth-scaled on GPU with YOLO on GPU; Depth Anything on GPU with YOLO on GPU; record per-layer and end-to-end fps, tracking error and mapping results.
4. Update the walkthrough README (choices table, CLI table, results) and the board.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| ZipDepth adapter | ScaledZipDepth | raw inverse depth, float32, on the RGB grid, plus finite mask | in memory per frame | experiments/02_stereo_depth/zipdepth.py:72-93 |
| RecordedSensorDepth reader | ScaledZipDepth (fit pixels only) | metres, valid below 4 m | original TUM files | src/walkthrough/steps/depth.py:59-74 |
| ScaledZipDepth | depth layer and every later layer | camera-axis metres with a boolean mask; run labelled `reference` | sealed run files | src/walkthrough/steps/depth.py:150-200 |

- Source of truth: TUM RGB and depth files plus the frozen settings below; a rerun with the same seed reproduces each frame's chosen pixels.
- The recorded depth reaches the method only through this labelled reference choice, and only at `points_per_frame` pixels per frame; the run's `is_measurement` is false.
- Process death leaves an incomplete run folder; rerun into a fresh folder.
- Backward compatibility: existing choices and CLI flags keep their meaning; `--checkpoint` remains an alias for the detector checkpoint.

## Hyperparameters

| name | value | source |
|---|---|---|
| ZipDepth build and checkpoint | phone build, passed explicitly as `build="npu"` (the adapter defaults to `gpu`, zipdepth.py:34); `data/models/ZipDepth/checkpoints/zipdepth_base_npu.pth` (SHA-256 627c04fd…), the CLI default for this choice | inherited experiments/02_stereo_depth/run.py:62 (export build) and Task62 receipts |
| ZipDepth device | same as `--device` (`cpu` default, or `cuda`) | inherited experiments/02_stereo_depth/zipdepth.py:45 |
| ZipDepth input size | 384 px short side | inherited experiments/02_stereo_depth/run.py:57 |
| points per frame | 50 | confirmed 2026-10-07 (owner delegated: "Progress the project and tasks as much as you can"); Task62 sparse study shows 50 points reach the every-pixel score |
| point sampling | uniform without replacement over pixels where both the recorded depth and ZipDepth's output are valid (`alignment_fit_pixels`); `default_rng([seed, frame_index])` | inherited experiments/02_stereo_depth/sparse_scale.py:46,111 and geometry.py:33-53 |
| seed | 0, one seed only | deviates from experiments/02_stereo_depth/sparse_scale.py:42 (seeds 0-4) because a pipeline run produces one depth map per frame; the study showed seeds change 50-point AbsRel by at most 0.001 on the phone build; confirmed 2026-10-07 (owner delegated) |
| fit | least-squares scale and shift in inverse-depth space | inherited experiments/02_stereo_depth/geometry.py:56 |
| fit failure | fewer than `points_per_frame` eligible pixels, or a non-positive fitted scale (which would turn near into far), fails the depth layer with the frame named | confirmed 2026-10-07 (owner delegated) |
| maximum depth | 20 m; fitted pixels beyond it are invalid | inherited src/walkthrough/steps/depth.py:88 (Depth Anything's indoor cap) |
| recorded depth decoding | 5000 units per metre, valid below 4 m, 0.02 s pairing | inherited src/walkthrough/steps/depth.py:43-45 |
| detector device | `cpu` (default) or GPU `0` | inherited experiments/06_object_recognition/pilot/detector.py:37 |

## Verification

- Contract test `src/walkthrough/tests/test_scaled_depth.py` with the assertions in How step 1, each seen failing first.
- Before: 0 ZipDepth walkthrough choices; 0.62 fps end to end on CPU. After: recorded in Receipts with the GPU runs, compared with the 1 fps floor.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

- Plan review 2026-10-08: PASS with seven advisory notes, all applied to the plan (fit pixels need valid ZipDepth output too; phone build passed explicitly; single seed marked as a deviation; 20 m cap; per-choice default checkpoint; only a missing zipdepth package points at PYTHONPATH; device and fit-failure rules declared; line citations corrected).
- Done 2026-10-08: `ScaledZipDepth` in `src/walkthrough/steps/depth.py`, `Yolo26x(device=)` in `steps/objects.py`, CLI `--depth zipdepth-scaled`, `--points-per-frame`, `--detector-device` and per-choice default checkpoints in `cli.py`; 13 new tests in `src/walkthrough/tests/test_scaled_depth.py` (seen failing first); 249 tests pass across walkthrough, experiment 02 and experiment 05; Ruff clean; walkthrough README flag table updated.
- Real CPU run 2026-10-08 (30 xyz frames, `outputs/task63_real_runs/zipdepth-scaled-cpu/`, with report pages): depth AbsRel 0.056 (δ1 98.1%) against Depth Anything's 0.389; camera position RMSE 71.8 mm against 218.3 mm (Kinect reference 21.2 mm); 29/29 steps tracked; desk-plane area 3.45 m² (Kinect 2.21, Depth Anything 7.44); depth 20.7 fps; processing 1.13 fps, which clears the owner's 1 fps floor on CPU; end to end 0.77 fps including model loading, pictures and scoring. Fit points are exact Kinect values, so this is optimistic for phone points.
- Parked 2026-10-08 (status back to open) so Task65 can run: the owner said not to use the GPU without permission, and the remaining step is a GPU run.
- still open because the GPU run (depth on cuda, YOLO on GPU 0) and the blind diff review have not been done. Next command: `$env:PYTHONPATH = "$PWD;$PWD\data\models\ZipDepth"; .venv-yolo/Scripts/python.exe -B -m src.walkthrough.cli --dataset outputs/task51_real_clips/rgbd_dataset_freiburg1_xyz_first60_every2 --run-root outputs/task63_real_runs --depth zipdepth-scaled --device cuda --mapping grid-footprint --detector-checkpoint checkpoints/yolo26x.pt --detector-device 0 --max-distance-m 0.35 --ambiguity-margin-m 0.05`, then read `metadata/timing.json`.
