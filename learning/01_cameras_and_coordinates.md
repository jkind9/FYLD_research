# 1. Cameras, images and coordinates

Every later chapter turns pixels into 3D points or 3D points into pixels. This chapter covers the camera model that does it, the numbers it needs, and the coordinate conventions that cause most bugs.

## The pinhole camera

Imagine light from a point in the scene passing through one tiny hole and landing on the sensor behind it. That is the pinhole model. In the camera's own coordinate frame (x to the right, y down, z forward out of the lens), a 3D point `(X, Y, Z)` lands on pixel `(u, v)`:

```text
u = fx · X / Z + cx
v = fy · Y / Z + cy
```

- `fx, fy` are the focal lengths in pixels: how strongly the lens magnifies. A larger value means a narrower view.
- `cx, cy` are the pixel coordinates of the image centre (where the forward axis hits the sensor).
- Dividing by `Z` is what makes far things small. It also throws away the distance: every point along one ray lands on the same pixel. **One image cannot tell you how far away anything is.** Depth has to come from somewhere else (chapter 2).

Running the formula backwards, a pixel with known depth `Z` becomes a 3D point:

```text
X = (u − cx) · Z / fx
Y = (v − cy) · Z / fy
```

This "back-projection" is how a depth image becomes a point cloud.

Real lenses bend straight lines a little (barrel or pincushion distortion). Calibration measures extra coefficients that undo this before the pinhole formula applies.

> **Project result.** TUM's recordings come with two calibrations: a simple default (`fx = fy = 525`, `cx = 319.5`, `cy = 239.5`, no distortion) and a published "fr1" set with five distortion terms. With the fr1 set, COLMAP matched 490,031 points on the desk recording but could not start a reconstruction; with the default, it placed all 298 frames. The cause is not established (the large sixth-order distortion term is suspected). Lesson: calibration is an input you have to test, not a constant you can copy. See `experiments/sfm/README.md`, "The published fr1 distortion set failed".

## Calibration

The four numbers `fx, fy, cx, cy` are the *intrinsics*. They are found by photographing a known pattern (a chessboard) from many angles and solving for the numbers that explain where its corners landed. On a phone, the operating system reports intrinsics per frame (ARCore does), but a plain video file from an unknown phone does not carry them. The project's rule: calibration is only trusted when the project's own capture app records it with each frame.

## Poses: where the camera is

A *camera pose* has a rotation `R` (3 × 3) and a position `t` (3 numbers). It is stored as one 4 × 4 matrix:

```text
T_world_camera = | R  t |
                 | 0  1 |
```

This *camera-to-world* matrix takes a point in the camera's frame and gives its position in the shared world frame: `p_world = R · p_camera + t`. The camera's centre in the world is `t`. Its inverse, *world-to-camera*, does the opposite and is what many libraries call "extrinsics".

The two directions are easy to mix up. A useful check: the camera-to-world translation is the camera's position; the world-to-camera translation is not.

Putting it together, to place pixel `(u, v)` with depth `Z` in the world:

1. back-project to the camera frame with the intrinsics;
2. multiply by `T_world_camera`.

That is the whole of "lifting a video into 3D", given depth and poses. The rest of the project is about getting good depth and good poses.

## Coordinate conventions

Different datasets and tools disagree about which way the axes point.

| Source | Camera axes | Notes |
|---|---|---|
| OpenCV, COLMAP, this project | x right, y down, z forward | Right-handed |
| OpenGL, many renderers | x right, y up, z backward | Right-handed |
| ICL-NUIM (as published) | y up, with a negative `fy` | Converted on load (below) |

> **Project result.** ICL-NUIM publishes its focal length as `fy = −480`, meaning a y-up camera with a mirrored world. The project flips the y axis of each camera (`F · T · F` with `F = diag(1, −1, 1, 1)`, see `experiments/sfm/src/sequences.py`, `FLIP_Y`). With that conversion, ICL's rendered depth fused along its true path lands 11.1 mm from the publisher's surface model, which shows the conventions are right (`experiments/sfm/README.md`, Task71).

Other details that bite:

- **Depth along the axis or along the ray.** "Depth" here is `Z`, the distance along the camera's forward axis, not the straight-line distance to the point. Some sensors and renderers give the ray length; it must be converted.
- **Depth units.** TUM and ICL store depth as 16-bit integers; divide by 5,000 to get metres. ARCore's raw depth is in millimetres. Zero means "no reading", not "zero distance".
- **Quaternions.** Rotations in trajectory files are often four numbers (`qx qy qz qw`). Order and normalisation vary between tools. The project's evaluator normalises them and once rejected a reference file because of rounded values.
- **Gravity is not an image axis.** "Down" in the image is not "down" in the world unless the camera is level. Maps (chapter 6) need gravity from the phone's motion sensors or from a fitted floor.

## Try it

The geometry check builds a scene from supplied depth and supplied poses, then compares it with the reference. It exercises every formula above:

```text
python -m pytest experiments/geometry_validation/tests -q
```

Read `experiments/geometry_validation/README.md` for what it checks, and `experiments/04_surface_reconstruction/README.md`, "From pixel to point", for the same maths in the surface layer.

## Further reading

- Lecture 2 (image formation) and lecture 4 (camera calibration) in [research/3d_vision_fundamentals](../research/3d_vision_fundamentals/README.md).
- The TUM file format page, summarised in [research/datasets_and_benchmarks/tum_rgbd.md](../research/datasets_and_benchmarks/tum_rgbd.md).
