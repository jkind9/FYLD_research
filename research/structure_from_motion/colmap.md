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

Since 13 October the project has run the official COLMAP 4.2.1 Windows build without CUDA, with pycolmap 4.2.1 only for reading models ([research/experiments/sfm](../experiments/sfm/README.md)).

## Lessons from the project's runs (13 October to 8 November 2026)

### A safety limit rejected a real lens calibration

The incremental mapper drops any camera with a lens distortion number above `--Mapper.max_extra_param` (default 1). The limit is there because a large value usually means COLMAP's own lens estimate has gone wrong. TUM's published fr1 calibration has k3 = 1.1633. The three distortion terms (0.26, −0.95 and 1.16) mostly cancel, so the image corner bends by only about 5%. Even so, every starting pair lost both cameras ("Discarding reconstruction due to bad initial pair") and no model was built.

With the limit raised to 2, the same matches placed all 298 desk frames: 15.2 mm path error after a best fit with size, against 24.0 mm with the plain default calibration. Converting pixels to rays and back with this calibration gives 0.00 px error, so the lens maths was never the problem. The global mapper has no such setting and still fails with this calibration, for a reason not yet found. The run is recorded in [research/experiments/sfm](../experiments/sfm/README.md).

The same check applies when COLMAP is used to estimate the Redmi's lens: raise the limit before trusting a failure.

### Why COLMAP is a reference here, not the product

- **It works after capture ends.** About 20 seconds of TUM desk video took about 2 minutes on a 32-thread desktop, and nothing comes out until the end. The owner requires updates at least once per second.
- **It uses only the images.** It ignores the motion sensors and ARCore depth, so the model has no real-world size. It also fails where images alone carry too little: blank walls (on ICL's synthetic living room the global mapper dropped 11 of 440 frames, the incremental mapper 7), blur, or turning on the spot.
- **Its output is sparse.** About 30,000 points on the desk clip, covering 4-20% of the surfaces (Task72). Its dense step (PatchMatch stereo) needs an NVIDIA GPU, which is not allowed.
- **It is desktop software.** The deployment target is the phone.

SLAM is the live counterpart. It tracks as frames arrive and re-solves only recent frames, plus a correction when a place is revisited. ARCore is that kind of tracker, already running live on the phone with the motion sensors. Systems that run COLMAP itself as live tracking are reviewed in [colmap_based_slam.md](../camera_tracking_and_slam/colmap_based_slam.md).

### COLMAP parts that fit a pipeline that already has ARCore's path

ARCore supplies the camera path live, so COLMAP's mappers are not needed. The useful parts start from known poses. All are BSD-3 and run on a CPU.

| Part | What it would do here | Where it fits | Status |
|---|---|---|---|
| Triangulation with known poses (`point_triangulator`, or `pycolmap.triangulate_points`), with `spatial_matcher` to pair frames by camera position | Matches features between frames taken from different spots and places each point in 3D along ARCore's path: thousands of real-size points, far ones included, to size learned depth beyond ARCore depth's ~2.5 m reach | Offline `room_build` first; a version limited to the last few keyframes could run in the live loop | Not tried on the Redmi walks. On TUM, sizing learned depth to SfM points fixed most of its size error (Task72) |
| Bundle adjustment from ARCore's poses (`bundle_adjuster`, or `pycolmap.create_pose_prior_bundle_adjuster` with `PosePrior`) | Refines path and points together, with ARCore positions as soft priors so the size holds. A test for walls that appear twice: if they merge, path drift caused them | Offline diagnosis (Task102) | Not tried |
| Lining up a COLMAP path with ARCore's (`model_aligner`, `pose_prior_mapper`) | An image-only path compared with ARCore's, or built with ARCore positions as a guide | Offline check (Tasks 75 and 102) | Planned |
| Lens self-calibration (mapper with lens refinement on) | Focal length and distortion of the Redmi from a walk, as a cross-check on ARCore and Task103 | Offline, one run | Not tried; raise `max_extra_param` first |
| Text model export and `image_undistorter` | The folder format every Gaussian splat trainer reads | Offline | Recommended in [lumina_open_source_parts.md](../gaussian_splatting/lumina_open_source_parts.md); not built |
| Multi-view agreement rule from `stereo_fusion` | Keeps surface only where views at least 3° apart agree | Room clean-up | In use as `clean.wide_support` (Task124): removed 17% of points, not the door echoes |

For dense depth along a known path without a GPU, [Mobile3DRecon](../dense_surface_fusion/mobile3drecon.md) ran multi-view stereo on one phone CPU core at 48 ms per keyframe. How triangulated points and dense stereo would combine with the project's learned depth: [triangulation_and_learned_depth.md](../dense_surface_fusion/triangulation_and_learned_depth.md).

Not needed: the mappers (ARCore gives the path), PatchMatch stereo (GPU), vocabulary-tree matching for revisits (ARCore corrects its anchors itself), and meshing (Open3D, already installed, has the same Poisson mesher).

### Triangulation with known poses compared with frame-to-frame feature linking

The owner's idea (8 November) of sticking frames together with ORB features is the same core step: find the same spot in two frames, then use where the cameras were to place it in 3D. Three details decide whether it works:

1. **Who supplies the camera positions.** Here ARCore does, with the motion sensors and real size. The matches are used only to place points. The project's earlier overlap chain (Task65) solved the path and carried the size forward through tracked corners at the same time, so errors built up: it still missed by 0.37 m on xyz and 1.01 m on desk.
2. **Which frames are paired.** At 30 frames a second and 1 m/s, neighbouring frames are about 3 cm apart. Depth error is roughly depth² × matching error ÷ (focal length × baseline). For a point 5 m away, a 500 px focal length and 1 px matching error, that is about 1.7 m between neighbouring frames and about 5 cm between frames 1 m apart. So frames have to be paired by distance between camera positions, not by time. COLMAP-SLAM measured the same effect: keyframes every 0.2 s gave errors up to 121 cm, against at most 10.3 cm every 1 s.
3. **Checks on each point.** Keep only matches that pass a two-view geometry check (RANSAC), points seen in several frames, a minimum angle between viewing rays, and a small reprojection error. COLMAP's triangulator does all four.

ORB against SIFT is a smaller choice. ORB is faster and fine in good light. COLMAP offers SIFT and ALIKED, not ORB. OpenCV, already installed, has ORB and `cv2.triangulatePoints` for a live version.

## Two next questions

1. Can representative safe phone captures register enough cameras to cover the target surfaces?
2. After setting scale with one reference, how closely do reconstructed distances match separate held-out measurements?
