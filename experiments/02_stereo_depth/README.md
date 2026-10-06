# Layer 2: depth estimation

This folder is layer 2 of the five-layer pipeline described in the [root README](../../README.md). It answers one question: **how far away is each pixel, in metres?**

A phone video is flat. Without depth, nothing in it can be measured. Depth is what turns pixels into points in space. The surface layer (layer 4) needs it to build a 3D model. The object layer (layer 5) needs it to give each object a position. The camera tracker (layer 3) can use it to fix the real-world scale of the camera path.

**Status:** planned. The test data is downloaded and checked; no depth method has been run in this folder yet. Other layers currently use depth recorded by a depth sensor in public benchmark data as a stand-in.

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
| [MobileStereoNet](https://arxiv.org/abs/2108.09770), [HITNet](https://arxiv.org/abs/2007.12140), [BANet](../../research/sources/04_banet.md) | On the phone | Learned stereo networks designed to be small and fast. | Check code and weight terms for each. |
| [Depth Anything V2](https://arxiv.org/abs/2406.09414) Small | On the phone | Small single-image depth model. Relative depth by default; metric versions exist. | The Small model is Apache-2.0; larger models are non-commercial. |

On-phone models run through a mobile runtime: [LiteRT](https://ai.google.dev/edge/litert) (formerly TensorFlow Lite), [ONNX Runtime Mobile](https://onnxruntime.ai/docs/tutorials/mobile/), [ExecuTorch](https://pytorch.org/executorch) or the precompiled models on [Qualcomm AI Hub](https://aihub.qualcomm.com/). Published speeds come from the authors' hardware and do not predict speed on these phones.

## Top 5 sources

| Source | What it is | Why it matters here |
|---|---|---|
| [ARCore Raw Depth](https://developers.google.com/ar/develop/java/depth/raw-depth) and the [project note](../../research/sources/06_arcore_raw_depth.md) | Google's documentation for phone depth with confidence | The cheapest route to depth on both test phones. It separates fresh depth from depth reused from earlier frames. |
| [FoundationStereo](https://arxiv.org/abs/2501.09898) | A 2025 stereo model trained on 1 million synthetic pairs | The strongest hosted option if the phones can capture two lenses at once. |
| [Depth Anything 3](https://arxiv.org/abs/2511.10647) | A 2025 model that predicts consistent depth across many views | The strongest hosted option for single-lens video. |
| [MobiDepth](../../research/sources/01_mobidepth.md) | Research on stereo depth from two phone cameras | Explains how lens differences and capture timing on real phones affect depth. |
| [Middlebury stereo, version 3](https://vision.middlebury.edu/stereo/submit3/) | A stereo benchmark with exact reference depth | The scoring data for this layer. |

More background: [HiMoDepth](../../research/sources/02_himodepth.md) on keeping image detail in phone stereo, [MobileStereoNet](../../research/sources/03_mobilestereonet.md), [BANet](../../research/sources/04_banet.md) and [HyperSight](../../research/sources/05_hypersight.md) on using camera motion for longer range.

## Where this layer stands

- The Middlebury version 3 quarter-resolution training data is downloaded and checked at `data/middlebury/dataset/MiddEval3/trainingQ/`. It has 15 indoor scenes with left and right images, calibration, reference disparity and masks. [Download records](../../data/README.md).
- No depth method, scene split or adapter code exists in this folder yet.
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

## Current delivery ownership, 6 October 2026

[Task54](../../task_list/open/54_implement_and_validate_real_metric_depth.md) owns the first implemented and independently scored real depth baseline. It chooses the usable phone or hosted route from the capture evidence; it does not wait indefinitely for stereo. [Task52](../../task_list/open/52_build_and_verify_a_usable_phone_recording.md) supplies phone observations and [Task53](../../task_list/open/53_collect_independent_scene_measurements_and_object_.md) supplies independent physical references. Code and runs remain absent until that work is executed.

## Walkthrough depth boundary

Step 2 is explicitly unavailable: no real metric-depth method or accuracy scorer has been implemented here. Task54 owns both. The root adapter accepts deterministic test providers only in labelled software controls. They do not constitute a depth method or measurement. See [the six-step runner](../../src/walkthrough/README.md).
