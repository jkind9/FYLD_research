# Open3D RGB-D odometry: motion from colour and supplied depth

Qian-Yi Zhou, Jaesik Park and Vladlen Koltun. **Open3D: A Modern Library for 3D Data Processing.** arXiv:1801.09847, 2018. [Library paper](https://arxiv.org/abs/1801.09847). This summary focuses on the [official Open3D 0.19.0 RGB-D odometry tutorial](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_odometry.html) and [API contract](https://www.open3d.org/docs/0.19.0/python_api/open3d.pipelines.odometry.compute_rgbd_odometry.html). [Official code](https://github.com/isl-org/Open3D).

## Main takeaway

Open3D provides an inspectable baseline when registered depth already exists. It helps isolate camera-motion and fusion errors before adding a learned depth model. It does not solve the separate question of obtaining reliable depth from ordinary phone video.

## What it does

The tutorial takes two consecutive colour/depth observations plus camera calibration and estimates their relative rigid motion. It assumes colour and depth are synchronized and registered. The hybrid method compares both image brightness and depth geometry, whereas the colour-only term compares brightness. The API returns success, a 4×4 motion transform and a 6×6 information matrix. [Tutorial and API](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_odometry.html).

The archived Task 00 implementation used this hybrid method on CPU with Open3D 0.19.0. It added texture, motion, timestamp-gap and depth-overlap checks. It accumulated accepted poses, backprojected supplied depth, averaged points within voxels and applied a statistical outlier filter. It stopped at the first tracking break. These describe the archived implementation, not claims from the library paper or the new experiment plans.

The resulting observed points are projected into colour and height maps. Unknown height cells remain missing. Counts represent retained fused samples, not confidence. Although Open3D also offers volume integration, including a truncated signed distance field (TSDF), this prototype does **not** implement that mesh-producing pipeline.

## Evidence and limits

The tutorial's input assumptions and API output are checked. Its numerical benchmark tables, hardware, resolution-dependent runtime and original method-paper results have **not been checked** here. The documented pyramid iteration defaults are `[20,10,5]`; they are not a phone performance claim.

Motion-estimation success does not guarantee that a plain surface constrains every direction of motion. Local gates may miss an incorrect estimate. Supplied depth gives this experiment metric scale, but surface accuracy still needs an independent geometry reference. A declared up direction also does not establish gravity alignment.

For FYLD, this motivates a controlled comparison: hold depth fixed and change the source of camera poses. The [independent experiment plans](../../experiments/README.md) separate that question from phone capture and depth estimation.

## Licence and two next questions

Open3D code is [MIT licensed](https://github.com/isl-org/Open3D/blob/main/LICENSE). Dataset terms are separate; this baseline uses no learned weights.

1. Which low-texture or low-overlap inputs pass the gates while producing an incorrect map?
2. Against a known surface, how much error comes from pose estimation versus voxel averaging and filtering?
