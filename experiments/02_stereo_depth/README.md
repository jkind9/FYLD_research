# Experiment 02: stereo depth estimation

## The piece we are testing

Given two images and their camera geometry, can we estimate useful distance at image locations? This piece owns depth quality. Its inputs can come from a recording, phone or backend. Phone execution is a later placement comparison, not a condition of the method.

Start with recorded fixtures so network or camera changes cannot silently change comparisons. Public calibrated stereo data supports initial testing without a phone or Experiment 01 implementation. Experiment 01 can later supply Samsung S23 or Redmi recordings. See the [dataset plan](../datasets/README.md).

## Development dataset and reference

Develop against the acquired Middlebury version 3 quarter-resolution training data at `data/middlebury/dataset/MiddEval3/trainingQ/`. Its 15 scenes have left/right images, scene calibration, left-view reference disparity and evaluation masks. Use the supplied disparity and masks only for evaluation, converting disparity to metres with each scene's calibration and principal-point offset. Inputs and reference files are already extracted and verified. [Local data and receipts](../../data/README.md).

Choose and record development and held-out scenes from these 15 labelled scenes before method tuning. The separately acquired test images have no public reference disparity, so they cannot provide a local accuracy score. The geometry adapter, scene split and estimator tests still need to be implemented. Middlebury supports initial independent development; outdoor and real phone performance remain later validation questions.

## Input and output agreement

Input comprises two images, camera identifiers, capture timestamps, intrinsics, distortion and relative camera pose. Calibration translation is in metres. Record crop, resize and rotation transformations; image coordinates refer to the declared processed images.

Output comprises depth in metres, a validity mask, and confidence only if provided. Define depth as distance along the selected camera's forward axis, or declare another convention. Preserve reference camera, timestamp and calibration identity. Failed matches are invalid. A stereo method's pixel displacement must be converted using the matching calibration before being called metric depth.

## Proposed steps and comparisons

1. Establish image alignment and calibration checks on static recorded pairs.
2. Run a conventional stereo baseline with settings recorded.
3. Compare against independently measured distances and visible boundaries.
4. Examine a learned stereo alternative after checking code and weight permissions.
5. Run the same inputs and method at alternative execution locations. Separate preprocessing, inference and delivery time.

Available native phone depth can be a comparison. Label its origin; it is not independent stereo ground truth.

## Measurements, failures and decision

Report distance error by range, valid coverage, edge error, timing sensitivity, runtime and memory. Phone execution adds sustained performance and thermal observations. Paper frame rates are not acceptance limits for our devices.

Include weak texture, occlusion, reflections, motion and differing exposure. Reject incompatible calibration and image dimensions explicitly. Distinguish inaccurate depth from unavailable depth.

Agree quality and coverage requirements before acceptance trials. A desktop success does not establish phone performance; fast phone execution does not establish accuracy.

## Research and reuse

[MobiDepth](../../research/sources/01_mobidepth.md) and [HiMoDepth](../../research/sources/02_himodepth.md) inform timing and mobile processing. [MobileStereoNet](../../research/sources/03_mobilestereonet.md) and [BANet](../../research/sources/04_banet.md) are candidate references. [ARCore raw depth](../../research/sources/06_arcore_raw_depth.md) provides a separate comparison route.

Promote a depth interface when tracking or reconstruction consumes its fixtures without knowing where inference ran. No method or result is claimed here. See the [experiment guide](../README.md).
