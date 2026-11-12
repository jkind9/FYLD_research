# Session

Reads a saved phone recording in file order. `frames(folder)` returns RGB images,
camera intrinsics, depth and tracked points, with all camera and anchor poses converted
to one matrix convention. `replay(folder, deliver)` delivers those frames at the recorded rate.
The recording format is defined in [FORMAT.md](FORMAT.md).

Poses come from ARCore's records, or from an open tracker. `read_tum` reads a tracker's
trajectory and `read_calibration` a phone's calibration; given both, `frames` and
`read_wire_session` pose every frame by the tracker, with one anchor a second.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `folder` | Path or string; `session.json`, `frames.jsonl`, image and depth folders | Recording format v1 or v2 |
| `Frame.image` | H × W × 3, uint8 RGB | Recorded pixel grid, without rotation |
| `Frame.camera` | `Camera(fx, fy, cx, cy, width, height)`, or None without ARCore | Pixels |
| `Frame.pose` | 4 × 4 float64 `world_from_camera`, or None without tracking | Metres; camera x right, y down, z forward; ARCore world y up |
| `Frame.depth` | `MeasuredDepth` with `source="arcore"`, or None; H × W float32 depth and uint8 confidence | Camera-plane metres; confidence 0–255; its own camera and timestamp |
| `Frame.points_world`, `points_pixel` | N × 3 and N × 2 float64 | World metres and recorded image pixels |
| `Frame.point_ids`, `points_confidence` | N int64 and N float64 | Phone point IDs and confidence |
| `Frame.anchor_created`, `anchor_updates` | Optional `(id, matrix)` and dict of matrices by ID | Same matrix convention as `Frame.pose` |
| `Frame.t_ns`, `arcore_t_ns` | int; ARCore timestamp may be None | Nanoseconds in their recorded clocks |
| `Frame.pose_source` | str | `"arcore"`, or the tracker's name |
| Trajectory file | Text, one pose per line: `time x y z qx qy qz qw` (TUM format) | Seconds on the camera clock (decimal or scientific); metres; the tracker's world |
| `Trajectory` | `t_ns` N int64, `world_from_camera` N × 4 × 4 | Nanoseconds; OpenCV camera axes in a world turned so +y is up |
| Calibration file | JSON: `camera` {fx, fy, cx, cy, width, height}, `distortion`, `imu_from_camera` 4 × 4 | Pixels; the camera's pose in the motion sensors' frame, metres |

## How it works

1. Read the recording version once, then parse each saved header with its image and depth bytes.
2. Check wire fields and point projections at this boundary, so stages can trust the records.
3. Decode JPEG as RGB and raw depth from millimetres into metres, preserving both pixel grids.
4. Convert camera and anchor quaternions to matrices and reverse camera y and z once for OpenCV axes.
5. Pace replay from the first camera timestamp and elapsed wall time, so processing time does not add drift.

With a tracker trajectory (`with_trajectory`):

6. Read times as exact decimals, turn each pose from the motion sensors to the camera (`imu_from_camera`), and turn the world so its up axis is +y, as ARCore's is; image orientation then works unchanged.
7. Give each frame the pose stamped within 1 µs of it, else interpolate between the poses either side (spherical for rotation) when they are at most 0.1 s apart. Otherwise the frame has no pose, as when tracking is lost.
8. Take intrinsics from the calibration. Drop ARCore's tracked points and anchors, which belong to ARCore's world; keep ARCore depth, which is measured in the camera, as a comparison.
9. Start a new anchor at the first posed frame and then once a second. An odometry tracker never corrects them.

## Run it

Run from the repository root in the locked environment:

```python
from sitescan import session

frames = list(session.frames("tests/fixtures/tum_desk_20"))
print(len(frames), frames[0].image.shape, frames[0].pose.shape)
print([f.seq for f in frames if f.depth is not None])
# 20 (480, 640, 3) (4, 4)
# [0, 3, 6, 9, 12, 15, 18]
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| `speed` | 1.0 | Reproduce camera timing; zero removes waiting | [Replay tests](../../tests/test_sitescan_session.py) |
| `stop` | None | Replay until the recording ends unless a caller supplies a stop event | [Replay tests](../../tests/test_sitescan_session.py) |
| `reader` | `frames` | New callers receive shared records; old live callers temporarily select wire records | [Architecture](../../DESIGN.md#5-target-architecture) |
| `PIXEL_TOLERANCE_PX` | 0.5 px | Accept recorded rounding while checking point projection | [Wire contract](FORMAT.md) |
| `QUATERNION_TOLERANCE` | 0.001 | Preserve the existing phone quaternion check | [Shared phone fixture tests](../../research/experiments/01_camera_capture_delivery/tests/test_session_v1.py) |
| `up` | (0, 0, 1) | Basalt's world has gravity along -z | [Session tests](../../tests/test_sitescan_session.py) |
| `SAME_TIME_NS` | 1 µs | Seconds since 1970 written as floating point are off by up to a few hundred nanoseconds | [Session tests](../../tests/test_sitescan_session.py) |
| `MAX_POSE_GAP_S` | 0.1 s | Three frames at 30 fps; a longer gap means the tracker lost track | [Session tests](../../tests/test_sitescan_session.py) |
| `KEYFRAME_EVERY_S` | 1.0 s | The anchor rate of the recorded walks and the fixture | [Session tests](../../tests/test_sitescan_session.py) |

## Limits

The reader does not align camera and ARCore clocks or reject stale depth. Frame choice
and freshness belong to the pipelines. Replay waits synchronously; stop is checked between
frames, so an outstanding wait completes first. V1 remains readable for existing tools;
new recordings use v2. `wire_v1`, `wire_v2` and `read_wire_session` keep the checked wire records, which both
pipelines still read; `arcore_depth` and `camera` turn their parts into the shared types.
Only `frames` returns whole package records. Switching the pipelines to `frames` changes
anchor axes and so the fused grid in floating point; it needs its own golden check.
Without a trajectory, poses and intrinsics come only from ARCore's records, so a camera-only
frame has neither. A trajectory needs a v2 recording. Its times must be on the camera clock:
the reader does not apply a camera-to-IMU time shift. Lens distortion is read but not applied.
Nothing reads `imu.csv`; the tracker runs outside the package and only its trajectory comes in.

## Tests

`python -B -m pytest -q tests/test_sitescan_session.py` checks RGB decoding, both recording
versions, metric depth, world-point projection, anchor conversion, missing tracking and
ARCore records, frame order, replay speed, late delivery and stop. For trajectories it
checks exact times in both number forms, the turn to a y-up world, the IMU-to-camera step,
interpolation, gaps, same-time matching, a trajectory of the recorded poses giving those
poses back, camera-only frames taking the calibrated camera, and anchors once a second. Existing phone tests
check raw and deflated grey images, IMU, protocol framing and the shared Java fixtures.
The golden lane checks unchanged room and live results on the public TUM recording.
