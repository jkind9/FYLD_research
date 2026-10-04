# Layer 3: camera position estimation

This folder (experiment 03) is layer 3 of the five-layer pipeline described in the [root README](../../README.md). It answers: **where was the camera, and which way was it pointing, for every frame?** This is called camera tracking or pose estimation.

Every later layer depends on it. The surface layer places each frame's depth into one shared 3D space using these positions. The object layer uses them to tell whether a returning object is in the same place as before. A wrong camera path bends walls and makes one object look like two. Recognising a place the camera has seen before is also how a site is identified on a return visit.

**Status:** a CPU tracker built on Open3D has been measured on 30 frames: **6.9 mm** camera-position error against a motion-capture reference. Full-length runs on 792 development frames and 573 held-out frames are approved and prepared, but have not run yet.

## How camera tracking works

A **camera pose** is a position (x, y, z in metres) and an orientation (which way the camera points) for one frame. Poses are given relative to a world origin, usually the first frame.

**Frame-to-frame tracking (visual odometry).** The tracker compares each new frame with the last one and works out how the camera moved. There are two main ways:
- **Feature-based:** find distinctive spots, such as corners, in both frames (ORB and SIFT are common detectors), match them, and solve for the movement that best explains the matches.
- **Direct:** shift one frame's pixels until their brightness and depth line up with the other frame. The current baseline here works this way.

**Scale.** With one camera and nothing else, the path's shape can be found but not its size in metres. Depth (layer 2), a second lens or the motion sensors supply the real scale.

**Drift and loop closure.** Each step has a small error, and the errors add up, so the path slowly wanders. When the camera returns to a place it has seen, the tracker can recognise it (place recognition), check the match geometrically, and then adjust the whole path so the two visits agree. This is loop closure. A tracker that also keeps a map is called SLAM (simultaneous localisation and mapping).

**Motion sensors (visual-inertial tracking).** The phone's gyroscope and accelerometer (the IMU) measure rotation and acceleration hundreds of times a second. They carry tracking through blur and fast turns, and give the direction of gravity. ARCore on the phone works this way.

**Learned trackers.** Newer methods use neural networks to match frames or predict 3D geometry directly, such as DROID-SLAM, MASt3R-SLAM and VGGT-SLAM. They handle hard footage well but need a large GPU.

**When tracking fails.** If the tracker loses its place, the next frames start a new segment with their own origin. Segments are never silently joined. A recorded, checked transform is needed before two segments share one map.

**Scoring.** Absolute trajectory error compares every estimated position with the reference after lining up the first pose, with scale fixed. Relative pose error measures the error of each small step, which shows drift.

## Methods: hosted and on the phone

