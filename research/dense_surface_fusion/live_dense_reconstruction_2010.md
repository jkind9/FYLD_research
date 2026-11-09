# Live dense reconstruction with one moving camera (Newcombe and Davison, 2010)

**Take-away:** The first system to build a dense surface live from one ordinary moving camera. It takes a sparse tracker's points, fits a rough surface to them, and corrects that surface pixel by pixel with optical flow between a reference frame and 3 nearby frames. It worked at desk scale (camera 0.3 m from the scene) on a PC with two GPUs, and reports no accuracy against a reference. Two of its ideas apply here: use the surface already built to predict each new view, and correct each pixel only along its camera ray. The same authors followed it with DTAM (2011), and Newcombe with KinectFusion (2011). No code was released. Added 8 November 2026 from an owner-supplied link; the paper was read in full; nothing was run.

## Citation and sources

Richard A. Newcombe and Andrew J. Davison, Imperial College London. "Live Dense Reconstruction with a Single Moving Camera." CVPR 2010, pages 1498-1505.

- [Paper (Imperial)](https://www.doc.ic.ac.uk/~ajd/Publications/newcombe_davison_cvpr2010.pdf) · [saved PDF](papers/newcombe2010_live_dense_reconstruction.pdf) · Newcombe's PhD thesis, *Dense Visual SLAM* (2012), covers this work and DTAM: [PDF](https://www.doc.ic.ac.uk/~ajd/Publications/newcombe_phd2012.pdf)
- **Code: none released** (checked 8 November 2026). The paper's video page, `doc.ic.ac.uk/~rnewcomb/CVPR2010/`, now returns 404. GitHub search found no implementation.
- **Nearest open code:**
  - [PTAM](http://www.robots.ox.ac.uk/~gk/PTAM/), the tracker the paper used.
  - [OpenDTAM](https://github.com/anuranbaka/OpenDTAM), a third-party version of the 2011 successor DTAM. Its tracking code is free only for non-commercial, non-military use. Its cost-volume and denoising code was merged into OpenCV in 2016 and is BSD.
  - Installed OpenCV 5.0.0 has TV-L1 image denoising (`cv2.denoise_TVL1`, as in step 6) and DIS and Farnebäck optical flow (`cv2.DISOpticalFlow_create`, `cv2.calcOpticalFlowFarneback`). It has no TV-L1 optical flow, the flow the paper used.

## What it does

| Question | Answer |
|---|---|
| Input | Live 640 × 480 video at 30 Hz from a Point Grey Flea2 camera with an 80° lens, calibrated with PTAM's tool |
| Also needs | PTAM's live camera poses and sparse 3D points |
| Output | A dense triangle mesh, made of local depth maps placed side by side |
| Hardware | Xeon quad-core PC; one GPU for optical flow and one for drawing |
| Speed | A desk was built from 8 groups of 4 images in under 30 s. Time per depth map is not given |
| Size | PTAM's, which has no real-world size |
| Accuracy | No comparison with a reference. Optical-flow leftovers had a variance under 0.04 pixels per group |

## The parts, in order

1. **Sparse tracking.** PTAM gives the live pose and thousands of 3D points. Points rejected as outliers more than 10 times are dropped. Each point gets a rough surface direction: the average viewing direction of the keyframes that see it.
2. **Rough surface ("base mesh").** A smooth function is fitted through the oriented points (multi-scale compactly supported radial basis functions), and its zero level is turned into a mesh. This is redone at every new PTAM keyframe.
3. **Group of cameras.** One reference frame and n nearby comparison frames (n = 3 in the results). A new reference starts when less than 30% of the current view is covered by the surface built so far. Comparison frames come from a buffer of the last 60 frames, chosen to spread their positions around the reference. In the paper's example the camera was 300 mm from the scene and the comparison frames within 50 mm of the reference.
4. **Predicted views.** The reference image is painted onto the rough surface and drawn from each comparison camera. Optical flow is then computed between this prediction and the real image (TV-L1 flow, on the GPU). The prediction removes the flow caused by the camera turning, up to 150 pixels in one example. Where the rough surface is nearly right, the remaining flow is small and easy to measure.
5. **Correct along the ray.** Each pixel's surface point may move only along the reference camera's ray through that pixel. That leaves one unknown per pixel, solved by least squares from the 2n flow measurements, for up to 3 rounds.
6. **Clean each depth map.** A 3-pixel median filter is applied first. The map is then denoised (TV-L1, weighted so strong image edges keep their depth jumps) and used as a better rough surface for a second round.
7. **Merge.** The surface already built is drawn into the new reference view. New points within a small distance of it are dropped, as are points seen side-on with high error. There is no volume and no averaging: the trimmed meshes sit side by side.

## Evidence and limits

- Results are pictures and videos of desk scenes, and an AR toy car that drives over the reconstructed desk with physics and correct hiding behind objects.
- Poses are treated as exact.
- Baselines of about 50 mm at 300 mm range: desk scale, not rooms.
- Flow ran on a GPU. Merging works only because each depth map is already good, as the authors note; noise is never averaged.

## Relevance here

The project's design follows this paper's outline: a sparse tracker, dense depth per keyframe, then merging. ARCore takes PTAM's place, and Depth Anything sized to ARCore takes the rough surface's place.

- **The surface already built as a prediction.** "Size new frames against the surface already built" is step 3 of the [order to try](README.md#order-to-try). This paper goes further: the prediction lets dense matching search only small leftover motion. With learned depth as the rough surface, the same along-the-ray correction would move each pixel's depth to agree with 2-3 neighbouring frames. That turns learned depth into triangulated depth without a full plane sweep; nobody has measured it here.
- **One unknown per pixel along the ray** is also how a plane sweep works ([Mobile3DRecon](mobile3drecon.md)).
- **Merging by drawing the model into the new view.** Adding new depth only where nothing exists yet is cheap and stops one spot's frames stacking copies. But it keeps the first copy even when that copy is wrong, as the stale-depth cushion was (Task116).
- **Not a candidate to run.** Desk-scale baselines, no real size, a GPU for flow, and no accuracy figures. Read it for the ideas.
