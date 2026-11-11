# Surface denoising and far depth: floaters, flying pixels and guessed sizes

What removes stray and doubled points from the project's fused surfaces, how other systems avoid guessing the size of far depth, and where both fit in the live pipeline. The far-depth part merges a note written the same day in `research/dense_surface_fusion/other_systems.md`, now removed. Started 8 November 2026, after the owner asked for a dedicated denoising stage, "particularly for low depth distance scenes": indoor scenes with surfaces under about 10 m from the camera (owner, same day). Sources were checked against the papers' own text unless a row says otherwise. A first trial on the 15 October walk (Task120) is reported below; the vote it found useful is not in the live processor yet.

The live pipeline today (`src/live`) runs depth → size → fuse → surface → map → objects. The live loop has no clean-up stage: its only filters are a depth range of 0.1-4.0 m and ARCore confidence ≥ 128 when choosing sizing targets. The offline `room_build` also rejects depth maps more than 0.1 s older than their photo and, since Task126, runs the owner's clean-up: the visibility vote, then the largest pieces ([below](#owners-setting-in-the-room-build-task126)).

The [surface grouping digest](surface_grouping.md), added 10 November 2026, examines joining patches by geometry, colour, texture and learned features. It identifies direct prior art for region-based depth scaling and proposes a controlled test of temporal surface association, measurement accuracy and distinct-object retention. The [RTAB-Map digest](../camera_tracking_and_slam/rtabmap.md) covers an existing mapping backend to use as a separate comparison.

## Terms used here