| Method | Route | What it does | Licence and notes |
|---|---|---|---|
| [Open3D RGB-D odometry](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_odometry.html) | Either | Direct colour-and-depth frame-to-frame tracking | MIT. The current baseline here. No loop closure. |
| [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) | Hosted or edge | Feature-based SLAM for single camera, stereo or depth, with or without IMU; loop closure and several maps | GPLv3. The main classical reference. |
| [RTAB-Map](https://github.com/introlab/rtabmap) | Hosted, edge or phone | Depth-camera SLAM with strong place recognition and long-term memory; an Android app runs on top of ARCore's position | BSD-3 core. Rank 2 for drift correction in the project's research. |
| [OpenVINS](https://docs.openvins.com/), [Basalt](https://gitlab.com/VladyslavUsenko/basalt) | Hosted or edge | Visual-inertial tracking with careful calibration and timing | GPLv3 and BSD-3 respectively. |
| [DROID-SLAM](https://github.com/princeton-vl/DROID-SLAM) | Hosted | Learned dense tracking | BSD-3 code; needs 11 GB or more of GPU memory. |
| [MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | Hosted | Learned matching with dense geometry and loop closure | Non-commercial licence. |
| [VGGT-SLAM 2.0](https://github.com/MIT-SPARK/VGGT-SLAM) | Hosted | Feed-forward dense submaps joined into one path, without needing calibration | BSD-2 wrapper; the original VGGT weights are non-commercial. |
| [COLMAP](https://colmap.github.io/) or [GLOMAP](https://arxiv.org/abs/2407.20219) | Hosted | Offline refinement over all frames at once (bundle adjustment) | BSD. Slow but accurate for a final camera path after upload. |
| [ARCore motion tracking](https://developers.google.com/ar/develop/fundamentals) | On the phone | Built-in visual-inertial tracking, live | Google terms. Both test phones are ARCore-supported; accuracy on them is unmeasured. |
| [Jetson-ORB-SLAM3](https://github.com/ClarityLab-Org/Jetson-ORB-SLAM3) | Edge box | ORB-SLAM3 with its front end on an NVIDIA Jetson GPU | GPLv3. Authors report 32 frames per second on a 7 W Jetson Orin Nano. |

For a deeper comparison, including Android ports and why most are not ready to use, see the [ORB-SLAM research note](../../research/orb_slam/README.md) and the [Android SLAM review](../../research/orb_slam/android/README.md).

## Top 5 sources

| Source | What it is | Why it matters here |
|---|---|---|
| [ORB-SLAM3](https://arxiv.org/abs/2007.11898) | The standard feature-based SLAM paper and code (2021) | The classical reference for tracking, revisits and multiple maps. |
| [MASt3R-SLAM](https://arxiv.org/abs/2412.12392) | Learned dense SLAM (CVPR 2025) | The strongest learned comparison when a GPU is available. |
| [VGGT-SLAM 2.0](https://arxiv.org/abs/2601.19887) | Feed-forward SLAM (2026) | Works without calibration and also runs on a Jetson edge computer. |
| [RTAB-Map](https://github.com/introlab/rtabmap) and the [project note](../../research/sources/12_rtabmap.md) | Long-term SLAM with place recognition | Best route to correcting drift on revisits, including on Android. |
| [TUM RGB-D benchmark](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) and the [project note](../../research/sources/15_tum_rgbd.md) | Recordings with a motion-capture reference path | The scoring data for this layer. |

## What can be improved

- **Run the approved full-length tests.** 792 development frames and 573 held-out frames give the first numbers beyond a 1-second clip.
- **Seed tracking with features.** Use ORB or SIFT matches with depth to give Open3D a starting guess, and compare against the current start-from-no-motion setting on the same frames.
- **Add drift correction.** Compare RTAB-Map and ORB-SLAM3 loop closure on recordings that revisit places, and measure drift before and after.
- **Add the IMU.** Test visual-inertial tracking on a dataset with motion sensors (EuRoC or TUM-VI) and on phone recordings.
- **Score ARCore's own path.** On phone recordings with a reference, check whether ARCore's position is good enough to skip running our own tracker on site.
- **Pass corrections downstream.** When the path is corrected, rebuild every surface and object position that used the old path, and record which version of the path each result used.
- **Speed.** The baseline runs at 2.14 image pairs per second on a CPU. Live use needs a GPU tracker, an edge box or ARCore.

The sections below are the detailed experiment record.

## Current status and role

Camera pose estimation means finding the camera's position and orientation from successive observations. That is camera tracking. A CPU baseline now wraps Open3D 0.19.0 motion estimation using colour and supplied depth. Its known-motion and failure fixtures pass. The 30-frame real-data trial has completed and its inputs, trajectory plot and metadata have been inspected. The [geometry validation control](../geometry_validation/README.md) uses supplied depth and supplied poses to check coordinate handling and exports.

Feature detection and matching supply correspondences to a pose solver. They are different from detecting and identifying scene objects, which belongs to [Experiment 06](../06_object_recognition/README.md). A backend may instead use image intensity or learned correspondences. The experiment boundary covers the complete motion estimator rather than splitting a SLAM package's internal stages into independent services.

## Flow and backend boundary

```text
calibrated images + times + optional depth or motion sensors
  -> backend observation matching
  -> rotation/translation estimation and refinement
  -> camera poses + tracking status + segment/world identity
  -> Experiment 04, together with depth observations
```

The backend adapter keeps dataset ingestion, backend invocation, evaluation and exporting in separate modules. The implemented layout is:

```text
03_camera_pose_estimation/
  src/
    dataset.py       observations and timestamp association; no reference poses
    backend.py       adapter to an existing motion-estimation implementation
    evaluation.py    compare estimates against independent reference poses
    run.py           selection, configuration, orchestration and timing
  tests/
  runs/<unique-id>/
    input/
    output/          estimated poses and tracking/failure records
    debug/           matching views, trajectory and error plots
    metadata/
```

Backend internals can include feature extraction, pose optimisation and map management. Do not rebuild these merely to match our file layout. Portable records keep hosted and edge implementations interchangeable; measure transfer delay separately from estimator time. Ask the user before each GPU run.

A method that recognises revisited places may revise earlier poses. Record pose versions and corrections; reconstruction must update affected geometry or rebuild it. A reset creates a new segment/world origin until an explicit relationship is established. Never silently merge unresolved origins.

## The piece we are testing

Can successive observations produce reliable estimates of camera position and orientation? This piece owns movement estimates. It can use supplied benchmark depth while phone stereo remains unresolved, then accept Experiment 02's depth through the same interface.

The purpose is to separate movement-estimation errors from depth errors. Supplied RGB-D data makes this experiment runnable without a phone or either preceding piece. See the [dataset plan](../datasets/README.md). A plausible reconstructed scene does not independently establish that the camera path is correct.

## Development dataset and reference

Develop against acquired TUM RGB-D Freiburg1 xyz at `data/tum/rgbd_dataset_freiburg1_xyz/`. Supply colour, registered depth and declared calibration to the tracker. Keep `groundtruth.txt`, the independently measured camera trajectory, available only to evaluation. The local check found 798 listed colour images, 798 listed depth images and 3,000 finite pose rows. Associate timestamps explicitly. [Data conventions and inspection receipt](../../data/README.md#tum-format-reminder).

Freiburg1 desk is the preselected held-out sequence. Its official archive is acquired at 344,011,403 compressed bytes and extracted to 367,285,514 payload bytes. It contains 613 RGB rows, 595 depth rows and 573 associated RGB/depth pairs within 0.02 seconds. All paired images decode at 640 by 480. The adapter preserves the 25.44% pixels without depth measurements as invalid and applies no smoothing or hole filling; 0.015% contain finite depth at or beyond its 4 m processing limit. The local archive SHA-256 is `e983d6830916e66dc4a46a71368046b149b283de87769690e7aa4e0b9483530c`; the publisher lists no checksum. These checks establish input readability, not tracking accuracy. The reference trajectory remains reserved for evaluation after estimates have been saved. Freeze settings using xyz first. [Selection record](../../data/icl_nuim/held_out_tracking.json), [dataset acquisition record](../../data/README.md#tum-format-reminder). The observation adapter reads colour and depth without a reference pose field. The runner first persists all estimated statuses, then opens the independent reference file for scoring.

## Run the CPU development inspection

The approved trial uses the first 30 consecutive associated Freiburg1 xyz observations. Timestamp matches are one-to-one within 0.02 seconds. Colour and depth remain at 640 by 480 pixels. Camera calibration uses focal lengths 525 pixels and image centre (319.5, 239.5), with no additional undistortion. Depth is raw/5000 metres. Open3D hybrid odometry uses iterations [20,10,5], positive depth below 4 metres (the backend truncates exactly 4 metres), a 0.03 metre depth correspondence limit and identity pair initialization. These settings were confirmed on 2 October 2026. [Publisher calibration guidance](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats) and [backend options](https://www.open3d.org/docs/0.19.0/python_api/open3d.pipelines.odometry.OdometryOption.html) describe their source.

```powershell
python -m venv .venv-tracking
.venv-tracking/Scripts/python -m pip install -r experiments/03_camera_pose_estimation/requirements.txt
.venv-tracking/Scripts/python -B tools/check.py -q experiments/03_camera_pose_estimation/tests
.venv-tracking/Scripts/python -B -m experiments.03_camera_pose_estimation.src.run --dataset data/tum/rgbd_dataset_freiburg1_xyz --frames 30
```

The pinned packages work in the current Windows Python 3.12 environment. A clean environment install has not been tested. Before importing Open3D, the adapter reads its build configuration and rejects CUDA or SYCL builds. It requires the actual geometry implementation to be the CPU module. No GPU is required or used.

The CLI accepts a positive `--frames` count only for the workspace's Freiburg1 xyz and desk paths. It checks each official source URL and compares archive size and SHA-256 with acquisition and extraction receipts. The checked-in [member hash record](../datasets/tum_freiburg1_member_hashes.json) links the selected images, timestamp tables and reference trajectory to the verified archives. The run checks selected observations before tracking and checks the reference hash only after all estimates are saved. It then hashes the copied inputs in the run manifest. Each run also records the sequence, actual selected count and resource limits in its configuration and hyperparameters; the Open3D settings remain unchanged. On 3 October 2026, the user approved all 792 xyz observations and all 573 desk observations, with a 30-minute wall-clock limit and a 2 GiB per-process memory limit per sequence. A separate supervisor holds the worker until its Windows Job Object limit is installed. The worker checks that limit and rechecks archive provenance before inference. It also has a deadline watchdog. The supervisor terminates over-time work, records a failed receipt before detail files, and does not accept incomplete estimates. A valid artifact completed just after the deadline keeps its original hashes; an adjacent supervisor receipt marks it rejected. Parent-side archive hash checks happen before the 30-minute clock starts. Worker imports, source capture, estimation, scoring and reports happen inside it. Full-sequence inference has not yet run.

For fresh data acquisition, download the official [Freiburg1 xyz archive](https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz). Check the final HTTPS publisher host, successful response, content length against downloaded bytes, archive completeness and SHA-256. Keep the provenance alongside the archive. Use `experiments.datasets.acquisition.publish_archive` for bounded safe extraction into a fresh destination. Its downloader is specific to ICL data and must not be used for this TUM archive. The existing workspace dataset already has verified acquisition receipts.

Every selected image gets a status and colour/depth thumbnail. Failed observations have no pose. The next usable observation starts a new origin. Gaps above 0.1 seconds also reset the origin. Identity anchors are not counted as tracked edges. Poses map camera coordinates into their own segment's world, in metres. The backend's relative transform is inverted before accumulation.

The review page links scores, poses and shared timing metadata. Loading, backend pairs, evaluation and reporting have separate timing stages. The `odometry_pairs` stage counts attempted image pairs, including a backend call that returns tracking failure. Its rate is pairs per second. End-to-end throughput counts the selected images and includes snapshots, backend loading, scoring and reporting. The shared timing record declares that final manifest hashing and completion publication are excluded; the supervisor wall clock includes them. Process resources record sampled resident memory, peak Windows working set and peak Job Object process commit. These desktop measurements do not establish phone performance. The estimator retains a current image pair and stores small pose records, without a map.

Scoring places each segment into the reference frame using its first matched reference pose, with scale fixed at one. Anchor-only segments have unavailable accuracy. Relative errors use only adjacent successful matched observations within a segment. Scores pool squared errors by sample count and retain separate segment scores. This baseline has no loop closure or map recovery.

## Input and output agreement

Input contains timestamped images, calibration and optional depth in metres with a validity mask. Sensor observations require units, reference frames and clock relationships. Declare whether depth is registered to the image camera before combining pixels and depth.

Output is timestamped poses plus success, failure and segment information. For metric inputs, declare a transform such as `T_world_camera`, mapping camera coordinates into the world frame with translation in metres. Define axis directions, rotation representation and quaternion order. The first camera can define the origin; it does not establish gravity or a surveyed site origin.

An image-only method may return arbitrary scale. Label that explicitly rather than presenting translation as metres.

## Proposed steps and comparisons

1. Use TUM RGB-D with checked depth and timestamp conventions.
2. Estimate poses without providing reference poses to the estimator.
3. Use reference poses only as a named control or held-out evaluation target.
4. Compare a local RGB-D estimator with a method that corrects drift when revisiting places, subject to verified permissions.
5. Replace supplied depth with stereo predictions only on a sequence with matched stereo observations and a reference trajectory. TUM has no calibrated stereo pair, and Middlebury has no tracking sequence, so neither starter supports this swap. Verify a suitable synchronized TartanAir subset or independently measured phone sequence before this comparison.

Record inputs and settings. Tuning on a reference trajectory cannot then be presented as independent evaluation.

## Measurements, failures and decision

Measure path error, local movement error, tracked proportion, time to failure, recovery, runtime and memory. Metric evaluation must not fit a scale correction that hides scale errors. Declare any alignment used.

Include weak texture, repeated appearances, gaps, rapid movement and depth loss. Each pose carries a segment identifier and world-frame identifier. Failed tracking creates a new segment if its origin is reset. Reconstruction must keep unresolved segments separate and reject cross-segment fusion until a recorded transform establishes their shared frame. Do not join segments by pretending the camera stayed still.

Agree numeric limits from the capture use case before acceptance trials. Decide which tracker and failure signals reconstruction can use.

## Dependencies and first tasks

The initial control is desktop CPU work. Candidate versions already observed in the archived environment are Python3.12.10, NumPy2.4.2, SciPy1.17.1, Pillow12.3.0, Open3D0.19.0 and pytest9.0.2. They are a reproducibility starting point, not a verified clean-install lock. Matplotlib3.10.8 and psutil7.2.2 support reporting. No CUDA, PyTorch, phone app or RTAB-Map build is required initially. The trial uses the installed, tested desktop environment; requirements.txt pins its direct dependencies. A clean isolated install remains a separate deployment check.

The [official Open3D0.19 odometry tutorial](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_odometry.html) defines input assumptions and the relative-transform API. It is a baseline reference, not an accuracy result for this project.

[Task 02: standard references](../../task_list/closed/02_verify_standard_tracking_and_reconstruction_refere.md) and [Task 03: geometry contracts](../../task_list/closed/03_define_observation_and_pose_contracts_with_known_g.md) are complete. [Task 05: supplied-depth tracking](../../task_list/closed/05_evaluate_tracking_with_supplied_benchmark_depth.md) implements movement estimation. Reconstruction can proceed independently under task 04 using supplied poses. Settings and acceptance limits must be agreed before starting those estimator/evaluation experiments.

## Completed CPU trial

The [30-frame review](runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0/review.html) contains all selected colour/depth views, estimated poses and the independent reference comparison. The first 30 associated Freiburg1 xyz observations span 1.136 seconds. Their 29 motion estimates succeeded without resets or failed observations. All 30 have matched reference poses. This is a short development inspection; full-sequence and held-out desk evaluation remain outstanding.

| Measurement | Result |
|---|---|
| Tracking throughput | 2.135 image pairs/s; 29 pairs in 13.581 seconds |
| Whole-run throughput | 1.693 frames/s; 30 images in 17.724 seconds |
| Camera-position root-mean-square error | 6.926 mm |
| Adjacent-movement translation root-mean-square error | 6.947 mm |
| Adjacent-movement rotation root-mean-square error | 0.462 degrees |
| Peak desktop process memory | 440.0 MiB, including backend import and plotting |

[Timing metadata](runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0/metadata/timing.json) records individual samples and stage totals. Whole-run time includes input/source snapshots, loading, computation, scoring and report generation; final manifest hashing and completion publication happen afterward. Stage FPS uses summed counts divided by summed time. An odometry count means an image pair. No GPU was used. The desktop runtime used its existing thread defaults; these results do not measure phone performance or one-core throughput. The estimator retains a bounded image pair, while reporting and reference scoring are desktop work.

The 172 published artifacts pass hash verification. All 60 selected original images and the reference file match their source hashes; all 64 report links resolve. The trajectory preview follows the reference path. A previous attempt is retained as failed because reference conversion rejected rounded quaternion values. The evaluator now normalizes finite nonzero reference quaternions, with the conversion recorded in configuration; original bytes remain unchanged. Anchor-only segments and segments with just one matched reference pose report unavailable accuracy.

The CPU suite passes 130 tests. Timing and tracking together have 91% statement coverage; lint, formatting and type checks pass. Reviews covered transform direction, pose-free inputs, failure/reset origins, depth truncation, publication and source snapshots. Clean installation, mobile packaging, long trajectories, weak texture, revisits and held-out accuracy are still unverified.

## Research and reuse

[TUM RGB-D](../../research/sources/15_tum_rgbd.md) supplies independent movement references. [Open3D](../../research/sources/13_open3d_rgbd.md) informs a CPU baseline. [RTAB-Map](../../research/sources/12_rtabmap.md) addresses revisits. [MASt3R-SLAM](../../research/sources/14_mast3r_slam.md) is a later comparison with separate permission and hardware questions.

The geometry agreement has passed known-transform and failure tests. Reconstruction also accepts supplied poses independently. CPU tracking and independent scoring have now completed the short trial above. See the [experiment guide](../README.md).


## Inspecting measured depth and estimated camera motion

The labelled three-dimensional viewer shows the estimated camera position and orientation against the independently recorded reference poses. It uses the same first matched reference for each segment, with scale fixed at one. Failed observations remain visible without an estimated pose. Separate segments are not joined.

TUM Kinect depth is observed sensor input, not ground-truth depth or a model prediction. The trial includes missing depth and sensor noise, so it is not a perfect-depth control. Ground truth here refers to the independently measured camera poses. The supplied 16-bit depth needs conversion to metres for display. The colour preview shows blue near, yellow far, and black for missing measurements without smoothing or hole filling. Sidecar metadata records the scale and missing fraction; source links retain the original measurement files.

The questioned image `1305031102.160407.png` exactly matches the downloaded dataset. It has 77,325 missing pixels out of 307,200 (25.17 percent). Across the selected 30 frames, missing depth averages 25.12 percent. [Publisher format](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats) defines zero as missing and raw values divided by 5000 as metres. Task 13 retains full development and held-out validation.

[Open the verified labelled 3D inspection](runs/20261002T195923.778722Z_8bcaf965d8dc496192563205df59d85c/viewer.html). This new publication preserves the numerical run and its original input files. The original computation timing and the separate visual-publication timing are both linked.

## Proposed feature and revisit comparisons

[Task25](../../task_list/open/25_compare_feature_seeded_odometry_and_verified_camer.md) follows the frozen full-development/held-out baseline in Task13. The current adapter uses direct projected-pixel intensity/depth alignment and identity pair initialisation, not ORB/SIFT descriptors. The approved 30-frame trial is a short baseline only; the full sequence is unfinished. Do not change Task13 settings or run its full sequence as part of Task16.

The first local comparison should extract masked ORB and SIFT correspondences, pair each RGB feature with valid calibrated depth, reject invalid/out-of-range points and estimate a metric rigid transform with a robust solver. Use that transform and its inlier support to initialise/refine the existing Open3D RGB-D odometry. Compare against the existing identity-initialised Open3D path on exactly the same pairs. Freeze feature detector, descriptor, match filtering, robust solver and Open3D settings before held-out evaluation. Image similarity alone is only a retrieval score and never a camera transform.

For revisits, rank earlier keyframes with an appearance descriptor such as ORB bag-of-words or a masked image embedding, optionally followed by masked ZNCC. Keep retrieval separate from geometric verification. For each candidate, establish calibrated feature correspondences with valid depth and fit a metric SE(3) constraint. Record correspondence IDs, valid-depth count, inliers and inlier ratio, image reprojection and 3D residual distributions, overlap, transform uncertainty/information, reverse-pair consistency and graph residual. Reject weak-parallax or degenerate geometry, dynamic-only matches, inconsistent reverse/cycle transforms and candidates whose graph residual is an outlier. A low appearance distance is not grounds to add a pose-graph edge.

Compare this local feature-seeded Open3D route with pinned releases of RTAB-Map 0.22.1 (BSD-3-Clause; RGB-D loop retrieval and graph correction) and ORB-SLAM3 v1.0-release (RGB-D relocalisation and loop closure; GPLv3, so licence/build suitability must be checked). RTAB-Map builds may inherit OpenCV nonfree/SURF terms depending on configuration. The upstream sources and qualified claims are linked in the [Task16 research shortlist](../../research/README.md#camera-correction-shortlist). Neither backend has a local result in this project. Use matching inputs, reference-pose isolation, timing scope and failure reporting. Do not compare a vendor or paper rate with the project's end-to-end rate.

Accept a correction only after geometric verification, then create an explicit new pose revision. Keep original observations and earlier pose revisions immutable. Recompute or invalidate all dependent object positions and surface geometry against the same committed revision; do not publish mixed generations. Measure absolute trajectory error, relative pose error, drift before/after revisit, valid loop precision/recall, false loop edges, recovery after tracking loss, corrected downstream geometry, full processing time and memory. Reference poses are evaluator-only. Exact retrieval, inlier, residual, overlap, uncertainty and graph thresholds remain unselected and must be recorded by Task25 before a run. The later owner direction delegates choices and GPU tests; Task13 remains preserved and unfinished. Task16's research design remains pending owner review and this comparison has not executed tracking. No feature-seeded or loop-corrected local result is claimed.
