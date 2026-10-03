# Experiment 03: camera pose estimation

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

For fresh data acquisition, download the official [Freiburg1 xyz archive](https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz). Check the final HTTPS publisher host, successful response, content length against downloaded bytes, archive completeness and SHA-256. Keep the provenance alongside the archive. Use `experiments.datasets.acquisition.publish_archive` for bounded safe extraction into a fresh destination. Its downloader is specific to ICL data and must not be used for this TUM archive. The existing workspace dataset already has verified acquisition receipts.

Every selected image gets a status and colour/depth thumbnail. Failed observations have no pose. The next usable observation starts a new origin. Gaps above 0.1 seconds also reset the origin. Identity anchors are not counted as tracked edges. Poses map camera coordinates into their own segment's world, in metres. The backend's relative transform is inverted before accumulation.

The review page links scores, poses and shared timing metadata. Loading, backend pairs, evaluation and reporting have separate timing stages. The `odometry_pairs` stage counts attempted image pairs, including a backend call that returns tracking failure. Its rate is pairs per second. End-to-end throughput counts the 30 unique selected images and includes snapshots, backend loading, scoring and reporting. The shared timing record declares that final manifest hashing and completion publication are excluded. Process memory includes the desktop backend and plotting, so these measurements do not establish phone performance. The estimator retains a current image pair and stores small pose records, without a map.

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
