# ICL-NUIM: checking the reconstructed surface, not only camera motion

Ankur Handa, Thomas Whelan, John B. McDonald and Andrew J. Davison. **A Benchmark for RGB-D Visual Odometry, 3D Reconstruction and SLAM.** ICRA, 2014. [Official dataset, paper and evaluation-tool links](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html).

## Main takeaway

ICL-NUIM can help answer whether a correct-looking map is geometrically correct. Its living-room data includes a reference surface, so it can test reconstruction error independently of trajectory error. This is a proposed follow-up; the dataset has not been downloaded or run here.

## What it provides

The publisher offers synthetic colour/depth sequences and reference camera poses for living-room and office scenes. The **living room** additionally has reference 3D surface geometry; the **office** does not have an explicit surface model. Clean and noisy versions are available, including a TUM-compatible image format that still requires the correct camera parameters. The **Surface Reconstruction Quality Evaluation** section links the SurfReg comparison tool. [Official specification](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html).

The inputs to a reconstruction method are colour/depth observations and calibration. The reference poses and surface should be used as controls or held-out evaluation targets according to an explicitly named experiment. Estimated output can then be compared with both the camera path and the known surface.

## Checked evidence and limits

The official page's dataset distinction, citation, noise variants and licence were checked. Its `lr kt0` listing gives **1,510 images**, **30 Hz** and about **51 seconds**. These describe the sequence, not processing speed. Render resolution, sensor-noise parameters, benchmark hardware, method runtime and numerical paper results have **not been checked** in this summary.

Synthetic scenes give known geometry but do not prove performance on real excavation footage. Wet reflections, moving people, sunlit soil and camera processing require separate site trials. The value here is controlled comparison: change noise or pose source while holding the scene fixed, then measure the change in observed geometry.

## Relevance to FYLD and scale

The current desktop prototype evaluates trajectory agreement but has no evaluated independent surface reference for its TUM run. The living-room benchmark could fill that specific gap. Compare supplied-pose fusion with estimated-pose fusion, keeping depth and selected observations identical. This would help separate tracking error from fusion/filtering error.

Use the dataset's metric geometry and checked depth convention. Do not rescale an erroneous output merely to improve a score. Evaluate only comparable observed surfaces, and report missing coverage separately from distance error. A method that reconstructs one easy wall accurately can still omit most of the useful scene.

## Licence and two next questions

The publisher states data is **CC BY 3.0**. Code tools and any estimator weights have separate terms; the data licence does not cover them. No learned weights are required to test the present baseline.

1. How much surface error remains with exact poses compared with estimated poses?
2. Which noise settings increase error or remove coverage, and do those failures resemble permitted real phone captures?
