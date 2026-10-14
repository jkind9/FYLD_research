# How the methods fit together: what each one needs and gives

A reference sheet for the boundaries between methods. The first part explains how SLAM, structure from motion, dense reconstruction and object detection relate. The second part lists every method this project uses or has considered, with its required inputs and its outputs.

## SLAM and SfM solve the same problem

SLAM and structure from motion (SfM) are not two layers stacked on each other. They are two ways of solving **the same problem**: given images, find where the camera was for each one and where some 3D points are.

| | Structure from motion | SLAM |
|---|---|---|
| Question answered | Where was each camera, and where are the matched points? | Same |
| Input | A set of images, any order (a video is fine) | An ordered stream of frames, one at a time |
| When it runs | Offline, after capture, over all images at once | Live, while the camera moves; each pose is available almost immediately |
| How it refines | Bundle adjustment over every camera and point together | Bundle adjustment over a recent window of keyframes, plus loop closure when a place is revisited |
| Output | Camera poses, sparse 3D points, which pixel saw which point | Same, plus a pose for every frame as it arrives |
| Accuracy | Usually the best, because every image constrains every other | Slightly lower, because it commits to poses before seeing later frames |
| Example | COLMAP, GLOMAP | ORB-SLAM3, DROID-SLAM, ARCore (strictly visual-inertial odometry with a map) |

Think of SLAM as the live version and SfM as the offline version. *Visual odometry* is SLAM with the map and loop closure removed: frame-to-frame only, so it drifts. The project's first tracker (Open3D RGB-D odometry) was odometry; COLMAP is SfM; ARCore on the phone is the live version.

**Neither produces a dense surface or knows about objects.** Both output camera poses and a sparse set of points: a few thousand distinctive spots, not every wall. Everything after that is separate stages that *consume* the poses.

### Where dense surfaces and objects come from

```text
                 ┌──────────────── camera tracking ────────────────┐
images ─────────►│ SfM (offline) │ SLAM (live) │ ARCore VIO (phone) │──► camera poses + sparse 3D points
                 └─────────────────────────────────────────────────┘        (no real size unless a
                                         ▲                                     depth sensor or IMU is used)
                      size source ───────┘  (IMU, depth readings, a known distance)

images + poses ──► dense depth per frame ──► depth images
                   (multi-view stereo, a depth sensor,
                    or learned depth resized to the sparse points)

depth images + poses ──► fusion (TSDF) ──► one surface in metres ──► top-down map, sizes, areas

images ──► object detector (YOLO) ──► 2D boxes and class names
              + depth + poses ──► each box placed in 3D ──► association across frames ──► object list, counts
```

So the object layer is not "SLAM on top of SfM". YOLO works on single 2D images and knows nothing about 3D. The project's object layer takes YOLO's boxes, looks up depth inside each box, moves that point into the world with the camera pose from tracking, and then decides whether a sighting is an object seen before (same place, similar appearance) or a new one. Tracking supplies the poses that make that possible; it does not do the detection.

Research does combine them under names such as *semantic SLAM* or *object-level SLAM*, where recognised objects become landmarks in the SLAM map. ConceptGraphs, cited in the object experiment, builds a persistent object map this way on top of known poses. In this project they stay separate layers so each can be tested alone.

## Names you will see, and what kind of thing each is

A name can be a whole software package, one complete system, one algorithm inside a system, a trained model, or a platform. Mixing these up causes most confusion: "COLMAP" and "bundle adjustment" are not alternatives, because COLMAP *uses* bundle adjustment.

### Toolkits: many algorithms in one package

