---
id: "54"
title: Compare three depth methods and validate real metric depth
status: open
priority: HIGH
type: experiment
approval_status: planning authorised 2026-10-06; owner named the three-method comparison on 2026-10-07; execution requires frozen settings and plan review
blocked_by: []
blocks: []
verification_test: "experiments/02_stereo_depth/tests/test_metric_depth.py"
plan_reviewed: null
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

Measure how well three different programs can estimate the distance from the camera to every point in a picture, using recordings where the true distances were also measured by a depth sensor. One program is small and gives real distances, one is large and slow but known for good shapes, and one is built to run fast on phones. Compare their errors, how much of each picture they cover, how long they take and how big they are. Then use the best phone-ready option in the full pipeline instead of borrowing the sensor's distances.

## Board update, 7 October 2026

Task51 was rescoped on 6 October 2026 to the first prerecorded pipeline. Field decisions (site, objects, survey, storage, numeric limits, phone processing split) now belong to Task61. Controls on existing recorded data can start now, so this task is not blocked.

Deployment must be on a phone (owner, 7 October 2026). The chosen depth route must have a path that runs on the phone: ARCore's Depth API, or a model small enough to convert and run on the device. If Task61 decides the phone only records and processing is hosted, still measure model size and speed so the choice can be revisited. The physical phone trial needs Task52's recording and Task53's survey.

## Methods compared (owner request, 7 October 2026)

