# 2. Depth

A depth image has one number per pixel: the distance from the camera to the surface seen there, in metres along the camera's forward axis. Pixels with no answer are marked invalid. Invalid is not the same as far away.

Chapter 1 showed that one image throws depth away. This chapter covers the four ways to get it back, the difference between metric and relative depth, and what the project found when it used a learned depth model.

## Four ways to get depth

| Approach | How it works | Good | Bad |
|---|---|---|---|
| **Two-camera stereo** | Two cameras a known distance apart (the *baseline* `B`) see the same point. It shifts sideways between the images by `d` pixels (the *disparity*). Depth `Z = f · B / d`. | Real metres from calibration alone; one instant, so moving objects are fine | Phone lenses are 1-2 cm apart, so `d` is tiny past a few metres and error grows with the square of distance. Fails on blank walls, repeated patterns and glare. Many phones do not let apps capture both lenses at once. |
| **Depth from motion** | One camera moves; two frames from different places act as a stereo pair with a longer baseline. | One camera; a longer baseline helps at range | Needs accurate camera motion (chapter 3). Moving objects confuse it. ARCore's depth works this way on most phones. |
| **Active sensors** | The device emits light and times its return: time-of-flight, lidar, or a projected pattern. The Kinect in the TUM recordings is one. | Accurate at short range, even on blank walls | Most Android phones have none. Sunlight and range limit it outdoors. |
| **Learned single-image depth** | A neural network guesses depth from one image, using what scenes usually look like. | Dense, sharp, works anywhere | Often the right shape at the wrong size. Errors are hard to predict. |

Modern systems mix them. A learned model gives dense, sharp depth, and a few reliable measured points (from ARCore or tracked features) fix its size.

## Metric, relative, scale and shift

- **Metric depth** is in real metres.
- **Relative depth** has the right shape, but every value is off by one unknown factor (the *scale*), and sometimes one unknown offset (the *shift*): `true ≈ scale · predicted + shift`.
- Some models output *inverse depth* (1/Z) up to scale and shift. ZipDepth, tested here, does.

A model that claims to output metres is "metric" only if that claim is checked. The project's depth models are scored two ways: raw (is it right in metres?) and after fitting each frame's scale and shift to the reference (is the shape right?). The second number tells you how good the model could be with a perfect size source; the gap between the two tells you how much the size source matters.

## Scores

- **AbsRel**: mean of `|predicted − true| / true`. 0.07 means 7% off on average.
- **RMSE**: root-mean-square error in metres.
- **δ1**: share of pixels within 25% of the truth.

## What the project found

> **Project result: learned "metric" depth is the wrong size, and the size changes every frame.** Depth Anything V2 Metric Small (25M parameters) reads distances 1.34 times too far on TUM xyz and 1.41 times too far on desk (median over frames). Raw AbsRel is 0.345 and 0.450. The factor moves between 0.86 and 2.09 from frame to frame, so one fixed correction cannot fix it. (`experiments/02_stereo_depth/README.md`, Task54.)

> **Project result: the shape is good; a few known points fix the size.** With each frame's scale and shift fitted, Depth Anything's AbsRel drops to 0.066 (xyz) and 0.082 (desk); ZipDepth's phone build reaches 0.070 and 0.068. Fitting from only 50 known points per frame reaches the same score as fitting to every pixel; 10 points cost about 0.01 AbsRel. (Task62, `sparse_scale.py`.)

> **Project result: the most accurate model was too slow.** Marigold V2 (a diffusion model) gave the best shape, AbsRel 0.036, but took 16.6 s per frame on the GPU and crashed on desk. The owner ruled that anything slower than 1 frame per second is not worth using, so it was dropped.

### Why a drifting size is so damaging

If each frame's depth is a different size, the same wall lands at a different distance from each camera. Combined, the wall appears several times along the viewing direction. Worse, a tracker that aligns depth images (chapter 3) reads a jump in size as the camera moving. On 30 xyz frames, at frame 16 the depth size jumped from 1.39 to 1.62 and the camera error jumped from 147 to 337 mm in the same frame (Task65).

The project tried three fixes (Task65):

1. **Overlap chain** (images only): carry each frame's size forward from earlier frames through tracked corners. Cut camera error by 48-73% but left 0.37 m (xyz) and 1.01 m (desk).
2. **Triangulation with metric motion** (the phone route): triangulate corners using known metric camera motion, standing in for ARCore, and fit each frame's size to them.
3. **Video Depth Anything**: a model that keeps depth consistent over 32-frame windows. Promising on a short clip; 0.77 frames per second on the CPU.

None made the old tracker accurate. The real fix came from changing the tracker (chapters 3 and 4) and sizing depth to the tracker's own points (chapter 5).

> **Project result: depth prompted with sparse points did not help.** Prompt Depth Anything takes a low-resolution metric depth map as a second input. Fed with the few hundred SfM points per frame (chapter 4), it was no better than Depth Anything resized to the same points: 168 against 166 mm surface error on xyz, 217 against 156 mm on desk, 147 against 93 mm on ICL. It was trained on dense iPhone lidar maps, and a sparse prompt is far from that. (Task79, `experiments/sfm/README.md`.)

## Try it

Score Depth Anything against Kinect depth on TUM (needs the checkpoint in `data/models/`):

```text
python -m experiments.02_stereo_depth.run --method depth-anything --checkpoint data/models/depth_anything_v2_metric_indoor_small --tum-root data/tum --output experiments/02_stereo_depth/runs/<new> --device cpu
```

Then look at `results.json` in the run folder: compare the raw AbsRel with the shape (aligned) AbsRel.

## Further reading

- Lecture 6 (depth estimation) in [research/3d_vision_fundamentals](../research/3d_vision_fundamentals/README.md).
- [research/depth_estimation](../research/depth_estimation/README.md): phone stereo (MobiDepth, HiMoDepth, BANet), Video Depth Anything, Prompt Depth Anything.
- The full survey of how other systems keep depth size consistent: `experiments/02_stereo_depth/README.md`, "What existing systems do".
