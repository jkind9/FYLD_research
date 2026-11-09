# SpAItial Echo-3: iPhone video to a metric splat scene, processed in the cloud (commercial)

**Take-away:** Echo-3 turns a few minutes of iPhone video into a Gaussian splat scene (a 3D scene made of many small soft coloured blobs that looks like a photograph from any angle). The vendor says the scene is at real-world scale and that the model fills in areas the capture missed. It runs on iPhones without a LiDAR laser sensor. That makes it the closest product found so far to this project's case of a phone with no laser sensor. No method, accuracy figure or benchmark is published. There is no open or free version of the model, and the terms of service forbid reverse engineering it. The legal routes are the free first month, used as a closed reference, and rebuilding the same chain from open parts (listed below). The project has no iPhone, and on 8 November the owner deferred splat scenes because the measure that matters is the dimensional accuracy of objects YOLO places in 3D. So this note is a reference, with no test planned.

Checked on 8 November 2026 from the vendor's product page, release post, capture guide, App Store listing, API documentation and terms, plus two news reports. Nothing was installed or tested. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Maker | SpAItial Ltd, Munich and London. Co-founders: Matthias Niessner (CEO; TU Munich professor; co-founder of Synthesia), Ricardo Martin-Brualla (formerly Google, reported to have worked on Project Starline and 3D shopping), David Novotny (formerly Meta, reported to have led its text-to-3D asset work), Luke Rogers (business; formerly McKinsey and Cazoo). $13M seed round, May 2025, reported led by Earlybird with Speedinvest (one aggregator source). An April 2026 interview said it plans to raise more in 2026 |
| Released | 27 October 2026, with a new SpAItial iPhone app (version 1.1.0 added export). Earlier: Echo (December 2025) makes 3D worlds from text or one image. Echo-2 (28 April 2026) adds splitting a world into objects for editing; the vendor claims it beats World Labs' Marble 1.1, HY-World 2.0 and Lyra 2.0 on the WorldScore benchmark. Developer API from May 2026 |
| Input | A slow walk round the space with an iPhone on iOS 18 or later. "Capture remains available on supported non-LiDAR iPhones"; the supported models are not listed. Android is "coming soon" |
| LiDAR | Optional. A LiDAR iPhone adds "live coverage guidance and dense point-cloud preview" |
| Output | A splat scene "scaled to real-world dimensions". View it in the app, take measurements, share a link that opens in a browser. Exports reported as SPZ, SOG, meshes, normals and depth; which plan gets which is not stated |
| Where it runs | Capture on the phone. Scans upload and are processed in the cloud ("Processing continues after you close the app"). Processing time not stated; the API docs say Echo-2 jobs take 6–8 minutes |
| Live | No. Only the coverage guide during capture is live, and only on LiDAR iPhones |
| Works from an Android phone with no laser sensor | Not yet. Works on iPhones without LiDAR |
| Measures in metres | Claimed: "Reconstructions are metric, so dimensions and distances match the real space." No error figure |
| Counts each object once | No. Echo-2 splits a generated world into objects for editing; Echo-3 does not mention this |
| Methods named | None. The vendor describes "treating reconstruction as a form of generation" |
| Cost | See [free ways to try it](#free-ways-to-try-it) |

## How it probably works

The vendor names no method. The steps below are inferences from its own wording and from the founders' published work. None is confirmed.

1. **Capture with phone poses.** The capture guide says "Move the camera gently from side to side until you see 3D points appearing on the screen." That is how ARKit, Apple's phone tracking, starts. ARKit combines the camera with the motion sensors, so its camera poses are in metres even without LiDAR. That is the likely source of the metric scale. ARCore does the same on this project's Redmi.
2. **A learned model that predicts the scene in one pass.** David Novotny is an author of [VGGT](../../../feed_forward_3d/vggt.md), a network that outputs 3D points and camera poses for many images in one pass. Open models of this kind that output splats are listed under [step 2](#2-splats-predicted-in-one-pass) below.
3. **Generated fill for missed areas.** Ricardo Martin-Brualla is an author of [CAT3D](https://arxiv.org/abs/2405.10314) (Google, NeurIPS 2024). CAT3D uses a diffusion model (a network that makes images by removing noise step by step) to generate new views, then builds 3D from them. The vendor's line is that Echo-3 "fills in the missing regions so they match the surroundings".
4. **Export.** SPZ is Niantic's open splat format. SOG is PlayCanvas's compressed format. The listed exports of normals and depth match what multi-output models such as WorldMirror predict.

Whether the app marks which areas were filled in rather than seen is not stated. For a measured site record, that is the key question.

## Free ways to try it

| Route | What is free | Limits |
|---|---|---|
| SpAItial iPhone app | Free download. "a one-month introductory free trial for eligible new subscribers" | Needs an iPhone on iOS 18 or later. Standard (£49.99) gives 7,500 credits a month, "up to 25 scan minutes", "for non-commercial work". Pro (£99.99) gives 15,000 credits, 50 scan minutes and commercial rights. The listing also shows £499.99 and £999.99 tiers without saying whether those are yearly. Credit packs: 1,600 for £14.99, 3,200 for £29.99, 8,000 for £79.99. A world costs 300 credits per scan minute, minimum 900 (3 minutes). The privacy section lists "Photos or Videos" and "Environment Scanning" as data linked to the user |
| Developer API | 800 credits a month on the free plan; 1 credit = $0.01 | Echo-2 (160 credits) and Echo HQ (800) only. These take text, an image or a 360° panorama, not a phone scan. "Echo-3 API access require[s] Enterprise". Jobs go to `POST /v1/worlds` at `https://api.spaitial.ai` and return a request id; the result gives signed links to the splat (SPZ by default, or SOG for about 25 s more), a panorama and a thumbnail |
| Public gallery and share links | Viewing in a browser | Viewing only |

No open weights, paper, code, model card or technical report exists for any Echo model. The "free version" is the trial.

## What the terms allow

From the [terms of service](https://spaitial.ai/terms), updated 27 October 2026. This is a reading of the text, not legal advice.

- **Reverse engineering is forbidden.** Clause 9.2 bars users from doing anything to "disassemble, decompile, translate, reverse engineer, crawl or scrape" the services. It also bars access "by any means other than by SpAItial's currently available interface". So: no unpacking the app and no pulling files out of the share viewer.
- **Outputs cannot be used to rebuild the model.** Clause 6.7 bars using generated worlds "to extract or reverse engineer the Underlying Model" or "to train, develop, or assist in developing an artificial intelligence". Using Echo-3 scenes as targets for this project's own models would fall under that. Whether a side-by-side accuracy comparison counts as "assist in developing" is not clear. That is for the owner to decide.
- **Benchmarking is not mentioned.** No clause forbids comparing the service with others.
- **Commercial use needs Pro.** On Free and Standard plans, outputs are for "personal, non-commercial purposes, non-commercial research". A trial does not grant permanent commercial rights.
- **Uploaded scans may be used to train SpAItial's model.** The user owns the generated world (6.1). But the user grants SpAItial "a worldwide, irrevocable, perpetual, royalty-free, sublicensable licence" to the content (6.9), and SpAItial may use it to train "the Underlying Model or any successor or derivative model" (7.1). Scans of client sites would therefore leave FYLD's control.

## The same chain from open parts

Each step of Echo-3 has open counterparts. This is the legal way to "reverse engineer" it: rebuild it from public methods and compare outputs. Capture, splat training and web viewing are already covered in [Lumina and the open-source parts](../../../gaussian_splatting/lumina_open_source_parts.md). The new parts are the splat models that work in one pass and the generated fill.

### 1. Capture with metric phone poses

This project's capture app already records ARCore poses in metres, intrinsics, raw depth and frames on the Redmi. What it lacks compared with Echo-3 and Lumina is the coverage guide during capture.

### 2. Splats predicted in one pass

These models take a set of frames and output a splat scene in seconds, without per-scene training. Details and licences are in [feed-forward splat models](../../../feed_forward_3d/feed_forward_splats.md).

| Model | Licence | Takes phone poses? | Fit for this project |
|---|---|---|---|
| [YoNoSplat](https://github.com/cvg/YoNoSplat) (ETH Zurich, ICLR 2026) | MIT code and weights | Yes, optional poses and intrinsics | Best licence and input fit. 100 views at 280 × 518 in 2.69 s on an NVIDIA GH200. Trained at 224 × 224 |
| [AnySplat](https://github.com/OpenRobotLab/AnySplat) (2025) | MIT code and weights | No; works out its own poses | Scale must be fitted to ARCore poses afterwards |
| [WorldMirror 1 and 2](https://github.com/Tencent-Hunyuan/HY-World-2.0) (Tencent, 2025–2026) | Tencent community licence that "DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA" | Yes: poses, intrinsics and depth | Closest match to Echo-3's outputs (splats, depth, normals, points, cameras). Its licence does not cover use in the UK |
| [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3), Giant models | CC BY-NC 4.0 | Yes | Research only. The Apache-2.0 Small and Base models have no splat output |

None of these outputs metres by itself. Scale comes from passing in the ARCore poses or fitting the predicted poses to them.

### 3. Generated fill for missed areas

| Model | Licence | Note |
|---|---|---|
| [Difix3D+](https://github.com/nv-tlabs/Difix3D) (NVIDIA, CVPR 2025) | NVIDIA licence: "only may be used or intended for use non-commercially", meaning "for research or evaluation purposes only" | One-step diffusion that cleans renders of a splat scene in thinly captured areas, then trains the scene again on the cleaned views |
| [ArtiFixer and World-from-Motion](../../../gaussian_splatting/generative_repair.md) | Non-commercial weights (ArtiFixer); Apache-2.0 (World-from-Motion) | Video diffusion repair; 80 GB-class GPU |
| HY-World 2.0 world expansion (WorldStereo 2.0) | Tencent licence, as above | Generates new views with memory of earlier ones, then rebuilds with WorldMirror 2.0 |

Generated areas are invented. They can help a scene look complete, but they carry no measurement.

### 4. Viewing, sharing and measuring

[Spark](https://github.com/sparkjsdev/spark) (World Labs, MIT) and [SuperSplat](https://github.com/playcanvas/supersplat) (PlayCanvas, MIT) show splats in a browser. SPZ and SOG files come from [splat-transform](https://github.com/playcanvas/splat-transform) (MIT). Measuring is better done on this project's fused surface, which is scored against a reference, than on splat centres.

## Evidence and limits

- Every claim is the vendor's. "State of the art" comes with no benchmark figure.
- The one comparison is a video of the same scene captured with Polycam, KIRI Engine and Niantic Scaniverse along a similar path. The vendor says "SpAItial produces sharp surfaces with no visible floaters". No numbers are given.
- Generated areas are invented. Where the capture missed part of an object, a filled-in surface gives it a shape and size nobody measured.

## Compared with this repository

| This repository's layer | Does Echo-3 cover it? |
|---|---|
| 1. Capture | Yes, on any supported iPhone; LiDAR optional. Coverage guide on LiDAR phones only |
| 2–3. Depth and camera position | Not stated; probably ARKit poses |
| 4. 3D model | Yes: splat scene with generated fill; metric claimed, accuracy unknown |
| 5. Objects | No |
| Object dimensions, the project's measure | No objects are found. Distances are measured by hand in the viewer, and generated fill can change how big an object looks |
| Live updates | No; cloud processing after capture |

The nearest commercial rival is World Labs' Marble, which also takes video input on paid plans. One secondary source reports a beta Marble API that turns posed views and depth into a splat scene; that was not confirmed. Marble's web viewer uses World Labs' open renderer, Spark. Neither product is open.

## How to test it here

Not planned. On 8 November 2026 the owner confirmed there is no iPhone, so Echo-3 cannot be tried. The owner also deferred splat scenes: the project's measure is the dimensional accuracy of objects that YOLO detects and places in 3D, and a splat scene with generated fill does not help with that.

If that changes:

1. **Splats from the Redmi:** run YoNoSplat with the Redmi ARCore poses on 16–32 frames. It needs a GPU, so it would go to the RTX 4060 laptop as a laptop experiment.
2. **An iPhone becomes available (iOS 18 or later, LiDAR not needed):** if the owner accepts the terms above, use the free month on the room of the 15 October Redmi walk. Compare tape-measured object sizes in the Echo-3 viewer with the same objects on the Redmi surface, and note which areas Echo-3 filled in.
3. **In either case,** do not unpack the app or pull files from share links (clause 9.2).

## Sources

- [Echo-3 product page](https://spaitial.ai/echo-3) · [release post](https://spaitial.ai/blog/echo-3-release) · [capture guide](https://spaitial.ai/blog/capture-guide) · [terms](https://spaitial.ai/terms)
- [SpAItial on the App Store](https://apps.apple.com/gb/app/spaitial/id6803571420)
- [API getting started](https://docs.spaitial.ai/api/getting-started) · [documentation](https://docs.spaitial.ai/overview/welcome)
- [Radiance Fields: Echo-3](https://radiancefields.com/spaitial-echo-3-turns-iphone-scans-into-3d-worlds) · [Runtime Wire: Echo-3](https://runtimewire.com/article/spaitial-echo-3-iphone-3d-world-capture) · [Radiance Fields: Echo-2](https://radiancefields.com/spaitial-ai-announces-new-model-echo-2)
- [Tech.eu: seed round](https://tech.eu/2025/05/27/spaitial-emerges-from-stealth-with-13m-seed-for-ai-native-3d-applications/) · [TechCrunch: co-founders](https://techcrunch.com/?p=3011494) · [Tech.eu: April 2026 interview](https://tech.eu/2026/04/16/we-are-where-chatgpt-was-five-years-ago-says-european-3d-ai-foundation-model-startup-boss/) · [Seedtable: seed round](https://seedtable.com/companies/spaitial/funding-rounds/seed-2025-05)
- [CAT3D, arXiv 2405.10314](https://arxiv.org/abs/2405.10314) · [VGGT paper](../../../feed_forward_3d/papers/vggt_2503.11651.pdf) (local copy)
- [World Labs Marble](https://www.worldlabs.ai/blog/marble-world-model)
