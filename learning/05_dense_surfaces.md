# 5. Dense surfaces

Structure from motion (chapter 4) gives accurate camera poses and a few thousand accurate 3D points. A site model needs whole surfaces: every wall, floor and object. This chapter covers how dense depth and poses become one surface, the three ways to get the dense depth, and how a surface is scored.

## From depth images to one surface

Given each frame's depth image and camera pose, back-project every valid pixel and move it into the world (chapter 1). Keeping every point is the simplest model (the walkthrough's current `MetricPoints` method) but overlapping frames pile up duplicates and noise is never averaged.

**TSDF fusion** is the standard fix, used since KinectFusion (2011):

1. Divide space into small cubes (*voxels*), 1-2 cm in this project.
2. For each frame, for each voxel near a surface the camera saw, store the signed distance from the voxel to that surface along the camera ray: positive in front, negative behind. Clip ("truncate") it to a few voxels so far-away surfaces do not interfere.
3. Average those distances over every frame that saw the voxel.
4. The surface is where the averaged distance crosses zero. Extract it as points or a triangle mesh (marching cubes).

Fusion averages noise and gives one clean surface, but only if the inputs agree. If each frame's depth has a different size (chapter 2), fusion averages several copies of a wall into one thick, blurred wall. **Fusion helps only after every frame's depth is consistent with the camera path.**

The project uses Open3D's `ScalableTSDFVolume` (`experiments/sfm/src/dense.py`), with truncation at 4 voxels and depth limited to 0.1-4 m.

## Three ways to get the dense depth

| Route | Idea | Agrees with the path? |
|---|---|---|
| **Depth sensor** | Kinect, lidar, ARCore depth | Yes, if timing and calibration are right |
| **Multi-view stereo (MVS)** | For each frame, use its neighbours and their known poses: try many depths per pixel ("plane sweep"), keep the depth where the neighbours' pixels match best. COLMAP's PatchMatch stereo is the standard tool. | Yes, by construction: it is triangulation |
| **Learned depth sized to tracked points** | A single-image model gives dense shape; each frame is resized so its depth agrees with the SfM (or ARCore) points that frame saw | Only as well as the resizing works |

MVS is the textbook step after SfM. COLMAP's version needs a CUDA GPU, and the project runs CPU-only unless the owner grants GPU use, so it has not been run yet. The project has tested the third route in detail.

### Sizing learned depth to tracked points

For each frame:

1. Take the SfM points that frame saw (track length ≥ 3 frames, reprojection error ≤ 2 px).
2. Compute each point's depth in that camera from the SfM pose.
3. Read the learned depth at the same pixels.
4. The frame's size is the median of (SfM depth ÷ learned depth). Multiply the whole depth image by it.

Then multiply everything by the SfM world's metric size (chapter 4) and fuse along the SfM path. On a phone, ARCore would supply both the path and the points.

## When the camera path changes

A live tracker such as ARCore sometimes corrects where it thinks the camera has been, for example when it recognises a place it saw earlier. A signed-distance volume cannot take back a frame it has already fused, so a surface fused into one big volume would keep the old, wrong positions.

The fix is to fuse into short pieces of surface, *fragments*, each stored in its own local frame (Choi, Zhou and Koltun, 2015, used 50-frame fragments). Each fragment is placed in the world by a pose that can change later. On the phone that pose comes from an ARCore *anchor*: a fixed point that ARCore keeps consistent with its own corrections. The project's live processor (`src/live`, Task89) starts one anchor per second and gives each group of 10 anchors one fragment. When ARCore moves an anchor, its fragment moves with it, at the cost of one matrix multiply. Counted objects are kept relative to an anchor in the same way.

The price: frames inside one fragment all follow the fragment's first anchor, so a correction that bends the path within 10 s moves the whole fragment rigidly. Where neighbouring fragments overlap, there are two layers of surface until both are placed correctly. Sources: [research/camera_tracking_and_slam/fragments_and_anchors.md](../research/camera_tracking_and_slam/fragments_and_anchors.md).

## Scoring a surface

Two numbers, always together:

- **Accuracy**: for each reconstructed point, the distance to the nearest reference point. Reported as the mean, the RMSE, and the share within 5 cm.
- **Coverage (completeness)**: the share of the reference surface that has a reconstructed point within 5 cm.

