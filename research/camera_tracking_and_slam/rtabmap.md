# RTAB-Map: a mapping baseline for the phone walkthrough

Assessed 10 November 2026 from official source, documentation and the authors' paper. **Recommendation: compare it with the current pipeline using the same recordings before deciding whether to adopt its mapping backend.** No RTAB-Map app, build or benchmark was run for this digest.

RTAB-Map supplies camera tracking options, recognition of revisited places, corrected camera graphs, coloured maps, reconstruction exports and recording/replay tools. Those overlap much of this project. Its documented outputs do not establish independently accurate worksite measurements or a persistent inventory of distinct cones and barriers. The proposed surface-property work is considered separately in [surface grouping](../surface_denoising/surface_grouping.md).

## Version and publication

The latest GitHub release inspected is **0.24.2**, at commit [`8cd2f81a735722402d1e220147c4e83a1a746eaf`](https://github.com/introlab/rtabmap/commit/8cd2f81a735722402d1e220147c4e83a1a746eaf). The [release page](https://github.com/introlab/rtabmap/releases/tag/0.24.2) displays 25 October; its extracted date omits the year. The [tagged build file](https://github.com/introlab/rtabmap/blob/0.24.2/CMakeLists.txt) confirms version 0.24.2. Rolling API pages inspected identify themselves as 0.24.4 or 0.24.5; their newer options must not be silently attributed to the release.

The earlier project note pinned **0.22.1**, commit `df6300e0ba3e90058f90b09c4d646279366d3516`. That remains a historical reference. No local checkout was upgraded.

Mathieu Labbé and François Michaud's main system paper is **RTAB-Map as an Open-Source Lidar and Visual SLAM Library for Large-Scale and Long-Term Online Operation**, *Journal of Field Robotics* 36(2), 416–446, **2019**. Its [author deposit](https://arxiv.org/abs/2403.06341) was submitted in 2024; that upload date does not make the system paper a 2024 contribution. [Journal DOI](https://doi.org/10.1002/rob.21831).

## What it is

SLAM means estimating sensor motion while building a map. RTAB-Map is a C++ library and standalone application, with a separate ROS integration. Its name expands to Real-Time Appearance-Based Mapping. It supports RGB-D cameras, calibrated stereo and lidar. Recognition of revisited places, called *loop closure*, adds constraints that can correct accumulated drift. It also supports localization against an existing map and multiple recording sessions. [Official overview](https://introlab.github.io/rtabmap/).

For this project, it can be an alternative mapper or a backend supplied with ARCore motion. Those are different experiments. A robot demonstration does not establish performance on first-person phone video.

## Architecture and memory

Its map is a graph: nodes contain observations and links constrain their relative poses. Each new observation updates memory and produces a revisit hypothesis. In RGB-D mode, a proposed link needs both a valid geometric registration and an acceptable graph-consistency result. Accepted links update the optimized camera poses. A visual resemblance alone does not establish a loop closure.

Recent observations enter short-term memory; selected observations remain in working memory; others can move to long-term storage. Matching a remembered region can retrieve its neighbours. Time and working-memory thresholds control transfer to storage, and both can be disabled. This bounds active work rather than promising an unconditional processing deadline. The mapping and localization modes treat the stored map differently. [Tagged pipeline definition](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/include/rtabmap/core/Rtabmap.h).

**Project implication:** retaining observations and graph relationships is useful for revisits, corrections and diagnosis. Measure delay and memory during those events, not only average throughput on a short walk.

## Camera tracking and external odometry

RTAB-Map exposes tracking choices, but its mapping API also accepts an externally estimated pose:

```text
Rtabmap::process(SensorData, odomPose, odomCovariance, ...)
```

The pose is required for RGB-D SLAM mode; an appearance-only call does not produce the equivalent metric mapping result. The API can return optimized poses and map corrections. [Rtabmap API](https://introlab.github.io/rtabmap/api/latest/classrtabmap_1_1Rtabmap.html).

`SensorData` provides calibrated RGB-D constructors, including a depth-confidence variant, and representations for other sensor inputs. This establishes a route for constructing observations from our recording. It does not mean our session format is directly readable or that every consumer uses confidence identically. [Tagged sensor container](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/include/rtabmap/core/SensorData.h).

**Proposed use:** retain our capture app, choose a recorded frame subset, and feed its RGB, registered depth and ARCore pose to the backend. Change the tracking algorithm in a separate comparison.

## Android ARCore support

The native Android driver reads ARCore poses, camera intrinsics, colour images and tracked points. It checks automatic-depth support and acquires a depth image. When its depth-from-motion setting is enabled, that depth can enter the observation; otherwise the path can use sparse tracked points without dense depth. This is implemented source. The inspected native path does not demonstrate consumption of the raw-depth confidence stream our app records. [Tagged ARCore driver](https://github.com/introlab/rtabmap/blob/0.24.2/app/android/jni/CameraARCore.cpp).

The mobile layer rotates images and depth with their camera model. It handles pose interpolation, origin offsets and upstream relocalization behaviour. Its odometry covariance includes heuristic values. These mechanisms deserve inspection before adapting our recordings; their existence does not establish statistically calibrated uncertainty. [Mobile camera source](https://github.com/introlab/rtabmap/blob/master/app/android/jni/CameraMobile.cpp).

The official installation guide includes an ARCore APK build route using Docker. We have not reproduced that build or checked its installation on the Redmi. Device support, usable depth and sustained mapping speed remain runtime questions. [APK instructions](https://github.com/introlab/rtabmap/wiki/Installation#rtab-map-arcore-apk).

## Maps, meshes and measurement

The tool suite exports assembled point clouds, meshes, textured meshes, poses, images and 2D occupancy grids. Database inspection, reprocessing, graph refinement, global bundle adjustment and recovery are available. `rtabmap-console` is an appearance-only loop detector; the RGB-D dataset tools and SLAM API are different entry points. [Official tool reference](https://introlab.github.io/rtabmap/api/latest/tools.html).

An occupancy grid labels space as occupied, free or unknown. A coloured point cloud attaches appearance to points. A textured mesh attaches photographs to a surface. None automatically supplies a validated site boundary, floor area or distinct-object inventory.

**Project implication:** a visually cleaner export is worth inspecting, but acceptance must measure dimensions and completeness. Photo texture cannot prove correct depth. A closed-looking mesh may bridge an unobserved gap; it should not become evidence that the gap was measured. Our independent dimensions and observed-coverage definition must remain outside the mapper's own success signals.

## Geometry, colour, texture and learned features

RTAB-Map includes geometry-based segmentation settings: surface normals for ground/obstacle separation, angle and height thresholds, cluster radius, minimum cluster size and voxel filtering. Occupancy generation also offers ray tracing. These are precedents for grouping and spatial evidence, but they are not a demonstrated general-purpose persistent surface-identity system. [Tagged parameters](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/include/rtabmap/core/Parameters.h).

Rolling master supports learned keypoint and matching routes, including SuperPoint and Python hooks, with newer ONNX detector, matcher and global-descriptor options. The inspected 0.24.2 parameter file lacks the ONNX descriptor/matcher options seen in master. Those features support registration or place recognition; their presence does not establish embedding-based clustering of every mapped surface. [Rolling parameters](https://github.com/introlab/rtabmap/blob/master/corelib/include/rtabmap/core/Parameters.h).

**Research distinction:** “these photographs show the same place”, “these patches belong to the same wall” and “these two barriers are one physical object” are separate decisions. Colour or semantic similarity can help, but can also merge distinct identical objects. See [surface grouping](../surface_denoising/surface_grouping.md) for the prior art and proposed tests.

## Published quantitative evidence

The 2019 paper evaluates **version 0.16.3**. Its native RGB-D frame-to-map configuration reports trajectory error of **2.9 cm on TUM fr1/desk** and **0.5 cm on fr2/xyz**, with **70 ms average odometry time**. The desktop uses an i7-3770; the relevant offline experiments use one core. Visual trajectories are scaled against ground truth to reduce depth/calibration scale effects. Offline processing allows frames to take longer than their capture interval. [Author paper, section 4 and Table 6](https://arxiv.org/html/2403.06341v1).

These numbers establish neither current-version speed nor phone dimensions in metres. They are trajectory scores, not dense-surface or inventory scores. Do not compare them directly with our results without matching frame selection, alignment, inputs and failure handling. The older configurations are informative controls, not a current SOTA leaderboard.

## Fit to the current project

Our current chain uses ARCore poses, learned depth fitted to metric targets, anchored Open3D fusion, and mapping. The room build additionally uses upright prediction, grid scale and cleanup. Object counting remains experimental. Its documented live and offline results are different operating conditions. [Current design](../../DESIGN.md#2-where-the-project-is), [shared stages](../../sitescan/README.md).

| Need | RTAB-Map relevance | What remains unproved here |
|---|---|---|
| Correct revisits | Explicit observation graph and loop closures | Better real-site dimensions than ARCore alone |
| Reuse recordings | Database replay, inspection and export | Adapter preserving timing and coordinate conventions |
| Produce a surface | Coloured map and mesh outputs | Completeness, wall thickness and dimensional error |
| Run online | Memory and input-rate controls | Sustained delay and memory on the selected hardware |
| Count distinct objects | Potential source of corrected geometry | Association and inventory accuracy |
| Join surfaces by properties | Geometry filters and visual-feature machinery | A persistent, measured patch/entity layer |

These are assessment judgments, not measured RTAB-Map results on our data. Its role could be to supply corrected observations to our measurement and grouping stages. Adoption should be justified by that improvement.

## Integration risks before a fair test

The following are proposed checks derived from the API and our recording design:

1. **Coordinates and calibration.** Verify camera-versus-device poses, image orientation, depth registration, units and camera extrinsics with a known projection. A plausible-looking map can hide an axis or scale mistake.
2. **Depth timing.** Preserve RGB and depth capture times and our freshness rule. Repeated old phone depth must not be relabelled with the newest RGB pose. Test the same eligible frames in both systems.
3. **Origin resets.** Split or explicitly transform discontinuous ARCore coordinate systems. A new origin is not physical motion and should not create a sequential odometry constraint.
4. **ARCore pose revisions.** Distinguish smooth relative motion from a later relocalization jump. Inspect the mobile driver's treatment before feeding a historical corrected trace into sequential links.
5. **Double correction.** Choose how graph-corrected poses place surfaces. Applying both RTAB-Map correction and our independent anchor correction to the same geometry could move it twice.
6. **Covariance and correlation.** Record the chosen covariance assumptions. ARCore poses, tracked points and depth are related estimates; treating them as independent ground truth would overstate confidence.
7. **Depth bias.** Hold the depth source fixed while testing the backend. Loop closure cannot automatically fix a far wall placed at inconsistent depths in successive images.

Our existing freshness and anchored-fusion behaviour is documented in [scale](../../sitescan/scale/README.md) and [fusion](../../sitescan/fusion/README.md). Those are compatibility constraints, not evidence that the adapter already exists.

## Licence and deployment

The core uses **BSD-3-Clause**, permitting redistribution and modification under its notice, disclaimer and endorsement conditions. That supports considering it for a product. Optional dependencies and model weights retain their own terms. [Core licence](https://github.com/introlab/rtabmap/blob/0.24.2/LICENSE).

The official site warns about nonfree OpenCV features, and the inspected release lists nonfree modules in desktop binaries. A downloadable installer is therefore a different review surface from a minimal source build. Check the selected components before distribution. [Official licence guidance](https://introlab.github.io/rtabmap/#license), [binary contents](https://github.com/introlab/rtabmap/releases/tag/0.24.2).

The standalone C++/CMake route avoids requiring ROS. Its dependency set includes computer-vision, point-cloud and storage libraries; GUI and selected driver/optimizer components add build choices. A desktop integration is a different workload from embedding it on Android. The `PythonInterface` file owns an embedded Python interpreter for Python-backed functionality; it does not establish a complete Python mapping wrapper. [Build configuration](https://github.com/introlab/rtabmap/blob/0.24.2/CMakeLists.txt), [Python interface](https://github.com/introlab/rtabmap/blob/master/corelib/include/rtabmap/core/PythonInterface.h).

## Proposed controlled comparison

This is an experiment proposal, not an implementation commitment or a result:

| Run | Fixed inputs | Changed component |
|---|---|---|
| A | Selected recording, frames and current depth | Existing pipeline control |
| B | Same RGB, depth, calibration and ARCore motion | RTAB-Map graph/backend |
| C | Same RGB, calibration and motion as B | Raw ARCore depth instead of fitted learned depth |
| D | Same RGB-D observations as B | RTAB-Map's own RGB-D odometry |

Use a measured return-to-start walk with repeated-looking surfaces, a narrow passage and a few distinct small objects. Add a separate interrupted/reset capture. Freeze settings on development recordings and score untouched recordings against tape/laser distances, an independently defined footprint and a labelled inventory.

Report error, missing coverage, false closures, repeated surfaces, object duplicates/merges, latency and memory together. Keep unscaled metric errors alongside any trajectory-aligned research score. Record whether corrections arrive late enough to invalidate a previously displayed measurement.

Adoption would be supported if B improves independent geometry while preserving acceptable update delay. If C is equally useful, the learned-depth stage needs a clearer benefit. If D improves only tracking, preserve that distinction. Property-based surface joining should then be tested on a fixed geometry baseline, including whether it preserves small real objects that size filtering currently risks removing.
