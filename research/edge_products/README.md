# Mobile stereo products for worksite mapping and object counting

Reviewed 2 October 2026. The field brief asks for a first-person walkthrough that identifies a worksite and estimates its size, plus a count of distinct objects even when they leave and re-enter view. A shared, metre-scaled 3D map could support both. That is a proposed application design, not a capability demonstrated by this project.

Commercial stereo cameras and local edge computers can reconstruct a scene live. The clearest numerical evidence found is NVIDIA's live Perceptor pipeline: 2.63 mesh updates per second on Nova Carter. Stereolabs offers the most direct commercial camera-and-computer kit to evaluate. These are mobile rigs. This review did not establish a turnkey ordinary Android phone product that uses its two rear cameras for live dense reconstruction at at least one map update per second.

## What counts as reconstruction

A qualifying system combines depth measurements from successive camera positions into one accumulated 3D scene. A depth image, a point cloud from one frame, or a sparse camera-tracking map is not enough. An accumulated point cloud can qualify even when it has no triangle mesh.

Camera capture, depth calculation, camera tracking, map integration, map publication and display each have a different rate. The desired one update per second applies to fresh accumulated geometry. Capture and tracking should remain faster during a moving walkthrough. Resolution in centimetres describes map detail; it does not establish measurement accuracy.

## Product shortlist

| Product or development stack | Local hardware and actual output | Evidence for at least one map update per second | Assessment |
| --- | --- | --- | --- |
| Stereolabs ZED 2i + ZED Box Mini; alternatively a ZED X rig + compatible ZED Box | Commercial stereo camera plus Jetson computer. ZED SDK accumulates a fused point cloud or mesh using depth and camera poses. | API demonstrates asynchronous continuous map retrieval. Its example requests updates every half-second; this is a request schedule, not a measured sustained result on a named Box configuration. | First commercial kit to evaluate. Genuine mapping is documented; the complete workload rate still needs measurement. |
| NVIDIA Isaac Perceptor / Isaac ROS nvblox with Hawk stereo cameras | Nova Carter is a mobile robot with Jetson AGX Orin. Camera-based pipeline produces an accumulated mesh and a distance map for navigation. | Release 3.2 live benchmark: three Hawk cameras, 1200p input, mesh 2.63 FPS, distance map 9.45 FPS, visual odometry 30.0 FPS. | Strongest numerical proof found that the requested rate is attainable on an edge platform. A robotics stack to integrate, rather than a finished walkthrough application. |
| Spectacular AI SDK + Luxonis OAK-D with IMU + local host | Stereo depth/features accelerated on camera; SDK mapping runs on connected host. Live Mapping API produces an environment point cloud. | Default depth input 30 FPS; viewer example targets 30 FPS. Neither establishes complete-map throughput on a named edge host. | Credible alternative. Confirm host support, power budget and commercial SDK terms. |
| Luxonis DepthAI v3 Basalt + RTAB-Map + OAK stereo/IMU | Stereo on camera; camera tracking and mapping are host nodes. Example produces live 3D occupancy and ground/obstacle point clouds. | Example configures 640 × 400 stereo at 60 FPS and IMU at 200 Hz. These are inputs, not a measured map rate. | Useful open development route. Host nodes are early preview; current DepthAI v3 does not support Android. |

