# Experiment 03: camera tracking

## The piece we are testing

Can successive observations produce reliable estimates of camera position and orientation? This piece owns movement estimates. It can use supplied benchmark depth while phone stereo remains unresolved, then accept Experiment 02's depth through the same interface.

The purpose is to separate movement-estimation errors from depth errors. Supplied RGB-D data makes this experiment runnable without a phone or either preceding piece. See the [dataset plan](../datasets/README.md). A plausible reconstructed scene does not independently establish that the camera path is correct.

## Development dataset and reference

Develop against acquired TUM RGB-D Freiburg1 xyz at `data/tum/rgbd_dataset_freiburg1_xyz/`. Supply colour, registered depth and declared calibration to the tracker. Keep `groundtruth.txt`, the independently measured camera trajectory, available only to evaluation. The local check found 798 listed colour images, 798 listed depth images and 3,000 finite pose rows. Associate timestamps explicitly. [Data conventions and inspection receipt](../../data/README.md#tum-format-reminder).

Freiburg1 desk is the preselected held-out sequence. It is not yet downloaded; acquire it before held-out evaluation and freeze settings using xyz first. Its acquisition is not required to implement the initial tracker. [Selection record](../../data/icl_nuim/held_out_tracking.json). The observation adapter and tracker have not yet been implemented in this experiment.

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

The initial control is desktop CPU work. Candidate versions already observed in the archived environment are Python3.12.10, NumPy2.4.2, SciPy1.17.1, Pillow12.3.0, Open3D0.19.0 and pytest9.0.2. They are a reproducibility starting point, not a verified clean-install lock. Matplotlib3.10.8 and psutil7.2.2 support reporting. No CUDA, PyTorch, phone app or RTAB-Map build is required initially. Recheck a clean environment before execution and pin the actually working set.

The [official Open3D0.19 odometry tutorial](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_odometry.html) defines input assumptions and the relative-transform API. It is a baseline reference, not an accuracy result for this project.

[Task 02: standard references](../../task_list/closed/02_verify_standard_tracking_and_reconstruction_refere.md) is complete. Begin with [Task 03: geometry contracts](../../task_list/open/03_define_observation_and_pose_contracts_with_known_g.md); [Task 05: supplied-depth tracking](../../task_list/open/05_evaluate_tracking_with_supplied_benchmark_depth.md) follows. Reconstruction can proceed independently after task 03. Settings and acceptance limits must be agreed before starting either experiment.

## Research and reuse

[TUM RGB-D](../../research/sources/15_tum_rgbd.md) supplies independent movement references. [Open3D](../../research/sources/13_open3d_rgbd.md) informs a CPU baseline. [RTAB-Map](../../research/sources/12_rtabmap.md) addresses revisits. [MASt3R-SLAM](../../research/sources/14_mast3r_slam.md) is a later comparison with separate permission and hardware questions.

Promote the pose agreement after known-transform and failure cases pass. Reconstruction must also accept supplied poses independently. This plan has not been run. See the [experiment guide](../README.md).
