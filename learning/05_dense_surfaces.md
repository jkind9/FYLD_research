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

### Multi-view stereo on a phone has been done

Mobile3DRecon (2020) ran MVS live on a 2018 mid-range Android phone, using the phone's tracker for poses. For each new keyframe it:

1. Picks two earlier keyframes taken about 0.6 m away, looking roughly the same way.
2. Tries many depths per pixel and compares small patches by their *Census* code, a record of which neighbours are brighter than the centre.
3. Smooths the result with *semi-global matching (SGM)*: passes along 8 image directions that penalise depth jumps except at image edges.
4. Drops pixels it is unsure of, removes leftover noise with a small network, and fuses the depth into a mesh that grows as the user walks.

It took 70 ms for depth and 31 ms for the mesh per keyframe, each on one CPU core, with about 5 keyframes a second. Against the phone's own time-of-flight depth sensor, its depth was 5.7-10.4 cm RMSE. The 0.6 m gap matters: triangulation error grows with distance squared divided by the gap, so a wide gap keeps far depth accurate. That is the project's missing piece beyond the 2.5 m ARCore depth reaches.

**The routes in the table above can be combined, and published systems do.** Triangulation needs texture and camera movement; learned depth needs neither but gets the size and some shape wrong. So systems triangulate where they can and let learned depth fill blank surfaces. There are two ways to do it:

- Use triangulated points as sizing targets for learned depth. The project does this already with ARCore depth and tracked points.
- Fuse triangulated depth directly where it is confident, and use learned depth only where triangulation has no answer. Mobile3DRecon and CNN-SLAM work this way.

The project's next test is the first way with many more points: features triangulated between frames 0.3-1 m apart along ARCore's path, so that far surfaces get sizing targets too. The source list and the order to try: [research/dense_surface_fusion/triangulation_and_learned_depth.md](../research/dense_surface_fusion/triangulation_and_learned_depth.md).

