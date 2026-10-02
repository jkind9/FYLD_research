# MASt3R-SLAM: dense reconstruction from one-camera video

Riku Murai, Eric Dexheimer and Andrew J. Davison. **MASt3R-SLAM: Real-Time Dense SLAM with 3D Reconstruction Priors.** CVPR, 2025; arXiv first submitted December 2024. [Primary paper](https://arxiv.org/abs/2412.12392). [Official code and setup](https://github.com/rmurai0610/MASt3R-SLAM).

## Main takeaway

This is a relevant research comparison for ordinary RGB video because it estimates dense geometry and motion without requiring a depth image as input. It remains a literature reference here. Permission for company execution has not been established.

## What it does

The paper builds a tracking-and-mapping system around MASt3R's learned two-view reconstruction and matching. It introduces matching, camera tracking, local fusion, a graph of views, revisit detection and global optimization. It permits unknown camera calibration under its stated camera-centre assumption and also supports a calibrated variant. [Paper abstract](https://arxiv.org/abs/2412.12392).

The intended input is a sequence of RGB images. Outputs are dense scene geometry and camera poses. Unlike the current FYLD RGB-D baseline, the method's learned prior contributes to the inferred shape. This makes it a way to investigate image-only reconstruction, but a plausible-looking model is insufficient evidence for trench depth or asset position.

## Checked performance evidence

The paper abstract reports **15 frames per second**. The repository's **Reproducibility** section says its experiments used an **RTX 4090** and warns that other GPUs and the released multiprocessing implementation may differ. Input resolution and the full timing breakdown have **not been checked** here. These statements do not establish on-phone speed. [Abstract](https://arxiv.org/abs/2412.12392), [repository Reproducibility](https://github.com/rmurai0610/MASt3R-SLAM).

The repository provides MP4/image-folder entry points, optional calibration and evaluation scripts. Its documented setup uses PyTorch and CUDA. No model download, inference run or phone deployment is reported by this project.

## Limits and relevance to FYLD

An image-only metre-valued result must have a tested scale source. A checkpoint name containing “metric” is not an independent measurement guarantee. Hold out physical references and compare dimensions across devices, surfaces and viewpoints. Unknown and occluded surfaces need explicit treatment even when the learned model produces dense output.

Before considering live capture, test complete recorded clips. Include wet soil, repeated textures, low light, moving people and revisits. Measure failures and map completeness alongside trajectory accuracy. Desktop GPU throughput should be separated from capture, decode, transfer and export delay.

## Licence and two next questions

The SLAM [code licence](https://github.com/rmurai0610/MASt3R-SLAM/blob/main/LICENSE.md) is CC BY-NC-SA 4.0. MASt3R weights have a separate [CHECKPOINTS_NOTICE](https://github.com/naver/mast3r/blob/main/CHECKPOINTS_NOTICE). Code, weights and evaluation data require separate permission decisions; none is cleared here for company execution.

1. Can the required permissions be obtained for company research and the intended checkpoint?
2. On permitted independent site data, do scale and surface errors remain acceptable across weak texture and partial views?
