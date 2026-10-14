# Camera tracking: what is missing, and what to use instead of our tracker

Research of 13 October 2026, after Task65's full-length results. The owner asked three questions. Is better depth the missing piece for turning 2D video into 3D VR? Do we need to estimate the camera's position at all, or could keypoint or panorama fitting replace it? And is there something better than COLMAP? Paper results quoted here are the authors' claims. The only numbers measured by this project are in the first table.

The 22 papers are saved in the `papers/` folder of each topic, listed at the end with their sources.

## Short answer

1. **Better depth is not the main gap; the camera tracker is.** With the Kinect sensor's own depth, our tracker misses the true camera path on the TUM desk recording by 112 mm after a best fit. Published image-only systems miss by 16-18 mm on the same recording.
2. **Our tracker compares each frame with the previous one only.** It keeps no map, never refines earlier positions, and never corrects drift when the camera returns to a place. Every established system does all three.
3. **Other projects take the camera path from the images, or from the phone's own tracking.** Learned depth is used afterwards to fill in surfaces, resized each frame to the tracker's 3D points.
4. **3D reconstruction needs camera positions, but not a separate tracker.** Fitting keypoints across moving views is structure from motion, and the camera positions are unknowns in that same fit.
5. **Watching the video in 3D in a headset needs no camera path.** Per-frame depth and two redrawn views give stereo video.
6. **Newer methods than classic COLMAP exist, and COLMAP itself has absorbed two of them.** COLMAP 4 includes GLOMAP's global mapper and learned feature matching. On short indoor video with a known camera, published accuracy differences between modern methods (9-18 mm on these recordings) are small next to our 112 mm gap.

## Evidence from our own runs

Camera path error on Task65's full-length clips (every 2nd frame), rescored on 13 October from the saved positions. "First frame" is the project's current score, which pins the paths together at the first frame. "Best fit" lines up the whole path, the TUM benchmark's standard. "Best fit with size" also fits one overall size, the score published for image-only methods.

| Recording and depth | First frame | Best fit | Best fit with size | Fitted size |
|---|---:|---:|---:|---:|
| xyz, Kinect depth | 67 mm | 34 mm | 34 mm | 1.01 |
| xyz, Depth Anything raw | 1,359 mm | 962 mm | 177 mm | 0.06 |
| xyz, Depth Anything with overlap chain | 371 mm | 253 mm | 128 mm | 0.38 |
| xyz, Depth Anything with per-frame Kinect size (control) | 231 mm | 133 mm | 98 mm | 0.64 |
| desk, Kinect depth | 220 mm | 112 mm | 112 mm | 1.00 |
| desk, Depth Anything raw | 1,720 mm | 823 mm | 710 mm | 0.55 |
| desk, Depth Anything with overlap chain | 1,009 mm | 663 mm | 438 mm | 0.60 |
| desk, Depth Anything with per-frame Kinect size (control) | 1,553 mm | 517 mm | 401 mm | 0.70 |

Published monocular results on the same recordings, from the MASt3R-SLAM paper's Table 1. They use every frame and fit size, so they are close to, not identical with, our best fit with size:

| Method | fr1/desk | fr1/xyz |
|---|---:|---:|
| ORB-SLAM3 monocular | 17 mm | 9 mm |
| DPV-SLAM | 18 mm | 10 mm |
| DROID-SLAM | 18 mm | 12 mm |
| MASt3R-SLAM | 16 mm | 9 mm |

Three conclusions follow:

- **Size correction alone cannot fix the path.** Giving Depth Anything the exact Kinect size every frame still leaves 401 mm on desk. The current tracker turns any depth error into motion.
- **The current score roughly doubles the error.** It also hides the path's size: raw Depth Anything's xyz path is about 16 times too long.
- **The tracker is weak even with perfect depth.** On desk, 112 mm against 16-18 mm published.

## Do we need to estimate the camera position?

