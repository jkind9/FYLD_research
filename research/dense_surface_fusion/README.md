# Dense surface fusion: floating and doubled surfaces

Why one object can appear twice in a fused room, and what removes the extra copy. Started 8 November 2026 (Task116) after the 15 October room showed the sofa and its red cushion in two places.

Terms used here:

- **Fusion**: merging many per-frame depth images, each placed by its camera pose, into one surface. This project uses Open3D's signed-distance volume (TSDF).
- **Fragment**: one TSDF volume holding about 10 s of frames, moved as a unit when ARCore corrects its anchor (`src/live/fragments.py`).
- **Sizing**: scaling learned depth to metres. `src/live/room_build.py` fits it to ARCore raw depth in an 8 × 6 grid of cells. A cell with fewer than 20 ARCore pixels takes the frame's median size (the **fallback**).
- **Stale depth**: an ARCore depth map whose timestamp is older than the image it is paired with.

## What the 15 October walk showed

Measured with `python -B -m src.live.landmark_probe`. For each frame, it places the red cushion's pixels in the world with ARCore depth and with the fused learned depth.

1. **The two copies come from one standing spot, not two.** Only frames 669-728 see the cushion. The phone moved about 15 cm across them, and all of them fall in fragment 2.
2. **Frames 669-691 carried depth maps 4.35-4.42 s old.** These are the only 9 of 147 depth maps more than 0.2 s old; the rest are 7-40 ms old. Learned depth sized to those maps put the cushion at about (0.50, 0.16, -1.00) m, 1.57 m from the camera.
3. **Frames 699-725 had fresh depth** and put the cushion at about (0.04, -0.09, -0.60) m, 2.26 m from the camera. That is 0.68 m from the first copy, almost all of it along the line of sight.
4. **ARCore's tracked feature points agree with the fresh copy.** These points come from ARCore's tracking, not its depth maps. Those landing on the cushion converge near (-0.07, -0.19, -0.42) m: about 0.2 m from the fresh copy and about 0.9 m from the stale one.
5. **The fused surface keeps both copies:** 112 red points at the stale position and 1,684 near the fresh one.
6. **The fallback is the normal case.** In the median fused frame, 66% of grid cells used the frame-median size, and 110 of 144 frames had at least half their cells on it. It did not cause this duplicate, but it is a likely source of smaller offsets: the fresh copy sits 0.2 m nearer than the tracked points, and ARCore depth had no pixels on the cushion in those frames.

Nothing in `src/live` checked depth age before Task116. `room_build` now skips depth more than 0.1 s older than its image (`MAX_DEPTH_AGE_S`). The live processor (`src/live/processor.py`) still uses depth of any age.

The rebuild confirmed the cause. With the rule, 10 frames were skipped and 134 fused, against 144 before. Within 25 cm of the stale copy's centre, the surface went from 121 red points to 0, and from 1,294 points of any colour to 77. The fresh copy kept all 1,277 red points. Viewers: `outputs/capture_task115_093913/viewer/redmi-room-15oct-cutaway.html` (before) and `outputs/capture_task116_093913/viewer/redmi-room-15oct-fresh-depth.html` (after), both local only.

## The doors echo too (Task117)

After the stale-depth fix, the owner measured the hallway door repeated as four parallel layers along the line of sight, 0.44 m, 0.5 m and 0.5 m apart, with the farthest layer the true surface.

- **ARCore depth does not reach that far.** Over the 134 fresh depth maps, confident ARCore depth has a median of 1.58 m. 95% is under 2.54 m and 0.8% is beyond 3 m. `room_build` fuses learned depth out to 4.0 m, so a surface 3-4 m away is always sized by the frame-median fallback.
- **The door is about 4.5 m from the first standing spot.** That distance comes from 13 ARCore tracked points on the doorway in frame 65. In every first-spot frame, the grid cells covering the door held 0 ARCore depth pixels.
- **The far frames put the door too near, by different amounts.** Sampled points near the camera-to-door line (`frames.npz`) sit 0.5-2.2 m nearer than the door in first-spot frames (fragments 0 and 1). Frames taken while walking up to the door (450-510) sit 0.0-0.4 m nearer. Each frame's median comes from whatever near objects fill its view, so each puts the door at a different depth.

`python -B -m src.live.depth_check` compares the fused depth (learned depth times grid size) with ARCore's tracked points over all 134 fused frames (11,821 point views). A ratio of 1.00 is right; below 1 is too near.

| Distance | Cells with their own ARCore size: median ratio (middle half) | Fallback cells: median ratio (middle half) |
|---|---|---|
| 0-1 m | 1.04 (1.00-1.07), 292 points | 1.10 (1.04-1.17), 38 points |
| 1-2 m | 1.02 (0.97-1.06), 4,192 | 1.00 (0.95-1.06), 705 |
| 2-3 m | 0.98 (0.94-1.02), 2,851 | 0.94 (0.85-1.01), 2,570 |
| 3-4 m | 0.86 (0.77-0.92), 142 | 0.84 (0.72-0.97), 1,031 |

