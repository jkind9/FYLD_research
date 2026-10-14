# Layer 2: depth estimation

This folder is layer 2 of the five-layer pipeline described in the [root README](../../README.md). It answers one question: **how far away is each pixel, in metres?**

A phone video is flat. Without depth, nothing in it can be measured. Depth is what turns pixels into points in space. The surface layer (layer 4) needs it to build a 3D model. The object layer (layer 5) needs it to give each object a position. The camera tracker (layer 3) can use it to fix the real-world scale of the camera path.

**Status:** Task54 and Task62 have completed the local model runs. Depth Anything V2 Metric Small and both ZipDepth builds were scored on CPU and GPU for both recordings. Marigold V2 scored best on xyz but takes 16.6 s per frame, so it fails the owner's 1 frame per second floor and was dropped. With only 50 known distances per frame, the phone build of ZipDepth reaches its every-pixel shape score (AbsRel about 0.07). ZipDepth's ONNX export matches PyTorch; generated TFLite files fail tensor allocation. These indoor recordings test close-range depth only; they do not establish worksite-range accuracy.

**Route decision: stereo if possible, otherwise single video.**
1. Layer 1 checks whether either phone lets an app record two rear lenses at the same moment. If one does, this layer computes stereo depth from the pair.
2. If neither does, this layer uses single-camera methods:
   - ARCore depth on the phone.
   - Learned video depth on a server, such as Depth Anything 3 or MapAnything.
   - Real-world scale from ARCore, GPS or objects of known size.
3. Phone lenses are only 1–2 cm apart, so stereo adds little beyond a few metres. The single-video route is developed alongside the stereo check rather than after it. It is also the only route that works on ordinary video recorded without a special app.

The folder keeps its original name, `02_stereo_depth`, but covers both routes.

## How depth estimation works

A depth image has one value per pixel: the distance in metres from the camera to the surface seen at that pixel, measured along the camera's forward axis. Pixels where the method has no answer are marked invalid. Invalid is not the same as far away.

There are four ways to get depth.

| Approach | How it works | Strengths | Weaknesses |
|---|---|---|---|
| **Two-camera stereo** | Two cameras a known distance apart (the baseline) see the same point. The point appears shifted sideways between the two images. That shift, in pixels, is the disparity. Depth = focal length × baseline ÷ disparity. | Real metric scale from the calibration alone. Works on a single moment, so moving objects are fine. | Phone lenses sit 1–2 cm apart, so the shift is tiny beyond a few metres and error grows with the square of distance. Fails on blank walls, repeated patterns, reflections and glare. Both lenses must capture at the same instant, which many phones do not allow apps to do. |
| **Depth from motion** | One camera moves. Frames taken from different positions act like a stereo pair with a longer baseline. ARCore's depth works this way on most phones. | Needs only one camera. A longer baseline helps at range. | Needs accurate camera motion (layer 3). Moving objects confuse it. |
| **Active depth sensors** | The device emits light and measures its return: time-of-flight, LiDAR or a projected pattern. The Kinect used in the TUM benchmark works this way. | Accurate at short range, even on blank walls. | Most Android phones have no such sensor. Sunlight and range limit it outdoors. |
| **Learned single-image depth** | A neural network estimates depth from one image, using what it has learned about how scenes look. | Dense, sharp, works anywhere a camera does. | The shape is often right while the scale is wrong, unless the model is trained to output metres ("metric" depth) and that claim is checked. Errors are hard to predict. |

Modern systems mix these. For example, a learned model gives dense, sharp depth, and a few reliable measured points (from ARCore or stereo) fix its scale.

Every depth result also needs the calibration of the camera that took it: focal length and image centre in pixels, lens distortion and, for stereo, the offset between the two cameras. Without calibration, depth cannot be turned into metres.

## Methods: hosted and on the phone

**Hosted** means the phone only records and a server with a large GPU computes depth. **On the phone** means it runs on the handset with no internet, mainly for quick checks on site. See the root README for how the two routes fit together.