| Goal | Needs a camera path? | How others do it |
|---|---|---|
| Watch the walk in 3D in a phone headset | No | Per-frame depth, then a left and right view drawn by shifting near pixels more than far ones. The open-source iw3 tool (MIT) does this with Depth Anything V2 or Video Depth Anything. The viewer sees only what the camera saw, from where it was. |
| Look around from one spot, by turning the head | No, if the camera only turns in place | Panorama stitching. It assumes the camera rotates about one point or the scene is flat. Walking adds parallax, so near and far objects shift differently and the stitch shows doubled edges (LiftProj paper). A single-viewpoint panorama responds to head turning, not head movement (Serrano et al. 2019). |
| Measure the site, count objects, look around a 3D model | Yes | Structure from motion or SLAM solves camera positions and 3D points together. "Fitting keypoints across views" is this method: the camera positions are unknowns in the same fit. Feed-forward models such as VGGT and MapAnything output both in one pass, but they still estimate the positions. |

The project's goals are site measurement and object counts, so a camera path is required. The phone headset in the root README follows head turning only, so a stereo video is a cheap separate output (Task73).

## Alternatives to classic COLMAP

COLMAP 4.0 (2026) added GLOMAP's global mapper and learned matching: ALIKED features with LightGlue matching, run through ONNX. COLMAP 4.2 added LoMa learned matching and keeps each disconnected part of the scene as its own model. The project's installed pycolmap is 3.12.6, from before these changes. pycolmap 4.2.1 is on PyPI for Windows; that wheel has no CUDA, which suits the CPU-only rule.

| Method | Kind | Hardware | Accuracy evidence | Code / weights licence | Use here |
|---|---|---|---|---|---|
| COLMAP 4.2, incremental mapper | Classic structure from motion | CPU | The reference others measure against; can fail on hard video (56% failure rate on 360° video in ORBIT++) | BSD | Task67 baseline |
| COLMAP 4.2, global mapper (GLOMAP) | Classic, solves all cameras at once | CPU | GLOMAP paper: on par with or better than COLMAP, much faster on large sets | BSD | Task67, beside incremental |
| ALIKED + LightGlue matching (inside COLMAP 4) | Learned matching for either mapper | CPU possible; faster on GPU | More matches on hard views than SIFT | ALIKED BSD-3, LightGlue Apache-2.0 | Task67, beside SIFT |
| FastMap | Structure from motion with GPU first-order optimisation, from a COLMAP database | GPU | Authors: up to 10 times faster than COLMAP and GLOMAP, comparable pose accuracy | MIT | Task74; speed matters for thousands of images, not our 400 |
| DROID-SLAM | Learned SLAM on ordered video | GPU | 18 mm fr1/desk | BSD-3 | Task74 |
| DPVO / DPV-SLAM | Learned visual odometry and SLAM | GPU | 18 mm fr1/desk | MIT | Task74 |
| ORB-SLAM3 | Classic SLAM, also with phone motion sensors | CPU | 17 mm fr1/desk; fails on some TUM sequences | GPLv3 | Reference only |
| Depth Anything 3 Small / Base | Feed-forward: depth and camera poses from any number of views | CPU may be possible at 0.08-0.12B parameters | Not checked on TUM here | Apache-2.0 (Small, Base, Metric-Large); Large and Giant are CC BY-NC | Task74, first: permissive and small |
| MapAnything | Feed-forward metric 3D points and poses | GPU | Not checked on TUM here | Code Apache-2.0; use the `map-anything-apache-v1` checkpoint, the default is CC BY-NC | Task74 |
| VGGT, VGGT-SLAM, VGGT-Long | Feed-forward poses and points; SLAM and long-video versions | GPU | Aerial evaluation: classic methods most accurate, VGGT placed every image where COLMAP placed 67%; improves with bundle adjustment | VGGT custom licence, commercial checkpoint by application; VGGT-SLAM code BSD-2 | Task74, if the commercial checkpoint is granted |
| MASt3R-SLAM, MASt3R-SfM | Two-view 3D prior with SLAM or SfM | GPU | MASt3R-SLAM 16 mm fr1/desk, about 15 fps on an RTX 4090; FastMap paper finds MASt3R-SfM well behind GLOMAP in pose accuracy | CC BY-NC-SA 4.0 (non-commercial) | Research reference only |
| VGGSfM | Learned structure from motion | GPU | FastMap and G-MASt3R-SfM papers compare it with classic methods | CC BY-NC 4.0 (non-commercial) | Research reference only |