| Name | What it is | What is inside | What this project uses it for |
|---|---|---|---|
| **COLMAP** | Software package for 3D from photos, mainly structure from motion | Feature extraction (SIFT, ALIKED), matching (brute force, LightGlue), the incremental and global (GLOMAP) SfM mappers, bundle adjustment, and multi-view stereo (PatchMatch) with fusion into a dense cloud | SfM camera paths and sparse points (Task67). Its multi-view stereo needs CUDA and is not run yet. |
| **pycolmap** | Python bindings for COLMAP | Same algorithms, called from Python | Reading COLMAP's saved models only (its Windows build crashed on ALIKED) |
| **Open3D** | General 3D data library | Point clouds and meshes, viewers, ICP registration, RGB-D odometry, TSDF fusion, plane fitting | Two pieces: RGB-D odometry as the walkthrough's first camera tracker, and TSDF fusion for surfaces. It is not "a camera tracker"; that is one function in it. |
| **OpenCV** | General computer vision library | Image processing, features (ORB, SIFT), calibration, PnP, stereo matching (SGBM), GrabCut | Corner tracking and PnP in the overlap chain (Task65), classical masks |
| **ARCore** | Google's Android augmented-reality platform | Visual-inertial tracking, depth, planes, anchors, recording and playback | The planned phone source of poses, size and points |
| **nvblox** | NVIDIA GPU library | TSDF fusion and meshing on a GPU | Researched for an edge box |

### Complete systems: input in, finished result out

| Name | Kind of system | Notes |
|---|---|---|
| **ORB-SLAM3** | Feature-based SLAM | Named after the ORB features it uses. The classic reference. |
| **stella_vslam** | Feature-based SLAM (a BSD-2 fork of OpenVSLAM) | Monocular, stereo or depth input; no IMU |
| **VINS-Mono, OpenVINS, Basalt, OKVIS2** | Visual-inertial odometry or SLAM | Camera plus IMU; GPLv3 (VINS-Mono, OpenVINS) or BSD-3 (Basalt) |
| **cuVSLAM** | GPU-accelerated feature SLAM (NVIDIA) | CUDA only; about 1-3 ms per frame on desktop and Jetson GPUs |
| **LEVIO** | VIO for microcontrollers | 20 fps under 100 mW, but metres of error on EuRoC |
| **FoundationSLAM, AIM-SLAM** | Foundation-model dense SLAM | Large GPU; claim the best TUM accuracy |
| **CUT3R** | Streaming 3D reconstruction (poses and points frame by frame) | GPU; about 30 fps, weaker poses |
| **RTAB-Map** | SLAM with strong revisit detection and dense mapping | Has an Android app that runs on top of ARCore |
| **DROID-SLAM, DPV-SLAM / DPVO** | Learned SLAM / learned visual odometry | Need a GPU |
| **MASt3R-SLAM, MASt3R-SfM** | Learned SLAM / SfM built on the MASt3R matching model | Non-commercial licence |
| **VGGSfM** | Learned SfM | Non-commercial licence |
| **GLOMAP** | Global SfM | Was a separate program; now inside COLMAP 4 as the global mapper |
| **KinectFusion** | Live depth-sensor SLAM with TSDF fusion | The 2011 system that made TSDF fusion standard |
| **iw3** | Stereo video maker | Turns ordinary video into side-by-side 3D with learned depth (Task73) |

### Algorithms and techniques: the building blocks

| Name | Type | Used in |
|---|---|---|
| **SIFT** | Feature detector and descriptor (classic) | COLMAP |
| **ORB** | Fast feature detector and descriptor (classic) | ORB-SLAM3, OpenCV |
| **ALIKED** | Feature detector and descriptor (learned) | COLMAP 4 option |
| **LightGlue** | Feature matcher (learned) | COLMAP 4 option, paired with ALIKED |
| **RANSAC** | Robust fitting: try many small random subsets, keep the model most data agrees with | Match verification, plane fitting (Task55) |
| **Essential / fundamental matrix** | Two-view geometry relation that true matches obey | SfM match verification |
| **PnP (perspective-n-point)** | Camera pose from known 3D points and their 2D pixels | Adding an image in incremental SfM; tracking against a map |
| **Triangulation** | 3D point from two or more views | SfM, SLAM |
| **Bundle adjustment** | Joint refinement of all poses and points by minimising reprojection error | SfM, SLAM |
| **Pose graph optimisation** | Spreads a loop-closure correction along the path | SLAM |
| **ICP (iterative closest point)** | Aligns two point clouds | Depth-based tracking and registration (Open3D) |
| **Umeyama / Horn alignment** | Best rotation, shift (and optional scale) between two point sets | Scoring camera paths (best fit) |
| **TSDF** | Surface representation and fusion method (averaged signed distance in voxels) | Surface fusion |
| **Marching cubes** | Extracts a triangle mesh from a voxel grid | Meshing after TSDF |
| **PatchMatch stereo** | Multi-view stereo by random search and propagation of depth guesses | COLMAP's dense step |
| **Hungarian algorithm** | Best one-to-one assignment between two lists | Matching sightings to object records |
| **ZNCC** | Patch similarity score, robust to brightness changes | Appearance comparison in the object layer |

