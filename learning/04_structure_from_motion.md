# 4. Structure from motion

Structure from motion (SfM) recovers camera poses and 3D points together from overlapping photos. It solves the same problem as SLAM (chapter 3), offline over all images at once instead of live frame by frame, and is the source of the project's most accurate camera paths. It outputs camera poses and sparse points only; dense surfaces (chapter 5) and objects (chapter 7) are later stages. See [How the methods fit together](methods_inputs_and_outputs.md). This chapter walks through its four stages, then shows what it gave on the project's recordings and why its result has no real-world size until something supplies one.

## Stage 1: features

In each image, find a few thousand distinctive spots and describe each one with a short vector (a *descriptor*) that stays similar when the same spot is seen from a slightly different angle or light.

- **SIFT** (classic): blob-like spots at many scales, 128-number descriptors. Robust; the project's default.
- **ALIKED** (learned): a neural network picks spots and descriptors; paired with **LightGlue**, a learned matcher.

## Stage 2: matching and geometric verification

For pairs of images, match descriptors (nearest neighbour in descriptor space). Many matches are wrong. Each pair is then checked against two-view geometry: if two images see a rigid scene, every true match obeys one 3 × 3 relation (the *essential matrix* with calibration, the *fundamental matrix* without). Fitting that relation with RANSAC (try many random small subsets, keep the model most matches agree with) throws out the wrong ones.

For video, the project matches each frame with its 10 neighbours in time plus a few further back ("sequential matching with quadratic overlap").

## Stage 3: triangulation

A point seen in two images with known poses lies where the two viewing rays cross. Noise means they never quite cross; triangulation picks the point closest to both. More views and wider angles between them make it more accurate. A point seen by only two nearly parallel rays has very uncertain depth.

## Stage 4: bundle adjustment

Bundle adjustment solves all camera poses and all 3D points together. For every observation (point `j` seen at pixel `x_ij` in image `i`) it measures the *reprojection error*: the distance between `x_ij` and where point `j` projects into camera `i`. It then adjusts every pose and every point to make the sum of squared errors as small as possible.

```text
minimise  Σ over observations  ‖ project(camera_i, point_j) − x_ij ‖²
```

It is the core of accurate 3D from images: every measurement constrains everything else, so errors do not accumulate the way they do in odometry.

### Two ways to build the model

- **Incremental mapper** (COLMAP's classic): start from one well-matched pair, add one image at a time (solve its pose from points already in the model, triangulate new points), bundle-adjust often. Accurate; slower on large sets.
- **Global mapper** (GLOMAP, built into COLMAP 4): solve every camera's rotation at once, then every position at once, then bundle-adjust once. Much faster on thousands of images; can be less robust on hard scenes.

## Why the result has no size

Multiply every point and every camera position by 2: every reprojection error stays exactly the same. The photos cannot tell a model from one twice its size. SfM therefore returns a world in arbitrary "SfM units". To get metres you need one extra measurement: a known distance, a depth sensor, or the phone's IMU (via ARCore).

> **Project result: 20 metric depth readings fix the size.** The project simulated a phone supplying a few depth readings at SfM points, using the Kinect (TUM) or rendered depth (ICL) as the stand-in. With 20 readings in total, drawn at random over the whole walk, the camera path error was 13.7 mm on xyz, 24.2 mm on desk and 34.1 mm on ICL, against 11.9, 21.5 and 34.1 mm with the size fitted to the true path. More readings did not help: with every reading the size was still 3.7% small on xyz, the Kinect's own bias. Five readings worked on a typical draw but the spread was wider. (Task78, `experiments/sfm/README.md`.)

> **Project result: Depth Anything's own size is unusable.** Taking SfM's size from Depth Anything gives 1.3-1.4 times too large, so the path misses by 58 mm (xyz) and 357-361 mm (desk) from size alone. (Task67.)

## What it gave on the project's recordings

COLMAP 4.2.1, CPU only, every second frame. "Best fit with size" lines up the path and fits one overall size (chapter 9).

| Recording | Features, mapper | Frames placed | Path error | Time (whole clip, 32 CPU threads) |
|---|---|---:|---:|---:|
| TUM xyz | SIFT, incremental or global | 399 / 399 | 11.9 mm | 134-340 s |
| TUM desk | ALIKED, incremental | 298 / 298 | 21.5 mm | 321 s |
| TUM desk | SIFT, global | 298 / 298 | 23.6 mm | 79 s |
| ICL living room | SIFT, incremental | 433 / 440 | 34.1 mm | 195 s |
| ICL living room | SIFT, global | 429 / 440 | 57.2 mm | 62 s |

What this teaches:

- **SfM from images alone beats depth-based odometry by 3-5 times** on TUM, even when the odometry gets the Kinect's depth (chapter 3).
- **The incremental mapper is the safer choice.** It is more accurate on ICL's large textureless walls, where the global mapper dropped 11 frames. The global mapper is 1.6-3.1 times faster.
- **Learned features are not automatically better.** ALIKED with LightGlue helped only with the incremental mapper on TUM. With the global mapper on TUM the positions collapsed (fitted size near 0) although every frame was registered; on ICL both ALIKED runs were far worse than SIFT. ALIKED kept about 450 points per TUM frame against SIFT's 1,800-2,800.
- **The sparse points are very accurate but sparse.** 64-83% of them lie within 5 cm of the true surface, but they cover only 4-20% of it (Task72). Dense surfaces need chapter 5.

Speed: 1.2-7.1 frames per second end to end, offline, on a desktop CPU. A phone would not run this; ARCore tracks the same kind of features live with its IMU. SfM's role in the project is the accurate reference path and the evidence for the design.

## Newer alternatives

Learned methods solve the same problem differently: DROID-SLAM and DPVO (learned SLAM on ordered video), VGGT, MapAnything and Depth Anything 3 (one network outputs poses and dense points for many images at once), MASt3R-SfM and VGGSfM (learned structure from motion). The 13 October review found classic bundle adjustment is still the most accurate when it succeeds, and that on short indoor video the differences between modern methods (9-18 mm) are small next to the old tracker's 112 mm. Several of the learned models have non-commercial licences; the review lists them.

## Try it

Run COLMAP on the TUM xyz clip and score it (needs `.venv-sfm` and the COLMAP build in `third_party/`; see `experiments/sfm/README.md`, "Running"):

```text
.venv-sfm\Scripts\python -m experiments.sfm.run_sfm --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2 --features sift --run-root experiments/sfm/runs/tum_xyz
.venv-sfm\Scripts\python -m experiments.sfm.report experiments/sfm/runs/tum_xyz/*
```

Open `debug/colmap/` in the run folder to see the database, the models and COLMAP's own logs.

## Further reading

- Lectures 3 (features), 5 (epipolar geometry, why size is unknown), 8 (SfM and bundle adjustment) in [research/3d_vision_fundamentals](../research/3d_vision_fundamentals/README.md).
- [research/structure_from_motion](../research/structure_from_motion/README.md): COLMAP note, GLOMAP and newer papers.
- `experiments/sfm/README.md`: method, settings and every result table.