What "better" means differs by method:

- **Speed.** GLOMAP and FastMap are much faster than COLMAP's incremental mapper on thousands of images. Our clips have 298 and 399 frames, where speed is not the problem.
- **Robustness.** Feed-forward models place every frame, even with weak texture or little overlap, where COLMAP may drop frames.
- **Accuracy.** Classic bundle adjustment is still the most accurate when it succeeds, per the FastMap, aerial and ORBIT++ papers. Learned SLAM on ordered video, such as DROID-SLAM and MASt3R-SLAM, matches it on TUM.

So the forum is right that COLMAP has better-performing successors, but for our question the choice of modern method matters less than replacing our frame-to-frame tracker with any of them. Task67 now runs COLMAP 4.2 with both mappers and both matchers on CPU. Task74 runs the learned methods with permissive licences, Depth Anything 3 Small first because it may run on CPU.

## Phone design this points to

- **Camera path:** ARCore on the phone, which combines the camera with the motion sensors and gives metric size. Published phone tests range from about 1.5 cm on short indoor sessions (RealityCheck) to over 10 cm on harder walks; Kim et al. 2022 measured about 0.02 m/s drift for the best of four commercial trackers. It must be measured on our handset (Task75).
- **Surfaces:** learned depth resized each frame to the tracked points (Task72). Prompt Depth Anything is a published version of depth guided by sparse metric points. Task62 showed 10-50 exact points per frame reach the every-pixel score.
- **Hosted refinement, if needed:** an offline structure-from-motion or SLAM pass over the uploaded video.

## Papers saved for this review

