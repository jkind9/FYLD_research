---
id: "54"
title: Compare three depth methods and validate real metric depth
status: closed
priority: HIGH
type: experiment
approval_status: planning authorised 2026-10-06; owner named the three-method comparison on 2026-10-07; execution requires frozen settings and plan review
blocked_by: []
blocks: []
verification_test: "experiments/02_stereo_depth/tests/test_metric_depth.py"
plan_reviewed: 2026-10-07 PASS
files:
  - experiments/02_stereo_depth/**
  - src/walkthrough/steps/depth.py
  - src/walkthrough/tests/**
docs:
  - experiments/02_stereo_depth/README.md
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: depth methods run and scored in experiment02
  baseline_value: "0 depth methods run in experiment02; downstream trials use supplied sensor depth"
  target: "3 methods scored on the same TUM frames (error, coverage, time, memory, model size), plus 1 phone-convertible model exported; 1 metric method wired into the walkthrough depth layer"
created: 2026-10-06
last_updated: 2026-10-07
superseded_by: null
---

# Task54: Compare three depth methods and validate real metric depth

## In plain English

Measure how well three different programs can estimate the distance from the camera to every point in a picture, using recordings where the true distances were also measured by a depth sensor. One program is small and gives real distances, one is very large and server-only but known for good shapes, and one is built to run fast on phones. Compare their errors, how much of each picture they cover, how long they take and how big they are. Then use the best phone-ready option in the full pipeline instead of borrowing the sensor's distances.

## Board update, 7 October 2026

Task51 was rescoped on 6 October 2026 to the first prerecorded pipeline. Field decisions (site, objects, survey, storage, numeric limits, phone processing split) now belong to Task61. Controls on existing recorded data can start now, so this task is not blocked.

Deployment must be on a phone (owner, 7 October 2026). The chosen depth route must have a path that runs on the phone: ARCore's Depth API, or a model small enough to convert and run on the device. If Task61 decides the phone only records and processing is hosted, still measure model size and speed so the choice can be revisited. The physical phone trial needs Task52's recording and Task53's survey.

## Methods compared (owner request, 7 October 2026)

| Method | Why it is in the comparison | Output | Size and licence | Phone route |
|---|---|---|---|---|
| [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) Small, metric indoor checkpoint (Hypersim, max 20 m) | Named candidate since Task51; the only one of the three that outputs metres directly | Depth in metres | 24.8M parameters. The official repository says it released smaller metric models based on the Small checkpoint and states the Small model is Apache-2.0. The exact Transformers metric card omits a separate licence field; use this official upstream licence basis and retain that metadata gap in the run receipt | Small enough to try converting; not built for phone chips |
| [Marigold v2](https://github.com/huawei-bayerlab/marigold-v2) (`huawei-bayerlab/marigold-v2-0`, depth checkpoint `Log-stage2`; [paper](https://arxiv.org/abs/2609.08084), released 8 September 2026) | Owner request. Strong shape quality; serves as the hosted accuracy reference | Affine-invariant log depth (correct shape; unknown scale and shift per image) | Qwen-Image-Edit-2509 diffusion transformer with LoRA adapters, quantised to 4-bit at first load; single-step prediction. Apache-2.0 for code and weights. README: about 17 GB GPU memory at 1024x1024 | None; hosted only. Linux only, so it runs under WSL Ubuntu on MasterPC |
| [ZipDepth](https://github.com/fabiotosi92/ZipDepth) (ECCV 2026) | Most promising phone model found: about 6.1M parameters, a separate build for phone AI chips (NPUs), and export to ONNX, TFLite and CoreML | Affine-invariant inverse depth | MIT licence in the official repository; both checkpoints ship inside that repository and no separate weight terms or third-party notice are listed. Use the repository MIT terms for the shipped checkpoint and record the source commit and file hash | Built for phones |

Marigold v2 comes from Huawei Bayer Lab, EPFL and the University of Bologna, not the original prs-eth repository (whose newest depth release is v1.1). MasterPC's RTX 5070 Ti has 16 GB, below the README's 17 GB figure for 1024x1024. TUM frames are 640x480 (about 30% of those pixels), so it is expected to fit, but this is unverified. If it runs out of memory, record that as a result and ask the owner before changing resolution or hardware.

ZoeDepth was considered and rejected. It outputs metres, but its repository was archived on 5 May 2025, it uses a large transformer backbone, and it makes no mobile claims. Other references already in the project (Depth Pro, Metric3D, UniDepth, MoGe, Prompt Depth Anything, Depth Anything 3) are listed with their licence notes in research/session_recovery/README.md:82-86 and experiments/02_stereo_depth/README.md:44-50. They are not part of this comparison.

## What

Add one adapter per method in experiment02 that reads a colour frame and returns that method's raw output, its output convention (metric depth, relative depth or relative inverse depth), and timing. Score all three on the same TUM frames against the recorded Kinect depth. Export ZipDepth's phone build to ONNX and TFLite and check the exported model gives the same output as the PyTorch model on the same frames. Wire the metric Depth Anything V2 adapter into the walkthrough depth layer as a real `DepthMethod`. Relative methods enter the walkthrough only with an explicit scale source (see How, step 5).

## Why

Depth is the missing link from phone images to physical measurements. All downstream trials so far use the recorded sensor depth, which a phone does not have. The three methods cover the realistic trade-off: real metres in a small model, best shape quality in a large hosted model, and a model built for phone chips.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| The walkthrough depth layer takes a `DepthMethod` with `load()` and expects camera-axis depth in metres plus a validity mask | walkthrough depth step | pipeline, surface, mapping and object layers | src/walkthrough/steps/depth.py:1,34-35,113 |
| A recorded TUM depth reader already exists as a labelled reference control (5000 units per metre, valid below 4 m, 0.02 s pairing tolerance) | `RecordedSensorDepth` | reference control and this scorer | src/walkthrough/steps/depth.py:39-74 |
| Metric decoding returns an explicit validity mask | shared geometry | new adapters and scorer | experiments/shared/geometry.py:10 |
| Experiment02 has a plan and method list but no code | experiment02 | this task | experiments/02_stereo_depth/README.md:7,44-50 |
| Licence notes for other depth models are already recorded | research recovery notes | method selection | research/session_recovery/README.md:82-86 |

1. **Freeze settings.** Fill the Hyperparameters table with owner-confirmed values before any run. Download weights into ignored local storage and record their file hashes.
2. **Tests first.** In `experiments/02_stereo_depth/tests/test_metric_depth.py`, assert unit conversion, the native output convention each adapter declares (Marigold v2 `Log-stage2`: affine-invariant log depth; ZipDepth: affine-invariant inverse depth, as its evaluator declares), invalid pixels staying invalid, image-grid mismatch rejected, alignment that recovers a known scale and shift on a synthetic frame, and reference depth never passed to an adapter.
3. **Score on TUM.** Same frames for all three methods. Reference is the Kinect depth, used for scoring only. Report two views and never mix them:
   - *Metric view* (Depth Anything V2 metric only): raw output against the reference.
   - *Shape view* (all three): align each prediction in its declared output convention to the reference on that frame. For Marigold's affine-invariant log depth, fit `a * predicted_log_depth + b` to `log(reference_depth_in_metres)`, exponentiate the aligned values, then score in metres. For relative depth, fit scale and shift to reference metres; for relative inverse depth, fit to inverse reference metres and invert positive aligned values. Label all results reference-aligned; they show shape quality, not independently recovered real-world distance. Exclude non-positive aligned values and report their share separately.
   Metrics: AbsRel, RMSE in metres, share of pixels within 1.25x of the reference (δ1), valid coverage, and each of these by distance band (0-1, 1-2, 2-4 m).
4. **Cost.** On MasterPC, GPU and CPU separately: model load time, warm per-frame time (after warm-up frames), peak memory, file size and parameter count. Marigold v2 runs under WSL Ubuntu, so record its operating system separately and count the first-load 4-bit quantisation in load time, not per-frame time. For ZipDepth also: ONNX and TFLite export, and the exported model's output difference from PyTorch on the same frames. On-phone timing belongs to Task57.
5. **Scale for relative methods.** In the walkthrough, a relative method needs a scale source. Allowed sources: the reference (labelled as a control, never counted as a result), or later ARCore's metric depth or tracked points on the phone (Task52/57). Do not add any other hidden scaling.
6. **Wire the metric method.** Add the Depth Anything V2 metric adapter as a `DepthMethod` in `src/walkthrough/steps/depth.py`, returning axial depth in metres and a validity mask. Its output must pass the layer's existing validation.
7. **Make the run reproducible.** Add pinned dependency files for the Windows/hosted methods and Marigold's WSL Linux runtime. Update this README with clean-environment install commands, TUM data location/download instructions, checkpoint acquisition steps, and the exact command for a first scored run. Record runtime versions in the run metadata. Do not fetch model weights until their checkpoint-specific licence questions are resolved and recorded.
8. **Publish** one run with per-method results, settings, weight hashes and environment. A method that performs badly or fails to convert is a valid result.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Each method adapter | scorer; walkthrough depth layer (metric method only) | native output plus declared convention; metric output is axial Z in metres with a validity mask on the source image grid | sealed run survives | src/walkthrough/steps/depth.py:34-35,113; experiments/shared/geometry.py:10 |
| Recorded TUM Kinect depth | scorer only | uint16 at 5000 units per metre, valid below 4 m, paired by timestamp within 0.02 s | original dataset files unchanged | src/walkthrough/steps/depth.py:43-45 |
| Downloaded weights | adapters | local files outside Git, identified by SHA-256 | re-download must match the recorded hash | n/a until downloaded |

Original frames, frozen settings and weight hashes are the source of truth. The reference never reaches an adapter. Alignment for the shape view happens in the scorer only and follows each method's declared output convention before converting aligned values to metres. An interrupted run stays incomplete; restart uses a fresh run directory. The README's pinned install steps, TUM data instructions, checkpoint instructions and scorer command must take a clean machine to its first successful run. Existing supplied-depth controls stay readable and labelled as controls.

## Hyperparameters

Proposed and confirmed by the owner on 2026-10-07.

| name | value | source |
|---|---|---|
| methods | Depth Anything V2 metric indoor Small; Marigold v2; ZipDepth | confirmed 2026-10-07 (owner named the first two and delegated the phone choice; ZipDepth chosen) |
| Marigold version and checkpoint | Marigold v2, `huawei-bayerlab/marigold-v2-0`, depth `Log-stage2` (repository default) | confirmed 2026-10-07 (owner supplied the repository link) |
| Depth Anything V2 input size and max depth | 518 px short side (repository default); 20 m (indoor checkpoint) | confirmed 2026-10-07 (owner agreed the proposed settings) |
| Marigold v2 resolution, steps, seed and quantisation | native 640x480 (already a multiple of 16); single step; seed 0; 4-bit quantisation as loaded by the repository | confirmed 2026-10-07 |
| ZipDepth build and input size | NPU build for the export check; GPU build for desktop scoring; 384 px short side | confirmed 2026-10-07 (repository README default, agreed by owner) |
| recordings and frames | TUM freiburg1_xyz and freiburg1_desk, every 10th colour frame | confirmed 2026-10-07 (owner agreed the proposed settings) |
| reference decoding | 5000 units per metre; valid when 0 < depth < 4 m; pairing tolerance 0.02 s | inherited src/walkthrough/steps/depth.py:43-45 |
| shape-view alignment | per-frame least-squares scale and shift in each method's native space, over valid reference pixels | confirmed 2026-10-07 (owner agreed the proposed settings) |
| distance bands | 0-1, 1-2, 2-4 m | confirmed 2026-10-07 (owner agreed the proposed settings) |
| ZipDepth prediction convention | affine-invariant inverse depth | inherited data/models/ZipDepth/zipdepth/evaluation/evaluator.py:3,51 |
| timing | 5 warm-up frames discarded; GPU and CPU timed separately; 3 repeats, median reported | confirmed 2026-10-07 (owner agreed the proposed settings) |
| output units for the walkthrough | axial Z in metres with validity mask | inherited src/walkthrough/steps/depth.py:113 |

## Verification

- Contract test `experiments/02_stereo_depth/tests/test_metric_depth.py`: a synthetic frame with known depth survives unit conversion exactly; alignment recovers a known scale and shift within 1e-6; invalid reference pixels are excluded from every metric; a mismatched image grid raises; each adapter declares its output convention; no adapter call receives reference depth.
- Walkthrough test under `src/walkthrough/tests/`: the Depth Anything V2 metric method passes the depth layer's validation on a fixture frame and returns the source frame ID.
- Shape-view contract test: synthetic metric, relative-depth, inverse-depth and affine-invariant log-depth maps recover the same known geometry after their declared alignment and conversion; Marigold's aligned log-depth values are exponentiated before metre-valued metrics.
- Reproduction check: README and pinned runtime snapshots identify model settings, software versions, local data paths and model hashes. Windows runner commands reproduce the two scored methods; the official WSL command records Marigold's GPU failure while the game stays open.
- Before: 0 methods run. After: Depth Anything V2 and ZipDepth scored on the same 138 TUM frames on CPU and GPU. ZipDepth outputs were re-scored after correcting its native convention to affine-invariant inverse depth. Marigold V2 was attempted in WSL and its GPU failure was recorded as requested; CPU inference is unsupported by its 4-bit quantizer. ZipDepth ONNX matched PyTorch within 6.3e-7 across all sampled frames. TFLite files were generated but failed LiteRT tensor allocation. Numeric acceptance limits come from Task61; no physical phone timing is claimed.

Checkpoint terms were reviewed before acquisition. The official Depth Anything repository says its Small model is Apache-2.0 and describes the released metric checkpoint as based on Small; the Transformers model card itself does not repeat the licence field. ZipDepth's official MIT repository includes both `.pth` checkpoints and gives no separate checkpoint terms. The run records these sources, exact revisions, and checkpoint hashes. This is a research evaluation of those upstream releases, not a claim that every redistribution scenario is covered.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Uncommitted workspace changes; no commit was requested |
| Files changed | `experiments/02_stereo_depth/geometry.py`, `dataset.py`, `scoring.py`, `evaluate.py`, `run.py`, `marigold.py`, `zipdepth.py`, `requirements-task54-host.txt`, `requirements-task54-marigold-wsl.lock`, all Task54 tests, `src/walkthrough/steps/depth.py`, `src/walkthrough/tests/test_adapters.py`, experiment and walkthrough READMEs, `task_list/README.md` |
| Test status | At close: 40 passed, 34 deselected; Ruff and `py_compile` passed. Review on 2026-10-07 ran the full set with a writable temp folder (`--basetemp`): 185 passed, 0 deselected. |
| Before measurement | 0 depth methods run in experiment02; downstream trials use supplied sensor depth |
| After measurement | 8 score rows: Depth Anything V2 and ZipDepth, two recordings each, CPU/GPU, all 138 frames; ZipDepth inverse-depth scores re-computed from saved predictions; Marigold WSL GPU failed on frame one and CPU stopped at GPU-only quantization; ONNX matched PyTorch within 6.30e-7; TFLite outputs failed LiteRT allocation |
| Delta | From no real model runs to two complete CPU/GPU comparisons plus a documented Marigold hardware failure and a verified ONNX export |
| Decision-gate outcome | Task complete for the local comparison. Marigold GPU failure was recorded per owner instruction. ZipDepth's ONNX path is verified; TFLite failure is recorded. Phone timing and device compatibility remain Task57. Plan review passed 2026-10-07. |

Review waiver: The staging directory for an interrupted or failed sequence is kept under .incomplete for diagnosis. Retrying uses a fresh output root; remove old incomplete run folders after preserving anything needed for debugging. The method-run directory is created exclusively, so another run cannot replace its shared checkpoint metadata.

## Review, 7 October 2026

A review after closing found gaps, now handled in [Task62](62_close_task_54_review_gaps_phone_build_score_memory.md):

- Depth Anything V2's raw metres read 1.34x (xyz) and 1.41x (desk) too far, and the per-frame factor ranges 0.86-2.09. It is wired into the walkthrough, but its output needs a per-frame scale source before it can measure anything.
- The 0.07 ZipDepth AbsRel came from the desktop checkpoint (`a559…`). The exported ONNX model uses the phone checkpoint (`627c…`), which was not scored here.
- The Marigold attempt ran while a game held 15,910 of 16,303 MiB of GPU memory. It shows nothing about whether Marigold fits on this GPU, so its result is "not measured", not "fails".
- CPU runs recorded no peak memory, although How step 4 asked for it.
- The Marigold scorer read the wrong folder (`<sequence>/predictions_npy` instead of `<sequence>/images/predictions_npy`), and its test copied the same mistake.
- `data/models/` was not ignored by Git: two Depth Anything JSON configs and the nested ZipDepth repository showed as untracked.
