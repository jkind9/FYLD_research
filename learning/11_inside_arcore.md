# 11. Inside ARCore

ARCore is the phone's built-in tracker, and the project's plan relies on it for the camera path, the real-world size and the depth images (chapter 8). It is closed source, but Google's documentation, two Google patents, a Google paper and an independent study describe how it works. This chapter explains each part from first principles and says what it means for the project. Where a statement comes from a patent, treat it as Google's described design, not a guarantee of the shipping code. Sources are in [research/phone_ar_platforms/arcore_internals.md](../research/phone_ar_platforms/arcore_internals.md).

## The big picture

```text
camera (30 fps) ─┐                              ┌──► pose every frame (fast, local)
                 ├──► FRONT END: visual-inertial ┤
IMU (100s Hz) ───┘    filter (MSCKF-style)       └──► feature descriptors, every few seconds
                                                            │
                                                            ▼
                                               BACK END: mapping (slow, global)
                                                            │ 3D map
                                                            ▼
                                               LOCALIZATION: loop closure
                                                            │ corrected pose
                                                            └──► fed back to the front end

recent frames + their poses ──► DEPTH FROM MOTION ──► depth image + confidence
feature points ───────────────► PLANES (clusters on flat surfaces)
```

Google's patent on "concurrent odometry and mapping" splits tracking into these three modules running at different speeds. The front end answers "where is the phone right now" every frame. The back end and localization answer "where has the phone been, consistently" every few seconds, and push corrections forward.

## The front end: a visual-inertial filter

### What the IMU contributes

The gyroscope measures rotation rate; the accelerometer measures acceleration plus gravity. Integrating the gyroscope once gives orientation; integrating the accelerometer twice (after removing gravity) gives position. Between two camera frames (33 ms) this *propagation* is accurate. Over seconds it drifts badly, because a tiny bias in acceleration grows with the square of time: a 0.01 m/s² bias becomes 4.5 m of error after 30 s.

Three things make the IMU essential anyway:

- **Real-world size.** Acceleration is measured in m/s², so the filter can tell how many metres the camera actually moved. A camera alone cannot (chapter 4).
- **Gravity.** The accelerometer at rest points down, so the map knows which way is up; floors are horizontal from the start.
- **Fast motion and blur.** When images smear, the IMU carries the pose until features are visible again.

### What the camera contributes

The camera corrects the IMU's drift. Distinctive points ("feature points") are found and followed from frame to frame. If the predicted camera motion is wrong, those points will not land where they were seen; the error says how to correct the pose and the IMU's biases.

### How they are combined: the MSCKF idea

An independent study describes ARCore's tracking as "MSCKF-style" (multi-state constraint Kalman filter, Mourikis and Roumeliotis, 2007). The filter keeps a *state*: the current IMU state (position, velocity, orientation, gyroscope and accelerometer biases) plus a sliding window of the last few camera poses. Its key trick:

1. Each new IMU reading *propagates* the state forward.
2. Each new image adds the current camera pose to the window (the oldest drops out).
3. A feature is tracked across several poses in the window. When its track ends, the filter triangulates it, compares where it should appear with where it was seen in each pose, and uses that mismatch to *update* all the poses in the window and the biases.
4. The 3D point itself is never added to the state; its constraint is used and then discarded.

Leaving points out of the state keeps the cost proportional to the number of features, not the square of the map size, which is why it runs in a few milliseconds on a phone. The price is that points are not remembered, so this front end alone still drifts slowly.

### Starting up

The filter needs motion to start: until the phone has moved and rotated enough, it cannot separate gravity from acceleration or fix the size. That is why AR apps ask you to "move your phone around" first, and why tracking is reported as not ready until then.

## The back end: mapping and loop closure