- **Fusion**: merging many per-frame depth images, each placed by its camera pose, into one surface. The project uses Open3D's signed-distance volume (TSDF) with 2 cm voxels and a truncation of 4 voxels.
- **Floater**: a patch of surface that sits in empty space, away from any real object.
- **Flying pixel**: a depth pixel on the boundary between a near object and a far one whose depth lies between the two. Back-projected, a row of them forms a sheet hanging from the object's edge toward the background.
- **Grazing angle**: the camera ray meets the surface almost side-on. The angle between the ray and the surface normal is close to 90°.
- **Observation count**: how many frames have added to a voxel or point. Open3D stores it as the voxel's *weight*.
- **Free-space carving**: deleting surface that a later frame looks straight through. If a frame measures a wall 3 m away along a ray, anything on that ray nearer than about 3 m must be empty.
- **Multi-view consistency check**: keeping a depth pixel only if neighbouring frames, projected into it, put the surface at the same depth.
- **Low-depth scene**: an indoor scene whose surfaces are all within about 10 m of the camera, such as a room, a corridor or a hall (owner's definition, 8 November 2026).

## What the project's surfaces show now

These come from the 15 October Redmi walk (`20261015_093913_walk`). ARCore depth serves as the yardstick; there is no ground truth for this house.

| Symptom | Measured | Cause found so far | Source |
|---|---|---|---|
| Floor is a thick band | About 30 cm thick, against a few centimetres for ARCore depth fused alone | Not established | Task113, [src/live/README.md](../../src/live/README.md) |
| Points below the floor | 5.2% of points more than 10 cm below it (4.0 m far limit) | Distant, smeared learned depth; capping at 2.5 m makes the floor the dominant plane | Task113 |
| Near objects smear | Anything within about 0.5 m of the camera smears (judged by eye in the viewer) | Not established | Task115 |
| One object twice | Red cushion 0.68 m apart, along the line of sight | 9 depth maps 4.4 s old; fixed in `room_build` by rejecting stale depth | Task116, [dense_surface_fusion](../dense_surface_fusion/README.md) |
| A door in four layers | Layers 0.44-0.5 m apart along the line of sight | The door is beyond ARCore depth's reach, so each frame sizes it with its own frame median | Task117, [dense_surface_fusion](../dense_surface_fusion/README.md) |

The last two are errors in each frame's size, not noise. A generic clean-up filter cannot tell which copy is right. The first three are the kind of error this folder is about.

## What is different about indoor scenes under 10 m

Three limits of the current pipeline decide what clean-up can do at this range:

- **Fusion stops at 4.0 m.** `src/live/fragments.py` (`DEPTH_RANGE_M`) and `room_build` (`--far`) drop depth beyond 4.0 m. The far part of a 10 m room is never fused.
- **ARCore depth reaches about 2.5 m.** On the 15 October walk, 95% of confident ARCore depth is nearer than 2.54 m and 0.8% is beyond 3 m (Task117). Beyond that, learned depth is sized from each frame's median, so each frame puts a far wall at a different depth. That is the cause of the door echoes.
- **Error grows with distance.** Learned depth sized to ARCore scored a median relative error of 0.044-0.058 (Tasks109 and 113), measured where ARCore has depth, mostly under 2.5 m. If that held further out, it would be 13-17 cm at 3 m and 44-58 cm at 10 m. Against ARCore's tracked points, depth beyond 3 m came out about 15% too near (Task117).

So in a 10 m room the main known error beyond about 2.5 m is sizing, which no clean-up step can fix. How much of the total it is has not been measured. Raising the 4.0 m limit before sizing is fixed would fuse more echoes, not fewer.

Within the range that is fused, four effects call for clean-up:

1. **Learned depth blurs across edges.** Pixel-Perfect Depth (NeurIPS 2025) explains that regression-trained depth models, naming Depth Anything V2 (the project's model) among them, "output an intermediate (average) depth value between the foreground and background at depth-discontinuous edges, in order to minimize regression loss". The flying-pixel sheet is as long as the depth gap. A chair edge 0.6 m from the camera, in front of a wall at 3 m, can leave points anywhere along the 2.4 m between them. Rooms have such edges everywhere: furniture against walls, doorways, stair edges. Near objects fill more of the image, so their edges add the most flying pixels per frame.
2. **Distant floor is seen side-on.** On the 15 October walk the floor is about 0.8-0.9 m below ARCore's origin, the phone's starting position (Tasks113 and 115). From 0.9 m up, the floor 2 m ahead is seen 66° from square-on, at 5 m 80° and at 10 m 85°. Nguyen, Izadi and Lovell (2012) measured Kinect depth noise growing with both distance and angle; Voxblox cites the same work for noise growing with distance squared. Far floor is both far and side-on, which may explain part of the 30 cm floor band.
3. **Monocular models are weakest in the indoor near field.** Wu et al. (CVPR 2022) report that depth models trained mainly on driving data "generalize poorly to unseen complex indoor scenes, where objects are cluttered and arbitrarily arranged in the near field". This fits the smear within about 0.5 m of the camera (Task115).
4. **Radiance fields and splats grow floaters near the camera during training.** Floaters No More (EGSR 2023) traces them to near-camera volume receiving more gradient. This applies only if the project trains photographic splats, which it does not yet.

Points 1-3 predicted that the floor band and the near-object smear are mostly grazing-angle and flying-pixel depth. The trial below found such pixels are 2-9% of the fused depth, and removing them cut points below the floor by only 11%. The prediction is not supported for the floor.

## Getting far depth right: what other systems do

Other systems mostly avoid guessing the size of far depth. They measure it, triangulate it, or let near readings outvote far ones when merging. A *baseline* here is how far the camera moves between two views used to triangulate a point; triangulation error grows with distance squared divided by the baseline.

| Approach | Example | What it does | Fits CPU, live, at least 1 fps? |
|---|---|---|---|
| A depth sensor that reaches far enough | iPhone LiDAR apps indoors; laser scanners for buildings and sites | Measures depth, so no size is guessed | The Redmi has no such sensor |
| Triangulate between frames | ARCore's own depth: [Valentin et al. 2018](https://research.google/pubs/depth-from-motion-for-smartphone-ar/) match the live frame against an earlier keyframe taken from elsewhere. Photogrammetry (COLMAP, drone mapping) does the same with metres of baseline | Depth from geometry, sized by the camera path | ARCore's version runs on the phone; its range is short because a handheld phone moves little between the two frames |
| Learned depth from several posed frames | [SimpleRecon](papers/sayed2022_simplerecon.pdf) (ECCV 2022, Niantic): a 2D network with a plane-sweep cost volume over posed keyframes, then ordinary TSDF fusion; "online real-time" in its abstract | Learned depth that agrees between views because it compares them | Real time was shown on a GPU, which the project may not use; CPU speed unknown |
| Learned depth as a first guess, corrected by geometry | [CNN-SLAM](papers/tateno2017_cnn_slam.pdf) (CVPR 2017) fuses network depth with depth from direct monocular SLAM and prefers the network where SLAM fails, such as low-texture regions. [TANDEM](../dense_surface_fusion/papers/koestler2021_tandem.pdf) tracks against depth rendered from its own TSDF | Each frame is pulled toward what the views agree on | The CNN-SLAM authors ran prediction on a GPU |
| Trust near readings more when merging | [Voxblox](papers/oleynikova2017_voxblox.pdf) weights each reading 1/z², from the Nguyen noise model: a reading at 1 m counts 16 times one at 4 m | Near, measured readings outvote far, guessed ones | Open3D 0.19 takes no per-pixel weight in either its legacy volume (used here) or its newer `VoxelBlockGrid` (checked 8 November). Fusing near pixels several times gives the same weighted average with the current volume |
| Solve the whole recording at once, offline | Photogrammetry bundle adjustment; [FrozenRecon](../dense_surface_fusion/papers/xu2023_frozenrecon.pdf) fits every frame's scale maps jointly; Gaussian splatting and NeRF apps fit all photos together | One consistent answer for the whole clip | No: whole clip, usually on a GPU. Reference only, under the owner's live rule |

Networks that predict geometry for many frames at once (VGGT, MASt3R, Depth Anything 3) belong to the third and last rows; see [research/feed_forward_3d](../feed_forward_3d/README.md). Depth Anything 3 Small was tried in Tasks79 and 80.

**A limit of near-first weights.** A TSDF averages only the readings that fall in the same voxels, within the truncation band (8 cm here). The door's echo copies are about 0.5 m apart, so they sit in different voxels and are never averaged together. Weighting should change each copy's shape but not delete any copy. Deleting a copy needs a vote in which near views that see through it outvote the far views that put it there. The trial below tests both.

**Indoors beyond 2.5 m and outdoors at 10-30 m, triangulation is the route that needs no new sensor.** ARCore's tracked points are already triangulated: on the 15 October walk there are 1,173 point views beyond 3 m (Task117). Using them to size cells without ARCore depth is tested below. Multi-view stereo between frames along ARCore's path is the next step; its CPU cost is not yet measured.

## Methods, by where they act in the pipeline

"Live fit" means CPU only and at least one update per second (owner rules of 7 and 14 October 2026).

### Stage 1: each frame's depth, before fusion

| Method | Source | What it removes | Live fit | Limits |
|---|---|---|---|---|
| Reject stale depth | [ARCore Raw Depth guide](https://developers.google.com/ar/develop/java/depth/raw-depth): compare depth and image timestamps | Wrongly sized frames | Yes; done in `room_build`, not yet in the live processor | Only one cause of doubling |
| Depth-jump (flying-pixel) mask | Watson et al. ([Learning Stereo from Single Images](papers/watson2020_learning_stereo_from_single_images.pdf), ECCV 2020) mark pixels whose disparity Sobel response exceeds 3 and give them the nearest good value. [Pixel-Perfect Depth](papers/xu2025_pixel_perfect_depth.pdf) explains why regression models produce them | Sheets between near and far surfaces | Yes; one image filter per frame | Thin objects (chair legs, cables) lose their edges. The threshold needs choosing on project data |
| Grazing-angle mask | Nguyen et al. 2012 noise model ([IEEE record](https://www.computer.org/csdl/proceedings-article/3dimpvt/2012/4873a524/12OmNAlvHUP)); KinectFusion's angle-based weight, as discussed in [Voxblox](papers/oleynikova2017_voxblox.pdf) | Points from surfaces seen side-on | Yes; normals from the depth image, one dot product per pixel | Floors seen from a low phone are near-grazing; a strict cut thins the floor |
| Confidence or support mask | Mobile3DRecon ([Yang et al. 2020](papers/yang2020_mobile3drecon.pdf), on two mid-range phones) removes depth pixels with confidence below 0.15 before fusion; ARCore raw depth carries a 0-255 confidence | Pixels the depth source itself doubts | Yes | Learned depth has no confidence. Task117's `--supported-only` (drop sizing cells with no ARCore pixels) is the nearest substitute |
| Edge-aware refinement guided by the photo | [Fast Bilateral Solver](papers/barron2016_fast_bilateral_solver.pdf) (ECCV 2016): edge-aware smoothing, 10-1000 times faster than the methods it was compared with. Google's [Depth from motion for smartphone AR](https://research.google/pubs/depth-from-motion-for-smartphone-ar/) (2018) extends it for phone depth | Noise inside surfaces; snaps depth edges to photo edges | Probably; CPU speed on project frames untested | Can also smooth a real step. Paywalled 2018 paper not read in full |

### Stage 2: during fusion

| Method | Source | What it removes | Live fit | Limits |
|---|---|---|---|---|
| Distance and angle weights | [Voxblox](papers/oleynikova2017_voxblox.pdf) (IROS 2017): weight 1/z² from the Nguyen noise model, with a linear drop-off behind the surface; real time on one CPU core | Lets near, square-on views outvote far, side-on ones | Needs code: Open3D 0.19's `ScalableTSDFVolume.integrate` and `VoxelBlockGrid.integrate` take no per-pixel weight | Weights change averages; they delete nothing |
| Multi-view consistency check | COLMAP ([Schönberger et al. 2016](papers/schoenberger2016_pixelwise_view_selection.pdf)) keeps a pixel only with photometric and geometric support from at least 3 other views; MVSNet-style methods such as [IterMVS](https://arxiv.org/abs/2112.05126) keep a pixel whose reprojection agrees in at least a set number of views | Depth that only one frame believes, including edge sheets | Probably: project each new frame against the last 3-6 fused frames at reduced resolution | Needs overlap between keyframes; live updates come about 0.6 s apart |
| Per-pixel inlier filter over time | [Vogiatzis and Hernández 2011](papers/vogiatzis2011_video_realtime_mvs.pdf); [REMODE](papers/pizzoli2014_remode.pdf) (ICRA 2014) models each measurement as a Gaussian inlier or a uniform outlier and drops pixels whose inlier ratio stays low; [Ling et al. 2018](papers/ling2018_probabilistic_dense_reconstruction.pdf) carries that inlier probability into a weighted TSDF (31 ms per frame at 0.1 m voxels; depth on a laptop GPU) | Unstable depth | The filter yes; the published depth steps used GPUs | Built for multi-view stereo depth, which changes from frame to frame; learned depth can be wrong the same way every frame |
| Free-space carving | [Merrell et al. 2007](../dense_surface_fusion/papers/merrell2007_visibility_fusion.pdf); [Keller et al. 2013](papers/keller2013_point_based_fusion.pdf) delete model points in front of a newly confirmed point; Mobile3DRecon pushes voxels that a new frame sees through toward empty; the [Directional TSDF](papers/splietker2021_directional_tsdf.pdf) (ECMR 2021) carves only where no depth jump larger than the truncation lies within 2 pixels | Floaters and ghost copies that later frames look through | Probably; cost grows with ray length | Carving near edges eats thin objects. It cannot remove a wrong copy that lies behind the right one (Task116 analysis) |
| Tracking-quality weight | No canonical method found. [Ling et al. 2018](papers/ling2018_probabilistic_dense_reconstruction.pdf) and [EvidMTL](https://arxiv.org/abs/2503.04441) weight by depth uncertainty instead | Frames fused under poor tracking | ARCore reports a tracking state and failure reason, not a pose covariance | The pasted summary's "weight inversely against tracking uncertainty" has no ready source for ARCore |

### Stage 3: on the fused surface, periodically

| Method | Source | What it removes | Live fit | Limits |
|---|---|---|---|---|
| Observation-count threshold | [Keller et al. 2013](papers/keller2013_point_based_fusion.pdf): a point becomes stable once its confidence reaches 10 (at least 10 merges), and points that stay unstable are deleted after a time limit; [ElasticFusion](papers/whelan2015_elasticfusion.pdf) (RSS 2015) uses a confidence threshold, default 10 in its [code](https://github.com/mp3guy/ElasticFusion); Open3D 0.19's `VoxelBlockGrid.extract_point_cloud(weight_threshold=3.0)` drops voxels seen fewer than 3 times | One-off depth from a single frame | Yes; free at extraction with the newer Open3D volume. The project's `ScalableTSDFVolume.extract_point_cloud()` has no threshold | Removes real surface seen only once, such as the room's edges. At about 1.7 updates per second, 3 sightings means about 2 s of view |
| Statistical outlier removal | Rusu et al. 2008, as implemented in [PCL](https://pointclouds.org/documentation/tutorials/statistical_outlier.html) and [Open3D](https://www.open3d.org/docs/latest/tutorial/geometry/pointcloud_outlier_removal.html) (`remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)` in the tutorial) | Isolated specks | Yes on thinned points | Does not remove a solid ghost patch: the stale cushion copy had 112 points together (Task116) |
| Radius outlier removal | [Open3D tutorial](https://www.open3d.org/docs/latest/tutorial/geometry/pointcloud_outlier_removal.html) (`remove_radius_outlier(nb_points=16, radius=0.05)`) | Sparse points | Yes | Same as above |
| Cluster size filter | Open3D `cluster_dbscan` on points, `cluster_connected_triangles` on meshes | Small detached islands | Yes, periodically | Small real objects are islands too |
| Plane snapping for floors and walls | RANSAC planes (the map stage already fits a dominant plane); [ManhattanSDF](papers/guo2022_manhattan_sdf.pdf) (CVPR 2022) applies plane constraints only where a segmentation network sees floor or wall | The 30 cm floor band; wavy walls | RANSAC yes; ManhattanSDF is a trained neural field, offline only | Flattens real objects on the floor unless they are masked out |
| Learned point-cloud denoisers | Two 2025 surveys: [Zhang et al.](papers/zhang2025_point_cloud_denoising_survey.pdf) split the task into outlier removal and surface-noise restoration; [Wang et al.](papers/wang2025_point_cloud_denoising_survey.pdf) benchmark learned methods on denoising quality and speed | General noise | Not checked; most need GPU training | Reference only |

### Connected-piece filters: chain linking, then a test on the whole piece

Owner's question, 8 November 2026: is there research that links surface points or splats into chains and removes pieces whose chain is too small or has the wrong make-up, like removing small contours from a 2D mask but in 3D?

*Chain linking* here means single-linkage grouping: two points belong to one *piece* when a chain of neighbours, each within a set distance of the next, joins them. A *piece test* then keeps or drops each whole piece by its size or by some other measure of the piece. Searched 8 November 2026.

| Source | Works on | Link rule | Piece test |
|---|---|---|---|
| Open3D `cluster_dbscan` (DBSCAN); PCL Euclidean cluster extraction | Points | Within a distance; DBSCAN also needs `min_points` neighbours to extend a chain | Size. `clean.keep_after("clusters")` uses 5 cm and drops pieces under 1,000 points |
| [PCL Conditional Euclidean Clustering](https://pointclouds.org/documentation/classpcl_1_1_conditional_euclidean_clustering.html) | Points | Within a distance *and* a user function of the two points returns true (the tutorial compares intensity and normals) | Minimum and maximum size; the too-small and too-large pieces can be read back |
| [2DGS `post_process_mesh`](https://github.com/hbb1/2d-gaussian-splatting/blob/main/utils/mesh_utils.py) (code, read 8 November) | Mesh extracted from Gaussians | Triangles sharing an edge (Open3D `cluster_connected_triangles`) | Keep the 1,000 largest pieces, and none under 50 triangles. Copies of this function appear in other Gaussian-mesh projects |
| PyMeshLab "remove isolated pieces" | Mesh | Triangles sharing an edge | Face count, or diameter as a share of the whole mesh's diameter |
| [GaussianCut](papers/jain2024_gaussiancut.pdf) (NeurIPS 2024) | Trained Gaussians | Graph over each Gaussian's k nearest neighbours | Graph cut from user clicks and 2D masks. Selects an object; does not remove floaters |
| [ROODI](papers/chang2025_roodi.pdf) (arXiv 2503.10256) | Trained Gaussians | K nearest neighbours, distance measured between whole Gaussians (Wasserstein), so a large splat is not called isolated | Per Gaussian, not per piece: drop if mean neighbour distance exceeds mean + α × std (statistical outlier removal) |
| [TIDI-GS](papers/yang2026_tidi_gs.pdf) (arXiv 2601.09291) | Trained Gaussians | K nearest neighbours | Per Gaussian: isolation distance combined with low opacity and low importance |
| [CleanGS](papers/shivottam2026_cleangs.pdf) (arXiv 2601.00913, current version) | Trained Gaussians | None | Per Gaussian: kept if two of three chosen views' object masks cover it. The first version of the paper used neighbour-based outlier removal instead |
| Volumetric attribute filters on a max-tree ([Westenberg, Roerdink and Wilkinson, IEEE TIP 2007](https://doi.org/10.1109/TIP.2007.909317), paywalled, not read) | Voxel volumes | 6- or 26-connected voxels, at every threshold level | Any measure of the piece: volume, surface area, shape moments. This is the 2D small-contour removal carried to 3D, with make-up as the measure |
| [ToMATo](papers/chazal2013_tomato.pdf) (Chazal, Guibas, Oudot and Skraba, J. ACM 2013) | Points with a density estimate | Neighbourhood graph; each point climbs to its densest neighbour | A piece survives only if its density peak stands out from the bridge joining it to a bigger piece by more than τ (its *prominence*); weaker pieces merge into their neighbour |

**What exists.** Chain-and-piece filters are standard on point clouds (DBSCAN, PCL) and on meshes, including meshes extracted from Gaussians (2DGS). No Gaussian-splatting paper was found that removes floaters by piece size as its method. The splat papers found test each Gaussian's isolation alone (ROODI, TIDI-GS) or vote with views (CleanGS, SparseGS). Make-up tests exist in two forms: on the link (PCL's condition function) and on the finished piece (attribute filters).

**What this means for the door and stair echoes (predicted before Task122, then tested in Tasks122 and 124).**

1. Size alone keeps a large echo. At 2 cm spacing, 1,000 points is about 0.4 m². A door-sized copy, about 0.8 × 2 m, would be about 1.6 m² if copied whole. Task122 confirmed it: size-only piece removal left the door echoes.
2. Single linkage joins an echo to the real wall or floor through any chain of points under 5 cm apart. A flying-pixel sheet or a carved edge can be that chain. The echo then sits inside the largest piece and is kept. Task122 confirmed it: at a 5 cm join, 96% of all points form one piece. ToMATo's prominence test, or a link rule as in PCL's conditional clustering, breaks such thin bridges. Task124 tests the PCL link rule.
3. A piece test needs a make-up measure that differs between echo and real surface. Task122 showed that how many frames saw a point does not: echo layers survived "seen by 5 frames". Task124 uses how many *standing spots* measured a point instead (see "Agreement between standing spots" below).

### Stage 4: photographic splats (offline, not built)

The project's viewer draws the fused surface as splats; it does not train them on photos. If training is added, these address floaters during training.

| Method | Source | Idea |
|---|---|---|
| Depth and normal priors | [DN-Splatter](papers/turkulainen2025_dn_splatter.pdf) (WACV 2025) | Regularise splats with sensor or monocular depth and normals; tested on indoor datasets (MuSHRoom, ScanNet++) |
| Pruning by evidence | [SparseGS](papers/xiong2023_sparsegs.pdf) (3DV 2025); [TIDI-GS](papers/yang2026_tidi_gs.pdf) (2026) | SparseGS prunes where the most opaque splat on a ray and the blended depth disagree; TIDI-GS prunes splats lacking support from several views |
| Low frequencies first | [EFA-GS](papers/wang2025_efa_gs.pdf) (Cyberworlds 2025) | Expand under-trained splats; 1.68 dB PSNR gain on the authors' own low-quality dataset |
| Near-camera gradient scaling | [Floaters No More](papers/philip2023_floaters_no_more.pdf) (EGSR 2023) | Scale down the extra gradient near-camera volume receives |

## The pasted summary, checked

The owner's request quoted a search summary with five strategies. What the sources support:

| Strategy in the summary | Finding |
|---|---|
| Statistical outlier removal | Real and cheap (Open3D, PCL). It removes isolated specks, not solid wrong patches. The claim that it erodes edges was not checked |
| Plane priors with signed-distance fusion | Real. The cited neural form (ManhattanSDF) is offline. A RANSAC plane snap is the live counterpart and is untested here |
| Octree and density clustering | Clustering is real (DBSCAN, connected components). An octree adds nothing here: Open3D's volume is already sparse |
| Frequency-aware optimisation (EFA-GS) | The paper exists and does what the summary says, but only for training photographic splats |
| Depth-aware regularisation | Real for splats (DN-Splatter, TIDI-GS). In this pipeline, sizing learned depth to ARCore depth already plays that role |
| "Weight updates inversely against tracking uncertainty" | No source found that does this with a phone tracker; ARCore exposes no pose covariance |

## Proposed clean-up stage for `src/live`

`src/live/clean.py` now holds the trial versions of the masks, the near-first passes and the visibility vote (Task120). The proposal below is revised by the trial results in the next section.

1. **Between size and fuse, per frame:** stale-depth rejection and better sizing beyond ARCore depth's reach. The depth-jump and grazing-angle masks are dropped as stand-alone fixes: on the 15 October walk they added floaters.
2. **After fusion, against recent views:** the visibility vote, with near views outvoting far ones. In the trial it removed 53-80% of the surface lying in empty space. Live, each update would add its newest view's votes to running totals kept per surface point, about 17 ms against a 680,000-point surface.
3. **When the surface is extracted:** an observation-count threshold, then outlier and cluster filters, then optional plane snapping. Run on each finished fragment once, not on the whole surface every update, so it stays inside the one-second budget.

Two Open3D facts shape the work. Version 0.19's legacy `ScalableTSDFVolume`, used by `src/live/fragments.py`, takes no per-pixel weights and has no observation-count threshold. The newer `o3d.t.geometry.VoxelBlockGrid` has the threshold (`extract_point_cloud(weight_threshold=3.0)`), exposes each voxel's weight, and can render depth from the model (`ray_cast`), which a consistency check against the built surface needs. It also takes no per-pixel weights, so stage 2 weights need custom code either way.

## How to score a clean-up

Every clean-up removes some real surface. Report what it removes and what it keeps, always together (see "Scoring a surface" in [learning/05_dense_surfaces.md](../../learning/05_dense_surfaces.md)):

- **ICL-NUIM living room** (exact reference model): accuracy (mean distance, share within 5 cm) and coverage (share of the reference within 5 cm) before and after. Pixel-Perfect Depth's edge-aware point-cloud metric is a candidate for scoring edges alone.
- **15 October walk** (ARCore depth as yardstick): floor band thickness, share of points more than 10 cm below the floor, points within 0.5 m of the camera path, and the count of points within 25 cm of the stale cushion copy (121 red points before Task116's fix, 0 after).
- **Cost:** milliseconds per update for each part, and whether the run still has no gap over 1 s.
- **Empty sight lines** (used in the trial below): ARCore saw each tracked point from its camera, so the line between them must be empty. The score is the share of 4 cm samples along those lines that have fused surface within 4 cm, stopping 15 cm (or 5% of the distance) short of the point. It counts floaters and echo copies in front of real surfaces without needing ground truth.

## Trial on the 15 October walk, 8 November 2026 (Task120)

`python -B -m src.live.denoise_trial --session <v2 session> --out <folder>` runs Depth Anything V2 Metric Small once per frame that `room_build` fuses (134 frames), then fuses and scores each variant below. CPU only, with the GPU hidden from the process; the whole run takes 81 s. Tracked points with even ids may be used for sizing; only odd ids (2,418 point views in cells without ARCore depth, and every odd-id view for the surface scores) are used for scoring. Tracked points are ARCore's own triangulation, not ground truth; ICL-NUIM has not been run yet. The settings are first guesses by Claude, not tuned: edge jump 5% in a 3 × 3 neighbourhood, side-on beyond 75°, vote margin the larger of 8 cm and 5%. The baseline reproduces `room_build` to within 2 of 676,855 points; the trial stores depth as 32-bit floats. A repeat run gave identical scores.

**Where the fused depth lies.** 10% of fused pixels are within 1 m, 76% at 1-2.5 m and 14% at 2.5-4 m; 1.2% of valid pixels lie beyond 4 m and are dropped. This walk is a small house, so it does not test a 10 m room. Depth-jump pixels are 1.8-3.0% of each band and side-on pixels 6.8-8.9%. The prediction that the floor band is mostly flying-pixel or side-on depth is not supported: removing both cut points below the floor by only 11%.

**Sizing beyond ARCore's reach,** measured at held-out tracked points in grid cells without ARCore depth (1.0 = right; "middle half" is the 25th to 75th percentile):

| Sizing | Under 2.5 m: median, middle half | 2.5 m and beyond: median, middle half |
|---|---|---|
| Current: frame median where a cell has no ARCore depth | 0.98, 0.92-1.04 | 0.84, 0.69-0.95 |
| Tracked-point size in every such cell | 1.03, 0.98-1.10 | 0.95, 0.87-1.02 |
| Tracked-point size only where depth reaches 2.5 m | 0.98, 0.92-1.04 | 0.89, 0.72-1.01 |

**The surface, by variant.** "Blocked" is the empty-sight-line score; lower is better. "Within 10 cm" is the share of held-out tracked points beyond 2.5 m with fused surface within 10 cm. "ARCore covered" is the share of ARCore depth points with surface within 5 cm.

| Variant | Points | Blocked, under 2.5 m | Blocked, 2.5 m and beyond | Within 10 cm, far | ARCore covered | Points over 10 cm below the floor | Fusion time for 134 frames |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline (`room_build` rules) | 676,853 | 9.2% | 8.6% | 61% | 84.9% | 38,171 | 1.5 s |
| Edge and side-on masks | 641,978 | 12.5% | 10.9% | 62% | 86.5% | 34,066 | 4.0 s |
| Near-first weights (1/z², by repeated fusion) | 783,264 | 14.2% | 12.8% | 63% | 87.3% | 40,035 | 7.2 s |
| Visibility vote, near views outvote far | 579,845 | **1.8%** | **4.1%** | 58% | 84.4% | 38,158 | 3.8 s |
| Tracked-point size in every cell without ARCore depth | 1,053,539 | 7.9% | 8.7% | **70%** | 79.2% | 169,026 | 1.9 s |
| Tracked-point size only beyond 2.5 m | 762,905 | 11.5% | 8.1% | 63% | 85.5% | 52,967 | 1.5 s |
| Tracked-point size beyond 2.5 m, then the vote | 678,342 | **1.6%** | **3.7%** | 61% | 85.0% | 52,949 | 3.9 s |

What this shows:

1. **The visibility vote is the one clean-up that works.** It removed 97,008 points (14%) and cut blocked sight lines by 80% under 2.5 m and 53% beyond, for 0.5 points less ARCore coverage. It removed no points below the floor (38,171 before, 38,158 after): those are hidden behind the floor, so no view sees through them.
2. **Near-first weights alone make floaters worse.** Blocked sight lines rose by about half (9.2% to 14.2%) and the point count by 16%, as the TSDF argument above predicted. They did tighten surfaces already near the right place: the median distance from far tracked points to the surface fell from 6.2 to 5.2 cm. The near-first idea works inside the vote, not in the averaging.
3. **Per-frame edge and side-on masks also added floaters** (blocked +35% under 2.5 m) while removing 7% of pixels. One possible reason, untested: the removed pixels also told the volume which space was empty.
4. **Tracked points fix far sizes but a single size per frame cannot.** Used in every cell without ARCore depth, they moved far depth from 16% too near to 5% too near and narrowed the spread by 43%. Far surface within 10 cm of tracked points rose from 61% to 70%. But the same size also applied to near floor cells, which ARCore depth also missed, and pushed the floor down: 4.4 times as many points below it. Applied only beyond 2.5 m, the floor damage fell to +39% and most of the far gain went too. A size that changes with distance, fitted to ARCore depth near and tracked points far, is the next step.

**Where the vote's deletions sit (Task121).** 98% of the 97,008 removed points lie between 0.1 m and 2.2 m above the floor, in the room's open space. It removed 2.8% of points within 10 cm of the floor and 0.4% above 2.2 m. It also removed 19% of all points at low-furniture height (0.1-0.76 m above the floor), so some real furniture may have gone with the floaters. Only a scene with a known true surface, such as ICL-NUIM, can tell how much.

**Viewer.** `python -B -m tools.demos.cleanup_scene --trial <denoise_trial folder> --session <v2 session> --out <viewer.html>` builds one offline page. It shows the room before clean-up, with two switches: one paints red what the vote removes, the other hides it to show the cleaned room. The results table above sits below the 3D view. The 15 October page is `outputs/denoise_trial_093913_v2/viewer/redmi-room-15oct-cleanup.html` (196,914 splats in 3 cm cells, 4.86 MB). It embeds household photos, so it stays local. Headless Chromium with software rendering (SwiftShader, no GPU) loaded it in three states (as opened, removed in red, removed hidden) with no console errors or network requests. Seen from above with the removed points hidden, the floor and table show through where a red layer hung before.

### Floating-piece removal against the door and stair echoes (Task122)

The owner reported that the vote left the floaters they could see (dark specks across the floor and shards in the air) and that the hallway door and the staircase still echo. The sight-line score above only checks lines to ARCore's tracked points, so it barely measures specks elsewhere. Task122 added the filters from the web search and two direct measures: **floating points** (points in pieces under about 0.4 m² that touch no other surface within 5 cm) and **door and stair blocked shares** (the sight-line score for frames within about 1 s of frame 65, which looks at the hallway door, and frame 420, which looks at the stairs). Same walk, same settings, CPU only.

| Variant | Points | Floating points | Blocked, door views | Blocked, stair views | ARCore covered | Points over 10 cm below the floor |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 676,853 | 12,889 | 6.4% | 8.2% | 84.9% | 38,171 |
| Statistical outlier removal (Open3D, 20 neighbours, 2.0) | 659,567 | 15,822 | 6.1% | 7.6% | 84.6% | 37,315 |
| Radius outlier removal (16 points in 5 cm) | 659,614 | 15,512 | 6.2% | 7.7% | 84.5% | 37,268 |
| Floating-piece removal, 5 cm join | 663,964 | 0 | 5.3% | 7.5% | 84.6% | 38,020 |
| Floating-piece removal, 3 cm join | 630,389 | 0 | 4.7% | 6.7% | 84.2% | 36,811 |
| Vote with see-through evidence to 8 m | 576,767 | 6,772 | 3.0% | 4.5% | 84.4% | 38,158 |
| Kept only where seen by 3 frames | 548,722 | 13,606 | 5.7% | 8.0% | 84.8% | 27,705 |
| Kept only where seen by 5 frames | 415,782 | 8,994 | 4.7% | 7.8% | 84.6% | 18,161 |
| Vote (8 m), then seen by 3, then floating pieces (3 cm) | 447,545 | 0 | **2.6%** | **4.0%** | 83.5% | 26,618 |

What this shows:

1. **Floating-piece removal works on what is truly detached, and that is little.** At a 5 cm join, 96% of all points (646,834) form one connected piece; 115 small pieces and 2,478 lone points stand apart. Most visible specks touch real surface within 3-5 cm, so a connectivity test cannot separate them. Outlier removal made it worse: deleting points split pieces, raising floating points by about 20%.
2. **The observation count thins the floor band.** Keeping points seen by at least 5 frames halved the points below the floor (38,171 to 18,161), for 39% of all points.
3. **No filter removes the door or stair echoes.** The best combination halves the blocked share at the door (6.4% to 2.6%) and the stairs (8.2% to 4.0%) and removes a third of all points. Seen from frames 65 and 420, it clears the haze in front of the camera, but it also deletes most of the staircase: the open banister lets frames see through to the wall behind, and few frames see the stairs. The door echoes do not visibly change.
4. **Why: each echo layer is backed by several frames.** Echo layers survived "seen by 5 frames", so frames taken from one spot agree with each other on a wrong size. A filter can only remove what frames disagree about. The echoes need consistent far depth when it is fused: triangulated depth along ARCore's path, or far sizing that agrees between standing spots.

Viewer with the combined clean-up shown in red: `outputs/denoise_trial_093913_v5/viewer/redmi-room-15oct-cleanup-combined.html` (`--kept vote_far_seen_3_clusters_3cm`), local only. Camera views from frames 65 and 420, before and after: `outputs/denoise_trial_093913_v5/camera_shots/`.

### Agreement between standing spots, and pieces by make-up (Task124)

Task122 found that echo layers survive because frames from one standing spot agree on the same wrong size. On the 15 October walk the first 360 recorded frames stay within about 0.4 m of the start. In 10 of the 12 30-frame windows among them, the camera stays within 1-9 cm of the window's mean position. The hallway door is 4.5 m away, so frames 0.4 m apart see it about 5° apart, but frames within one such window see it about 1° apart or less. Multi-view stereo already handles this case: a view too close in angle to the first adds no independent evidence. Three open-source examples were read on 8 November 2026:

| Code | Rule | Default values |
|---|---|---|
| COLMAP [`patch_match_options.h`](https://github.com/colmap/colmap/blob/main/src/colmap/mvs/patch_match_options.h) and the filter loop in [`patch_match_cuda.cu`](https://github.com/colmap/colmap/blob/main/src/colmap/mvs/patch_match_cuda.cu) | A source image counts towards a pixel only if the rays meet at the point at least `filter_min_triangulation_angle` apart and the depths agree on reprojection. The pixel is deleted if fewer than `filter_min_num_consistent` images count | 3°; 2 images; 1 px forward-backward error |
| COLMAP [`fusion.h`](https://github.com/colmap/colmap/blob/main/src/colmap/mvs/fusion.h) | Depth pixels are fused into a point only if enough of them agree | `min_num_pixels` 5; depth within 1%; reprojection within 2 px; normals within 10° |
| MVSNet (PyTorch port) [`eval.py`](https://github.com/xy-guo/MVSNet_pytorch/blob/master/eval.py), `check_geometric_consistency` | Each source view's depth is projected into the reference; it agrees if it lands within 1 px and 1% depth. A pixel is kept if at least 3 views agree and the network's confidence is over 0.8 | 1 px, 1%, 3 views |
| PCL tutorial [`conditional_euclidean_clustering.cpp`](https://github.com/PointCloudLibrary/pcl/blob/master/doc/tutorials/content/sources/conditional_euclidean_clustering/conditional_euclidean_clustering.cpp) | Two neighbours join one cluster only if a condition holds; the example tests intensity, or normals within 30°. Clusters smaller than a thousandth or larger than a fifth of the cloud are set aside and can be read back | 30°; size limits N/1000 and N/5 |

Two rules were built from these (`src/live/clean.py`):

- **Spots rule** (`wide_support`, after COLMAP's filter). A surface point is kept if some view measured it nearer than 2.5 m, where ARCore depth sizes the learned depth. Otherwise it needs two more views that measured it at the same depth (within the vote margin, the larger of 8 cm and 5%) from rays at least 3° from the first measuring view's ray. Angles are taken against the first view that measured the point, which is cheaper than comparing every pair. So a point whose first view sat between two others can be dropped even though those two are more than 3° apart.
- **Pieces by make-up** (`piece_majority`, after PCL's conditional clustering). Points within 3 cm whose normals differ by under 30° join one piece, so the side-on strip at a corner does not join an echo copy to the wall behind it. A piece is removed whole when more than half its points fail the spots rule. This is the "remove a component by its make-up" idea from the chain-linking section above.

The trial also gained two scores. **Within 10 cm, door or stairs**: the share of held-out tracked points from the door or stair views that still have surface within 10 cm; it falls when a filter deletes real surface there. **Behind**: the blocked count, taken from just past each tracked point to 1 m past it, where an echo copy behind a wall would sit. A room seen through an open door also counts there, so it never reaches zero.

Same walk and settings as Task122, CPU only with the GPU hidden; the run of all 22 variants took 157 s. Baseline and Task122 rows are repeated from the same run for comparison.

| Variant | Points | ARCore covered | Blocked, door / stairs | Behind, door / stairs | Behind, all tracked points beyond 2.5 m | Within 10 cm, door / stairs |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 676,853 | 84.9% | 6.4% / 8.2% | 42.6% / 21.0% | 14.0% | 82.4% / 93.5% |
| Kept only where seen by 5 frames (Task122) | 415,782 | 84.6% | 4.7% / 7.8% | **30.3%** / **11.2%** | **9.5%** | 79.4% / 89.8% |
| Vote (8 m), seen by 3, floating pieces 3 cm (Task122) | 447,545 | 83.5% | **2.6%** / **4.0%** | 32.2% / 12.7% | 10.2% | 73.5% / 87.4% |
| Spots rule, 3° | 562,842 | **84.9%** | 5.7% / 8.1% | 40.7% / 18.6% | 10.7% | 80.2% / 92.8% |
| Spots rule, 6° | 533,081 | 84.9% | 5.6% / 8.0% | 40.0% / 18.2% | 9.7% | 79.4% / 92.8% |
| Spots rule, one-spot depth trusted only under 2.0 m | 479,790 | 84.4% | 5.4% / 7.9% | 40.0% / 17.3% | 10.1% | 80.0% / 91.9% |
| Spots rule, then pieces by make-up | 560,788 | 84.9% | 5.7% / 8.0% | 40.7% / 18.5% | 10.7% | 80.2% / 92.8% |
| Vote (8 m), then spots rule | 469,347 | 84.3% | 2.8% / 4.4% | 37.7% / 17.7% | 10.3% | 74.1% / 91.1% |
| Vote (8 m), spots rule, pieces by make-up | 466,723 | 84.3% | 2.8% / 4.4% | 37.7% / 17.6% | 10.3% | 74.1% / 91.1% |

What this shows:

1. **The spots rule removes far copies without touching measured surface.** It deleted 114,011 points (17%) and ARCore depth coverage stayed at 84.9%. Surface behind far tracked points fell by a quarter (14.0% to 10.7%). Seen from above, what it removes is mostly outer copies of walls around the room's edge: the left wall beside the first standing spot drops from three or four parallel copies to one or two (`top_slices/left_wall.png`). It also kept the staircase: stair coverage fell 0.7 points, against 6.1 points for Task122's combination.
2. **It barely changes the door.** Behind the door's tracked points, surface fell only from 42.6% to 40.7%. At door height the farthest streak along frame 65's line of sight goes, as with Task122's combination, but a fan of layers within about 0.4 m of the door stays (`top_slices/door.png`). The 6° and 2.0 m versions change the door by under 1 point. So the remaining door layers are not kept by near views or narrow angles. Views from other spots measured them at the same depth, within the agreement margin of 5% (about 22 cm at 4.5 m).
3. **By the behind score, "seen by 5 frames" clears more at the door** (30.3% against 40.7%), but it deletes 2.3 times as many points (261,071 against 114,011) and more of the stairs and door surface.
4. **Pieces by make-up added almost nothing:** 2,054 more points (0.3%). Pieces where most points fail the spots rule are rare, so the rule's failures are scattered inside pieces that are mostly supported.
5. **Cost:** the spots rule took 2.2 s for 134 frames against the whole surface, about 16 ms per frame. Live, each update would check its newest view only, as planned for the vote. The piece test took 1.0 s once on 676,853 points.

Filtering can only remove what views disagree about. The spots rule finds disagreement between standing spots and removes it, but at the door several spots agree on wrong sizes. This supports the Task122 conclusion: the door echoes need consistent far depth at fusion time.

**Viewer and pictures (local only; they embed household photos).** `python -B -m tools.demos.cleanup_scene --trial outputs/denoise_trial_093913_v7 --session <v2 session> --out <page.html> --kept wide --views 65 420`. `--views` adds camera buttons for the door (frame 65) and stair (frame 420) views; the table gained the within-10 cm and behind columns. Pages: `outputs/denoise_trial_093913_v7/viewer/redmi-room-15oct-cleanup-wide.html` (spots rule alone) and `...-vote_far_wide_pieces.html` (vote, spots rule and pieces). Both loaded in headless Chromium with software rendering, with no console errors or network requests. Camera shots from frames 65 and 420, and from above, each as opened, with removals in red and with removals hidden: `outputs/denoise_trial_093913_v7/camera_shots/<variant>/`. Top-down slices 0.9-1.5 m above the floor: `outputs/denoise_trial_093913_v7/top_slices/`. From frame 65's own camera the echo layers lie behind one another along the line of sight and hide each other; the top views show them.

### Clean-up tuner page (Task125)

The owner asked for every clean-up setting on a slider, starting from the raw room, to tune chain linking by eye. Two steps build it:

    python -B -m src.live.cleanup_attributes --session <v2 session> --out <folder>
    python -B -m tools.demos.cleanup_tuner --attributes <folder> --session <v2 session> --out <page.html> --views 65 420

The first fuses the room under `room_build` rules (`raw.ply`, no clean-up) and stores, per point, the evidence the depth-map stages test: frames measuring it, see-through share of the weighted vote, nearest measured depth, second-widest angle between measuring views, and mean distance to its 20 nearest neighbours. The second builds one offline page (17.3 MB for 676,853 points; local only, it embeds photos). Each stage has an on/off tick and each parameter a slider with a description: vote share; minimum frames; spots angle and trusted distance; outlier spread; radius and neighbour count; and for chain linking the link distance, neighbours needed to extend a chain (DBSCAN's `min_points`; 1 is plain chain linking), maximum normal difference for a link (PCL's rule), minimum piece size, and how many of the largest pieces to keep (2DGS's rule). Radius outliers and chain linking run in the page on the raw points (1-3 s per change in headless Chromium without a GPU).

**Check against the trial.** Set to each trial's settings, the page kept the same number of points to within 0.13%: "seen by 3" exactly (548,722), chain linking at 5 cm 663,949 against 663,964, at 3 cm 630,272 against 630,389, the vote 577,276 against 576,767, and the spots rule 563,580 against 562,842. The small gaps come from storing evidence in 8 and 16 bits.

**Chain linking on this room, from the page** (minimum piece 1,000 points):

| Link distance | Plain chain (1 neighbour) | 10 neighbours (trials) | 20 neighbours |
|---|---|---|---|
| 2.0 cm | 24% of points kept; largest piece 13.5% | 0.5% kept | 0% kept |
| 2.5 cm | 94% kept; largest 87.6% | 48% kept | 1.7% kept |
| 3.0 cm | 96% kept; largest 91.0% | 93% kept | 32% kept |
| 4.0 cm | 98% kept; largest 95.0% | 97% kept | 86% kept |

Fused points sit about 2 cm apart, so the room falls apart between 2 and 3 cm, and the neighbour count matters as much as the distance. Which setting removes echoes without removing real surface has to be judged by eye; the numbers only show how strongly the room holds together.

Local outputs: `outputs/cleanup_tuner_093913/{raw.ply,attributes.npz,redmi-room-15oct-tuner.html}`.

### Owner's setting in the room build (Task126)

The owner's result from the tuner, 8 November 2026: the visibility vote at 0.5, then chain linking at 5 cm with 7 neighbours, normal rule off, keeping the 50 largest pieces of at least 5,000 points (7,079 in the pasted settings). It kept 561,317 of 676,853 points. No other stage or parameter made a visible difference. The owner called this a key stage and asked for it in the pipeline at once, and for pieces to be joined surface regions, like touching splats or 2D contours, rather than chains of points.

Checked on the tuner's raw room with Open3D 0.19 on the CPU, after the vote (577,276 points):

| Rule | Points kept | Pieces kept | Second-largest piece | Time |
|---|---:|---:|---:|---:|
| DBSCAN, 5 cm, 7 neighbours (the tuner setting) | 561,318 | 1 | 4,377 | 1.04 s |
| DBSCAN, 5 cm, 1 neighbour (plain chain) | 563,460 | 1 | 4,385 | 1.05 s |
| Radius outliers (5 cm, 16), then the tuner setting | 545,884 | 1 | — | 0.31 s + 1 s |
| Touching filled cells, 2 cm | 554,551 | 1 | 4,311 | 0.13 s |
| Touching filled cells, 3 cm | 571,204 | 1 | 1,649 | 0.07 s |
| Touching filled cells, 5 cm | 574,555 | 1 | 2,320 | 0.03 s |

What this shows:

- **The rule keeps one piece on this walk.** The whole room joins into one piece, and the second-largest is under 5,000 points at every setting, so the cap of 50 never comes into play and 5,000 against 7,079 makes no difference. The minimum size does the work.
- **Chain linking already contains a radius-outlier test.** DBSCAN's neighbour minimum is a radius-outlier rule. Here it removes only 2,142 points (7 neighbours against 1). The separate radius stage at 16 neighbours removes 14,951 points, mostly inside the room (only 3,764 of them are also outside the kept piece), so it thins real surface rather than removing floaters. Neither is needed.
- **Touching cells give nearly the same room, 8 times faster.** Joining filled 2 cm cells (`scipy.ndimage.label` with 26 neighbours) keeps all but 6,807 of the tuner's points and adds 40. Those 6,807 points sit in small pieces (median 106 points), a median of 8 cm and at most 25 cm from the room, that 5 cm point chains hang onto it.
- **Bigger cells join more.** As with wider splats, 3 and 5 cm cells glue nearby specks onto the room (571,204 and 574,555 kept). The cell size is the one setting, and the 2 cm fusion voxel is the default.

`room_build` now runs the vote and touching-cell pieces at 2 cm. On the 15 October walk it kept 554,067 of 676,855 points (vote −100,086, pieces −22,702) in 2.41 s for the vote over 134 frames and 0.15 s for pieces. The vote here uses each frame's sized depth, not 8-bit stored evidence, so its count differs slightly from the tuner's (576,769 against 577,276 after the vote). The dense cell grid uses one byte per cell plus a 4-byte label: 12 million cells (about 60 MB) for this room at 2 cm; a 10 × 3 × 10 m room is 37.5 million.

Local outputs: `outputs/room_build_clean_up_093913/{surface.ply,raw_surface.ply,summary.json,redmi-room-15oct-clean.html}` (the viewer is local only; it embeds photos).

Local outputs: `outputs/denoise_trial_093913_v7/{results.json,<variant>.ply}` (all 22 variants, Task124; earlier variants give the same scores as before), `outputs/denoise_trial_093913_v5/` (Task122's 16 variants), `outputs/denoise_trial_093913_v2/` (Task120), and the first run in `outputs/denoise_trial_093913/`. It lacks the two "beyond 2.5 m" rows, has the same numbers for the rest, and adds one more variant (tracked-point size in every cell, masks and vote: blocked 1.2% and 4.2%, 119,990 points below the floor). Tests: `src/live/tests/test_clean.py` and `test_denoise_trial.py`.

## Order to try

1. **Put the visibility vote in the live processor:** each update votes with its newest view against the current surface (about 17 ms). Check on ICL-NUIM, where the true surface is known, that it removes floaters and not real surface.
2. **Size beyond ARCore's reach with a size that varies with distance:** fit, per frame, size against learned depth from ARCore depth pixels near and tracked points far, instead of one fallback for all cells. Score it at held-out tracked points as above, and against the floor.
3. **Find the floor band's cause.** Edges and side-on pixels are not it. Candidates: sizing in floor cells ARCore depth misses, and how the 8 × 6 size grid blends across the floor. Plane snapping comes after the cause is known.
4. **Multi-view stereo between frames along ARCore's path** for depth beyond 2.5 m: the one route that gives consistent far depth without a new sensor, and the likely fix for the door and stair echoes (Task122). Measure its CPU cost first. [Mobile3DRecon](../dense_surface_fusion/mobile3drecon.md) published one figure: two reference keyframes about 0.6 m away, Census matching and semi-global matching, 48 ms per keyframe on one core of a 2018 phone chip (Snapdragon 710), before its learned clean-up.
5. **The spots rule beside the vote** (Task124): it removes far copies, mostly outer wall copies, with no loss of ARCore-measured surface and keeps the staircase. It does not fix the door echoes. Live, each update checks its newest view, about 16 ms.
6. **Observation count (seen by 3-5 frames) for the floor band,** tested in Task122; live it needs per-voxel counts, which `VoxelBlockGrid` keeps.
7. **Floating-piece removal: done in the room build (Task126)** at the owner's setting, after the vote: the 50 largest touching-cell pieces of at least 5,000 points. Pieces by make-up (Task124) added 0.3% more removals and are not worth their cost here.

A clean-up step cannot choose between two wrong copies, so sizing fixes come first where sizing is the cause (Tasks116 and 117).

## Papers in `papers/`

PDFs are gitignored and stay on this machine.

| File | What it is |
|---|---|
| [xu2025_pixel_perfect_depth.pdf](papers/xu2025_pixel_perfect_depth.pdf) | Pixel-Perfect Depth (NeurIPS 2025): why depth models produce flying pixels; an edge-aware point-cloud metric |
| [watson2020_learning_stereo_from_single_images.pdf](papers/watson2020_learning_stereo_from_single_images.pdf) | Learning Stereo from Single Images (ECCV 2020): flying pixels found by a Sobel threshold on disparity |
| [barron2016_fast_bilateral_solver.pdf](papers/barron2016_fast_bilateral_solver.pdf) | The Fast Bilateral Solver (ECCV 2016): edge-aware depth smoothing guided by the photo |
| [wu2022_distdepth_indoor.pdf](papers/wu2022_distdepth_indoor.pdf) | Toward Practical Monocular Indoor Depth Estimation (CVPR 2022): near-field indoor scenes are hard for monocular depth |
| [yang2020_mobile3drecon.pdf](papers/yang2020_mobile3drecon.pdf) | Mobile3DRecon (IEEE TVCG 2020): live meshing on mid-range phones; confidence filtering before fusion and visibility-conflict removal in the volume |
| [oleynikova2017_voxblox.pdf](papers/oleynikova2017_voxblox.pdf) | Voxblox (IROS 2017): 1/z² TSDF weights with drop-off behind the surface; CPU real time |
| [schoenberger2016_pixelwise_view_selection.pdf](papers/schoenberger2016_pixelwise_view_selection.pdf) | Pixelwise View Selection (ECCV 2016, COLMAP's stereo): keep depth with support from at least 3 views |
| [vogiatzis2011_video_realtime_mvs.pdf](papers/vogiatzis2011_video_realtime_mvs.pdf) | Video-based, real-time multi-view stereo (Image and Vision Computing 2011): per-pixel Gaussian inlier and uniform outlier model |
| [pizzoli2014_remode.pdf](papers/pizzoli2014_remode.pdf) | REMODE (ICRA 2014): per-pixel depth filter that rejects estimates by their uncertainty |
| [ling2018_probabilistic_dense_reconstruction.pdf](papers/ling2018_probabilistic_dense_reconstruction.pdf) | Probabilistic Dense Reconstruction from a Moving Camera (IROS 2018): inlier probability carried into a weighted TSDF |
| [keller2013_point_based_fusion.pdf](papers/keller2013_point_based_fusion.pdf) | Point-based fusion (3DV 2013): stable after 10 observations; unstable and free-space-violating points deleted |
| [whelan2015_elasticfusion.pdf](papers/whelan2015_elasticfusion.pdf) | ElasticFusion (RSS 2015): surfel map with confidence and a time window |
| [splietker2021_directional_tsdf.pdf](papers/splietker2021_directional_tsdf.pdf) | Directional TSDF (ECMR 2021): carving free space, skipped near depth jumps |
| [guo2022_manhattan_sdf.pdf](papers/guo2022_manhattan_sdf.pdf) | ManhattanSDF (CVPR 2022): plane constraints on floor and wall regions |
| [zhang2025_point_cloud_denoising_survey.pdf](papers/zhang2025_point_cloud_denoising_survey.pdf) | Deep Learning for Point Cloud Denoising: A Survey (arXiv 2508.11932) |
| [wang2025_point_cloud_denoising_survey.pdf](papers/wang2025_point_cloud_denoising_survey.pdf) | A Survey of Deep Learning-based Point Cloud Denoising (arXiv 2508.17011) |
| [turkulainen2025_dn_splatter.pdf](papers/turkulainen2025_dn_splatter.pdf) | DN-Splatter (WACV 2025): depth and normal priors for indoor splats |
| [xiong2023_sparsegs.pdf](papers/xiong2023_sparsegs.pdf) | SparseGS (3DV 2025): depth priors and floater pruning for splats |
| [yang2026_tidi_gs.pdf](papers/yang2026_tidi_gs.pdf) | TIDI-GS (arXiv 2601.09291): indoor floater pruning by multi-view evidence |
| [wang2025_efa_gs.pdf](papers/wang2025_efa_gs.pdf) | EFA-GS (Cyberworlds 2025): floaters traced to under-trained splats |
| [philip2023_floaters_no_more.pdf](papers/philip2023_floaters_no_more.pdf) | Floaters No More (EGSR 2023): near-camera floaters in radiance fields |
| [sayed2022_simplerecon.pdf](papers/sayed2022_simplerecon.pdf) | SimpleRecon (ECCV 2022): learned depth from several posed frames, then TSDF fusion |
| [jain2024_gaussiancut.pdf](papers/jain2024_gaussiancut.pdf) | GaussianCut (NeurIPS 2024): graph cut over a k-nearest-neighbour graph of Gaussians |
| [chang2025_roodi.pdf](papers/chang2025_roodi.pdf) | ROODI (arXiv 2503.10256): statistical outlier removal on Gaussians with Wasserstein neighbour distances |
| [shivottam2026_cleangs.pdf](papers/shivottam2026_cleangs.pdf) | CleanGS (arXiv 2601.00913): keeps Gaussians that two of three object masks cover |
| [chazal2013_tomato.pdf](papers/chazal2013_tomato.pdf) | ToMATo (J. ACM 2013): clustering that merges pieces whose density peak has low prominence |
| [tateno2017_cnn_slam.pdf](papers/tateno2017_cnn_slam.pdf) | CNN-SLAM (CVPR 2017): network depth fused with direct monocular SLAM depth |

Not stored: Nguyen et al. 2012 (IEEE, paywalled) and Valentin et al. 2018 (ACM, paywalled); links are in the tables. Merrell et al. 2007, TANDEM and FrozenRecon are in [dense_surface_fusion/papers](../dense_surface_fusion/papers/).
