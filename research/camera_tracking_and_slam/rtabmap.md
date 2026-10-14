# RTAB-Map: tracking and mapping with revisits

Mathieu Labbé and François Michaud. **RTAB-Map as an Open-Source Lidar and Visual SLAM Library for Large-Scale and Long-Term Online Operation.** Journal of Field Robotics, 36(2), 416–446, 2019. [Journal DOI](https://doi.org/10.1002/rob.21831). [Author arXiv deposit](https://arxiv.org/abs/2403.06341), submitted in 2024 and explicitly naming the 2019 journal reference. [Official code](https://github.com/introlab/rtabmap).

## Main takeaway

RTAB-Map is a candidate for testing whether recognizing an earlier viewpoint reduces accumulated drift. That directly addresses a limitation of the present FYLD desktop experiment, which estimates adjacent motion and has no loop closure. The candidate has been fetched as a reference, not executed.

## What it does

The paper describes estimating a sensor's motion while building a map, called simultaneous localization and mapping (SLAM). RTAB-Map began with recognizing revisited places from appearance and managing memory for long operation. It supports visual and lidar configurations, allowing comparisons with different sensors rather than requiring one fixed camera setup. The abstract names KITTI, EuRoC, TUM RGB-D and MIT Stata Center among its evaluation data. [Paper abstract](https://arxiv.org/abs/2403.06341).

For FYLD, a useful first comparison would supply the same registered colour/depth observations used by the simple baseline. The outputs of interest would be the trajectory, observed map and corrections after revisits. Stereo or inertial capture would be a separate configuration with its own calibration and synchronization requirements.

## Evidence and limits

The abstract and publication metadata are checked. Hardware, resolution, individual benchmark tables and runtime have **not been checked** in this summary. The term “online” describes the paper's goal; it does not establish a latency or battery budget on a FYLD phone.

Revisit correction is only useful if it improves the measured map. A falsely matched revisit could distort it. An evaluation should therefore include similar-looking work areas, moving equipment, an interrupted recording and a return to an earlier viewpoint. Compare independent dimensions before and after correction, not just whether the application reports success.

Metric scale depends on the selected sensor configuration. A depth camera or calibrated stereo pair can supply a physical scale source; one-camera images alone require an explicit scale treatment. A robot benchmark also does not establish that footage collected for site risk assessment has sufficient overlap.

## Licence and local status

Reference version 0.22.1 is pinned to `df6300e0ba3e90058f90b09c4d646279366d3516`. Its [code licence](https://github.com/introlab/rtabmap/blob/0.22.1/LICENSE) is BSD-3-Clause. Optional dependencies, datasets and any added weights need separate checks. No RTAB-Map build or run has been completed in this project.

## Two next questions

1. Does loop closure improve independently measured surface dimensions on a controlled revisit sequence?
2. What desktop memory, processing delay and restart behavior does the chosen configuration show on longer phone recordings?