### Trained models: a network with weights

| Name | Task | Notes |
|---|---|---|
| **Depth Anything V2** (Metric Small) | Single-image depth | The project's main depth model |
| **Depth Anything 3** | Depth and poses from one or many images | Task80 (Small) |
| **Video Depth Anything** | Depth consistent across video | Task65 |
| **Prompt Depth Anything** | Depth from an image plus a coarse metric depth map | Task79 |
| **ZipDepth** | Small single-image depth (relative) | Phone candidate |
| **Marigold** | Diffusion-based depth | Most accurate shape, too slow |
| **VGGT, MapAnything** | Feed-forward poses and 3D points | Researched |
| **YOLO** (YOLO26x here) | Object detection: boxes and classes | Object layer |
| **SAM, SAM 2, SAM 3** | Segmentation: masks from prompts | Researched |
| **DINOv2** | General image features for appearance comparison | Researched |

### Trackers that are not camera trackers

"Tracking" means two different things in this project. **Camera tracking** finds where the camera is (odometry, SLAM). **Object tracking** follows boxes from frame to frame in 2D: ByteTrack does this, and it knows nothing about the camera's position. The persistent-identity step in the object layer is a third thing: matching sightings to objects in 3D across long absences.

## Every method: inputs and outputs

"Required" inputs must be supplied. "Optional" inputs improve the result if available. "Metric?" says whether the output is in real metres without any extra size source.

### Camera tracking: odometry, SLAM and SfM

| Method | Kind | Required input | Optional input | Output | Metric? | Live? | Status here |
|---|---|---|---|---|---|---|---|
| Open3D RGB-D odometry | Visual odometry, direct | Colour and depth for consecutive frames; intrinsics | — | Pose per frame (frame to frame) | Yes, from the depth | Yes | The walkthrough's first tracker; 112 mm on TUM desk with Kinect depth |
| COLMAP, incremental mapper | SfM | Images | Intrinsics (else estimated); matching order for video | Poses, intrinsics, sparse 3D points, pixel-to-point links | No | No | Task67: 11.9-34 mm path error |
| COLMAP, global mapper (GLOMAP) | SfM | Same | Same | Same | No | No | Task67: faster, dropped frames on ICL |
| SIFT; ALIKED + LightGlue | Features and matching, a stage inside SfM or SLAM | Images | — | Keypoints, descriptors, matches | — | — | Task67 |
| ORB-SLAM3 | SLAM, feature-based | Video; intrinsics | Second camera, depth, or IMU | Poses, keyframes, sparse map | With stereo, depth or IMU | Yes | Reference only (GPLv3) |
| RTAB-Map | SLAM, strong revisit detection | Colour and depth, or stereo; an odometry source | IMU, lidar | Poses, a map graph, dense cloud or mesh built from the depth | Yes | Yes | Researched |
| DROID-SLAM, DPV-SLAM | Learned SLAM | Video; intrinsics | Stereo, depth | Poses and dense depth for keyframes | Only with stereo or depth | Yes, on a GPU | Researched |
| MASt3R-SLAM | Learned SLAM | Video | Intrinsics | Poses and dense point maps | Approximately | Yes, on a GPU | Researched (non-commercial) |
| ARCore motion tracking | Visual-inertial odometry with a map | Phone camera and IMU (on the device) | Depth sensor | Pose per frame, gravity, tracked 3D points, planes, intrinsics | Yes | Yes, on the phone | Not yet measured (Task75) |