Up to 3 m, cells with their own ARCore size are within 5%. Beyond 3 m, both kinds are about 15% too near. Fallback cells also spread widely there: at 3.5 m their middle half spans 2.5-3.4 m, enough for layers 0.5 m apart.

Three rebuilds of the walk, all without stale depth, viewed from frame 65's camera and from above:

| Build | Splats at 3 cm | Hallway door |
|---|---:|---|
| 4.0 m, all cells (Task116) | 196,914 | Several white and blue layers |
| 4.0 m, only cells with their own ARCore size (`--supported-only`) | 73,265 | One door frame, but the stairs, TV wall and ceiling are gone |
| 2.5 m, all cells | 151,032 | Stairs and TV kept; the doorway still smears |

So the echoes come from sizing in cells without ARCore depth, mostly beyond what ARCore measures. Leaving those cells out removes the echoes and most of the room with them. A distance limit alone does not remove them. The next step is a size source for those cells: ARCore's tracked points, which reach 3-4 m, or the surface already built.

## Options, and how each fits this failure

| Option | Source | What it does | Fits CPU, live, at least 1 fps? | Would it fix the stale-depth copy? |
|---|---|---|---|---|
| Reject stale depth | [ARCore Raw Depth](https://developers.google.com/ar/develop/java/depth/raw-depth) says to compare the depth timestamp with the frame's to tell new depth from old | Skip a depth map older than one depth period | Yes; one comparison per frame | Yes, by removing its cause |
| Size against the surface already built | [TANDEM](papers/koestler2021_tandem.pdf) tracks against depth rendered from its own TSDF; the [Dong et al. CVPR 2023 supplement](https://openaccess.thecvf.com/content/CVPR2023/supplemental/Dong_Fast_Monocular_Scene_CVPR_2023_supplemental.pdf) solves each frame's scale against the model | Project the fused points into the new frame and add them as sizing targets, so a new frame agrees with what is already there | Yes; projecting about 700,000 points is cheap. An early error can spread, so ARCore depth should win where present | Partly: it would have pulled the stale frames toward the fresh surface only if fresh frames came first |
| Per-cell local scale map | [FrozenRecon](papers/xu2023_frozenrecon.pdf) (ICCV 2023) fits a global scale and shift plus a local scale map per frame, jointly over all frames | The same idea as the 8 × 6 grid, solved across frames | No: whole-clip optimisation, so offline reference only | Not directly |
| Robust per-frame fit | [SfM-guided monocular depth](papers/sfm_guided_monocular_depth_2025.pdf) (2025) fits scale and shift per frame with RANSAC before TSDF fusion | Ignores outlier targets in the fit | Yes | No: every target in a stale map is wrong in the same way |
| Visibility-based fusion | [Merrell et al. 2007](papers/merrell2007_visibility_fusion.pdf) keeps a depth estimate only if its support outweighs free-space and occlusion violations in other views; up to 25 fps on a GPU | Removes surfaces that other views see through | CPU speed untested | Here, yes but narrowly: the stale copy is nearer, so the 10 fresh frames see through it, against 9 stale frames supporting it. If the wrong copy were the farther one, nothing would see through it. It needs a confidence weight, such as ARCore support, to choose reliably |
| Statistical outlier removal | Open3D `remove_statistical_outlier` | Deletes isolated points | Yes | No: the stale copy is a solid 112-point patch, not specks |
| Fragment alignment (ICP) | Open3D reconstruction system ([open3d_rgbd note](../camera_tracking_and_slam/open3d_rgbd.md)) | Registers overlapping fragments rigidly | Yes, periodically | No: both copies are in one fragment |
| Depth that uses ARCore depth as input | [Prompt Depth Anything](../depth_estimation/papers/prompt_depth_anything_2412.14015.pdf) (CVPR 2025), fed low-resolution metric depth | Learned depth guided by the sensor map | 2.2-2.6 fps on CPU (Task79) | No: a stale prompt gives the same wrong size. Task79 used SfM points as the prompt, not ARCore depth, and found no gain |
| Depth consistent over time | [Video Depth Anything](../depth_estimation/papers/video_depth_anything_2501.12375.pdf) (CVPR 2025), 32-frame windows | Keeps relative depth steady across frames | No: 0.77 fps on CPU (Task65), below the 1 fps minimum | No: sizing still comes from ARCore depth |

## Order to try

1. Reject stale depth (done in `room_build`; the live processor still needs it).
2. Count how much of the remaining doubling is fallback sizing: rebuild with fallback cells left out and compare the walls.
3. Size new frames against the surface already built, with ARCore depth taking priority.
4. Only then consider surface clean-up, weighted by how well each copy was supported. Clean-up methods and a proposed clean-up stage are in [research/surface_denoising](../surface_denoising/README.md).

## What other systems do

[Getting far depth right](../surface_denoising/README.md#getting-far-depth-right-what-other-systems-do), in research/surface_denoising (8 November 2026), compares six approaches to depth beyond the sensor's range: longer-range sensors, triangulation between frames, learned multi-view depth (SimpleRecon), learned depth refined by geometry (CNN-SLAM, TANDEM), near-weighted fusion (Voxblox) and whole-clip solving.

## Live reconstruction from one camera: three earlier systems

Three papers supplied by the owner on 8 November 2026, each with its own note. Each tracks the camera live and builds a 3D shape from an ordinary camera, with no depth sensor.

| System | Depth from | Merging | Hardware and speed | Code | What this project can take |
|---|---|---|---|---|---|
| [Mobile3DRecon](mobile3drecon.md) (IEEE TVCG 2020) | Multi-view stereo between each keyframe and two earlier ones about 0.6 m away, with a confidence filter and a small clean-up network | Growing TSDF volume; voxels a new view sees through are deleted; only changed parts re-meshed | 2018 mid-range Android phones, one CPU thread: 70 ms depth and 31 ms mesh per keyframe on a Snapdragon 710 | None released | Far depth triangulated along the tracker's path, with a published phone CPU cost |
| [Newcombe and Davison](live_dense_reconstruction_2010.md) (CVPR 2010) | A rough surface fitted to the tracker's points, corrected per pixel along camera rays by optical flow against predicted views | Local meshes side by side; new points near existing surface dropped | PC with two GPUs; desk scale | None released; OpenDTAM is a third-party version of the 2011 successor | Predict new views from the surface already built; correct learned depth along each ray |
| [Prisacariu et al.](mobile_object_reconstruction_2015.md) (IEEE TVCG 2015) | No depth: one object's outline in each frame | Inside/outside probabilities in a 128³ voxel volume | iPhone 5s: tracking 31 fps, shape update 0.5 s | Phone code not released; its PWP3D tracker is downloadable | Outer shape of counted objects from their masks; not for rooms |

Mobile3DRecon is the one to act on. Step 4 of the [surface_denoising order](../surface_denoising/README.md#order-to-try), multi-view stereo along ARCore's path, said to measure its CPU cost first. Mobile3DRecon published one: 48 ms per keyframe on one 2018 phone core, before its learned clean-up.

**Triangulation combined with learned depth.** [triangulation_and_learned_depth.md](triangulation_and_learned_depth.md) answers the owner's question of 8 November: should COLMAP-style triangulation be combined with the depth maps? Yes. It lists the project's five depth sources by distance and eight published systems that combine triangulated and learned depth. It then sets out a CPU order to try: sparse points triangulated along ARCore's path as sizing targets first, then dense multi-view stereo fused where it is confident.

## Papers in `papers/`

PDFs are gitignored and stay on this machine. Mobile3DRecon's PDF is in [research/surface_denoising/papers](../surface_denoising/papers/yang2020_mobile3drecon.pdf).

| File | What it is |
|---|---|
| [koestler2021_tandem.pdf](papers/koestler2021_tandem.pdf) | TANDEM (CoRL 2021): monocular tracking against depth rendered from a TSDF built from learned depth |
| [xu2023_frozenrecon.pdf](papers/xu2023_frozenrecon.pdf) | FrozenRecon (ICCV 2023): global and local scale maps per frame for a frozen depth model, solved over the whole clip |
| [sfm_guided_monocular_depth_2025.pdf](papers/sfm_guided_monocular_depth_2025.pdf) | Multi-view Reconstruction via SfM-guided Monocular Depth Estimation (arXiv 2503.14483): RANSAC scale-and-shift per frame before TSDF fusion |
| [merrell2007_visibility_fusion.pdf](papers/merrell2007_visibility_fusion.pdf) | Real-time visibility-based fusion of depth maps (ICCV 2007): stability test against free-space and occlusion violations |
| [newcombe2010_live_dense_reconstruction.pdf](papers/newcombe2010_live_dense_reconstruction.pdf) | Live Dense Reconstruction with a Single Moving Camera (CVPR 2010): rough surface from tracked points, corrected by optical flow ([note](live_dense_reconstruction_2010.md)) |
| [prisacariu2015_mobile_object_reconstruction.pdf](papers/prisacariu2015_mobile_object_reconstruction.pdf) | Real-Time 3D Tracking and Reconstruction on Mobile Phones (IEEE TVCG 2015): one object's shape from its outlines on an iPhone ([note](mobile_object_reconstruction_2015.md)) |

Prompt Depth Anything and Video Depth Anything are already in [research/depth_estimation](../depth_estimation/README.md).
