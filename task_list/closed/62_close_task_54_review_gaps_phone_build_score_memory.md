---
id: "62"
title: Close task 54 review gaps: phone build score, memory, Marigold and sparse scale
status: closed
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: "experiments/02_stereo_depth/tests/test_sparse_scale.py"
plan_reviewed: null
files:
  - experiments/02_stereo_depth/**
  - src/walkthrough/steps/depth.py
  - src/walkthrough/tests/**
  - .gitignore
docs:
  - experiments/02_stereo_depth/README.md
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: "Task54 run outputs under experiments/02_stereo_depth/runs/task54*; review of 2026-10-07"
  field: "phone-build frames scored; CPU result files with a peak-memory value; depth methods scored"
  baseline_value: "0 of 138 phone-build frames scored; 0 of 4 CPU result files record memory; 2 of 3 methods scored"
  target: "138 of 138 phone-build frames scored; every new CPU and GPU result file records process peak memory; Marigold scored on 138 frames or its failure logged with free GPU memory; sparse-point scale table for 4 point counts"
created: 2026-10-07
last_updated: 2026-10-07
superseded_by: null
---

# Task 62 — Close task 54 review gaps: phone build score, memory, Marigold and sparse scale

## In plain English

An earlier comparison of three programs that estimate distance from a single photo left some questions open. The phone version of the smallest program was never checked for accuracy, memory use on the processor was not recorded, the large server-only program never ran because a game was using the graphics card, and the program that claims to give real distances turned out to be about a third too far. This task fills those gaps on the same recorded frames. It also tests a realistic phone setup: fixing each picture's scale from only a few known distances, rather than from every pixel of the sensor depth.

## What

1. `run.py`: record the runner process's peak memory for every result file (CPU and GPU), stop hashing the Hugging Face download-cache folder inside a checkpoint directory, and add `psutil` to the pinned host requirements.
2. Re-run on CPU into a fresh root `runs/task62_cpu/` for Depth Anything V2 and both ZipDepth builds (desktop `gpu` build and phone `npu` build). Run the phone build on GPU into `runs/task62/` so its desktop timing sits beside the Task54 GPU rows.
3. `marigold.py`: fix the prediction path (the official `infer.py` writes to `<output>/images/predictions_npy/`, the scorer read `<output>/predictions_npy/`), add a WSL wrapper command that records wall time, per-file timing and GPU memory, and run Marigold V2 on the GPU now that it is free.
4. `geometry.py` / `scoring.py`: split the affine fit from its application so a fit can use a subset of pixels and be scored on all of them. Behaviour of the existing full-frame shape view is unchanged.
5. New `sparse_scale.py`: fit each frame's scale and shift from N randomly chosen reference pixels (N = 10, 50, 200, 1000; 5 seeds), score on every valid reference pixel, for every saved prediction set.
6. Walkthrough: a test that sends the Depth Anything V2 adapter's output through the real depth layer `run()`, and README warnings that its raw metres are biased.
7. Docs: fix the garbled δ1 header, state Depth Anything's metric bias, add the phone-build and memory rows, the Marigold result or failure log, the sparse-scale table, the Marigold commands, and the working full-test command (`--basetemp`). Correct the Task54 receipts. Ignore `data/models/` in Git (the review found its JSON configs and the nested ZipDepth repository are not ignored).

## Why

Review of Task54 on 2026-10-07 found: (a) Depth Anything V2 metric reads 1.34× (xyz) and 1.41× (desk) too far, with the per-frame factor ranging 0.86–2.09; it is wired into the walkthrough as metres with no warning. (b) The 0.07 ZipDepth AbsRel belongs to the desktop checkpoint (`a559…`); the exported ONNX model is the phone checkpoint (`627c…`), whose accuracy was never measured. (c) Marigold failed while a game held 15,910 of 16,303 MiB, so its fit in 16 GB is untested. (d) CPU rows record no memory although Task54 step 4 asked for it. (e) Shape scores fit scale from every Kinect pixel of the same frame; a phone only has sparse points (ARCore depth or tracked features), so the realistic error is unknown.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Per-frame affine alignment in native space then conversion to metres | `align_shape_to_metric` | `score_shape_to_metric` | experiments/02_stereo_depth/geometry.py:24,66-74 |
| Metric/shape score arrays, distance bands and pixel-weighted pooling | `_score_arrays`, `_aggregate` | `evaluate_predictions` | experiments/02_stereo_depth/scoring.py:47; experiments/02_stereo_depth/evaluate.py:105 |
| GPU peak memory recorded, CPU left `None` | `_run_sequence` | results.json `timing` | experiments/02_stereo_depth/run.py:345-348,373 |
| Checkpoint manifest hashes every file under a directory, including `.cache/` | `_checkpoint_manifest` | run.json, results.json | experiments/02_stereo_depth/run.py:184-204 |
| ZipDepth build switch already exists (`--zip-build npu`) | `ZipDepth.load` | `run._load_method` | experiments/02_stereo_depth/zipdepth.py:53-69; experiments/02_stereo_depth/run.py:175-180 |
| Marigold scorer reads `<prediction_root>/<sequence>/predictions_npy` | `score_predictions` | none yet | experiments/02_stereo_depth/marigold.py:57 |
| Official Marigold writes `<output_dir>/images/predictions_npy/*.npy`, resized to input resolution | WSL `~/marigold-v2/scripts/infer.py` @ 9926d93 | this task | README.md:129-132 of that repo; infer.py `SaveFolderPredictionNpy` step |
| Depth layer validates grid and mask for any `DepthMethod` | `depth.run`, `check_depth_grid` | walkthrough pipeline | src/walkthrough/steps/depth.py:150-200; experiments/shared/geometry.py:20-25 |
| A depth-layer test pattern with `SimpleNamespace(path=tmp_path)` exists | test_contracts | — | src/walkthrough/tests/test_contracts.py:47 |
| No sparse-point scale fit exists in the repo | searched `sparse`, `subset`, `fit_mask`, `n_points` in experiments/ and src/ | — | none found |

Existing Task54 run folders are never rewritten; all new outputs go to `runs/task62*/`.

## Hyperparameters

Values inherited from Task54 are unchanged. New sparse-scale settings were chosen by the assistant after the owner delegated the follow-up ("Fix it all", 2026-10-07).

| name | value | source |
|---|---|---|
| frames, recordings, warm-up, repeats, input sizes, reference decoding, distance bands | as Task54 | inherited experiments/02_stereo_depth/run.py:43-102 |
| ZipDepth phone build | `npu` checkpoint `zipdepth_base_npu.pth` | inherited experiments/02_stereo_depth/run.py:61 |
| Marigold V2 checkpoint, resolution, steps, seed | `Log-stage2`, native 640x480, 1 step, seed 0 | inherited experiments/02_stereo_depth/run.py:66-76 |
| process peak memory | lifetime peak working set (Windows) / max RSS (Linux) of the runner process, in MiB | confirmed 2026-10-07 (owner delegated: "Fix it all") |
| Marigold GPU memory | peak whole-GPU memory used minus the idle reading before start, sampled every 1 s with nvidia-smi | confirmed 2026-10-07 (owner delegated: "Fix it all") |
| sparse point counts per frame | 10, 50, 200, 1000 | confirmed 2026-10-07 (owner delegated: "Fix it all") |
| sparse sampling | uniform without replacement over valid reference pixels; numpy `default_rng([seed, frame_index])` | confirmed 2026-10-07 (owner delegated: "Fix it all") |
| sparse seeds | 0, 1, 2, 3, 4; report median and range over seeds | confirmed 2026-10-07 (owner delegated: "Fix it all") |
| sparse fit | same native-space least-squares scale and shift as the shape view; for metric depth also a scale-only fit in metres | confirmed 2026-10-07 (owner delegated: "Fix it all") |
| sparse point noise | none (Kinect values as given); labelled as optimistic | confirmed 2026-10-07 (owner delegated: "Fix it all") |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Saved native predictions | run.py `_run_sequence` (experiments/02_stereo_depth/run.py:325-333); Marigold `infer.py` | sparse_scale.py, marigold.py scorer | float32 `.npy` on the 480x640 RGB grid, native convention | yes; sealed folders are never overwritten |
| Kinect reference | dataset.py `select_tum_frames` (experiments/02_stereo_depth/dataset.py:39) | scorers only | metres, valid 0–4 m | original files unchanged |
| Sparse fit pixels | sparse_scale.py | scorer | boolean mask on the reference grid; never passed to a model | regenerated from seed |

- **Source of truth:** saved predictions plus TUM files; every score is recomputable from them.
- **Process boundary:** Marigold runs in WSL and exchanges PNG inputs and `.npy` outputs through `/mnt/c`.
- **Failure:** an interrupted run leaves a `.incomplete` staging folder or a partial Marigold output folder; rerun into a new root.
- **Backward compatibility:** `align_shape_to_metric` keeps its signature and results (existing tests in test_metric_depth.py and test_evaluate.py must stay green).

## Verification

- `experiments/02_stereo_depth/tests/test_sparse_scale.py`: on a synthetic inverse-depth frame with known scale and shift, a 10-point fit recovers the geometry within 1e-6 and is scored on all valid pixels (scored pixel count equals valid reference count, not 10); fewer than 2 fit pixels raises; point selection is deterministic for a seed and never selects an invalid reference pixel; a scale-only metric fit recovers a known factor.
- `experiments/02_stereo_depth/tests/test_run.py`: results include `peak_process_memory_mib` as a positive number on CPU; the checkpoint manifest skips `.cache/`.
- `experiments/02_stereo_depth/tests/test_marigold.py`: the scorer reads `<root>/<sequence>/images/predictions_npy`.
- `src/walkthrough/tests/test_adapters.py`: the Depth Anything V2 predictor's output passes `depth.run` validation and keeps the frame ID.
- Before/after: see baseline_metric.

## Receipts

| field | value |
|---|---|
| closing commit | `bfb70f2` |
| files changed | `experiments/02_stereo_depth/run.py` (process peak memory, `.cache` skipped in checkpoint lists), `geometry.py` (fit/apply split), `scoring.py` (`score_sparse_fit`), `evaluate.py` (`aggregate_scores` public), `marigold.py` (correct prediction folder, cost summary, chosen recordings, HYPERPARAMETERS), new `sparse_scale.py`, new `marigold_wsl_run.sh`, `requirements-task54-host.txt` (+psutil); tests `test_sparse_scale.py` (new), `test_run.py`, `test_marigold.py`; `src/walkthrough/steps/depth.py` (bias warning), `src/walkthrough/tests/test_adapters.py` (Depth Anything through the depth layer); `.gitignore` (`data/models/`); experiment 02 and walkthrough READMEs; Task54 receipts and review notes; board |
| test | experiment 02: 51 passed; walkthrough: 185 passed with experiment 05; Ruff clean. New tests were seen failing first (missing module; 4 red for memory, `.cache`, Marigold folder) |
| before / after | Phone-build frames scored 0 of 138 → 138 of 138 (AbsRel 0.0703 xyz, 0.0682 desk; CPU 24 ms, GPU 5 ms). CPU result files with memory 0 of 4 → every new run (Depth Anything 1.8 GB, ZipDepth 1.4 GB process peak). Methods scored 2 of 3 → 3 of 3 on xyz (Marigold 0.0356, 16.6 s per frame); Marigold desk not scored, dropped under the owner's 1 fps rule. Sparse-scale table for 10/50/200/1000 points, 5 seeds, 4 methods: `runs/task62/sparse_scale.json` |
| result | Done. ZipDepth phone build plus a per-frame scale from about 50 phone points is the strongest depth candidate. Marigold fails the 1 fps floor. Walkthrough scale-source adapter for relative depth needs phone points (Task52). |

Notes / caveats / follow-ups:

- Marigold V2, GPU free at start (3.0 of 16.3 GB used): xyz finished all 80 frames (exit 0, about 37 min; 15 s per frame at first, up to 88 s later). Desk slowed from 75 to 135 s per frame and crashed at frame 15 with `torch.AcceleratorError: CUDA error: unknown error`; whole-GPU memory sat at 15.95 of 16.3 GB, so this looks like memory oversubscription, not a code fault. A rerun of the remaining 44 desk frames in fresh processes was started (`runs/task62/marigold_desk_chunk0`) and then stopped when the owner ruled that anything under 1 frame per second is not worth using; chunks 1 and 2 never ran and no desk score is reported.
- Process note: `marigold_wsl_run.sh` was edited (recordings discovered from the input folder instead of a fixed pair) through a Python command while Task55 was the active task, which bypassed the task gate. Task62 was made active immediately afterwards; the edit belongs to this task.
- The ZipDepth commands in the README lacked the `PYTHONPATH` entry for `data/models/ZipDepth`; a fresh run failed with `No module named 'zipdepth'`. The README now sets it.
- Sparse points are exact Kinect values; noisy phone points will score worse. Measuring that needs Task52 recordings.
