# SceneView: Android depth, room scanning and object merging

Reviewed 9 November 2026. **Recommendation: study its scanning and object code before adding another reconstruction system.** SceneView is an Apache-2.0 3D/AR SDK, but its current Android demo also implements much of our chain: ARCore capture, fused surfaces, room coverage, object detection and merging across views. It is a useful implementation reference and a candidate phone benchmark. Its accuracy on our Redmi recordings is unknown.

This is a source review, not an execution result. Main resolved to commit [`5ba0247805c4820629601153f84fda5e152c0a24`](https://github.com/sceneview/sceneview/commit/5ba0247805c4820629601153f84fda5e152c0a24), dated 7 November 2026. The links below pin that revision. No SDK, APK, model or checkout was installed. The [comparison with Open3Dmap](../products/sceneview_open3dmap_review_2026-11-09.md) ranks the follow-up work.

## What it provides

| Question | Evidence and implication |
|---|---|
| What is the main product? | Declarative 3D rendering and AR app components. Android uses Filament and ARCore. It does not replace ARCore's tracker. |
| Does it build a room? | Yes, source exists in the Android 3D Scan/Rerun demo. This capability extends beyond placing a downloaded model in AR. |
| Does it need phone LiDAR? | The Android scan uses ARCore raw depth where available. A separate ML depth module supplies metric depth from camera images and ARCore anchors on devices without the Depth API. Compatibility with our Redmi is untested. |
| Does it recognise objects? | The demo has a detector, 2D-to-3D lifting, multi-view merging, fitted boxes and a room inventory. This is closer to our object stage than a generic viewer. |
| Is everything a reusable SDK API? | No. ML depth lives in library modules. Much of room reconstruction and recognition lives under `samples/android-demo/.../internal/`; adopting it needs more work than adding a library dependency. |
| Can we use the code commercially? | The repository has an Apache-2.0 licence. ARCore and downloaded models have their own terms. Keep model provenance separate from the SDK licence. |

Sources: [project overview](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/README.md), [licence](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/LICENSE), [scan controller](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/RerunScan.kt).

## Learned depth and real-world scale

There are two separate paths to distinguish: the raw-depth scan demo and the library's ML depth facility. Finding both in this repository does not establish that the scan demo automatically uses ML depth when raw depth is absent.

`DepthAnythingV2Estimator` implements relative inverse depth using Depth Anything V2 Small and LiteRT, Google's on-device model runtime. CPU and GPU backends are exposed. `ModelSource` pins a 27,733,680-byte TFLite conversion by model revision and SHA-256. This is an Android deployment reference for a model family we already use, not evidence of a better depth shape. Our current model is **Metric Indoor Small**; this estimator's **relative inverse-depth** output has a different contract.

Sources: [estimator](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/arsceneview-depth-ml/src/main/java/io/github/sceneview/ar/depth/ml/DepthAnythingV2Estimator.kt), [model source and digest](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/arsceneview-depth-ml/src/main/java/io/github/sceneview/ar/depth/ml/ModelSource.kt).

`MlDepthSession` copies the image, metric anchors and source camera pose, then performs inference on a worker. It allows one inference in flight instead of building a queue. Its default target is 5 maps/s, with motion and thermal gates. The source pose travels with the result, which matters when inference finishes after the camera has moved. The source comment's 100–300 ms latency is an upstream claim, not a measured Redmi result. The session scales using ARCore **plane samples and tracked feature points**, rather than our preferred confident raw-depth pixels.

Source: [ML depth session](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/arsceneview/src/main/java/io/github/sceneview/ar/depth/MlDepthSession.kt).

The scale fitter solves `1/z = s*d + t`, where `d` is the network output and `z` is metric optical-axis depth. It uses consensus seeding, confidence-weighted robust fitting and a weak prior. Defaults require 12 inliers spanning a depth ratio of at least 1.5. It rejects a nonpositive scale, singular fit or insufficient support. The temporal smoother holds a failed fit for at most 5 ML maps, then returns no scale. This gives us concrete rejection rules to compare with our live fallback, which can carry the previous scale without this expiry.

Source: [fit and smoother](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/arsceneview/src/main/java/io/github/sceneview/ar/depth/DepthScaleFit.kt). Anchor projection and plane sampling are separate in [DepthAnchors](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/arsceneview/src/main/java/io/github/sceneview/ar/depth/DepthAnchors.kt).

**Project inference:** the anchor-span check and bounded hold are more useful leads than swapping our depth model for the same family. Our [live sizing](../../sitescan/scale/fit.py) uses a median depth ratio; the [room build](../../sitescan/pipelines/room.py) uses an 8 × 6 grid of local ratios. Compare these contracts explicitly. A two-parameter fit on relative inverse depth cannot be dropped into metric-depth code unchanged. Neither approach establishes accuracy outside the distances covered by its anchors.

## Freshness: a match to our doubled-surface problem

`DepthFreshness` distinguishes fresh, already fused, stale and ahead-of-frame timestamps. Its normal age limit is 100 ms and its allowed timestamp lead is 5 ms. It also handles a restarted session clock. **However, its `DepthWindow` relaxes the age/lead rejection after 500 ms without accepted depth, admitting distinct estimates so the scan can continue.** A 2 s starvation signal supports feedback.

Source: [freshness judgement and fallback](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/DepthFreshness.kt).

`DepthIntake` records why depth was skipped, including a busy worker, absent depth, repeated depth and missing confidence. These counts are a useful pattern for our capture diagnostics. Source: [depth intake](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/DepthIntake.kt).

**Project inference:** copy the diagnostic ideas into a future design, not the relaxed acceptance policy by default. Task116 already traced a doubled cushion to depth 4.4 s older than its image; our room build therefore rejects depth older than 0.1 s. Keeping the scanner moving and preserving measured geometry are different acceptance criteria. The upstream fallback needs the same stale-depth replay before adoption.

## Fusion and bounded memory

A **surfel** is a small surface sample with position, colour and normal. `DenseFusion` merges these into spatial cells, averages repeat observations and counts distinct depth-frame contributions. Saved clouds can discard samples supported by too few frames. Under memory pressure it coarsens chunks rather than discarding all later parts of a walk. This is useful for a phone map that needs to cover more than the first room. Coarsening changes detail; it does not prove centimetre accuracy.

Source: [surfel fusion](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/DenseFusion.kt).

A separate Kotlin **TSDF**, a grid that averages signed distances around a surface, produces the triangle mesh. `RerunTsdf` uses sparse 8³ blocks, a default 2.5 cm voxel, a truncation band of 3 voxels and a 48 MiB budget. When that budget fills, it drops new blocks and exposes counters. This differs from the surfel map's coarsening policy. The scan controller feeds live surfel and model workers without queuing every arriving depth map.

Sources: [TSDF](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/RerunTsdf.kt), [controller](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/RerunScan.kt).

The finishing code also has cleanup, simplification and photo-texturing stages. An optional reconstruction route uses Screened Poisson, which fills a surface from oriented points. Treat filled or flattened geometry separately from observed geometry when scoring dimensions. Sources: [model finishing](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/model/CleanModel.kt), [reconstruction choice](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/ReconstructionChoice.kt).

**Project inference:** this is evidence that a bounded Android implementation of our main stages exists. It is not evidence that we should replace Open3D or our anchor-corrected fragments. This review did not establish an equivalent to our pose-revision and fragment-correction contract.

## Objects: useful overlap with the counting stage

The reviewed detector model is **YOLOX-Tiny**, not our YOLO26x. Its model record identifies an Apache-2.0 source and a 10,178,328-byte converted TFLite asset with a digest. The room label set includes chairs, tables and other furniture; doors and windows can come from wall openings. It does not include cones or barriers in that mapping.

Sources: [detector model record](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/semantic/SceneModel.kt), [labels](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/semantic/SceneLabel.kt).

`SceneRecognizer` selects up to 24 posed keyframes across the recording and runs detection, lifting and fusion. This is a bounded review pass over the room, not evidence of a persistent live inventory. `SceneLift` casts up to 5 rays through a detection, grows the hit surface region and projects its box back into the image. The projected box must overlap the original detection: minimum intersection-over-union is 0.25, with an early acceptance at 0.6. This is a practical check against lifting a chair detection onto the wall behind it.

Sources: [recognizer](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/semantic/SceneRecognizer.kt), [lifting](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/semantic/SceneLift.kt).

`SceneFusion` merges observations if they share at least 30% of the smaller surfel set or have floor-footprint intersection-over-union of at least 0.4. It votes on the class and supporting surfels, refits the box and suppresses overlapping results at 0.5 footprint overlap. The grouping loop does not require equal class labels before merging; labels are voted afterward.

Source: [multi-view object fusion](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/semantic/SceneFusion.kt).

**Project inference:** compare this with our 0.35 m centre-distance association. Shared surface membership can distinguish two nearby objects better than centres alone when the geometry is stable. But footprint-only merging and suppression can merge distinct overlapping objects, while map drift can split one object. There is no demonstrated solution here for moved objects, cross-session identity or our own revisit count. The [design status](../../DESIGN.md) reports 14–15 chair detections accumulated in replays, making this an actionable comparison after stable geometry and a labelled inventory exist.

## Capture guidance and integration cost

`ScanCoverage` maintains a 25 cm ground grid with a minimum of 3 points per covered cell. `RoomScan` includes prompts for lost tracking, absent depth, slow movement and room coverage. Coverage of that grid is not a measure of how much of every object has been seen. These are still useful references for the feedback our phone capture lacks.

Sources: [coverage](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/ScanCoverage.kt), [scan guidance and upright photos](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/samples/android-demo/src/main/java/io/github/sceneview/demo/demos/internal/RoomScan.kt).

The reviewed README advertises Android SDK version 4.67.0, minimum API 24, compile SDK 37, AGP 9.4.0+, Kotlin 2.4 and Java/JVM 21. Those are upstream build requirements, not our installed toolchain. Before a demo build, select a compatible pinned release and check the actual build files. Its Compose integration also differs from simply embedding our current capture activity. Source: [quickstart](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/docs/docs/quickstart.md).

## Suggested checks, not run

1. After the planned refactor, score scale-fit rejection and bounded scale hold on the 14 and 15 October recordings. Separate well-supported near depth from unsupported far depth. Keep the existing grid fit as the control.
2. Compare current centre-distance association with surface-overlap association on identical detections and the same fused cloud. Label the actual chairs; report both duplicate counts and merges of distinct objects.
3. Check SceneView's Android demo on the Redmi as a bounded phone benchmark. Record depth availability, export contents, model accuracy, update rate, memory and heat. A Pixel demo video cannot supply those results.
4. If an Android depth port is needed, test the pinned LiteRT Small conversion and source-pose handling. Measure accuracy and sustained cost; a target rate in source is not achieved throughput.

No new experiments or architecture changes are approved by this note. The owner's 8 November order remains: refactor first; preserve ARCore as the metric reference; optimise dimensional accuracy rather than splat appearance.