| Method | Route | What it does | Licence and notes |
|---|---|---|---|
| [FoundationStereo](https://arxiv.org/abs/2501.09898) (NVIDIA, CVPR 2025) | Hosted | Stereo depth that works on new scenes without retraining. [Fast-FoundationStereo](https://arxiv.org/abs/2512.11130) is a faster variant. | NVIDIA research licence; check terms. Needs two lenses that capture together. |
| [RAFT-Stereo](https://arxiv.org/abs/2109.07547) | Hosted | A well-established learned stereo baseline. | Check code and weight terms before use. |
| [Depth Anything 3](https://arxiv.org/abs/2511.10647) | Hosted | Depth and camera rays from any number of frames, with or without known camera positions. | Licence differs by model size; check per checkpoint. |
| [MapAnything](https://arxiv.org/abs/2509.13414) (Meta) | Hosted | Metric 3D geometry and cameras from images, optionally using known calibration, depth or poses as extra input. | Check code and checkpoint terms. |
| [Depth Pro](https://arxiv.org/abs/2410.02073) (Apple) | Hosted | Metric depth from a single image, with sharp edges. | Apple sample-code licence; check terms. |
| [ARCore Depth API](https://developers.google.com/ar/develop/java/depth/raw-depth) | On the phone | Depth from motion, plus a per-pixel confidence. Uses a depth sensor if the phone has one. Both test phones are listed by Google as supporting it ([device list](https://developers.google.com/ar/devices), checked 4 October 2026). | Google terms. Confidence values are not calibrated error bars. Quality on our phones is unmeasured. |
| OpenCV semi-global block matching ([StereoSGBM](https://docs.opencv.org/4.x/d2/d85/classcv_1_1StereoSGBM.html)) | Either | Classical stereo matching with no learned weights. The planned first baseline. | Apache-2.0. Runs on a CPU. |
| [MobileStereoNet](https://arxiv.org/abs/2108.09770), [HITNet](https://arxiv.org/abs/2007.12140), [BANet](../../research/depth_estimation/banet.md) | On the phone | Learned stereo networks designed to be small and fast. | Check code and weight terms for each. |
| [Depth Anything V2](https://arxiv.org/abs/2406.09414) Small | On the phone | Small single-image depth model. Relative depth by default; metric versions exist. | The Small model is Apache-2.0; larger models are non-commercial. |

On-phone models run through a mobile runtime: [LiteRT](https://ai.google.dev/edge/litert) (formerly TensorFlow Lite), [ONNX Runtime Mobile](https://onnxruntime.ai/docs/tutorials/mobile/), [ExecuTorch](https://pytorch.org/executorch) or the precompiled models on [Qualcomm AI Hub](https://aihub.qualcomm.com/). Published speeds come from the authors' hardware and do not predict speed on these phones.

## Top 5 sources

| Source | What it is | Why it matters here |
|---|---|---|
| [ARCore Raw Depth](https://developers.google.com/ar/develop/java/depth/raw-depth) and the [project note](../../research/phone_ar_platforms/arcore_raw_depth.md) | Google's documentation for phone depth with confidence | The cheapest route to depth on both test phones. It separates fresh depth from depth reused from earlier frames. |
| [FoundationStereo](https://arxiv.org/abs/2501.09898) | A 2025 stereo model trained on 1 million synthetic pairs | The strongest hosted option if the phones can capture two lenses at once. |
| [Depth Anything 3](https://arxiv.org/abs/2511.10647) | A 2025 model that predicts consistent depth across many views | The strongest hosted option for single-lens video. |
| [MobiDepth](../../research/depth_estimation/mobidepth.md) | Research on stereo depth from two phone cameras | Explains how lens differences and capture timing on real phones affect depth. |
| [Middlebury stereo, version 3](https://vision.middlebury.edu/stereo/submit3/) | A stereo benchmark with exact reference depth | The scoring data for this layer. |

More background: [HiMoDepth](../../research/depth_estimation/himodepth.md) on keeping image detail in phone stereo, [MobileStereoNet](../../research/depth_estimation/mobilestereonet.md), [BANet](../../research/depth_estimation/banet.md) and [HyperSight](../../research/depth_estimation/hypersight.md) on using camera motion for longer range.

## Where this layer stands

- The Middlebury version 3 quarter-resolution training data is downloaded and checked at `data/middlebury/dataset/MiddEval3/trainingQ/`. It has 15 indoor scenes with left and right images, calibration, reference disparity and masks. [Download records](../../data/README.md).
- TUM Freiburg1 `xyz` and `desk` recordings are available under `data/tum/`. The existing timestamp reader in experiment 03 finds 792 paired frames in `xyz` and 573 in `desk`. Every-tenth-frame samples loaded successfully: 80 and 58 frames, respectively.
- `geometry.py` converts metric maps and aligns metric, relative, inverse-relative and affine-invariant log-depth maps to the sensor reference for a clearly labelled shape score. Invalid metric pixels do not enter the alignment fit. `scoring.py` keeps raw metric accuracy separate from reference-aligned shape scores and reports AbsRel, RMSE, δ1, coverage, distance bands and the share of aligned values that are non-positive.
- `src/walkthrough/steps/depth.py` has an offline-only Depth Anything V2 metric adapter. It requires a local checkpoint folder and sets `local_files_only=True`; it cannot download weights.
- Depth Anything V2 Metric Small and ZipDepth have each run on the same 138 TUM color frames on CPU and GPU. The score table in [Task54 measurements](#task54-measurements-on-tum) separates raw metric depth from shape scores aligned to the sensor reference.
- Checkpoint hashes, run outputs, CPU/GPU timing details and per-frame depth maps are stored under the ignored `experiments/02_stereo_depth/runs/task54*` directories. They are local research artifacts and are not committed.
- Marigold V2 uses the official WSL inference program. The first frame failed in VAE `conv3d` with cuDNN "GET was unable to find an engine to execute this computation" while the active game and desktop used 15,910 of 16,303 MiB of GPU memory. The owner asked to keep the game open and record this result. One CPU retry failed before inference because bitsandbytes requires a GPU for 4-bit quantization. Task62 reran it with the GPU free: xyz completed (shape AbsRel 0.0356, 16.6 s per frame), and the model was then dropped for being under 1 frame per second.
- ZipDepth's NPU build exports to ONNX with output differences below 6.3e-7 on all sampled frames. TFLite float32 and float16 files were generated, but LiteRT cannot allocate their tensors because a multiply has incompatible broadcast shapes. No phone runtime timing has been measured; Task57 owns that check.
- Layers 3, 4 and 5 currently use depth from the TUM and ICL-NUIM benchmark recordings. The object layer ignores depth at or beyond 4 m. Nothing here establishes accuracy at worksite distances.

## How this layer will be tested

### Data and reference

Use the 15 Middlebury training scenes. Choose development and held-out scenes before tuning anything, and record the choice. The separate Middlebury test images have no public reference disparity, so they cannot be scored locally.

The reference disparity and masks are used only for scoring. Convert disparity to depth with each scene's calibration:

`depth_mm = baseline_mm × focal_length_px ÷ (disparity_px + doffs_px)`

Here `doffs` is the horizontal offset between the two image centres. Leaving it out gives wrong depth. [Middlebury calibration description](https://vision.middlebury.edu/stereo/data/scenes2014/).

### Inputs and outputs

- **Input:** two images, camera identifiers, capture times, focal lengths, image centres, distortion and the relative pose between the cameras with translation in metres. Any crop, resize or rotation is recorded, because calibration only applies to the image size it was measured for.
- **Output:** depth in metres, a validity mask, and a confidence only if the method provides one. Depth is distance along the reference camera's forward axis unless another definition is declared. Failed matches are invalid, not zero distance.

### Steps

1. Check image alignment and calibration on static recorded pairs.
2. Run the classical StereoSGBM baseline with its settings recorded.
3. Score depth error by distance range, valid coverage and error at object edges.
4. Compare a learned stereo model after checking code and weight licences.
5. Run the same input on the phone and on a server. Time preprocessing, inference and delivery separately.

ARCore phone depth can be compared on phone recordings. Label where it came from; it is not an independent reference.

### Measurements and failure cases

Report depth error by distance band, valid coverage, edge error, sensitivity to capture timing, runtime and memory. On the phone, add sustained speed and heat. Paper frame rates are not targets for these devices.

Test weak texture, occlusion, reflections, motion and mismatched exposure. Reject incompatible calibration and image sizes with a clear error. Keep "inaccurate depth" separate from "no depth".

No numeric pass mark is set yet. Agree quality and coverage limits before acceptance trials. Good desktop accuracy does not show phone performance, and fast phone speed does not show accuracy.

## What can be improved

- **Start the baseline.** Run StereoSGBM on a fixed Middlebury split to get the first measured number for this layer.
- **Measure ARCore depth on both phones.** Film a scene with tape-measured distances and score ARCore depth and confidence against it. This decides whether on-phone depth is good enough for site checks.
- **Combine learned and measured depth.** Use ARCore or stereo points to fix the scale of a dense learned depth map, and measure whether the result beats either alone.
- **Test range.** Error grows with distance. Worksites need checks beyond the current 4 m indoor limit, with outdoor references.
- **Calibrate confidence.** Check whether low-confidence pixels really are the wrong ones before using confidence to weight later layers.
- **Find a sequence with stereo and a reference camera path.** TUM has no stereo pair and Middlebury has no camera path, so neither can test how stereo depth affects tracking. A synchronised stereo dataset or a measured phone recording is needed for that swap.

Once tracking or reconstruction can read this layer's output without knowing where it was computed, promote the depth record format into [experiments/shared](../shared/README.md). See the [experiment guide](../README.md) for how the layers connect.

## Task54 measurements on TUM

Runs use every tenth timestamp-associated color frame: 80 frames from `rgbd_dataset_freiburg1_xyz` and 58 from `rgbd_dataset_freiburg1_desk`. The Kinect depth images were used only by the scorer. The models received RGB pixels without the references. Each score map is the pixelwise median of three predictions after five warmup frames.

| Method and score view | Recording | Device | AbsRel | RMSE (m) | δ1 | Reference coverage | Median time/frame |
|---|---|---:|---:|---:|---:|---:|---:|
| Depth Anything V2 metric, raw metric | xyz | GPU | 0.3450 | 0.4294 | 0.2772 | 100% | 133.89 ms |
| Depth Anything V2 metric, raw metric | xyz | CPU | 0.3449 | 0.4294 | 0.2773 | 100% | 280.07 ms |
| Depth Anything V2 metric, raw metric | desk | GPU | 0.4496 | 0.4687 | 0.2570 | 100% | 132.87 ms |
| Depth Anything V2 metric, raw metric | desk | CPU | 0.4496 | 0.4687 | 0.2570 | 100% | 318.11 ms |
| ZipDepth inverse depth, reference-aligned shape | xyz | GPU | 0.0716 | 0.1941 | 0.9282 | 100% | 27.25 ms |
| ZipDepth inverse depth, reference-aligned shape | xyz | CPU | 0.0716 | 0.1941 | 0.9282 | 100% | 34.36 ms |
| ZipDepth inverse depth, reference-aligned shape | desk | GPU | 0.0698 | 0.1920 | 0.9434 | 100% | 27.49 ms |
| ZipDepth inverse depth, reference-aligned shape | desk | CPU | 0.0698 | 0.1919 | 0.9434 | 100% | 34.36 ms |

The ZipDepth predictor returns affine-invariant inverse depth. Its shape rows align each frame in inverse-depth space, then invert to metres. They do not show independent metric accuracy, so compare them only with other shape rows.

Run either tested model from the repository root after installing `requirements-task54-host.txt` and placing the named checkpoint locally. The runner reads the existing TUM recordings and never downloads weights. ZipDepth's own code is imported from its cloned repository, so put that folder on the import path first (without it the run stops with `No module named 'zipdepth'`):

```powershell
$env:PYTHONPATH = "$PWD;$PWD\data\models\ZipDepth"
python -m experiments.02_stereo_depth.run --method depth-anything --checkpoint <local-metric-checkpoint> --tum-root data/tum --output experiments/02_stereo_depth/runs/task54 --device cuda
python -m experiments.02_stereo_depth.run --method depth-anything --checkpoint <local-metric-checkpoint> --tum-root data/tum --output experiments/02_stereo_depth/runs/task54_cpu --device cpu
python -m experiments.02_stereo_depth.run --method zipdepth --checkpoint data/models/ZipDepth/checkpoints/zipdepth_base.pth --tum-root data/tum --output experiments/02_stereo_depth/runs/task54 --device cuda --zip-build gpu
python -m experiments.02_stereo_depth.run --method zipdepth --checkpoint data/models/ZipDepth/checkpoints/zipdepth_base.pth --tum-root data/tum --output experiments/02_stereo_depth/runs/task54_cpu --device cpu --zip-build gpu
```

Each sequence writes native predictions and `results.json` under a new method folder. Existing results are never overwritten. If Windows denies the final directory rename, the runner copies the finished staging folder and checks the published file list and sizes before removing staging.

Depth Anything V2 used 24,785,089 parameters, a 99,173,660-byte checkpoint and about 332 MiB of PyTorch CUDA allocation. ZipDepth used 6,143,710 parameters, a 27,298,978-byte GPU checkpoint and about 89 MiB of PyTorch CUDA allocation. Their SHA-256 values are `e990eb82fbf11b05b7813261196a2b841bdcf5a05f64396724a8987fa90504a3` and `a55910bb0b99c8c5e641cb9206e810b269690ad94e8a2ef08c827c4679391a65`, respectively. The NPU checkpoint is also present locally for the export check.

The Windows runs used Python 3.12.10, PyTorch 2.11.0+cu128, Transformers 5.14.1, NumPy 2.4.2 and Pillow 12.3.0 on an RTX 5070 Ti. The pinned runtime snapshots are in `requirements-task54-host.txt` and `requirements-task54-marigold-wsl.lock`. The official ZipDepth repository declares PyTorch 2.12 or newer; this run used 2.11, so the observed result does not establish the repository's supported minimum. Task54 GPU timings are host observations because the game and desktop shared the GPU; Task62's GPU timings were taken with it free.

Marigold V2 source was pinned to `9926d93b0780de5f64bee20895b25a56a98ffbf8`. Its `Log-stage2/trainables.safetensors` SHA-256 is `3edec69490ba8e8fdc8d63e130f93cb93f514360d415a22701250b2535056892`; the prompt embedding and mask hashes are `ba752b582571d990c75ad6aac2a2eeb0cf04c2fe01b233b1675028eabf342a6d` and `80973a6521f21a5a6faf6402cae185dafef840d91e654efbeb1097914e634798`. The Task54 attempt ran while a game held the GPU and produced no prediction; Task62 below reran it with the GPU free.

## Task62 follow-up measurements, 7 October 2026

A review of Task54 found gaps; [Task62](../../task_list/closed/62_close_task_54_review_gaps_phone_build_score_memory.md) filled them. The same 138 frames and settings as above.

**Phone build scored.** The 0.07 ZipDepth rows above come from the desktop checkpoint (`a559…`). The model exported to ONNX is the separate phone checkpoint (`zipdepth_base_npu.pth`, SHA-256 `627c04fd…`, 6,142,058 parameters). It is slightly more accurate:

| ZipDepth build | Recording | Shape AbsRel | RMSE (m) | δ1 | CPU time/frame | GPU time/frame |
|---|---|---:|---:|---:|---:|---:|
| Desktop | xyz | 0.0716 | 0.1941 | 0.9282 | 25.0 ms | — |
| Desktop | desk | 0.0698 | 0.1919 | 0.9434 | 25.5 ms | — |
| Phone (the ONNX export) | xyz | 0.0703 | 0.1890 | 0.9332 | 23.9 ms | 5.2 ms |
| Phone (the ONNX export) | desk | 0.0682 | 0.1883 | 0.9465 | 24.0 ms | 5.3 ms |

GPU times here are with the GPU free; Task54's 27 ms was measured while a game shared it. ONNX matches the phone build's PyTorch output within 6.3e-7, so these scores also describe the ONNX file.

**Memory.** The runner now records the peak memory of its whole process on every run, CPU and GPU (`peak_process_memory_mib`; it includes PyTorch itself and model loading). On CPU: Depth Anything about 1.8 GB (4.3–4.6 fps, 218–231 ms per frame), ZipDepth about 1.4 GB. The ZipDepth GPU run used about 2.0 GB of host memory and 89 MiB of GPU memory. Checkpoint lists no longer hash Hugging Face's `.cache` bookkeeping files.

**Marigold V2, with the GPU free.** On xyz all 80 frames finished: shape AbsRel **0.0356**, RMSE 0.115 m, δ1 0.986, half the error of the other two. The cost rules it out: 16.6 s per frame (median; later frames took up to 88 s), 73.8 s before the first map, 12.9 GB of GPU memory above idle (15.97 of 16.30 GB in use) and 10.6 GB of host memory. Desk slowed to 135 s per frame and crashed at frame 15 with `CUDA error: unknown error` while the GPU was full. The owner ruled on 7 October 2026 that anything under 1 frame per second is not worth using, so Marigold was dropped and the desk rerun stopped. Its desk score is not reported. `marigold_wsl_run.sh` runs the official program in WSL and records wall time, per-map timing, process memory and whole-GPU memory per recording.

**Scale from a few known points.** A phone cannot use the dense Kinect depth that the shape rows fit to. It can know the distance at a few points (ARCore depth, tracked features). `sparse_scale.py` fits each frame's scale and shift from N randomly chosen reference pixels and scores every pixel. Five seeds per count; the table gives the median AbsRel with the range over seeds:

| Method | Recording | 10 points | 50 points | 200 points | 1000 points | Every pixel |
|---|---|---|---|---|---|---|
| ZipDepth phone build | xyz | 0.080 (0.078–0.082) | 0.073 | 0.071 | 0.070 | 0.070 |
| ZipDepth phone build | desk | 0.080 (0.077–0.082) | 0.070 | 0.069 | 0.068 | 0.068 |
| ZipDepth desktop build | xyz | 0.083 (0.081–0.083) | 0.074 | 0.072 | 0.072 | 0.072 |
| ZipDepth desktop build | desk | 0.082 (0.080–0.084) | 0.072 | 0.070 | 0.070 | 0.070 |
| Depth Anything, scale and shift | xyz | 0.075 (0.071–0.077) | 0.069 | 0.067 | 0.066 | 0.066 |
| Depth Anything, scale and shift | desk | 0.093 (0.083–0.102) | 0.086 | 0.082 | 0.082 | 0.082 |
| Depth Anything, one scale factor only | xyz | 0.082 (0.078–0.083) | 0.075 | 0.073 | 0.073 | raw 0.345 |
| Depth Anything, one scale factor only | desk | 0.112 (0.103–0.114) | 0.105 | 0.105 | 0.105 | raw 0.450 |
| Marigold V2 | xyz | 0.044 (0.042–0.044) | 0.038 | 0.036 | 0.036 | 0.036 |

Fifty known distances per frame are enough to reach the every-pixel result, and ten cost about 0.01 AbsRel. For Depth Anything, one scale factor from ten points cuts its error from 0.345 to 0.082 on xyz. The chosen points are exact Kinect values, so a real phone's noisier points will do worse; measuring that needs phone recordings (Task52). Run it with:

```powershell
python -m experiments.02_stereo_depth.sparse_scale `
  --set "ZipDepth phone build=experiments/02_stereo_depth/runs/task62_gpu_npu/zipdepth" `
  --set "Depth Anything=experiments/02_stereo_depth/runs/task54/depth-anything" `
  --output experiments/02_stereo_depth/runs/<new>/sparse_scale.json
```

**Which depth method for the pipeline.** On these numbers the phone build of ZipDepth with a per-frame scale from about 50 phone points is the strongest candidate: about 0.07 shape error, 42 fps on CPU and 190 fps on the desktop GPU, 6.1 million parameters and an ONNX export. Depth Anything's raw metres need the same scale source anyway. The walkthrough does not yet have a scale-source adapter for relative depth; that needs ARCore depth or tracked points from a phone recording (Task52).

Tests for this experiment: `python -m pytest experiments/02_stereo_depth/tests -q` (51 tests).

ZipDepth NPU export used the original fused model graph, `dynamo=False`, and ONNX opset 17. The resulting 24,604,413-byte model has SHA-256 `ecf73a4ffd16562be0c67f89404530b29926ac3b562034d00eb3b0f35ae913ed`. Across the 138 selected TUM frames, mean absolute output differences from PyTorch were 2.57e-8 (xyz) and 2.35e-8 (desk); maximum differences were 6.30e-7 and 5.55e-7. ONNX Runtime CPU inference is verified for the exported graph. TFLite conversion produced float32 (24,615,956 bytes) and float16 (12,331,112 bytes) files, but LiteRT failed allocation at a multiply with shapes `[1,48,64,96]` and `[1,64,96,96]`. These files are not usable phone exports.

## Task65: depth whose size changes from frame to frame, 8 October 2026

### The problem

In the walkthrough, Depth Anything V2 Metric Small gets each frame's shape about right but its size wrong, and by a different amount in each frame. On 30 TUM xyz frames its median predicted/sensor distance moves between 1.21 and 1.63. When the frames are combined, the same surface lands at a different distance from each camera, so the 3D view shows it several times along the viewing direction. The camera tracker (Open3D RGB-D odometry) reads each jump in size as camera motion: at frame 16 the size jumps from 1.39 to 1.62 and camera error from 147 to 337 mm in the same frame.

[Task65](../../task_list/done/65_diagnose_and_fix_frame_to_frame_depth_scale_drift.md) measures this and tests fixes. Results are below the survey.

### What existing systems do (survey, 8 October 2026)

Every source below was opened. The ones marked "checked" were also re-opened by hand before being used in a recommendation. "Not published" means the number was not on the page. Speeds come from the authors' hardware (mostly NVIDIA A100 or RTX GPUs) and do not predict this CPU or the phone.

| Family | Method (source, date) | Input | Metric size from | Published accuracy and speed | Size and licence | Phone or host |
|---|---|---|---|---|---|---|
| Scale kept from frame to frame | Consistent Video Depth (Luo et al., [arXiv 2004.15021](https://arxiv.org/abs/2004.15021), SIGGRAPH 2020); Robust Consistent Video Depth (Kopf et al., [arXiv 2012.05901](https://arxiv.org/abs/2012.05901), 2021) | Video; structure-from-motion poses or none | None | Fine-tune the network on each video at test time; run time not published | Licence not checked | Host, offline |
| | VI-Depth (Wofk et al., ICRA 2023, [repo](https://github.com/isl-org/VI-Depth)), checked | RGB plus sparse metric points from visual-inertial tracking | The phone-style tracking points: one global fit, then a learned per-pixel scale map | VOID: AbsRel 0.069 after the global fit, 0.046 with the scale map | Up to DPT-Large; MiDaS-small option; MIT; archived 25 Aug 2025 | MiDaS-small variant plausible on a phone, untested |
| | PTC-Depth ([arXiv 2604.01791](https://arxiv.org/abs/2604.01791), CVPR 2026) | Video plus wheel odometry or GPS | Optical-flow triangulation with metric motion; a recursive Bayesian filter tracks the depth model's scale | No numbers in abstract | No code seen | Unknown |
| Video depth models | Video Depth Anything (Chen et al., [arXiv 2501.12375](https://arxiv.org/abs/2501.12375), CVPR 2025, [repo](https://github.com/DepthAnything/Video-Depth-Anything)), checked | RGB video, 32-frame windows | Metric variants trained on synthetic Virtual KITTI (driving) and IRS (indoor) | Small: 9.1 ms per frame on A100 (FP32) | Small 28.4M parameters, 116 MB; code and Small weights Apache-2.0; Base/Large CC BY-NC 4.0 | Host CPU plausible (measured below); phone untested |
| | DepthCrafter ([arXiv 2409.02095](https://arxiv.org/abs/2409.02095), CVPR 2025) | RGB video | Relative only | 2.1 fps at 1024x576 on A100, about 26 GB | Diffusion model; academic-only licence | Host GPU only |
| | VeloDepth ([arXiv 2512.10725](https://arxiv.org/abs/2512.10725), 3DV 2026) | RGB, optional calibration; online | Metric, from UniDepthV2 | 26.2 fps on RTX 3090; 2.7 fps on an Apple M1 Pro | 409M parameters; CC BY-NC 4.0 | Host |
| | ChronoDepth, Depth Any Video, FlashDepth (2024-2025) | RGB video | Relative | GPU only; diffusion or large models | Non-commercial or unverified weights | Host GPU |
| Many views at once, SLAM | Depth Anything 3 ([arXiv 2511.10647](https://arxiv.org/abs/2511.10647), [repo](https://github.com/ByteDance-Seed/Depth-Anything-3)), checked | Any number of images; poses optional | Only DA3Metric-Large (0.35B, single image) or the non-commercial Nested model | Beats VGGT by 44% on pose, 25% on geometry (paper) | DA3-Small 0.08B Apache-2.0, not metric | Host GPU |
| | MASt3R-SLAM ([arXiv 2412.12392](https://arxiv.org/abs/2412.12392), CVPR 2025) | Monocular video | MASt3R's approximately metric point maps | 15 fps on RTX 4090 | ViT-L; CC BY-NC-SA 4.0 | Host GPU |
| | VGGT, VGGT-SLAM 2.0, MapAnything, Pi3, CUT3R, StreamVGGT (2025-2026) | Images or video | Mostly not metric (MapAnything predicts a metric factor) | Under 1 s per scene on GPU | About 1B parameters; mostly non-commercial (MapAnything has an Apache variant) | Host GPU |
| | DROID-SLAM, DPVO (2021-2024) | Monocular, stereo or RGB-D | Monocular has no scale | GPU, at least 11 GB for DROID | BSD-3 / MIT | Host GPU |
| | ORB-SLAM3 ([arXiv 2007.11898](https://arxiv.org/abs/2007.11898)) | Camera, optional IMU | IMU, stereo or depth sensor | 3.6 cm on EuRoC (stereo-inertial) | GPLv3 | CPU; no Android build stated |
| No per-frame depth | COLMAP and GLOMAP structure from motion; Gaussian splatting | Images | None unless a known distance is added | Offline; splatting trains for minutes on a GPU | BSD; original splatting non-commercial (gsplat Apache-2.0) | Host, offline |
| Phone scale | ARCore motion tracking (checked: Kim et al., *Sensors*, 15 Dec 2022, [PMC9785098](https://pmc.ncbi.nlm.nih.gov/articles/PMC9785098/)) | Camera plus IMU | Visual-inertial tracking | ARCore 1.29 on an LG V60, final drift: corridor 0.12 m, hallway 0.09 m, campus 0.07 m, parking 1.14 m, stairs 3.98 m, car 140 m | Built in | Phone, live |
| | ARCore Depth API ([docs](https://developers.google.com/ar/develop/depth)), checked | Phone movement, plus a time-of-flight sensor if present | Depth from motion on the metric tracking | Depth 0-65 m; most accurate 0.5-5 m; poor on blank surfaces | Built in | Phone; Redmi Note 11 Pro listed |
| Fusion over time | KinectFusion, Open3D TSDF, nvblox, VoxelHashing | Depth plus poses | Whatever the inputs carry | Real time on GPU; Open3D on CPU | MIT / Apache / non-commercial | Host |

Two conclusions shape the tests below. First, fusion (averaging frames into a voxel grid) does not fix a scale that changes per frame: it averages the repeated surfaces into one thick, blurred one, and its own tracking can still read a scale jump as motion. Fusion helps only after each frame's scale is consistent. Second, nothing in the survey with a permissive licence and a CPU-feasible size makes single-video depth metric by itself; metric size needs a sensor (ARCore tracking or depth, an IMU) or a known distance.

Shortlisted and tested here:

1. **Overlap chain** (no phone sensor). Each frame's scale is carried from the frames before it, through corners tracked into it and a PnP solve. It is the scale-propagation idea of the first row, made light enough for a CPU.
2. **Triangulation with metric camera motion** (the phone route). Corners are triangulated with the camera's metric motion, standing in for ARCore or IMU tracking, and each frame's scale is fitted to them. This is the VI-Depth and PTC-Depth idea in its simplest form.
3. **Metric Video Depth Anything Small** (no phone sensor). It is the one permissive, small video depth model.

### Standard evaluation and the rolling-correlation idea

The research scan already covered temporal scale alignment, video depth models, multi-view reconstruction, phone motion sensors, and depth fusion. It found no single standard algorithm for correcting frame-to-frame metric-depth scale. There is a standard way to compare camera paths: the TUM RGB-D benchmark publishes Kinect colour/depth sequences with motion-capture camera poses and an official trajectory evaluator. This project uses its `freiburg1_xyz` and `freiburg1_desk` recordings and compares camera position against those poses. These runs keep the project's first-matched-pose alignment and every-second-frame sampling, so they are not leaderboard results from the full-rate official evaluation.

Published work supports using geometry or shared multi-frame constraints instead of comparing raw depth arrays. *Consistent Video Depth Estimation* links tracked image points through 3D and adjusts depth jointly across a video. Video Depth Anything trains temporal features and constrains depth changes across frames. *Video Depth without Video Models* is especially close to the rolling-average suggestion: it predicts depth on overlapping video snippets and jointly fits each snippet's scale and shift so predictions agree where snippets overlap. Our earlier CPU check of Metric Video Depth Anything Small was 0.77 fps by itself and 0.81 fps with the overlap chain, below the project's 1 fps depth-layer floor.

ZNCC (zero-mean normalized cross-correlation) is useful when two image patches show the same content after a translation, with brightness offset and contrast changes. A depth map from a moving camera does not meet that assumption: camera rotation requires an intrinsics-based image warp, translation causes depth-dependent parallax, and occlusion changes which surfaces are visible. Rotating a fixed-size NumPy array would rotate image coordinates, not the measured 3D points. Sliding one depth array along its value axis would test additive depth offsets; the error seen here is mostly multiplicative scale. A true 3D volume correlation would first need camera poses and a shared voxel grid, which risks circularly using the same uncertain poses and scale we are trying to fix. We therefore did not use ZNCC as the scale estimator.

The useful part of the idea is consensus across several overlapping frames. The existing overlap-chain method already estimates each frame from up to four earlier partners (lags 1, 2, 4, and 8) and takes their median, rather than trusting one previous frame. A later experiment could solve all supported pairwise scale constraints together in log-scale, weighted by match count and reprojection error, with no additive depth shift. The overlapping-snippet method above is a published precedent for joint scale alignment. This graph-wide fit remains a proposal; it has not been implemented or measured here.

### Camera path comparison: raw depth and overlap chain

The [offline camera-path report](../../outputs/task65_runs/camera_path_comparison.html) compares Depth Anything V2 Metric Small with the same depth method corrected by the RGB-only overlap chain. It plots the top-down camera path against TUM motion-capture ground truth and the per-frame position error. Lower RMSE means a closer camera path.

| TUM recording sample | Frames matched | Raw depth camera RMSE | Overlap-chain RMSE | Change |
|---|---:|---:|---:|---:|
| `freiburg1_xyz`, short clip | 30 | 218 mm | 113 mm | 48% lower |
| `freiburg1_xyz`, full every-second-frame clip | 398 | 1,359 mm | 371 mm | 73% lower |
| `freiburg1_desk`, full every-second-frame clip | 298 | 1,720 mm | 1,009 mm | 41% lower |

**Rescored with the standard best-fit path error (Task70, 13 October 2026).** The numbers above pin the estimated path to the true path at the first frame only. The TUM benchmark instead lines up the whole path (best fit), and image-only methods are scored after also fitting one overall size. The 30-frame clip, from `runs/task65/clip30_scale_drift.md`:

| 30-frame xyz run | First pose | Best fit | Best fit with size | Fitted size |
|---|---:|---:|---:|---:|
| recorded | 21 mm | 13 mm | 13 mm | 0.97 |
| depth-anything | 218 mm | 118 mm | 100 mm | 0.47 |
| reference-frame | 56 mm | 30 mm | 29 mm | 0.95 |
| reference-global | 167 mm | 79 mm | 78 mm | 1.22 |
| overlap-chain | 113 mm | 51 mm | 26 mm | 0.72 |
| video-depth-anything | 93 mm | 37 mm | 32 mm | 1.19 |
| video-depth-anything-chain | 63 mm | 26 mm | 10 mm | 0.83 |
| zipdepth-scaled | 72 mm | 25 mm | 24 mm | 0.94 |
| chain-pose-anchor-exact | 71 mm | 21 mm | 21 mm | 0.97 |

A fitted size well below 1 means the estimated path is too long; raw Depth Anything's path is about twice the true length on this clip. The full-length clips (`runs/task65/{xyz,desk}_scale_drift.md`):

| Full-length run | xyz first pose | xyz best fit | xyz best fit with size (size) | desk first pose | desk best fit | desk best fit with size (size) |
|---|---:|---:|---:|---:|---:|---:|
| recorded | 67 mm | 34 mm | 34 mm (1.01) | 220 mm | 112 mm | 112 mm (1.00) |
| depth-anything | 1359 mm | 962 mm | 177 mm (0.06) | 1720 mm | 823 mm | 710 mm (0.55) |
| reference-frame | 231 mm | 133 mm | 98 mm (0.64) | 1553 mm | 517 mm | 401 mm (0.70) |
| reference-global | 644 mm | 456 mm | 164 mm (0.17) | 1179 mm | 892 mm | 783 mm (0.47) |
| overlap-chain | 371 mm | 253 mm | 128 mm (0.38) | 1009 mm | 663 mm | 438 mm (0.60) |
| zipdepth-scaled | 356 mm | 279 mm | 139 mm (0.34) | 481 mm | 299 mm | 289 mm (0.92) |
| chain-pose-anchor-exact | 260 mm | 159 mm | 119 mm (0.57) | 934 mm | 480 mm | 438 mm (0.79) |

Even with the Kinect sensor's depth (`recorded`), the walkthrough tracker misses the desk path by 112 mm after a best fit. Structure from motion on the same frames, from the images alone, scores 24 mm on desk and 12 mm on xyz (experiments/sfm/README.md), so the tracker itself, not only the depth, limits the camera path.

Both full-recording paths improve, but still miss ground truth by 0.37 m on xyz and 1.01 m on desk. The result supports the scale-drift diagnosis and the overlap chain as a candidate. It does not make the camera path accurate enough for deployment. The Kinect-depth rows are sensor-backed controls, not RGB-only alternatives.

Sources: [TUM RGB-D benchmark and trajectory evaluation](https://cvg.cit.tum.de/data/datasets/rgbd-dataset), [TUM evaluation instructions](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/rgbdslam_eval), [Consistent Video Depth Estimation](https://arxiv.org/abs/2004.15021), [Video Depth Anything (CVPR 2025)](https://openaccess.thecvf.com/content/CVPR2025/html/Chen_Video_Depth_Anything_Consistent_Depth_Estimation_for_Super-Long_Videos_CVPR_2025_paper.html), [Video Depth without Video Models (CVPR 2025)](https://openaccess.thecvf.com/content/CVPR2025/html/Ke_Video_Depth_without_Video_Models_CVPR_2025_paper.html).

### Code and model files

- `src/walkthrough/steps/depth_scale.py`: `ScaleCorrected(base, scale)` with four scale sources (`OverlapChainScale`, `PoseTriangulatedScale`, and the reference controls `ReferenceFrameScale` and `ReferenceGlobalScale`); `--depth-scale` on the walkthrough command line.
- `src/walkthrough/steps/video_depth.py`: `MetricVideoDepthAnything`; `--depth video-depth-anything`. It needs the upstream code cloned at commit `4f5ae23172ba60fd7bc11ef671cca678842c7072` (7 October 2025) into `data/models/Video-Depth-Anything` and that folder on `PYTHONPATH`. The weights are `checkpoints/metric_video_depth_anything_vits.pth`: 116,444,063 bytes, SHA-256 `3c28432b4e1f0d7bb31cad5151b6313b49457db5aa58d82e85bfb0f8b1311b33`, from `depth-anything/Metric-Video-Depth-Anything-Small`. One extra package went into `.venv-yolo`: `easydict==1.13` (LGPL-3.0, used once upstream to hold settings). The upstream pins (PyTorch 2.1.1, NumPy 1.24) were not installed, and the optional `xformers` is not used.
- `src/walkthrough/consistency.py`: the surface-gap measure. It moves frame B's points into frame A's camera with the run's poses and compares them with A's depth along A's view, nearest point per pixel only. The report's surface page now shows it per frame and by frame separation. The depth page now shows each frame's scale ratio.
- `scale_drift.py`: `clip` makes full-length every-2nd-frame clips that the tracker can follow; `summarise` reads finished runs into one table; `check-space` stops a queue below 30 GB free.

## Current delivery ownership, 6 October 2026

[Task54](../../task_list/closed/54_implement_and_validate_real_metric_depth.md) implemented and scored local real depth methods. It chooses the usable phone or hosted route from capture evidence; it does not wait indefinitely for stereo. [Task52](../../task_list/open/52_build_and_verify_a_usable_phone_recording.md) supplies phone observations and [Task53](../../task_list/open/53_collect_independent_scene_measurements_and_object_.md) supplies independent physical references.

## Walkthrough depth boundary

The offline experiment runner and a local Depth Anything V2 metric adapter are implemented. The recorded walkthrough still has no selected real depth method in its default run, and its other layers remain incomplete. Deterministic test providers stay labelled as software controls; they do not count as physical measurements. See [the six-step runner](../../src/walkthrough/README.md).