| File | Paper | Why it is here |
|---|---|---|
| [mast3r_slam_2412.12392.pdf](papers/mast3r_slam_2412.12392.pdf) | MASt3R-SLAM, CVPR 2025 | TUM monocular table, 16 mm desk |
| [dpv_slam_2408.01654.pdf](papers/dpv_slam_2408.01654.pdf) | Deep Patch Visual SLAM | TUM monocular table, ORB-SLAM3 failures |
| [droid_slam_2108.10869.pdf](papers/droid_slam_2108.10869.pdf) | DROID-SLAM | Permissive learned SLAM |
| [orb_slam3_2007.11898.pdf](papers/orb_slam3_2007.11898.pdf) | ORB-SLAM3 | Classic SLAM reference |
| [glomap_2407.20219.pdf](../structure_from_motion/papers/glomap_2407.20219.pdf) | Global Structure-from-Motion Revisited (GLOMAP) | Now COLMAP 4's global mapper |
| [fastmap_2505.04612.pdf](../structure_from_motion/papers/fastmap_2505.04612.pdf) | FastMap | GPU structure from motion; compares learned SfM |
| [vggsfm_2312.04563.pdf](../structure_from_motion/papers/vggsfm_2312.04563.pdf) | VGGSfM | Learned structure from motion |
| [mast3r_sfm_2409.19152.pdf](../structure_from_motion/papers/mast3r_sfm_2409.19152.pdf) | MASt3R-SfM | Learned structure from motion |
| [g_mast3r_sfm_2606.22856.pdf](../structure_from_motion/papers/g_mast3r_sfm_2606.22856.pdf) | G-MASt3R-SfM | ETH3D comparison of COLMAP, VGGSfM, VGGT, MASt3R-SfM |
| [vggt_2503.11651.pdf](../feed_forward_3d/papers/vggt_2503.11651.pdf) | VGGT, CVPR 2025 | Feed-forward poses and points |
| [vggt_slam_2505.12549.pdf](papers/vggt_slam_2505.12549.pdf) | VGGT-SLAM | VGGT batches joined into a SLAM map |
| [vggt_long_2507.16443.pdf](papers/vggt_long_2507.16443.pdf) | VGGT-Long | VGGT on long sequences |
| [mapanything_2509.13414.pdf](../feed_forward_3d/papers/mapanything_2509.13414.pdf) | MapAnything | Feed-forward metric 3D |
| [depth_anything_3_2511.10647.pdf](../feed_forward_3d/papers/depth_anything_3_2511.10647.pdf) | Depth Anything 3 | Depth and poses from any views; Apache Small and Base |
| [dust3r_mast3r_vggt_aerial_evaluation_2507.14798.pdf](../feed_forward_3d/papers/dust3r_mast3r_vggt_aerial_evaluation_2507.14798.pdf) | Evaluation of DUSt3R/MASt3R/VGGT on aerial blocks | Feed-forward against classic accuracy |
| [orbit_plus_plus_sfm_360_video_2608.22039.pdf](../structure_from_motion/papers/orbit_plus_plus_sfm_360_video_2608.22039.pdf) | ORBIT++ | Structure from motion on real video; COLMAP failure rate |
| [prompt_depth_anything_2412.14015.pdf](../depth_estimation/papers/prompt_depth_anything_2412.14015.pdf) | Prompt Depth Anything | Depth guided by sparse metric points |
| [consistent_video_depth_2004.15021.pdf](../depth_estimation/papers/consistent_video_depth_2004.15021.pdf) | Consistent Video Depth Estimation | Depth made consistent through tracked points |
| [video_depth_anything_2501.12375.pdf](../depth_estimation/papers/video_depth_anything_2501.12375.pdf) | Video Depth Anything | Temporal depth, used in Task65 |
| [liftproj_panorama_stitching_2512.24276.pdf](../vr_and_stereo_viewing/papers/liftproj_panorama_stitching_2512.24276.pdf) | LiftProj | Why panorama stitching fails with parallax |
| [serrano_2019_vr_6dof_360_video.pdf](../vr_and_stereo_viewing/papers/serrano_2019_vr_6dof_360_video.pdf) | Serrano et al., IEEE VR 2019 | Head turning versus head movement in VR |
| [realitycheck_2021_arcore_drift.pdf](../phone_ar_platforms/papers/realitycheck_2021_arcore_drift.pdf) | RealityCheck, ISM 2021 | ARCore drift measured on a phone |

Not saved: Kim et al. 2022, [A Benchmark Comparison of Four Off-the-Shelf Proprietary Visual-Inertial Odometry Systems](https://doaj.org/article/4845749bf71543bb9d8bd51082e46690), Sensors 22(24) 9873. The publisher blocked the automated download; it is open access at that link.

## Web sources

- [TUM RGB-D evaluation tools](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/rgbdslam_eval)
- [COLMAP 4.0 release summary](https://radiancefields.com/colmap-4.0-introduces-major-performance-and-infrastructure-updates) and [COLMAP 4.2.0 release summary](https://radiancefields.com/colmap-4.2.0-adds-multi-component-global-mapping-and-loma-learned-matching)
- [GLOMAP repository](https://github.com/colmap/glomap)
- [iw3 README](https://github.com/nagadomi/nunif/blob/master/iw3/README.md)
- [MapAnything Apache checkpoint](https://huggingface.co/facebook/map-anything-apache-v1)
- [Depth Anything 3 model list and licences](https://github.com/ByteDance-Seed/Depth-Anything-3)
- [ARCore recording and playback](https://developers.google.com/ar/develop/java/recording-and-playback/developer-guide)
- Licences read from each repository on 13 October 2026: [MASt3R](https://github.com/naver/mast3r), [MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM), [VGGSfM](https://github.com/facebookresearch/vggsfm), [VGGT](https://github.com/facebookresearch/vggt), [DROID-SLAM](https://github.com/princeton-vl/DROID-SLAM), [DPVO](https://github.com/princeton-vl/DPVO), [FastMap](https://github.com/pals-ttic/fastmap), [LightGlue](https://github.com/cvg/LightGlue), [VGGT-SLAM](https://github.com/MIT-SPARK/VGGT-SLAM).
