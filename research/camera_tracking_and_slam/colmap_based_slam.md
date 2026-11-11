# COLMAP run as live tracking: COLMAP-SLAM, colmap-odometry and related projects

Read on 8 November 2026, after the owner sent the [colmap-odometry](https://github.com/3DOM-FBK/colmap-odometry) link. Accuracy and speed figures are the authors' claims. Nothing here was installed or run, except the pycolmap function checks marked "checked".

## Short answer

- **SLAM versions of COLMAP do exist.** The most developed come from the 3D Optical Metrology unit (3DOM) at FBK in Trento: COLMAP-SLAM (2023) and its replacement colmap-odometry (March 2026). Like ORB-SLAM, both work out the camera path from the images. Each new keyframe goes through COLMAP's incremental mapper, which places it, adds new points and re-solves the recent part of the map.
- **They don't replace ARCore here.** With one camera they give no real-world size. Neither feeds the motion sensors into the solution: the 2023 paper only tested orientation from the sensors on its own. colmap-odometry has no loop closure. The 2023 system kept up with the camera only when frames came in at 5 a second, with matching on a GPU.
- **Four things are worth taking:** a cheap rule for choosing keyframes; the per-keyframe loop of triangulation plus bundle adjustment over recent keyframes, run with ARCore's poses; their measured evidence that short distances between frames give poor geometry; and a memory habit.

## Terms

- **Keyframe**: a frame kept in the map. Other frames are only used to check how far the camera has moved.
- **Visual odometry (VO)**: tracking from images, frame to frame, with no correction when a place is revisited (*loop closure*). Errors build up over the walk (*drift*).
- **Sliding-window bundle adjustment**: re-solving only the last N keyframes and the points they see, so the cost per keyframe stays flat as the map grows.
- **Median matching distance (MMD)**: the median distance in pixels that matched features have moved between the last keyframe and the current frame. A larger value means more change in viewpoint.
- **Pose prior**: a soft constraint telling the solver roughly where a camera is. Here the prior would come from ARCore.
- **Baseline**: the distance between the two camera positions that see a point. The depth error of a triangulated point grows with depth squared and shrinks with baseline.

## The projects

| Project | Licence | What it is | State |
|---|---|---|---|
| [COLMAP-SLAM](https://github.com/3DOM-FBK/COLMAP_SLAM) | MIT | Python around the COLMAP program: RootSIFT features, GPU matching, the incremental mapper run again for each keyframe. One camera, stereo or several cameras. Loop closure only for one camera with RootSIFT. Uses satellite positions stored in the image files (EXIF) for scale | 312 stars. Superseded: "A newer version of the code is released, see the new repo colmap-odometry". Last push 25 March 2026 |
| [colmap-odometry](https://github.com/3DOM-FBK/colmap-odometry) | LICENSE text is three-clause BSD; GitHub records no licence identifier | Built on pycolmap 3.11.1, pyceres 2.4, PyTorch and kornia. Features: ALIKED, SuperPoint or ORB. Matching: LightGlue or mutual nearest neighbour. Bundle adjustment over the last 10 keyframes. A stereo pair is held together by a relative-pose prior in its own bundle adjustment code | 14 stars, 5 commits, created 24 March 2026, last push 26 March 2026. The README gives no results. Sample configs for CARLA (a driving simulator) and EuRoC |
| COLAM, "An Offline Python SLAM using COLMAP" ([project page](https://tenhearts.github.io/3dv.html)) | Not checked | ETH Zurich student project. Offline. Uses pycolmap for registration, triangulation and local refinement. Tested on TUM and KITTI | Code reported at Chiaki530/COLMAPSLAM, not checked |
| [AlanSavio25/COLMAP_SLAM](https://github.com/AlanSavio25/COLMAP_SLAM) | Not checked | A pycolmap-based system the 2023 paper cites but did not compare against | Not checked |
| On-the-fly SfM ([arXiv 2309.11883](https://arxiv.org/abs/2309.11883); v2 [arXiv 2407.03939](https://arxiv.org/abs/2407.03939), ISPRS Journal 2025) | GitHub records no licence identifier for [sygant/onthefly](https://github.com/sygant/onthefly) | Structure from motion that runs while photos are taken. Finds earlier images that look similar with learned whole-image descriptors (a vocabulary tree, then HNSW graphs in v2), then runs bundle adjustment weighted by each new image's neighbours. v2 merges maps from several capturers. Tested on an i9-12900K with an RTX 3080 | 45 stars, last push 27 September 2025. COLMAP appears as a comparison baseline. Whether it is built on COLMAP was not checked |
| [hloc](https://github.com/cvg/Hierarchical-Localization) | Apache-2.0 | Places new images against a saved map. Its `triangulation.py` builds a map from known camera poses by calling `pycolmap.triangulate_points` | 4,262 stars. Its SuperPoint and SuperGlue weights carry their own terms (not checked) |

## How COLMAP-SLAM works

From [Morelli et al. 2023](papers/colmap_slam_morelli2023.pdf) (ISPRS Archives XLVIII-1/W1-2023, 317-324, CC BY 4.0):

1. **Keyframe test on each new frame.** ORB or ALIKE features are matched to the last keyframe and checked against two-view geometry (Pydegensac). The frame becomes a keyframe if the MMD is above a threshold (80 px in the EuRoC tests) and enough new matches are found. The test takes about 0.05 s per frame.
2. **Matching.** Each keyframe is matched to the previous k keyframes (k = 1 by default). After n frames fail to be placed, the window widens to k + n, so tracking can recover.
3. **Mapping.** COLMAP's mapper places the new keyframes, triangulates new points and adjusts points and poses. Then the loop repeats.
4. **Size.** The first 30 keyframes set the coordinate frame. The scale comes from satellite positions or the stereo baseline in that first batch only. With one camera the size is unknown.
5. **Motion sensors.** Orientation from the imufusion package (a Madgwick-style filter) was compared with ground truth. It was not fed into tracking.

Results on EuRoC Machine Hall (drone flights indoors), on an Intel i9-10900F with a GTX 1080 GPU and 1024 features per keyframe. Errors are root mean square after lining up the path; one-camera results also fit one overall size.

| Test | COLMAP-SLAM | OpenVSLAM (based on ORB-SLAM2) |
|---|---|---|
| MH01, one camera, 1 keyframe per second | 3.3 cm with loop closure, 7.6 cm without | 6.2 cm |
| MH02 and MH03, one camera, no loop closure | 5.7 and 9.0 cm | 3.1 and 5.7 cm (stereo, with loop closure) |
| MH02 and MH03, stereo, scale fixed from the first 30 keyframes | 10.4 and 36.0 cm | as above |
| MH01, keyframes every 1 s against every 0.2 s, 5 runs each | 1 s: 4.9-10.3 cm. 0.2 s: 9.9-121.1 cm | — |
| MH04 and MH05, keyframes chosen by MMD from a 5 frame-per-second stream | ORB: 6.5 and 10.7 cm. ALIKE: 11.5 and 4.8 cm. 89-98 keyframes, 72-83 s in total | 989.9 cm (lost in low light) and 7.3 cm |

Speed: the system ran at the camera's pace only with 5 frames a second coming in and the keyframe test on. "Attempting to process more than 10 frames per second without keyframe selection leads to significant delays." The slow step is "the global BA performed at each iteration".

## The 2025 evaluation of colmap-odometry

From [Morelli et al. 2025](papers/dl_visual_odometry_morelli2025.pdf) (ISPRS Archives XLVIII-1/W5-2025, 93-99, CC BY 4.0). The test drive was a simulated 1.2 km loop at 50 km/h in CARLA: 858 stereo pairs at 5 frames per second, with a distortion-free camera and loop closure off. Error is root mean square after lining up the whole path:

| Scene | ORB-SLAM3 | COLMAP-SLAM, ALIKED + LightGlue | COLMAP-SLAM, SuperPoint + LightGlue | DROID-SLAM, one camera with learned depth, size corrected |
|---|---:|---:|---:|---:|
| Day, no traffic | 0.34 m | 0.87 m | 0.57 m | 7.28 m |
| Rainy night, no traffic | 1.80 m | 0.82 m | 0.71 m | 10.46 m |
| Day, traffic | 0.30 m | 0.49 m | 0.65 m | 7.55 m |
| Foggy night, traffic | lost tracking | 19.47 m | 11.45 m | 35.67 m |

- ORB-SLAM3 lost tracking with its default settings. It only completed when the feature count (700-2,000) and pyramid levels (8 or 10) were tuned per drive, and "No single parameter combination was found to generalize well across all datasets".
- The learned features needed no tuning. Capping them at 1,000 per image made the error up to 2 times worse than leaving about 3,000.
- Keyframes were chosen at 5 px of average feature motion.
- The paper gives no speed or hardware figures.

## What fits this project

This project already gets its camera path from ARCore, live, with the motion sensors and real-world size. So the main output of these systems duplicates ARCore. For the open-source route (replacing ARCore), Basalt and OpenVINS fit better because they use the motion sensors (see [sota_slam_review_2026-10-14.md](sota_slam_review_2026-10-14.md)). What carries over:

1. **Keyframe choice by pixel motion.** Keep a frame for triangulation once the median matched feature has moved far enough since the last keyframe. They used 80 px at 752 × 480 on EuRoC and 5 px on CARLA. It costs about 0.05 s per frame. Here it would pick frame pairs with enough baseline for far points. It would also give `room_build` fewer, more different frames, which matters because the visibility vote's cost grows with frames × points.
2. **The per-keyframe loop, run with ARCore's poses.** Place each keyframe from ARCore instead of solving it, triangulate its matches against earlier keyframes, then adjust the last few keyframes with ARCore's positions as priors. The pycolmap 4.2.1 in the repository's `.venv` has what this needs (checked 8 November): `triangulate_points` (the known-pose triangulation hloc calls), `estimate_triangulation`, `IncrementalTriangulator`, and `create_pose_prior_bundle_adjuster` with `PosePrior`. colmap-odometry's own bundle adjustment needs pycolmap 3.11.1's `cost_functions` module and pyceres, and pycolmap 4.2.1 has neither, so take the idea, not the code.
3. **Short baselines make poor geometry.** On MH01, keyframes every 0.2 s gave errors up to 121 cm, against at most 10.3 cm with keyframes every 1 s, "likely due to the shorter baselines". This supports matching frames taken from different spots rather than neighbouring frames.
4. **Features.** ORB is fast but fragile in poor light and needs tuning. Learned features held up in rain and fog but need PyTorch, and on this project's CPU, ALIKED with LightGlue ran 2-4 times slower than SIFT (Task67, `experiments/sfm`). A learned feature built for CPUs is XFeat ([CVPR 2024](https://arxiv.org/abs/2404.19174), Apache-2.0). It has not been tested here.
5. **Memory.** colmap-odometry discards each non-keyframe's features as soon as the keyframe test rejects it, and it logs memory per frame with psutil. Any triangulation stage added to `sitescan/pipelines` should do the same: keep features only for keyframes inside the window, so memory stays flat over a long walk.
6. **Placing new images against a saved map** (hloc) is the open-source way to merge several scans of one site, as Lumina does. This is for later.

Not useful here: COLMAP-SLAM's loop closure (one camera with RootSIFT only), its scale from the first 30 keyframes (ARCore gives size throughout), and the DROID-SLAM results (GPU, and about 10 times worse in the 2025 tests).

## Papers

| File | Paper |
|---|---|
| [colmap_slam_morelli2023.pdf](papers/colmap_slam_morelli2023.pdf) | Morelli, Ioli, Beber, Menna, Remondino, Vitti. COLMAP-SLAM: A framework for visual odometry. ISPRS Archives XLVIII-1/W1-2023. [doi:10.5194/isprs-archives-XLVIII-1-W1-2023-317-2023](https://doi.org/10.5194/isprs-archives-XLVIII-1-W1-2023-317-2023) |
| [dl_visual_odometry_morelli2025.pdf](papers/dl_visual_odometry_morelli2025.pdf) | Morelli, Trybała, Razzino, Remondino. Deep Learning in Visual Odometry for Autonomous Driving. ISPRS Archives XLVIII-1/W5-2025. [doi:10.5194/isprs-archives-XLVIII-1-W5-2025-93-2025](https://doi.org/10.5194/isprs-archives-XLVIII-1-W5-2025-93-2025) |

PDFs stay local (`*.pdf` is ignored by Git).