| Method | Why it is in the comparison | Output | Size and licence | Phone route |
|---|---|---|---|---|
| [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) Small, metric indoor checkpoint (Hypersim, max 20 m) | Named candidate since Task51; the only one of the three that outputs metres directly | Depth in metres | 24.8M parameters. The relative Small model is Apache-2.0; confirm the metric indoor Small checkpoint's licence on its model card before the run | Small enough to try converting; not built for phone chips |
| [Marigold Depth v1.1](https://github.com/prs-eth/marigold) (`prs-eth/marigold-depth-v1-1`) | Owner request. Strong shape quality; serves as the hosted accuracy reference | Relative depth (correct shape, unknown scale and offset) | Stable Diffusion 2 U-Net and image encoder, roughly 0.9B parameters (estimate; record the real count at load). Code Apache-2.0; weights under the RAIL++-M licence, which carries use restrictions | None; hosted only |
| [ZipDepth](https://github.com/fabiotosi92/ZipDepth) (ECCV 2026) | Most promising phone model found: about 6.1M parameters, a separate build for phone AI chips (NPUs), and export to ONNX, TFLite and CoreML | Relative depth | MIT licence on the repository (confirm it covers the weights); released July 2026 | Built for phones |

The owner asked for "Marigold v2". The newest Marigold depth release found on 7 October 2026 is v1.1 (15 May 2025); no v2 exists in the official repository. Confirm v1.1 before running.

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
2. **Tests first.** In `experiments/02_stereo_depth/tests/test_metric_depth.py`, assert unit conversion, the native output convention each adapter declares (Marigold: relative depth; ZipDepth: confirm from its code whether it outputs relative depth or relative inverse depth), invalid pixels staying invalid, image-grid mismatch rejected, alignment that recovers a known scale and shift on a synthetic frame, and reference depth never passed to an adapter.
3. **Score on TUM.** Same frames for all three methods. Reference is the Kinect depth, used for scoring only. Report two views and never mix them:
   - *Metric view* (Depth Anything V2 metric only): raw output against the reference.
   - *Shape view* (all three): per-frame least-squares scale and shift fitted in each method's native space against the reference, then scored. Label this as reference-aligned; it shows shape quality, not real-world distance.
   Metrics: AbsRel, RMSE in metres, share of pixels within 1.25x of the reference (δ1), valid coverage, and each of these by distance band (0-1, 1-2, 2-4 m).
4. **Cost.** On MasterPC, GPU and CPU separately: model load time, warm per-frame time (after warm-up frames), peak memory, file size and parameter count. For ZipDepth also: ONNX and TFLite export, and the exported model's output difference from PyTorch on the same frames. On-phone timing belongs to Task57.
5. **Scale for relative methods.** In the walkthrough, a relative method needs a scale source. Allowed sources: the reference (labelled as a control, never counted as a result), or later ARCore's metric depth or tracked points on the phone (Task52/57). Do not add any other hidden scaling.
6. **Wire the metric method.** Add the Depth Anything V2 metric adapter as a `DepthMethod` in `src/walkthrough/steps/depth.py`, returning axial depth in metres and a validity mask. Its output must pass the layer's existing validation.
7. **Publish** one run with per-method results, settings, weight hashes and environment. A method that performs badly or fails to convert is a valid result.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Each method adapter | scorer; walkthrough depth layer (metric method only) | native output plus declared convention; metric output is axial Z in metres with a validity mask on the source image grid | sealed run survives | src/walkthrough/steps/depth.py:34-35,113; experiments/shared/geometry.py:10 |
| Recorded TUM Kinect depth | scorer only | uint16 at 5000 units per metre, valid below 4 m, paired by timestamp within 0.02 s | original dataset files unchanged | src/walkthrough/steps/depth.py:43-45 |
| Downloaded weights | adapters | local files outside Git, identified by SHA-256 | re-download must match the recorded hash | n/a until downloaded |

Original frames, frozen settings and weight hashes are the source of truth. The reference never reaches an adapter. Alignment for the shape view happens in the scorer only. An interrupted run stays incomplete; restart uses a fresh run directory. A fresh machine needs the pinned environment, the hashed weights and the local TUM data. Existing supplied-depth controls stay readable and labelled as controls.

## Hyperparameters

Proposed on 2026-10-07. Values marked "pending" need the owner's confirmation before the run.

| name | value | source |
|---|---|---|
| methods | Depth Anything V2 metric indoor Small; Marigold Depth v1.1; ZipDepth | confirmed 2026-10-07 (owner named the first two and delegated the phone choice; ZipDepth chosen) |
| Marigold version | v1.1 (`prs-eth/marigold-depth-v1-1`) | n/a pending owner confirmation; owner asked for "v2", which does not exist |
| Depth Anything V2 input size and max depth | 518 px short side (repository default); 20 m (indoor checkpoint) | n/a pending owner confirmation |
| Marigold denoising steps, ensemble size, processing resolution | 1 step, ensemble 1, 768 px (repository's practical setting) | n/a pending owner confirmation |
| ZipDepth build and input size | NPU build for the export check; GPU build for desktop scoring; repository default input size | n/a pending owner confirmation |
| recordings and frames | TUM freiburg1_xyz and freiburg1_desk, every 10th colour frame | n/a pending owner confirmation |
| reference decoding | 5000 units per metre; valid when 0 < depth < 4 m; pairing tolerance 0.02 s | inherited src/walkthrough/steps/depth.py:43-45 |
| shape-view alignment | per-frame least-squares scale and shift in each method's native space, over valid reference pixels | n/a pending owner confirmation |
| distance bands | 0-1, 1-2, 2-4 m | n/a pending owner confirmation |
| timing | 5 warm-up frames discarded; GPU and CPU timed separately; 3 repeats, median reported | n/a pending owner confirmation |
| output units for the walkthrough | axial Z in metres with validity mask | inherited src/walkthrough/steps/depth.py:113 |

## Verification

- Contract test `experiments/02_stereo_depth/tests/test_metric_depth.py`: a synthetic frame with known depth survives unit conversion exactly; alignment recovers a known scale and shift within 1e-6; invalid reference pixels are excluded from every metric; a mismatched image grid raises; each adapter declares its output convention; no adapter call receives reference depth.
- Walkthrough test under `src/walkthrough/tests/`: the Depth Anything V2 metric method passes the depth layer's validation on a fixture frame and returns the source frame ID.
- Before: 0 depth methods run. After: 3 methods scored on the same frames with both views, cost on GPU and CPU, and the ZipDepth export check. Failing an accuracy limit is a valid reported outcome. Numeric limits come from Task61.

Before starting this HIGH task: confirm the pending settings, run task-plan lint, and obtain a fresh plan review.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan only; implementation not started |
| Test status | Planned contract checks; no run claimed |
| Before measurement | 0 depth methods run in experiment02; downstream trials use supplied sensor depth |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Open; settings confirmation, plan review and execution pending |

still open because this plan has not been implemented or measured.