A small accurate patch scores well on accuracy and badly on coverage; a big blurry blob does the reverse. The project's references: ICL-NUIM's published surface model (exact, synthetic), and for TUM, Kinect depth fused along the motion-capture path (which carries the Kinect's own error and about 30 mm of timing error).

## What the project found

Mean distance from the reconstructed surface to the reference (lower is better). "Ceiling" uses the true camera path and sizes each frame of Depth Anything exactly to the sensor: the best any per-frame size correction could do.

| Depth and path | ICL living room | TUM desk | TUM xyz |
|---|---:|---:|---:|
| Rendered sensor depth, true path | 11 mm | — | — |
| Depth Anything raw, true path | 167 mm | 399 mm | 467 mm |
| Depth Anything, exact per-frame size, true path (ceiling) | 82 mm | 129 mm | 158 mm |
| Depth Anything sized to SfM points, SfM path, 20 metric readings | 93 mm | 156 mm | 166 mm |
| Prompt Depth Anything fed with SfM points, same path | 147 mm | 217 mm | 168 mm |
| Depth Anything 3 Small, single image, sized to SfM points | 83 mm | 288 mm | 299 mm |
| Depth Anything 3 Small, given the camera poses, sized to SfM points | **79 mm** | 318 mm | 490 mm |
| SfM sparse points alone (best-fit size) | 77 mm, 4% covered | 48 mm, 20% covered | 57 mm, 21% covered |

Sources: Tasks 71, 72, 78, 79 and 80 in `experiments/sfm/README.md`, which also lists Depth Anything 3's other modes.

**Live, 14 October (Task89).** The live processor, fed ICL in the phone stream format with the true path and the rendered depth standing in for ARCore's raw depth, fused 28 frames while the clip played at its recorded speed (about one frame a second). Its surface is 46 mm from the reference on average, with 71% of points within 5 cm, but it covers only 22% of the room. It is not comparable with the table above, which fuses every frame: fewer frames give fewer points to be wrong and less of the room. See `src/live/README.md`.

What this teaches:

- **The pipeline is sound.** Rendered depth on ICL lands 11 mm from the reference, so the poses, conventions, fusion and scoring are right.
- **Sizing per frame matters most.** It cuts Depth Anything's error by 2-3 times.
- **The image-only path costs almost nothing.** Depth Anything sized to SfM points along the SfM path (the deployable design) is within 8-27 mm of the true-path ceiling.
- **What remains is the depth model's shape.** Even with perfect size and poses, Depth Anything's surface is 8-16 cm off on average, and only 23-53% of its points are within 5 cm. Better size correction cannot fix that.
- **Newer models are not automatically better here.** Prompt Depth Anything was worse everywhere. Depth Anything 3 Small, given the camera poses and sized to the points, was the best result on synthetic ICL (79 mm, below V2's ceiling) but two to three times worse on the real TUM recordings; the cause is not established.
- **A model that takes camera poses still needs the poses to span enough motion.** Depth Anything 3 sets its depth size by fitting its own predicted poses to the given ones; five consecutive frames (about 0.3 s) were too little, giving 282-814 mm until each frame was resized to the points.
- **The sparse SfM points are the most accurate geometry**, 48-77 mm mean with 64-83% within 5 cm, but they cover a fifth of the scene or less. Multi-view stereo would densify exactly these.

## Try it

Fuse Depth Anything along the SfM path, sized to SfM points, and score it (TUM desk; paths in `experiments/sfm/README.md`):

```text
.venv-sfm\Scripts\python -m experiments.sfm.run_dense --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_desk_every2 --depth model-sfm-size --depth-maps <Depth Anything run> --poses sfm:<SfM run>/output/incremental --sfm-size best-fit --run-root experiments/sfm/runs/dense_tum_desk
.venv-sfm\Scripts\python -m experiments.sfm.report --dense experiments/sfm/runs/dense_tum_desk/*
```

`output/surface_points.npy` in the run folder can be opened in any point-cloud viewer.

## Further reading

- Lecture 9 (multi-view stereo, plane sweep) and lecture 12 (3D representations) in [research/3d_vision_fundamentals](../research/3d_vision_fundamentals/README.md).
- [Open3D RGB-D note](../research/camera_tracking_and_slam/open3d_rgbd.md) for fusion.
- `experiments/04_surface_reconstruction/README.md` for the representations table (points, TSDF, surfels, splats, feed-forward 3D).
