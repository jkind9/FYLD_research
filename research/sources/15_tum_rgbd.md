# TUM RGB-D: a controlled benchmark for camera motion

Jürgen Sturm, Nikolas Engelhard, Felix Endres, Wolfram Burgard and Daniel Cremers. **A Benchmark for the Evaluation of RGB-D SLAM Systems.** IROS, 2012. [Primary paper](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf). [Official dataset and tools](https://cvg.cit.tum.de/data/datasets/rgbd-dataset). [Canonical formats and calibration](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

## Main takeaway

TUM supplies physical depth and independently recorded camera motion. It lets this project test tracking and observed-surface fusion without first solving phone depth estimation. It is an indoor Kinect benchmark, not a phone stereo or outdoor worksite validation.

## What is supplied

The format page specifies 640×480 RGB PNGs and registered 16-bit depth PNGs. Depth divides by **5,000** to obtain metres; zero is missing. Poses use Unix seconds followed by translation and quaternion `qx qy qz qw`. The camera reference is defined by the motion-capture system. That reference must not be silently treated as the project's gravity or site level. [Formats, colour/depth and ground-truth sections](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

The publisher recommends the ROS-default intrinsics without additional undistortion for these registered images. Its depth correction is already applied. The local adapter follows that guidance rather than applying the Freiburg1 correction a second time. [Formats, calibration section](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

## Checked evidence and local use

The official format and licence statements were checked. The original paper's hardware table, reconstruction accuracy and algorithm runtime have **not been extracted** for this summary. A dataset's acquisition frame rate is not a processing speed result.

Task 00 acquired the Freiburg1 xyz archive, recorded as **448,204,271 bytes**, and used a short matched subset for the supplied-pose versus estimated-pose comparison. In that archived implementation, the supplied-pose branch was a control and ground truth reached the estimated branch only after reconstruction for evaluation. Local results belong in the experiment receipts rather than being attributed to the benchmark paper. The new tracking experiment must establish this separation independently.

This comparison can expose drift and transformation mistakes. It cannot establish surface accuracy where no independent surface reference is evaluated. Nor does registered Kinect depth demonstrate that browser phone video will have synchronized cameras, depth or calibration.

## Licence and FYLD use

The publisher states data is **CC BY 4.0 unless otherwise specified**, while accompanying code is **BSD-2-Clause**. [Official licence section](https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license). No pretrained weights are required for the present CPU baseline.

For FYLD, use TUM to test software contracts and failure reporting before evaluating safe phone recordings. Keep unknown map areas visible and evaluate metric scale with rigid alignment, without fitting a scale correction that hides an error.

## Two next questions

1. How does the estimator behave on longer TUM sequences with weak texture, gaps and revisits?
2. Which failures reappear on phone captures once supplied depth is removed?