Two older systems in the same line were also read. Newcombe and Davison (2010) fitted a rough surface to a tracker's points, drew it from nearby viewpoints, and corrected each pixel's depth along its camera ray with optical flow. Prisacariu et al. (2015) built one object at a time on an iPhone from its outline alone; that gives the outer shape but no hollows. Notes on all three: [research/dense_surface_fusion](../research/dense_surface_fusion/README.md#live-reconstruction-from-one-camera-three-earlier-systems).

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

## When one object appears twice

A fused room can show the same object in two places. Two different frames each put it somewhere, and the volume keeps both. In the 15 October room the sofa's red cushion appeared twice, 0.68 m apart along the camera's line of sight. Both copies came from frames taken at the same spot (Task116).

The cause was depth timing. ARCore's raw depth arrives at about 10 a second, and each depth map carries the time it was measured. For 9 of the walk's 147 depth maps, that time was 4.4 s before the photo they were paired with. Depth measured 4.4 s earlier, from somewhere else, sized the learned depth too small, so those frames put the cushion 0.7 m too near. ARCore's tracked feature points, which do not use depth maps, agree with the copy from fresh depth to about 0.2 m. The room build now skips depth more than 0.1 s older than its photo.

Two lessons follow:

- **Check the data before cleaning the surface.** A clean-up step that deletes one of two copies has to know which copy is right. Here a timestamp told us; a point-count vote between 9 stale and 10 fresh frames would have been close to a coin toss.
- **Agreement can be built in.** Learned depth sized to ARCore depth will agree with ARCore depth even when both are wrong. An independent check, here ARCore's tracked points, is needed.

With the stale depth gone, the doors still echoed: the hallway door showed as four parallel layers about 0.5 m apart (Task117). The cause is sizing where ARCore has no depth. The room build sizes learned depth in an 8 × 6 grid of cells. A cell with fewer than 20 ARCore depth pixels takes the whole frame's median size. ARCore's confident depth rarely goes past 2.5 m: 95% of it is nearer than that. A door 4.5 m away is therefore always sized from nearer objects, and each frame's near objects differ. Against ARCore's tracked points, depth beyond 3 m came out about 15% too near, and spread by about ±0.45 m at 3.5 m. Fusing only cells with their own ARCore size removed the echoes, but also took away the stairs, the TV wall and the ceiling.

Other systems avoid guessed sizes in one of three ways:
- **Measure far depth directly**, with LiDAR or a laser scanner.
- **Triangulate it from several views.** ARCore's own depth works this way, comparing the live frame with an earlier one taken from elsewhere.
- **Let near readings outvote far ones when merging.** Voxblox, a robot mapping library, weights each reading by one over its distance squared.

The last looks cheapest, but a trial on the same walk (Task120) showed it does not remove echoes by itself. The volume averages only readings that land within a few centimetres of each other, and the echo copies are 0.5 m apart, so each copy stays. Weighted this way, 50% more of the space ARCore saw through held surface. What worked was a vote: each surface point is checked in every frame, and a frame that sees straight through it votes to delete it, with near frames' votes counting more. That cut such points by 53-80%. Sizing far depth from ARCore's tracked points, which ARCore triangulated, moved far depth from 16% too near to 5% too near. But one size for every unmeasured part of the image also pushed the near floor down, so sizing needs to vary with distance. Indoors beyond 2.5 m and outdoors at 10-30 m, triangulation is the route that needs no new sensor. See [research/surface_denoising](../research/surface_denoising/README.md#getting-far-depth-right-what-other-systems-do).

Sources and the list of fixes: [research/dense_surface_fusion](../research/dense_surface_fusion/README.md).

## Cleaning up a fused surface

Averaging in the volume removes random scatter, but some errors survive it. Three kinds matter here:

- **Flying pixels.** Where a near object sits in front of a far wall, learned depth models such as Depth Anything give the edge pixels a depth between the two, because an average is the safest guess when training penalises distance from the answer. Back in 3D, those pixels form a sheet hanging from the object's edge toward the wall. The closer the object and the farther the wall, the longer the sheet. Indoor rooms, with furniture in front of walls everywhere, are full of such edges.
- **Side-on surfaces.** A surface seen almost edge-on, at a *grazing angle*, gets poor depth from every kind of sensor. The floor far ahead is always side-on: from a phone 0.9 m above it, the floor 5 m away is seen 80° from square-on.

The owner's target scenes are indoor, with surfaces up to about 10 m away. The pipeline fuses depth only out to 4.0 m, and ARCore depth, which sizes the learned depth, rarely reaches past 2.5 m. Beyond that, the main known error is the size of each frame's depth, as with the door echoes above, and clean-up cannot fix it.
- **Floaters.** Patches in empty space, from a frame that got something wrong once.

The offline room build now cleans its surface (below); the live processor does not yet. Methods exist for each point in the pipeline:

1. **Before fusion, per frame:** drop pixels on large depth jumps and pixels seen side-on. Cheap: one pass over each depth image.
2. **During fusion:** keep a pixel only if recent frames, projected into it, agree on its depth (a *consistency check*). Delete surface that a later frame looks straight through (*free-space carving*). Weight near, square-on views above far, side-on ones.
3. **After fusion:** keep only voxels seen by several frames, delete isolated points and small islands, and pull points near a fitted floor or wall onto it.

Two later trials on the same walk (Tasks122 and 124) asked whether any filter removes the echoes, the extra copies of the hallway door and staircase. None does. The reason is that a filter can only remove what frames disagree about. Frames taken from one standing spot share one guess at the size of far depth, so they agree with each other even when they are wrong. Counting frames (keep surface seen by 5 frames) therefore removes echoes only by also deleting much real surface: 39% of all points. Counting standing spots works better. Multi-view stereo programs such as COLMAP only count a second view as support if it sees the point from at least 3° away. Applied here, that rule deleted 17% of the surface, mostly outer copies of walls, without losing any surface that ARCore depth measured, and it kept the staircase. But the door copies survived, because views from several spots agreed on the wrong depth. Echoes need far depth that is consistent when it is fused, not cleaning afterwards.

"Small islands" are found by chain linking: two points belong to one piece if a chain of neighbours, each a few centimetres from the next, joins them. Each piece is then kept or dropped as a whole, by its size or by what it is made of, such as how many of its points a later frame saw through. This is the 3D form of removing small blobs from a 2D mask. It is standard for point clouds and meshes; no splat paper found uses it as its main floater filter. It has two weak spots. A large echo passes a size test. A thin chain of stray points can join a floater to a real wall, and then the floater counts as part of the wall.

**The clean-up the project uses (owner, 8 November 2026).** After tuning every stage by eye, the owner kept two: the vote that deletes surface frames see through, then keep only the largest pieces (up to 50, each with at least 5,000 points). A walk filmed as one continuous video joins the whole room into one or a few large pieces, so anything smaller is a floater. The room build joins pieces from touching grid cells rather than chains of points, the 3D form of finding contours in a 2D mask. Wider cells, like wider splats, bridge wider gaps. On the 15 October walk this removed 18% of the points and kept the room as one piece. The vote took 2.4 s and the pieces 0.15 s on a desktop CPU.

Every clean-up also deletes some real surface, so it is scored like any surface: accuracy and coverage together (next section). A clean-up cannot fix a sizing error such as the cushion's second copy: it has no way to know which copy is right.

The first trial (Task120, 15 October walk) gave a clear answer for this house. Edge and side-on pixels are only 2-9% of the fused depth. Dropping them, or weighting near readings above far ones, left *more* surface in space ARCore had seen through. The vote that deletes surface a frame sees straight through, with near frames counting more, cut that surface by 53-80% for 0.5 points of ARCore coverage. It also takes less than 20 ms per frame on the CPU.

Sources, the CPU cost of each method, the trial and the next steps: [research/surface_denoising](../research/surface_denoising/README.md).

## Photo-realistic scenes: training splats from photos

A fused surface is built for measuring. A *splat scene* is built to look like the photos. Many thousands of Gaussian splats (soft coloured blobs) are adjusted until renders from the recorded camera poses match the images. The result looks real from any angle. Its shape can still be wrong where the photos agree with a wrong shape, such as a blank wall, so sensor depth is added to the training to hold the shape.

Lumina, a commercial product checked on 8 November 2026, shows the usual chain:

1. A LiDAR iPhone records images, depth and camera poses, and colours the camera view by coverage.
2. The phone refines poses and merges scans.
3. It exports a *COLMAP dataset*: images plus text files of lens numbers, poses and sparse points.
4. A PC with an NVIDIA graphics card trains the splats, then measures and draws floor plans.

Every step has open-source parts. Brush (Apache-2.0) trains without NVIDIA's CUDA and builds for Android. DN-Splatter adds a phone-depth loss that is weaker at colour edges, where phone depth is noisy. PocketGS (a paper, no code) trains on an iPhone 15 in about 4 minutes. Training is offline and needs a graphics card, so it does not replace this project's live CPU surface. It could sit beside it as a viewing layer. The cheapest first step is writing the recorded ARCore poses into a COLMAP dataset, which every trainer reads. Full comparison: [research/gaussian_splatting](../research/gaussian_splatting/lumina_open_source_parts.md).

SpAItial Echo-3, released 27 October 2026, skips per-scene training. It takes a few minutes of iPhone video, with no LiDAR needed, and returns a splat scene at real-world scale from the cloud. Its model also generates the parts of the room the camera missed. Nothing about the method or its accuracy is published, and its terms forbid reverse engineering. Open models do the first half in one pass: YoNoSplat and AnySplat (both MIT) predict a splat scene from a set of frames in seconds on a GPU, and YoNoSplat can take the phone's poses so the scene comes out in metres. Generated areas look complete but are invented, so a measured record has to mark them as not seen. On 8 November the owner deferred splat scenes for this project. What matters is how accurately objects found by YOLO are sized in 3D, and a nicer-looking scene does not change that. Details: [the Echo-3 note](../research/products/e2e_product_research/10_spaitial_echo3/README.md) and [feed-forward splat models](../research/feed_forward_3d/feed_forward_splats.md).

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

### View a surface as Gaussian splats

A Gaussian splat is a small soft blob with position, orientation, width, colour and transparency. Overlapping blobs can draw a surface without a triangle mesh. Training those blobs to match photographs is a separate operation; drawing an existing surface as splats does not improve its geometry by itself.

Task100 turns the Redmi walk's saved surface into an offline interactive HTML. It displays 78,328 splats grouped from 845,428 reconstructed points, with height colours, orbit/zoom, a top view and eight recorded-camera/photo bookmarks. The original point cloud is preserved. These are surface-derived splats; photographic Gaussian training has not been run. Source and display settings: [surface Gaussian viewing](../research/3d_vision_fundamentals/surface_gaussian_viewing.md).

```text
.venv-yolo\Scripts\python -B -m tools.demos.capture_scene --surface <surface.ply> --session <v2 session folder> --out <viewer.html>
```

### Fuse and score depth

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
