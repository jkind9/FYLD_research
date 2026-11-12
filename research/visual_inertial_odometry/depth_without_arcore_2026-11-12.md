# Metric depth without ARCore: templates, parts and what the code must change

**Question (owner, 12 November 2026).** The product should not rely on ARCore. Depth will come from our own learned model, sized by depth we measure ourselves, with real-world size tied to the phone's motion sensors. Which open repositories or papers do this already and could serve as a template, following the triangulation order in the [project plan](../../PROJECT_PLAN.md#the-design-the-evidence-supports)? And is `sitescan/` modular enough to swap ARCore's parts out?

**Short answer.**

- **No permissive repository does the whole chain on a phone CPU.** Every part exists under a permissive licence, though, and the plan's order still holds:
  - Basalt for poses in metres;
  - sparse points triangulated along its path as sizing targets;
  - learned depth sized to them;
  - plane-sweep stereo where texture allows.
- **OKVIS2-X (BSD-3, ETH, 2025) is the closest whole-chain template.** It has a visual-inertial estimator, multi-view stereo between keyframes with a depth uncertainty per pixel, volumetric submaps, and alignment factors that feed the map back into the estimator. Its multi-view weights derive from SimpleRecon, which is non-commercial. All its published timings are on a GPU.
- **Two projects have built this on Android without ARCore.** DAVIO (GPL-3) and 3d-recon (AGPL-3) are references only. 3d-recon's author reports that handheld tracking, not depth, is what failed. So calibrating the Redmi ([Task103](../../task_list/open/103_measure_redmi_camera_and_imu_calibration_from_owne.md)) and running Basalt on Redmi walks ([Task104](../../task_list/open/104_compare_open_trackers_and_surfaces_on_the_same_red.md)) move onto the critical path.
- **`sitescan/` is modular in its stages but built around ARCore in its data and pipelines.** Depth model, scale fit, clean-up and mapping can be swapped today. Poses, intrinsics, frame choice, scale sources, fusion anchors and object anchors all assume ARCore. A frame recorded without ARCore has no pose and no intrinsics, so both pipelines skip it. Five changes are needed; [details below](#is-sitescan-ready-to-swap-these-in).

Sources were read on 12 November 2026: each repository's README and licence, and papers on arXiv. Speeds and accuracies are the authors' claims. Nothing was installed or run. Items marked *unverified* come from a paper or a linked document that was not read in full.

## What has to be replaced

| ARCore gives today | Replacement | Source of the replacement |
|---|---|---|
| Camera frames, through ARCore's shared-camera mode | Plain Camera2 capture in the same app | The capture app's own code. This also lets the app lock exposure, white balance and focus, which ARCore controls today |
| Intrinsics on every frame | A per-phone calibration | Kalibr, already reproduced on TUM-VI ([calibration.md](calibration.md)). Camera2 can also report intrinsics; whether the Redmi does is unchecked |
| Camera path in metres, with gravity | Visual-inertial odometry | Basalt (BSD-3), the [first candidate](vio_systems.md) |
| Tracked points | The tracker's landmarks | Basalt's sliding-window landmarks ([below](#step-0-poses-and-free-sparse-points-from-basalt)) |
| Raw depth up to about 2.5 m | Depth triangulated along the path, sparse then dense | Steps 1 and 3 below |
| Anchor corrections | Keyframe poses, corrected only if a back end with loop closure is added | Basalt's mapping, or OKVIS2's loop closure |
| The size reference in scoring | Tape-measured distances, and triangulated points held out from the fit | Next recording round ([plan](../../PROJECT_PLAN.md#what-to-take-from-rtab-map-and-the-surface-grouping-review)) |

Losing ARCore depth costs the near range as well as the far. Today ARCore depth sizes everything under about 2.5 m, and it does that well (within 5% of tracked points up to 3 m, Task117). Triangulation must now cover near surfaces too. Near is the easy case: triangulation error grows with distance squared divided by baseline, so a short baseline is enough close up.

The v2 walks already recorded the uncalibrated gyroscope and accelerometer beside ARCore. Every method below can therefore be tried on existing walks, with ARCore's answer kept as a comparison rather than an input.

## Whole-chain templates

| System | Licence (from LICENSE file) | Last commit | What it combines, and how | Hardware | Use here |
|---|---|---|---|---|---|
| [OKVIS2-X](https://github.com/ethz-mrl/OKVIS2-X) ([paper](https://arxiv.org/abs/2510.04612)) | BSD-3 | 11 Nov 2026 | Visual-inertial factor graph. A stereo network (from Unimatch) or multi-view network (from SimpleRecon) gives depth plus an uncertainty per pixel. Depth is fused into supereight2 occupancy submaps, which are aligned back into the estimator by map-to-map and map-to-live factors. Paper: one camera works, a little worse than stereo; EuRoC map accuracy 0.055 m with one camera, against SimpleMapping's 0.072 m (*unverified*) | C++ with LibTorch; GPU optional (`USE_GPU`). Paper: multi-view thread 13 Hz on an RTX 3080, depth capped at 3 m (*unverified*). No CPU timing | **Template for the whole chain.** Lift the depth-with-uncertainty integration, submaps and alignment factors. Treat the multi-view weights as unshippable (SimpleRecon is non-commercial) |
| [DenseReconstructionTools](https://github.com/RobotVisionHKA/DenseReconstructionTools) | BSD-3; [MonoRec](https://github.com/Brummi/MonoRec) MIT | Dec 2024 | A **Basalt fork** that exports camera poses and sparse 3D points. MonoRec then builds a multi-frame cost volume from those poses, so its depth is metric | Offline; Python and C++; no speeds or accuracy published | **The only permissive chain found that is built on Basalt.** Read its fork to see how landmarks are exported (format *unverified*) |
| [VI-Depth](https://github.com/isl-org/VI-Depth) ([paper](https://arxiv.org/abs/2303.12134)) | MIT | Archived Aug 2025 | Least-squares scale and shift of learned inverse depth to VIO points. Then ScaleMapLearner, a small network, predicts a scale correction per pixel. Up to 30% lower inverse-depth error than global alignment on VOID and TartanAir | PyTorch; an OpenVINO CPU demo exists | The minimal code for "learned depth to metres from VIO points". Weights exist for MiDaS and DPT only, and there is no training code |
| [mono_depth_rescaler](https://github.com/rislab/mono_depth_rescaler) ([paper](https://arxiv.org/html/2509.08159v1)) | MIT | Sep 2025 | Depth Anything V2 Small, sized per frame to visual-inertial feature depths. Per the paper, a monotonic spline maps relative disparity to metric (*unverified* in the code) | ROS1 and Python; paper reports 15–20 Hz on a Jetson Orin with TensorRT | A size that varies with distance, which the plan's far-depth error needs |

**Reference only.** These are copyleft or non-commercial, so they are read for ideas and the ideas are re-implemented from the papers.

| System | Licence | Why it matters |
|---|---|---|
| [DAVIO](https://github.com/be2rlab/DAVIO) ([paper](https://arxiv.org/html/2609.27702)) | GPL-3 (OpenVINS inside) | The nearest match to our setup. It ships an Android camera-and-IMU recorder and claims to handle phones without calibration through online calibration (asserted, not measured in the README). Depth Anything 3 is conditioned on the filter's metric poses. Per the paper (*unverified*): a scale per frame fitted by iteratively reweighted least squares, a log-scale graph over submaps, scale applied only along camera rays, and a depth check across views before fusion. NVIDIA GPU, 6 GB |
| [3d-recon](https://github.com/ChRotsides/3d-recon) | AGPL-3 | Android, **no ARCore**. Runs OpenVINS, Depth Anything V2 on the phone's CPU or NPU, and voxel-hash TSDF fusion. Its README says "handheld tracking is not yet reliable enough for everyday use: startup, drift and relocalization are the open problems". On a Samsung S23 Ultra, a scale fitted per frame cut the frame-to-frame scale spread from 2.36× to 1.11× and the median depth error from 0.36 m to 0.18 m |
| [ScaRF-SLAM](https://github.com/ori-drs/ScaRF-SLAM) ([paper](https://arxiv.org/html/2606.00307)) | GPL-3 | Fits a scale per frame and per submap to LightGlue-matched 3D points, with poses held fixed. Claims about 2 cm error per 10 m indoors. GPU |
| [SimpleMapping](https://github.com/yingyexin/SimpleMapping) ([paper](https://arxiv.org/abs/2306.08648)) | MIT on top, but built on ORB-SLAM3 (GPL-3) | Sparse VIO points are completed into a dense depth, which then guides the multi-view cost volume. 55 ms per frame, hardware not stated |

**Checked, not useful:**

- **Copyleft or unlicensed, and old:** VI-MEAN, open_quadtree_mapping and MVDepthNet (GPL-3, 2017–2021, CUDA). DenseSurfelMapping (no licence, archived 2019). DM-VIO and FLAME (GPL-3).
- **GPU-only learned SLAM:** VIGS-SLAM, VINGS-Mono and DBA-Fusion.
- **No mapping:** RD-VIO/xrslam (Apache-2.0) gives poses only.
- **Papers with no code found:** CodeVIO, VIMD (2025), MDE-VIO (2026) and VIDAR (2026).

## The parts, by step of the plan

### Step 0: poses and free sparse points from Basalt

Basalt keeps each landmark as a direction plus inverse distance in its host keyframe, with its 2D sightings. They are already metric and free, but few, and only for the frames in its sliding window. Basalt never writes them to a file; they reach its visualisation queue (`out_vis_queue`) as world points. DenseReconstructionTools' fork shows one way to export them. `basalt_mapper` can re-detect, match, triangulate and optimise offline from Basalt's saved marginalisation data. These details are from the source (`landmark_database.h`, `vio_estimator.h`) as reported by the search, and were not built here.

### Step 1: sparse triangulation along the path

| Part | Licence | What to take |
|---|---|---|
| pycolmap `triangulate_points` with fixed poses (installed, 4.2.1) | BSD-3 | The plan's step 1, unchanged |
| [hloc](https://github.com/cvg/Hierarchical-Localization) `triangulation.py`, `pairs_from_poses.py` | Apache-2.0 | Builds the COLMAP database from known poses. Checks matches against those poses with an epipolar test (4 px), and pairs frames by camera distance, rejecting pairs whose viewing directions differ by 30° or more |
| pycolmap `triangulate_multi_view_point`, `calculate_triangulation_angle` | BSD-3 | Triangulation without a database, for a live version |
| GTSAM `triangulateSafe` | BSD | A phone-side C++ option that reports why a point failed (degenerate, behind the camera, outlier, too far) |

### Step 2: sizing learned depth with the measured points

Today's sizing is a median ratio in an 8 × 6 grid ([fit.py](../../sitescan/scale/fit.py)). The literature adds four things. The scale fit takes `(pixels, metres)` and does not care where they came from, so each can be tried one at a time.

1. **Weight each point by how much it can be trusted.** A triangulated depth's error is about z² · σ_px / (f · b). Here z is depth, σ_px is the matching error in pixels, f is the focal length in pixels and b is the baseline. Far points from short baselines should count for less. Weight w = 1 / (σ_learned² + σ_triangulated²).
2. **Drop bad points before fitting.** A robust line fit (Theil–Sen) of measured against learned depth, then a median-absolute-deviation test. This is the MRAC paper's rule (2026, [arXiv 2607.04101](https://arxiv.org/abs/2607.04101), *unverified*). It needs no code to copy and costs microseconds.
3. **Let the size change with distance.** Fit one monotonic curve per frame from learned to metric depth (mono_depth_rescaler's approach). This targets the plan's "about 15% too near beyond 3 m" directly, which a single size per cell cannot.
4. **Spread the remaining correction smoothly.** Two options:
   - a confidence-weighted log-scale field solved with OpenCV's fast bilateral solver (`ximgproc`, Apache-2.0), which keeps corrections from crossing image edges;
   - a least-squares solve on the learned depth's gradients with the points as weighted constraints, as OMNI-DC does (BSD-3).

   Image-Adaptive Scale Fields reports plain local fits collapsing with only 10–15 points (*unverified*), so check how many points each frame actually gets.

**A model that uses the points to fix shape, not just size.** [Any2Full](https://github.com/zhiyuandaily/Any2Full) (ECCV 2026) is Apache-2.0 and ships a ViT-S checkpoint (`Any2Full_vits.pth.tar`, 204 MB, checked on Hugging Face). Per its paper (*unverified*), it feeds the sparse depth, normalised so only relative structure remains, into a Depth Anything V2 decoder through a prompt encoder, then fits one global size. The paper reports VOID-150 relative error of 0.045, against OMNI-DC's 0.057. This differs from Prompt Depth Anything, which reads raw metric depth and gave no gain here (Task79). Any2Full is the one model found that could cut the 8–16 cm shape error. It has no training code, and its speed on a CPU is unknown.

VI-Depth's ScaleMapLearner is the MIT fallback if Any2Full fails. Prior Depth Anything's coarse stage (Apache-2.0 code) fits a scale and shift on the five nearest points per pixel, which is a cheap local fit to compare against. Its refinement weights are non-commercial.

### Step 3: dense triangulation between keyframes

No permissive code was found that does a plane sweep with Census costs and semi-global matching on unrectified views on a CPU. FaSS-MVS (2024) is the closest published method, with no code, on CUDA. So the plan's Mobile3DRecon-style step is written here, from parts:

| Part | Licence | What to take |
|---|---|---|
| [gishi523/semi-global-matching](https://github.com/gishi523/semi-global-matching) | MIT | Census 9 × 7 and 8-direction SGM aggregation in C++ with SSE and OpenMP. The aggregation only needs a cost volume, so it can run over a plane sweep's inverse-depth levels instead of disparities |
| [MaGNet](https://github.com/baegwangbin/MaGNet) | MIT | The idea of searching only near a prior: test depths around the sized learned depth instead of the whole range, which cuts the number of planes on a CPU |
| [DeepVideoMVS](https://github.com/ardaduz/deep-video-mvs) | MIT | Keyframe and reference-frame scoring (pose distance with an optimal baseline, short baselines penalised). Mobile3DRecon's 0.6 m and 10° rule is the alternative |
| [slambook2 ch12 `dense_mono`](https://github.com/gaoxiang12/slambook2) | MIT | A small CPU depth filter on known poses (7 × 7 ZNCC epipolar search, Gaussian fusion of each pixel's depth over frames). Suits a live version. The search reports bugs in it: `update()` never returns a value, and the border checks are wrong |
| [PolarCalibration](https://github.com/nestormh/PolarCalibration) | Apache-2.0 | Polar rectification works when the camera moves forward, which breaks ordinary rectification. A cheap first check: polar-rectify a keyframe pair, then run the installed OpenCV `StereoSGBM` |

**Confidence.** No permissive library was found. Two checks are easy to write: project each depth into another keyframe and test agreement, as COLMAP's fusion does; and the ratio of the best to the second-best matching cost.

### Learned multi-view depth, for when a GPU is free

- **Depth Anything 3 with poses.** Its `inference()` takes world-to-camera `extrinsics` and `intrinsics`. With `align_to_input_ext_scale=True` (the default) it rescales depth to the input poses, so Basalt's metric poses would give metric depth ([API docs](https://github.com/ByteDance-Seed/depth-anything-3/blob/main/docs/API.md)). The project's Task80 ran DA3 Small without poses. This pose-conditioned mode has not been tried, and the docs do not say which model sizes support it.
- **OKVIS2-X's multi-view network.** A useful reference, but its weights are non-commercial, as above.
- **MapAnything.** Its Apache-2.0 checkpoints take poses and output metric depth, but it is heavy.

### The depth model on the phone

Depth Anything V2 Small stays the baseline. Its code and weights are Apache-2.0; its Base and Large weights are non-commercial. Arm lists an INT8 build at 728 ms per frame at 518 × 686 on a vivo X300 CPU, a 2025 flagship. The Redmi's Helio G96 is slower, so a smaller input will probably be needed. Measure that rather than estimate it. Two permissive models to compare on the same frames:

- **Distill-Any-Depth-Small** (MIT). The same architecture, so it is a weight swap.
- **MoGe-2 ViT-S** (MIT). It gives metric points and surface normals at similar cost.

Not usable for a product: UniDepth (non-commercial weights), Depth Anything V2 Base and Large, and Depth Pro, whose weight terms were not confirmed.

## Is `sitescan/` ready to swap these in?

**Stages: yes.** Each stage is a plain function on arrays, as [DESIGN.md](../../DESIGN.md#7-key-design-choices) intended:

- The depth model is a callable passed in, so any loader that returns `(depth_m, valid)` replaces Depth Anything V2 ([model.py:42](../../sitescan/depth/model.py#L42)). An ONNX or LiteRT model needs only a new loader.
- The scale fits take any `(pixels, metres)` targets ([fit.py:30](../../sitescan/scale/fit.py#L30), [fit.py:54](../../sitescan/scale/fit.py#L54)). `point_targets` already turns any world points and their pixels into targets ([targets.py:27](../../sitescan/scale/targets.py#L27)), so triangulated points fit it as they are.
- Clean-up and mapping take points and cameras only. Mapping finds "up" from camera positions, not from an axis.

**Data model and pipelines: no.** ARCore is built into the data and the wiring:

| Where | What assumes ARCore | Effect without ARCore |
|---|---|---|
| [types.py:21](../../sitescan/types.py#L21), [types.py:44-48](../../sitescan/types.py#L44-L48) | `ArcoreDepth`; `Frame` carries ARCore anchors, tracking state and ARCore time. No field for motion sensors or for where a pose came from | A second pose or depth source has nowhere to go |
| [wire_v2.py:150](../../sitescan/session/wire_v2.py#L150), [read.py:53](../../sitescan/session/read.py#L53) | Pose and intrinsics come only from ARCore's record. A camera-only frame gets `pose=None` and `intrinsics=None` | `session.camera()` returns None; nothing downstream can run |
| [room.py:91-110](../../sitescan/pipelines/room.py#L91-L110) | Fuses only frames with fresh ARCore depth; sizes only to ARCore depth; keyframes are ARCore anchors | Every frame is skipped |
| [live.py:42-53](../../sitescan/pipelines/live.py#L42-L53), [live.py:79-90](../../sitescan/pipelines/live.py#L79-L90) | Scale sources hard-coded as ARCore depth, then ARCore points, then the previous scale. Prefers frames with ARCore depth. Anchors from ARCore | Every update returns "no scale source yet" |
| [fragments.py:56](../../sitescan/fusion/fragments.py#L56), [tracks.py:58-69](../../sitescan/objects/tracks.py#L58-L69) | Fusion and object positions are stored relative to anchors and fail if none was set | The mechanism is general (an anchor is a pose that may be corrected later), but only ARCore supplies anchors |
| [orientation.py:23](../../sitescan/depth/orientation.py#L23) | Finds "down" from the world y axis, ARCore's up | Basalt's world has gravity along z, so images would be turned the wrong way, without any error |
| [room.py:25](../../sitescan/pipelines/room.py#L25), [live.py:26](../../sitescan/pipelines/live.py#L26) | Pose conversions from ARCore's OpenGL camera axes; DESIGN's [finding 5](../../DESIGN.md#findings) notes the two conventions are still mixed | A new source must be expressed in ARCore's axes to fit |
| `sitescan/` as a whole | Nothing reads `imu.csv`. There is no tracking or triangulation stage | Motion sensors reach only `research/experiments/open_vio` |
| Capture app ([SharedCameraRig.java](../experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/SharedCameraRig.java), [CaptureActivity.java:307](../experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CaptureActivity.java#L307)) | Opens the camera through ARCore's shared-camera session; ARCore sets frame rate, focus and exposure | No ARCore-free recording mode exists |

The test fixture shows the workaround in use today. `tum_desk_20` writes motion-capture poses and Kinect depth into the ARCore fields of a v2 recording ([fixtures README](../../tests/fixtures/README.md)). The same trick would let a first trial feed Basalt poses and triangulated depth through unchanged pipelines. It hides where the data came from, so it suits an experiment, not the product.

**Five changes, in order.** DESIGN rule 4 says no choosing mechanism until two real methods exist. ARCore and an open tracker are now two, so a plain setting or `if` is justified, but still no registries.

1. **Pose and intrinsics from outside the recording.** `session.frames()` takes an optional trajectory and calibration, matched to frames by timestamp. The open-VIO host already writes the TUM trajectory format. Convert the world to gravity-up once, at the reader, so [orientation.py](../../sitescan/depth/orientation.py) and everything after it stay unchanged. This one change lets every existing walk run on Basalt poses, with ARCore's path kept for comparison.
2. **Measured depth not tied to ARCore.** Rename `ArcoreDepth` to a measured-depth record with a `source` field. Dense triangulated depth then fits the same slot as ARCore depth, with its freshness and confidence rules.
3. **Scale targets chosen by name in settings.** For example ARCore depth, ARCore points, VIO landmarks, sparse triangulation or dense triangulation, each returning `(pixels, metres, weight)`. Both pipelines read the same setting instead of a hard-coded cascade. Add weights to `fit_grid` when step 2's weighting is trialled.
4. **A new `sitescan/triangulate/` stage.** Sparse known-pose triangulation, keyframe selection and, later, the plane sweep. It holds a rolling keyframe window in one small class, as `Fragments` does for fusion.
5. **Anchors from keyframes.** An open tracker's keyframe poses become anchors. With odometry only they are never corrected, which `Fragments` already handles. If a back end with loop closure is added, its updated keyframe poses become anchor updates.

The ARCore-specific wiring sits in `session/`, `types.py` and the two pipelines. Those files are about 1,100 of the package's 2,200 lines, and much of `session/` is wire parsing that stays. The maths in depth, scale, fusion, clean-up, mapping and object matching does not change. Each change can keep the golden outputs ([tests/fixtures](../../tests/fixtures/README.md)) by leaving ARCore as the default source until a trial is adopted.

## Proposed order

The order adopted from this review is kept in one place, the project plan's [Next steps](../../PROJECT_PLAN.md#next-steps). In short:

- **Start now, no new recordings needed:**
  - Code change 1, poses from outside the recording.
  - The triangulation stage, developed on public visual-inertial data.
- **When the owner's recordings arrive:**
  - Calibrate the Redmi (Task103).
  - Run Basalt on the recorded walks (Task104).
  - Rebuild the 15 October room on Basalt's poses, first with ARCore depth, then sized by triangulated depth alone.
- **Then:**
  - Any2Full-S.
  - The dense plane sweep.
  - A capture mode without ARCore.
  - Tape-measured walks.
- **When a GPU is free:** Depth Anything 3 given Basalt's poses, and OKVIS2-X.

## Sources

Whole-chain systems:

- OKVIS2-X: [repository](https://github.com/ethz-mrl/OKVIS2-X), [paper](https://arxiv.org/abs/2510.04612)
- DenseReconstructionTools: [repository](https://github.com/RobotVisionHKA/DenseReconstructionTools)
- VI-Depth: [repository](https://github.com/isl-org/VI-Depth), [paper](https://arxiv.org/abs/2303.12134)
- mono_depth_rescaler: [repository](https://github.com/rislab/mono_depth_rescaler), [paper](https://arxiv.org/html/2509.08159v1)
- DAVIO: [repository](https://github.com/be2rlab/DAVIO), [paper](https://arxiv.org/html/2609.27702)
- [3d-recon](https://github.com/ChRotsides/3d-recon)
- ScaRF-SLAM: [repository](https://github.com/ori-drs/ScaRF-SLAM), [paper](https://arxiv.org/html/2606.00307)
- SimpleMapping: [repository](https://github.com/yingyexin/SimpleMapping), [paper](https://arxiv.org/abs/2306.08648)
- [SimpleRecon licence](https://github.com/nianticlabs/simplerecon)

Sizing:

- Any2Full: [repository](https://github.com/zhiyuandaily/Any2Full), [checkpoints](https://huggingface.co/zhiyuandaily/Any2Full/tree/main/checkpoints)
- [OMNI-DC](https://github.com/princeton-vl/OMNI-DC)
- [Prior Depth Anything](https://github.com/SpatialVision/Prior-Depth-Anything)
- [MRAC](https://arxiv.org/abs/2607.04101)
- [OpenCV ximgproc filters](https://docs.opencv.org/4.13.0/da/d17/group__ximgproc__filters.html)

Triangulation:

- [hloc](https://github.com/cvg/Hierarchical-Localization)
- [pycolmap](https://colmap.github.io/pycolmap/pycolmap.html)
- [GTSAM](https://github.com/borglab/gtsam)
- [Basalt](https://gitlab.com/VladyslavUsenko/basalt)
- [gishi523/semi-global-matching](https://github.com/gishi523/semi-global-matching)
- [MaGNet](https://github.com/baegwangbin/MaGNet)
- [DeepVideoMVS](https://github.com/ardaduz/deep-video-mvs)
- [slambook2](https://github.com/gaoxiang12/slambook2)
- [PolarCalibration](https://github.com/nestormh/PolarCalibration)
- [FaSS-MVS](https://arxiv.org/pdf/2112.00821)
- [Depth Anything 3 API](https://github.com/ByteDance-Seed/depth-anything-3/blob/main/docs/API.md)
- [MapAnything](https://github.com/facebookresearch/map-anything)

Depth models:

- [Depth Anything V2 Small](https://huggingface.co/depth-anything/Depth-Anything-V2-Small)
- [Arm INT8 build](https://developer.arm.com/ai/models/hugging-face/Arm/depth-anything-v2-small-int8-xnnpack-executorch-vivo-x300/depth-anything-v2-small-int8-pte)
- [Distill-Any-Depth-Small](https://huggingface.co/xingyang1/Distill-Any-Depth-Small-hf)
- [MoGe](https://github.com/microsoft/MoGe)
- [UniDepth](https://github.com/lpiccinelli-eth/UniDepth)
