# ETH3D: separate tests for stereo surfaces and camera tracking

The official index identifies two source papers. Thomas Schöps, Johannes Lutz Schönberger, Silvano Galliani, Torsten Sattler, Konrad Schindler, Marc Pollefeys and Andreas Geiger. **A Multi-View Stereo Benchmark with High-Resolution Images and Multi-Camera Videos.** CVPR, 2017. Thomas Schöps, Torsten Sattler and Marc Pollefeys. **BAD SLAM: Bundle Adjusted Direct RGB-D SLAM.** CVPR, 2019. [Current official dataset index, publication links and code links](https://eth3d.ethz.ch/).

## Main takeaway

ETH3D is relevant to two different questions: whether stereo observations recover detailed surfaces, and whether a camera-tracking system estimates motion well. These are separate benchmarks. A result on one must not be presented as evidence for the other.

## What it provides

The official index separates the **stereo benchmark**, introduced by the 2017 paper, from the **SLAM benchmark**, introduced with BAD SLAM in 2019. Stereo evaluation concerns geometry from multiple views; SLAM concerns estimating motion while constructing a map. [Official index, Benchmarks and Publications](https://eth3d.ethz.ch/).

For FYLD, the intended outputs to evaluate would be reconstructed surfaces for stereo and camera trajectories/maps for tracking. The precise inputs, calibration, depth availability and reference geometry must be checked for the selected track and sequence before adapting the pipeline. “ETH3D” alone is not a complete input specification.

## Evidence and limits

The current index, paper identities and dataset licence were checked. Track-specific image resolution, sensor hardware, published algorithm runtime and accuracy tables have **not been checked** in this summary. No ETH3D data was downloaded or executed here. The previous `www.eth3d.net` address is not the current source used by this review.

These benchmarks are possible later tests, not permission-cleared company experiments. Even a strong result would need a further trial on construction and utility recordings. Wet ground, moving workers, narrow exposed assets and inaccessible viewpoints can affect the useful observed geometry. Benchmark rankings alone do not identify which surfaces a safe handheld recording misses.

Stereo's physical scale depends on calibrated camera geometry and baseline. RGB-D uses a depth scale. Neither should be mixed with image-only reconstruction that obtains scale differently. Evaluation must record its alignment rule and preserve unobserved regions.

## Licence and proposed role

The official data licence is **CC BY-NC-SA 4.0**. [Publisher licence section](https://eth3d.ethz.ch/). Company R&D permission has not been established, so no download or execution is authorized by this summary. Dataset terms are separate from the linked benchmark software's code licence and any model weights; those assets are not cleared here.

If permission is obtained, choose a track that isolates a specific weakness: stereo surface error or RGB-D tracking drift. Compare the same method settings with other permitted data before attributing a change to scene difficulty.

## Two next questions

1. Can the publisher confirm permission for the proposed company research use?
2. Which specific benchmark track and reference measurements best test the surface errors FYLD needs to detect?
