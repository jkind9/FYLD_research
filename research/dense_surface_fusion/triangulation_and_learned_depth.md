# Combining triangulation with learned depth

**Question (owner, 8 November 2026):** should COLMAP-style triangulation be combined with the project's depth maps?

**Answer: yes.** Published live systems combine the two, and the project already does in a small way. The common pattern has three parts:

- Triangulate depth wherever the surface has texture and the camera has moved far enough between views.
- Let learned depth fill blank surfaces.
- Take real size from the tracker's poses.

The project's gap is beyond 2.5 m, where it has only ARCore's sparse tracked points. Triangulating between frames 0.5-1 m apart along ARCore's recorded path would add far depth that agrees with the path, and it runs on a CPU.

**Update, 12 November 2026.** The product will not use ARCore ([owner decision 10](../../PROJECT_PLAN.md#owner-decisions-in-force)).

- **Triangulation now carries all of the size.** It runs along the open tracker's path (Basalt first), whose metres come from the motion sensors. It covers near surfaces as well as far, because ARCore depth no longer sizes anything under 2.5 m. Near is the easy case: a short baseline is enough close up.
- **First trials may stand in ARCore's path.** Until the Redmi is calibrated and Basalt runs on its walks ([Task103](../../task_list/open/103_measure_redmi_camera_and_imu_calibration_from_owne.md), [Task104](../../task_list/open/104_compare_open_trackers_and_surfaces_on_the_same_red.md)), the method can be developed on ARCore's recorded path for existing walks. Public visual-inertial recordings with reference poses can also serve.
- **ARCore depth and tracked points are a comparison only.** They are not a sizing target in any version meant for the product.
- **Where to find code.** Open templates and parts for every step are in [depth_without_arcore_2026-11-12.md](../visual_inertial_odometry/depth_without_arcore_2026-11-12.md): hloc's known-pose triangulation, SGM code, weighted and distance-aware sizing, and Any2Full.

Terms used here:

- **Triangulation**: placing a point in 3D from where it appears in two or more images whose camera poses are known.
- **Baseline**: how far the camera moved between two such images. For the same matching error, depth error grows with distance squared divided by the baseline.
- **Sparse triangulation**: a few hundred to a few thousand distinctive points (corners), as in COLMAP's triangulator or ARCore's tracked points.
- **Dense triangulation (multi-view stereo, MVS)**: a depth for most pixels, found by trying many depths per pixel against neighbouring frames (a *plane sweep*).
- **Learned depth**: a network's depth from one image (Depth Anything here). It has good shape but no reliable size.
- **Sizing**: scaling learned depth so it agrees with measured depth (`sitescan/scale/fit.py`, in an 8 × 6 grid of cells).

## What the project has, by distance

| Depth source | How it is made | Where it works | Measured here |
|---|---|---|---|
| ARCore raw depth | ARCore triangulates the live frame against a recent keyframe ("depth from motion"), 160 × 90 pixels | Near: 95% of its confident depth is under 2.54 m | Sizes learned depth; within 5% of tracked points up to 3 m (Task117) |
| ARCore tracked points | ARCore's own sparse triangulation | Reaches 3-4 m. About 19 points per frame on the first Redmi test walk; 1,173 point views beyond 3 m on the 15 October walk | As sizing targets, far depth moved from 16% to 5% too near. One size per frame also pushed the floor down (Task120) |
| Learned depth (Depth Anything V2) | A network, one image at a time | Everywhere, blank walls included | Shape 8-16 cm off even with perfect size and poses; beyond 3 m still about 15% too near after sizing (Task117) |
| Sparse COLMAP triangulation along ARCore's path | `point_triangulator` with known poses (pycolmap 4.2.1 is in the repository's `.venv`), frames paired by camera distance | Wherever corners are seen from spots far enough apart | Not tried on the Redmi. On TUM, learned depth sized to SfM points came within 8-27 mm of the best possible (Task72) |
| Dense multi-view stereo along ARCore's path | A plane sweep between keyframes, as in [Mobile3DRecon](mobile3drecon.md) | Textured surfaces, near and far | Not tried |

The first two rows are triangulation already: ARCore does it on the phone. What they lack is baseline. ARCore depth comes from a hand-held phone against a recent keyframe, so its reach is short, and the tracked points are few.

## How published systems combine the two

| System | Triangulated part | Other part | How they are combined |
|---|---|---|---|
| [Mobile3DRecon](mobile3drecon.md) (2020, phone CPU) | Dense: semi-global matching (SGM) against two keyframes about 0.6 m away | Small clean-up network | Triangulate first, drop pixels it is unsure of, then the network removes leftover noise |
| [Newcombe and Davison](live_dense_reconstruction_2010.md) (2010) | Sparse: the tracker's points (PTAM) | A rough surface fitted to those points | The sparse points give a first surface; dense optical flow then corrects each pixel along its camera ray |
| [CNN-SLAM](../surface_denoising/papers/tateno2017_cnn_slam.pdf) (2017) | Semi-dense depth from direct monocular SLAM | Network depth per keyframe | Each pixel takes the triangulated depth where SLAM has one, and the network's where SLAM fails, such as blank walls |
| [SfM-guided monocular depth](papers/sfm_guided_monocular_depth_2025.pdf) (2025) | SfM points | Single-image depth | Scale and shift fitted per frame to the points with RANSAC, then TSDF fusion |
| [TANDEM](papers/koestler2021_tandem.pdf) (2021) | Learned multi-view stereo over posed keyframes | A TSDF built from it | Tracking runs against depth rendered from the TSDF |
| [SimpleRecon](../surface_denoising/papers/sayed2022_simplerecon.pdf) (2022) | A plane-sweep cost volume over posed keyframes | A 2D network reads the cost volume | The network does the matching; TSDF fusion follows |
| ARCore depth ([Valentin et al. 2018](https://research.google/pubs/depth-from-motion-for-smartphone-ar/)) | Matching between two frames on the phone | A smoothing solver that fills gaps | Sparse matches made dense. This is already the project's near depth |
| [Prompt Depth Anything](../depth_estimation/papers/prompt_depth_anything_2412.14015.pdf) (2025) | Low-resolution metric depth fed in | The network | The network reads the sparse depth. Tested here with SfM points: no gain (Task79) |

So there are two ways to combine:

- **A. Triangulated points as sizing targets for learned depth.** The project does this now with ARCore depth and tracked points. It is cheap and fits the current code. It keeps learned depth's shape error, and it needs targets at every distance, so that the size can change with distance (Task120's conclusion).
- **B. Triangulated depth fused directly where it is confident, learned depth only where triangulation has no answer.** Mobile3DRecon and CNN-SLAM work this way. It removes the 8-16 cm shape error wherever triangulation works, at the cost of a plane sweep per keyframe.

## Proposed order, all on the CPU

1. **Sparse first (way A).** On the 15 October walk:
   - Triangulate features along the tracker's path with pycolmap's known-pose triangulator, pairing frames 0.3-1 m apart. That means the open tracker's path, or ARCore's recorded path only as a development stand-in until the tracker runs on the Redmi (update above).
   - Keep COLMAP's checks: two-view geometry, at least 3 views, a minimum angle between rays and a small reprojection error.
   - Use the points as sizing targets with a size that varies with distance, for example a scale and shift per frame as the 2025 SfM-guided paper fits.
   - Score beyond 3 m against held-out triangulated points and, as a comparison on existing walks, ARCore tracked points, with `python -B -m research.evaluation.depth_check`. Look at the hallway door. Tape-measured distances are the reference once the next recording round has them.
2. **Dense next (way B).**
   - Plane sweep with Census costs and SGM between keyframes about 0.6 m apart, as in Mobile3DRecon.
   - Keep the confident pixels, fill the rest with sized learned depth, and fuse.
   - Score as in step 1, plus the floor band.
3. **Live version.** Both steps use only the last few keyframes, so either can run in the live loop if its cost holds. Mobile3DRecon's 48 ms per keyframe on one phone core suggests the dense step can.

## Things to watch

- **Score with points the method did not use.** If tracked points size the depth, score with other tracked points or with COLMAP points.
- **Blank walls give no triangulation.** Learned depth must fill them, which is why combining beats replacing.
- **Pose error becomes depth error.** Triangulation trusts the tracker's poses. Pair frames within one fragment (about 10 s on one anchor or keyframe), so that a path correction cannot split a point between two pose sets.
- **Wide baselines change how a surface looks.** Frames 0.6 m apart see a surface from different angles. Patch codes such as Census tolerate less change than SIFT features, which is why Mobile3DRecon limits the difference in viewing direction to about 10°.
- **It avoids stale depth.** Triangulation reads the images, not ARCore's depth maps, so the 4.4 s old depth maps that doubled the cushion (Task116) cannot affect it.
- **Moving people break both methods.** Mobile3DRecon deletes voxels a new view sees through, which removes a person who stood still and then left.

Related: [COLMAP parts that fit ARCore's path](../structure_from_motion/colmap.md#colmap-parts-that-fit-a-pipeline-that-already-has-arcores-path), and [getting far depth right](../surface_denoising/README.md#getting-far-depth-right-what-other-systems-do).