According to the patent, the front end keeps only a short history and treats earlier 3D points as fixed. Every few seconds ("every five seconds" is the patent's example) it hands feature descriptors to the back end, which:

- builds a 3D map of distinctive points by a non-linear estimation over many frames (bundle-adjustment-like, chapter 4);
- matches what the camera sees now against stored map points (*localization*); when the camera returns to a mapped place, it closes the loop with a Gauss-Newton or Levenberg-Marquardt optimisation;
- sends a corrected pose back to the front end.

**Consequence: poses can shift after the fact.** When a loop closes, earlier positions move. ARCore exposes *anchors* for this: content pinned to an anchor moves with the correction. Anything the project builds from past poses (a fused surface, object positions) has to be rebuilt or re-anchored when the path is corrected (chapter 5, "when the camera path changes"). The live SLAM experiment saw the same effect offline: live poses were 1-5 mm worse than each system's refined path.

## Depth from motion

Most Android phones have one usable camera for depth, so ARCore makes depth the way multi-view stereo does (chapter 5), but on one CPU core. Google's paper and patent describe the pipeline:

1. **Keep a pool of recent keyframes**, only frames where tracking was confident.
2. **Pick the best partner for the current frame** with a cost that wants a large baseline (camera moved far enough for parallax), a small time gap (scene unchanged), large view overlap and low tracking error.
3. **Rectify the pair** so matching points lie on the same image row. A *polar* rectification is used so that walking forwards (the common case, where standard rectification breaks) still works.
4. **Match pixels** between the two images with a PatchMatch/HashMatch search: start from random depth guesses and spread good guesses to neighbours, using SIMD instructions on the CPU.
5. **Throw out unreliable pixels** (untextured or repeating patterns) with a small decision tree. These become "no depth".
6. **Fill and smooth** with a planar bilateral solver, which assumes surfaces are locally flat and edges follow image edges; then average over time and align the result to the newest frame.

The **Raw Depth API** gives the result before most of the smoothing, plus a confidence for each pixel.

What follows from this design:

- **Depth needs motion.** Standing still gives no baseline, so no new depth. Fast rotation without movement gives little parallax.
- **Depth needs texture.** Blank walls and floors get no raw depth; the smoothed depth fills them by assuming planes.
- **Depth is coarse.** Matching runs at low resolution to fit one CPU core.

## Planes, points and hit tests

- **Planes** are clusters of feature points that lie on a common horizontal or vertical surface. No texture means no points, so no plane.
- **The point cloud** is the set of feature points ARCore is currently using, with 3D positions.
- **Hit testing** casts a ray from a screen point and returns the plane or point it meets, with a pose.

## What the project measured on its Redmi

| Measure | Value | What it means |
|---|---|---|
| Tracking | 100% of 891 frames over a 15 s, 5.5 m walk | The front end coped with ordinary walking indoors |
| Update time | 4.9 ms median, 20.9 ms at the 95th percentile | Tracking leaves most of the phone's time free |
| Tracked points | Median 19 per frame | The point cloud is too sparse to resize learned depth reliably on its own; the SfM tests used hundreds per frame |
| Raw depth | 160 x 90, 48% of pixels valid, low confidence | Usable as a size source where valid (about 7,000 pixels per frame), not as a finished surface |
| Depth sensor | ARCore does not use the phone's time-of-flight sensor | All depth comes from the motion-stereo pipeline above |

Published drift for ARCore (on another phone, loop closure switched off): 0.09-0.12 m after 84-145 m indoor walks and 0.07 m after a 514 m campus walk, but 4 m on stairs and 140 m in a car. Indoor walking is its strength; stairs and vehicles are not.

## What this changes in the plan

- **Size each frame's learned depth with ARCore's raw depth where its confidence is high**, not only with the sparse point cloud. Chapter 2 showed 50 good points per frame are enough; raw depth supplies thousands.
- **Keep every pose update, not just the first.** When ARCore corrects its path, the fused surface and object positions must follow.
- **Ask users to move, not just turn**, and to point at textured surfaces, so depth from motion has parallax.
- **Treat stairs and vehicles as hard cases** to test explicitly in the field.

## Further reading

- [research/phone_ar_platforms/arcore_internals.md](../research/phone_ar_platforms/arcore_internals.md): sources, quotes and saved papers.
- Chapter 3 (tracking and SLAM), chapter 5 (multi-view stereo, fusion) and chapter 8 (the phone).
