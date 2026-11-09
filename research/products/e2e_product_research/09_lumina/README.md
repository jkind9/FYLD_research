# Lumina 3D and Lumina Studio: iPhone LiDAR capture, desktop splat training (commercial)

**Take-away:** Lumina follows the same split this project chose: the phone captures, a PC processes. The iPhone app records images, LiDAR depth and camera poses with live coverage colouring, refines and merges scans, and exports a COLMAP dataset. The Windows app trains a photo-realistic 3D scene (a Gaussian splat) on an NVIDIA GPU, then measures and draws floor plans. It needs a LiDAR iPhone; versions for phones without LiDAR and for Android are planned for 2027. Every part has an open-source counterpart, listed in [Lumina and the open-source parts](../../../gaussian_splatting/lumina_open_source_parts.md).

Checked on 8 November 2026 from the vendor's pages and App Store listing, after the owner saw a demo. The [Reddit announcement](https://www.reddit.com/r/GaussianSplatting/comments/1xo5id3/lumina_3d_v23_lumina_studio_v014_are_now_available/) could not be read, because Reddit refuses automated reading. Nothing was installed or tested. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Maker | Deluva (3D-Deluva); App Store seller Nicolas Tsuchiya |
| Versions | Lumina 3D 2.3 (iPhone/iPad). Lumina Studio 0.1.4 beta for Windows, released 4 November 2026 |
| Input | Live iPhone or iPad camera with LiDAR (iOS 26.1+). Studio also takes image folders, COLMAP datasets, 360° video and RealityScan exports |
| Recorded | RGB images, LiDAR depth and camera poses together; manual or locked exposure and white balance; near and far depth limits |
| Output | Merged point cloud and COLMAP dataset (phone). Splat scene as PLY, SPLAT or SOG; measurements; floor plans as GLB, PNG, SVG, DXF and PDF (PC) |
| Where it runs | Capture, refinement, merging and beta splat training on the phone. Full training on a Windows PC: "NVIDIA CUDA required", minimum RTX 3060 8 GB, recommended RTX 4090 24 GB |
| Live | The capture view and its 2D/3D coverage map. Training happens after capture |
| Works from an Android phone with no laser sensor | No. Both are on the roadmap for 2027 |
| Measures in metres | Partly. Studio measures distances and areas; no accuracy is published |
| Counts each object once | No |
| Cost | Lumina 3D free with Pro at $14.99 a month or $119 a year. Studio sold through Gumroad, licence for two PCs; the App Store text calls it "a free Beta for Windows" |
| Methods named | None. COLMAP appears only as a file format |

## How it works

1. **Capture.** The app records images, LiDAR depth and poses at once. Coloured marks in the camera view show "which areas are well captured and where additional scanning is needed". A 2D and 3D map shows the path and coverage. "AutoMagic" measures the light and locks camera settings. Point spacing adapts "from 5 cm down to 1 mm".
2. **Refine and merge on the phone.** "Refine camera poses and captured geometry using RGB images, LiDAR depth, joints and spatial anchors." Overlapping scans merge into one dataset; originals are kept.
3. **Export.** A COLMAP dataset (images undistorted) for LichtFeld Studio, PostShot or Brush, or a `.lumi` project for Studio.
4. **Train on the PC.** Studio trains with resolution raised in stages, a default target of 3 million splats, sensor depth when present and person masks. A live viewer shows training scores.
5. **Measure and plan.** Distances, areas and floor plans from the point cloud or splat centres.

## Evidence and limits

- No method, accuracy or speed figure is published. The vendor does not define "joints".
- Splat scenes are optimised to look right from the captured views. Their shape can still be wrong, so they are not a measurement record.
- iPhone LiDAR is low resolution (256 × 192 in apps that save it raw, such as Stray Scanner) and is usually quoted as reaching about 5 m. The Pro app's listing gives an adjustable depth range of 0.15–10 m; the version 2.2 notes extend it to 20 m as "Work in Progress".

## Compared with this repository

| This repository's layer | Does Lumina cover it? |
|---|---|
| 1. Capture | Yes, on an iPhone with LiDAR; locked exposure and coverage view, which this project's app lacks |
| 2–3. Depth and camera position | LiDAR depth and ARKit poses, refined on the phone; method unpublished |
| 4. 3D model | Yes: merged point cloud and splat scene; measurement accuracy unknown |
| 5. Objects | No; only automatic person masks |
| Live updates | Capture preview only |

## How to test it here

The project has no iPhone of any kind (owner, 8 November 2026), so Lumina cannot be tried here. The owner also deferred splat scenes that day: the measure that matters is the dimensional accuracy of objects YOLO places in 3D. Steps 1 and 2 below stay useful only if splats are wanted later; step 1's COLMAP export also helps COLMAP refine ARCore's path.

1. Write a known-pose COLMAP export from the 15 October Redmi walk, the step Lumina performs on the phone.
2. If the owner allows GPU use, train it in Brush or LichtFeld Studio, the same trainers Lumina exports to, and compare the splat scene with the fused surface.
3. With a LiDAR iPhone, capture the same room with Lumina 3D Light (free) and compare five tape-measured distances against the Redmi surface.

## Sources

- [3D-Deluva site](https://3d.deluva.de/) · [Lumina 3D](https://3d.deluva.de/index.php/lumina-3d/) · [Lumina Studio](https://3d.deluva.de/index.php/lumina-studio/) · [Roadmap](https://3d.deluva.de/index.php/roadmap/)
- [Lumina 3D on the App Store](https://apps.apple.com/app/id6759076903) · [Lumina 3D Light](https://apps.apple.com/app/id6767272286)
- [Lumina Studio on Gumroad](https://deluva.gumroad.com/l/lumina-studio)
