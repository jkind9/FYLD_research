# Session

Reads a saved phone recording in file order. `frames(folder)` returns RGB images,
camera intrinsics, depth and tracked points, with all camera and anchor poses converted
to one matrix convention. `replay(folder, deliver)` delivers those frames at the recorded rate.
The recording format is defined in [FORMAT.md](FORMAT.md).

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `folder` | Path or string; `session.json`, `frames.jsonl`, image and depth folders | Recording format v1 or v2 |
| `Frame.image` | H × W × 3, uint8 RGB | Recorded pixel grid, without rotation |
| `Frame.camera` | `Camera(fx, fy, cx, cy, width, height)`, or None without ARCore | Pixels |
| `Frame.pose` | 4 × 4 float64 `world_from_camera`, or None without tracking | Metres; camera x right, y down, z forward; ARCore world y up |
| `Frame.depth` | `ArcoreDepth`, or None; H × W float32 depth and uint8 confidence | Camera-plane metres; confidence 0–255; its own camera and timestamp |
| `Frame.points_world`, `points_pixel` | N × 3 and N × 2 float64 | World metres and recorded image pixels |
| `Frame.point_ids`, `points_confidence` | N int64 and N float64 | Phone point IDs and confidence |
| `Frame.anchor_created`, `anchor_updates` | Optional `(id, matrix)` and dict of matrices by ID | Same matrix convention as `Frame.pose` |
| `Frame.t_ns`, `arcore_t_ns` | int; ARCore timestamp may be None | Nanoseconds in their recorded clocks |

## How it works

1. Read the recording version once, then parse each saved header with its image and depth bytes.
2. Check wire fields and point projections at this boundary, so stages can trust the records.
3. Decode JPEG as RGB and raw depth from millimetres into metres, preserving both pixel grids.
4. Convert camera and anchor quaternions to matrices and reverse camera y and z once for OpenCV axes.
5. Pace replay from the first camera timestamp and elapsed wall time, so processing time does not add drift.

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
| `QUATERNION_TOLERANCE` | 0.001 | Preserve the existing phone quaternion check | [Shared phone fixture tests](../../experiments/01_camera_capture_delivery/tests/test_session_v1.py) |

## Limits

The reader does not align camera and ARCore clocks or reject stale depth. Frame choice
and freshness belong to the pipelines. Replay waits synchronously; stop is checked between
frames, so an outstanding wait completes first. V1 remains readable for existing tools;
new recordings use v2. `wire_v1`, `wire_v2` and `read_wire_session` keep the checked wire records, which both
pipelines still read; `arcore_depth` and `camera` turn their parts into the shared types.
Only `frames` returns whole package records. Switching the pipelines to `frames` changes
anchor axes and so the fused grid in floating point; it needs its own golden check.

## Tests

`python -B -m pytest -q tests/test_sitescan_session.py` checks RGB decoding, both recording
versions, metric depth, world-point projection, anchor conversion, missing tracking and
ARCore records, frame order, replay speed, late delivery and stop. Existing phone tests
check raw and deflated grey images, IMU, protocol framing and the shared Java fixtures.
The golden lane checks unchanged room and live results on the public TUM recording.