### Feed-forward 3D models (one network, many outputs)

| Method | Required input | Optional input | Output | Metric? | Status here |
|---|---|---|---|---|---|
| VGGT | Several images | — | Poses, intrinsics, depth, 3D points per image | No | Researched (licence limits) |
| MapAnything | Images | Intrinsics, depth, poses | Poses and 3D points | Yes (predicts a size) | Researched |
| Depth Anything 3 | One or more images | Poses and intrinsics | Depth, confidence, poses, intrinsics | Only the Metric-Large model | Task80 (Small, CPU) |

These blur the boundary: one pass gives what SfM and dense depth give separately. They still estimate poses; they just do it inside the network.

### Depth for each frame

| Method | Required input | Optional input | Output | Metric? | Status here |
|---|---|---|---|---|---|
| Kinect or other depth sensor | (hardware) | — | Depth image | Yes | TUM reference and control |
| Two-camera stereo (e.g. OpenCV SGBM) | Two images taken at the same instant; stereo calibration | — | Disparity, then depth | Yes | Planned |
| Multi-view stereo (COLMAP PatchMatch) | Several images, their poses and intrinsics | — | Depth and surface direction per image | Same size as the poses | Needs GPU permission |
| ARCore depth | Phone camera moving, IMU | Depth sensor | Low-resolution depth and confidence (about 160 × 120) | Yes | Not yet measured |
| Depth Anything V2 Metric Small | One image | — | Depth claimed in metres | Claimed; 34-45% off on TUM | Main learned model |
| ZipDepth | One image | — | Inverse depth up to scale and shift | No | Task54/62 |
| Video Depth Anything | Video in 32-frame windows | — | Depth consistent across the window | Metric variants exist | Task65 |
| Prompt Depth Anything | One image and a low-resolution metric depth map | — | Depth in metres | Yes, from the prompt | Task79: no gain with sparse prompts |

### Turning depth and poses into a surface and a map

| Method | Required input | Output | Status here |
|---|---|---|---|
| Back-projection (point accumulation) | Depth images, poses, intrinsics | Point cloud | Walkthrough `MetricPoints` |
| TSDF fusion (Open3D) | Depth images, poses, intrinsics | One fused surface (points or mesh) | `experiments/sfm/src/dense.py` |
| Per-frame size to tracked points | Learned depth, sparse 3D points with their pixels, poses | Learned depth resized to agree with the points | Task72 |
| Grid footprint | 3D points in metres; which way is up | Ground plane, top-down height grid, seen and unknown area | Task55 |

### Objects

| Method | Required input | Optional input | Output | Status here |
|---|---|---|---|---|
| YOLO (YOLO26x here) | One image | — | Boxes, class names, confidences | Early trials |
| SAM family | One image and a prompt (box or point) | Video (SAM 2) | Pixel mask per object | Researched; classical masks tested |
| ByteTrack | Boxes per frame | — | Short-term track IDs; forgets objects out of view | Researched |
| 3D placement | Box or mask, depth, pose, intrinsics | — | A 3D point on the object's visible surface | Implemented |
| Persistent identity (association) | 3D sightings, appearance, earlier object records | — | Object records with every sighting; distinct counts | Implemented, not yet independently scored |

## The questions to ask of any new method

1. **What must I give it?** Images only, images plus calibration, ordered video, depth, poses, IMU?
2. **What does it give back?** Poses, sparse points, dense depth, a surface, labels?
3. **In what size?** Metres, or arbitrary units that need a size source?
4. **When?** Live while walking, or offline after upload?
5. **On what?** Phone CPU, desktop CPU, or a large GPU; and at what frames per second (the project's floor is 1)?
6. **Under what licence**, for both code and trained weights?
