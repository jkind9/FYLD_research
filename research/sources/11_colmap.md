# COLMAP: reconstructing a scene from overlapping photographs

Johannes Lutz Schönberger and Jan-Michael Frahm. **Structure-from-Motion Revisited.** CVPR, 2016. [Primary paper](https://openaccess.thecvf.com/content_cvpr_2016/html/Schonberger_Structure-From-Motion_Revisited_CVPR_2016_paper.html). [Official documentation](https://colmap.github.io/). [Official code](https://github.com/colmap/colmap).

## Main takeaway

COLMAP is a useful reference for the question “can these photographs support a reconstruction at all?” It offers an image-only desktop comparison before assuming that ordinary phone footage contains enough information for a measurable worksite map. A preliminary local run used benchmark images; construction-site performance remains untested.

## What it does

The documented pipeline recovers camera positions and a sparse set of scene points from overlapping images, a process called structure from motion (SfM). A separate dense stage compares views to create more detailed geometry, called multi-view stereo (MVS). Ordered video frames and unordered photographs are supported. Its sparse camera model and dense surface output are different products; registering some cameras does not prove a complete surface was recovered. [Official overview, Features](https://colmap.github.io/).

For this project, the important input is a collection of photographs with shared visible detail. The intended outputs would be camera poses, sparse points and, if a dense stage succeeds, surface geometry. Without an independent physical scale reference, an image-only reconstruction cannot automatically be treated as a metre-valued site measurement.

## Evidence and limits

This summary checks the official overview and the publication identity. The original paper's benchmark tables, exact hardware, image resolution and runtime have **not been checked** here. No numerical speed or accuracy result is adopted. COLMAP is treated as a batch desktop baseline; the overview is not evidence of real-time phone execution.

FYLD footage may show plain soil, wet surfaces, repeated patterns or moving workers. Those conditions should be tested rather than assumed equivalent to the paper's images. Safe viewpoints may also leave hidden trench surfaces. A reconstruction should preserve those omissions, not turn them into an apparent complete excavation.

## Licence and local status

The reference checkout is pinned to 3.12.6, commit `4d5b60e19ad268072adaf1267d21fa38a9a828ca`. Its [code licence](https://github.com/colmap/colmap/blob/3.12.6/COPYING.txt) is BSD-3-Clause. Dependencies and input datasets have separate terms. The baseline requires no pretrained weights.

A preliminary CPU run using pycolmap 3.12.6 registered 120 of 120 TUM colour images in its largest component and exported 8,217 sparse points. Mean reprojection error was 0.7854 pixels. This measures image consistency, not physical accuracy. Runtime was 172.32 seconds. These are local measurements, separate from the paper's benchmarks. The output remains at arbitrary scale and is not a dense surface. Final independent implementation review is pending.

## Two next questions

1. Can representative safe phone captures register enough cameras to cover the target surfaces?
2. After setting scale with one reference, how closely do reconstructed distances match separate held-out measurements?