Stereolabs sells a [Single Stereo USB Kit](https://www.stereolabs.com/products/zed-box) containing ZED 2i, ZED Box Mini and cable. Power supply, battery arrangement, mounting and operator ergonomics still need assessment for a walkthrough. [Spatial mapping documentation](https://docs.stereolabs.com/docs/development/zed-sdk/modules/spatial-mapping) establishes accumulated geometry; the [mapping API](https://www.stereolabs.com/docs/development/zed-sdk/modules/spatial-mapping/using-the-api) describes continuous extraction and the cost of finer resolution.

NVIDIA's numbers are a **vendor benchmark from release 3.2**, not a result from our project or a guarantee for a smaller handheld rig. The [performance table](https://nvidia-isaac-ros.github.io/v/release-3.2/performance/index.html) labels this as a live Nova Carter graph. [Nova Carter hardware](https://nvidia-isaac-ros.github.io/v/release-3.1/robots/nova_carter/index.html) identifies Jetson AGX Orin. The [camera-based pipeline description](https://nvidia-isaac-ros.github.io/v/release-3.1/reference_workflows/isaac_perceptor/technical_details.html) traces stereo images through depth and reconstruction. Do not transfer the 2.63 FPS figure to Orin NX, one camera, a different map size or added detection without testing.

Spectacular AI's [Mapping API](https://spectacularai.github.io/docs/sdk/mapping.html), [OAK wrapper](https://spectacularai.github.io/docs/sdk/wrappers/oak.html) and [live example](https://github.com/SpectacularAI/sdk-examples/blob/main/python/oak/mapping_visu.py) establish the development route. ARM/C++ SDK variants require vendor contact. Its [SDK repository](https://github.com/SpectacularAI/sdk) distinguishes free noncommercial use from commercial licensing.

Luxonis's [Basalt and RTAB-Map example](https://docs.luxonis.com/software-v3/depthai/examples/vslam/basalt_vio_rtab) provides the stereo/IMU configuration and map outputs. [Release notes](https://docs.luxonis.com/software-v3/depthai/release-notes) identify VIO/SLAM as host nodes. The [DepthAI core repository](https://github.com/luxonis/depthai-core) states the Android limitation for v3. Avoid describing this as all computation running inside the camera.

## How one map could serve both field requests

1. Capture calibrated stereo and inertial measurements. Estimate camera motion while repeatedly refining a map in metres.
2. Identify the relevant work area. Let an operator confirm its boundary, or use a task-specific model for the relevant surfaces and landmarks.
3. Measure the selected area in the map. Report footprint, surface area and volume separately. Retain gaps where the walkthrough never observed the scene.
4. Detect the requested object classes in selected frames. Locate detections in the same 3D coordinate system and keep an object record with location, extent, appearance and supporting views.
5. Associate a returning detection with an existing object record before increasing the count. Correct object positions when camera tracking revises the map after recognising a previously visited location.

This is most promising for stationary equipment, materials and fixtures. A camera can look away from a valve and then return to the same mapped valve. For workers, vehicles, moved equipment or identical objects packed closely together, location alone cannot establish identity. Appearance matching, motion history and uncertain associations are still needed.

“Identify a worksite” needs a product definition. Recognising a construction activity, finding the visible work-area boundary, and recognising a previously visited site are separate tasks. Geometry helps with each, but does not supply their labels or boundaries automatically. A walkthrough measures what it sees; an unseen side of the site cannot be assigned a reliable size from that evidence alone.

## Counting and segmentation

A pixel mask does not by itself tell whether an object is one already counted. The proposed default is a task-specific lightweight detector, short-term tracking and the persistent 3D object records described above. Use segmentation on selected views where overlapping objects, boundaries or dimensions require it. Compare this with a smaller segmentation model before assuming full SAM is needed for every frame.

[ConceptGraphs](https://concept-graphs.github.io/) is a useful design reference: it projects segmented, posed colour/depth views into 3D and associates observations into object records using geometry and visual features. It is research software, not a verified one-update-per-second edge product. Earlier [Fusion++](https://arxiv.org/abs/1808.08378) builds a persistent graph of reconstructed objects and reports 4–8 Hz excluding relocalisation. That result is not a current phone or stereo edge benchmark. Both support investigating a map of individually identified objects as the common foundation for the brief.

For short-term tracking, [ByteTrack](https://github.com/ifzhang/ByteTrack) associates detections through motion and box overlap. [BoT-SORT](https://github.com/NirAharon/BoT-SORT) adds camera-motion compensation and optional appearance matching. Both expire lost tracks, so neither replaces the longer-lived object records. Their pedestrian-focused evaluations also do not establish equipment identity after long revisits. [SAM 2](https://github.com/facebookresearch/sam2) propagates prompted video masks, but does not supply the whole map-based inventory application.

Stereolabs' [support discussion about unique IDs](https://community.stereolabs.com/t/persistent-unique-ids-for-objects-using-the-sdks-object-detection/8377) directly matches this brief: looking away from room objects can result in new IDs on return. Staff describes unseen-track timeouts. The report concerns SDK 4.2.5, so it is evidence of a failure mode, not a benchmark of the current SDK. Application-level object identity must be tested independently.

NVIDIA's same release-3.2 [performance table](https://nvidia-isaac-ros.github.io/v/release-3.2/performance/index.html) reports Mobile SAM at 8.40 FPS on AGX Orin and 2.22 FPS on Orin NX for its 720p segmentation graph. Those component results do not establish simultaneous mapping, segmentation and counting throughput.

Keeping a map during one scan is also different from extending it tomorrow. Stereolabs' [.area map tutorial](https://www.stereolabs.com/docs/development/zed-sdk/modules/positional-tracking/vslam-mapping-tutorial) concerns camera localisation landmarks. An [August 2026 vendor support reply](https://community.stereolabs.com/t/combining-sequential-scan-for-spatial-mapping-to-achieve-better-scan/11627) says dense mapping starts fresh each session; loading a previous dense mesh and continuing integration is not supported. A shared localisation frame can support separate scans, but external geometry merging is required.

## Phone routes and misleading comparisons

Spectacular AI shows [live meshing on Huawei phones with a time-of-flight depth sensor](https://www.spectacularai.com/mapping). The page does not establish a named handset and sustained map rate. This is a different input from mobile stereo. Its phone NeRF/Gaussian workflow records first and then processes with a powerful NVIDIA GPU, so that workflow does not satisfy live on-phone reconstruction.

An ordinary phone with two rear lenses still needs simultaneous frames, calibration, usable overlap and stable timing to become a stereo capture device. A stereo peripheral plus a local computer avoids some handset restrictions but introduces a hardware product. Keep those deployment options separate when selecting a prototype.

## Proposed evaluation

Start with a ZED 2i and an Orin NX 16GB configuration as a practical commercial baseline. This is a recommendation for an evaluation, not a measured hardware requirement. Use NVIDIA's live result as a performance reference and retain OAK as an alternative.

Measure the combined workload during representative walkthroughs:

- Fresh accumulated geometry updates per second, update latency, longest stalls, thermal behaviour, memory growth and battery duration. Require at least one update per second under the user's intended meaning of sustained performance; define allowable stalls before accepting a system.
- Footprint and dimensions against independently measured references, plus map completeness and uncertainty. Agree the required size accuracy with Field before selecting map detail.
- Distinct-object count against a manually labelled inventory. Include looking away, returning by another route, close identical objects, occlusion, moved objects and tracking loss.
- Duplicate counts, missed objects and incorrect merges separately. A correct total can hide equal numbers of duplicates and omissions.

No hardware purchase, vendor contact or local mapping benchmark was performed in this review. The next experiment should establish whether the same rig meets geometry and counting requirements together.
