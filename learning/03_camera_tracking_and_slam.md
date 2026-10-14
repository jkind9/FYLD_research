# 3. Camera tracking and SLAM

To put every frame's pixels into one 3D space, we need each frame's camera pose (chapter 1). Camera tracking estimates those poses from the video. This chapter builds up from the simplest tracker to full SLAM, then explains why the project's first tracker failed and what replaced it.

## Step 1: frame-to-frame tracking (visual odometry)

The simplest tracker compares each new frame with the previous one and works out how the camera moved between them. Chaining those small motions gives the whole path. This is *visual odometry*. There are two families:

- **Feature-based.** Find distinctive spots (corners, blobs) in both frames, match them by their descriptors, and solve for the motion that best explains the matches. ORB and SIFT are common features. With depth for the first frame, this is a "perspective-n-point" (PnP) problem: known 3D points, their 2D positions in the new image, solve for the pose.
- **Direct.** Skip features. Shift and rotate one frame until its pixel brightness (and depth, if available) lines up with the other. Open3D's RGB-D odometry, the project's first tracker, works this way.

Both are fast and simple. Both have the same flaw.

## Step 2: drift

Every step has a small error. The path is the sum of the steps, so errors add up and the path slowly wanders away from the truth. Nothing in pure odometry ever corrects an earlier step. After a few hundred frames, a millimetre-per-step error is centimetres or more.

Odometry from images alone has a second problem: no size. A camera that moved 10 cm past a wall 1 m away produces the same images as one that moved 20 cm past a wall 2 m away. The path's shape is recoverable, its size is not. Depth, a second camera or motion sensors provide it.

## Step 3: keep a map and refine (SLAM)

*SLAM* (simultaneous localisation and mapping) adds memory:

1. **Keyframes and a map.** Keep selected frames and the 3D points they saw. Track each new frame against the map, not only against the last frame, so errors do not compound as fast.
2. **Local bundle adjustment.** Regularly re-solve the recent keyframe poses and map points together so that every point projects back onto the pixels where it was seen (chapter 4 explains bundle adjustment). Earlier poses get corrected as new evidence arrives.
3. **Loop closure.** When the camera returns to a place, recognise it (place recognition, often a "bag of visual words" lookup), check the match geometrically, and add a constraint saying "these two poses see the same place". Optimising the *pose graph* (poses as nodes, measured motions as edges) spreads the correction along the whole loop and removes accumulated drift.

ORB-SLAM3 (classic, feature-based), RTAB-Map (strong place recognition), DROID-SLAM and MASt3R-SLAM (learned) are SLAM systems. They differ in features and hardware, but all do these three things.

## Step 4: add motion sensors (visual-inertial)

A phone's IMU (gyroscope and accelerometer) measures rotation and acceleration hundreds of times a second. Combined with the camera, it:

- carries tracking through blur and fast turns, where images fail;
- gives the direction of gravity, so the map knows which way is down;
- gives metric size, because acceleration is measured in metres per second squared.

This is *visual-inertial odometry* (VIO). ARCore on Android works this way, live, on the phone.

## SLAM against structure from motion

They solve the same problem. SLAM is usually live and processes frames in order; structure from motion (chapter 4) is usually offline and can use every frame at once. Offline gives the most accurate path; live gives a path while the person is still on site. The owner ruled on 14 October 2026 that the deployed system must be live (or update at least once per second), so SLAM, in practice ARCore on the phone, is the deployable choice; SfM is used only as an accurate reference on recorded data. Neither builds dense surfaces or recognises objects: those are later stages that use the poses. [How the methods fit together](methods_inputs_and_outputs.md) draws the boundary and lists every method's inputs and outputs.

## Why the project's first tracker failed

> **Project result: the tracker, not depth, was the main gap.** The walkthrough's tracker is Open3D RGB-D odometry: direct, frame to frame, no map, no refinement, no loop closure. Even fed the Kinect sensor's own depth, its path misses the truth by 34 mm on TUM xyz and 112 mm on desk (best fit, chapter 9). Published image-only SLAM systems on the same recordings: 9-12 mm on xyz, 16-18 mm on desk (MASt3R-SLAM paper, Table 1). (`research/camera_tracking_and_slam/tracking_review_2026-10-13.md`.)

> **Project result: depth errors become camera motion.** With Depth Anything's depth, the same tracker misses by 177 mm (xyz) and 710 mm (desk) even after fitting one overall size, and by 438 mm on desk with the best depth correction tried. Giving it the exact Kinect size every frame still leaves 401 mm on desk. A direct tracker turns any depth error into motion. (Task65 and Task70.)

> **Project result: tracking from images alone, with refinement, works.** Structure from motion (COLMAP) on the same frames, from the images alone, places every frame with 11.9 mm error on xyz and 21.5-24 mm on desk after a best fit with size: 3-5 times better than the old tracker with Kinect depth, and close to published SLAM. (Task67, chapter 4.)

The lesson generalises: **joint refinement over many frames beats chaining frame-to-frame motion**, and a camera path should come from image features (or the phone's VIO), not from aligning learned depth maps.

## When tracking fails

If a tracker loses its place (blur, a blank wall, a person walking past), later frames start a new *segment* with its own origin. Segments must never be silently joined: two segments share a map only after a checked transform links them. The project's tracking and SfM code keep each segment (SfM "model") separate and score them separately.

## Try it

Score a saved camera path against TUM's motion-capture path with the project's evaluator (best fit, best fit with size, 1 s relative error):

```text
python -m pytest experiments/03_camera_pose_estimation/tests -q
```

`experiments/03_camera_pose_estimation/src/evaluation.py` holds the scoring code; `evaluate()` returns `ate_rigid_rmse_m`, `ate_scaled_rmse_m`, `ate_scaled_size` and `rpe_1s_translation_rmse_m`.

## Further reading

- [research/camera_tracking_and_slam](../research/camera_tracking_and_slam/README.md), starting with the 13 October tracking review.
- [ORB-SLAM note](../research/camera_tracking_and_slam/orb_slam/README.md) and the Android SLAM review beside it.
- Lecture 8, second file (incremental SfM, loop closure, SLAM) in [research/3d_vision_fundamentals](../research/3d_vision_fundamentals/README.md).
- `experiments/03_camera_pose_estimation/README.md` for the layer's methods table and the first CPU trial.
