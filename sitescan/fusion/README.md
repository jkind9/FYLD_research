# Fusion

Fuses scaled depth into surface fragments using Open3D's truncated signed distance
function (TSDF), a voxel grid that averages measured surfaces. `Fragments` retains one
volume per group of keyframes. Each volume is tied to one anchor, so a correction moves
its extracted points without fusing those frames again. RGB colours follow the same point order.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `depth_m` | H × W float array | Scaled camera-plane metres on the recorded grid |
| `colour` | H × W × 3 uint8 RGB | Same pixel grid |
| `intrinsics` | `(fx, fy, cx, cy)` | Pixels |
| `world_from_camera` | 4 × 4 float64 | Metres; OpenCV camera axes in ARCore world |
| Anchor ID and `world_from_anchor` | Integer and 4 × 4 float64 | Metres; anchor-local grid to world |
| `surface()` | N × 3 float64 | World metres in fragment insertion order |
| `colours()` | N × 3 float64 | RGB from 0 to 1, aligned with `surface()` |
| `frames_per_fragment()` | dict of integer counts | Integrated frames by fragment ID |

## How it works

1. Group keyframe IDs by integer division by 10 to bound each volume's share of the walk.
2. Bind a new group to its first anchor, or the first received anchor when a recording begins mid-group.
3. Express each camera relative to that placing anchor and integrate depth and RGB into the volume.
4. Extract local points and colours only after new depth has changed the volume.
5. Move local points by the current anchor, retaining the volume and point order after corrections.

## Run it

Run in `.venv-sitescan` from the repository root. Fixture depth stands in for scaled learned depth:

```python
from sitescan import session
from sitescan.fusion import Fragments

frame = next(session.frames("tests/fixtures/tum_desk_20"))
fragments = Fragments(voxel_m=0.02)
fragments.set_anchor(0, frame.pose)
k = frame.depth.camera
rgb = frame.image[::4, ::4].copy()
fragments.integrate(frame.depth.depth_m, rgb, (k.fx, k.fy, k.cx, k.cy), frame.pose, 0)
print(fragments.surface().shape[1], fragments.frames_per_fragment())
# 3 {0: 1}
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| `voxel_m` | Required; room and live use 0.02 m | Adopted surface resolution; 52 mm mean surface error on the synthetic ICL control | [Measured chain](../../DESIGN.md#2-where-the-project-is) |
| `keyframes_per_fragment` | 10 | Adopted grouping keeps correction work local | [Fragment tests](../../src/live/tests/test_fragments.py) |
| `TRUNCATION_VOXELS` | 4 | Retain the existing signed-distance averaging band | [Original fusion control](../../experiments/sfm/src/dense.py) |
| `DEPTH_RANGE_M` | 0.1–4.0 m | Preserve the adopted near and far integration limits | [Fusion tests](../../tests/test_sitescan_fusion.py) |

## Limits

This stage trusts camera calibration, depth scale and anchor events. It cannot repair
shape errors or a wrong camera path. An anchor must be received before its first frame.
Only the anchor that first binds a group places that group's volume; a later group-start
event does not rebind it. Anchor updates must keep the same local grid basis as integration.
The stage applies no visibility vote, component filtering or frame selection.

## Tests

`python -B -m pytest -q tests/test_sitescan_fusion.py src/live/tests/test_fragments.py`
checks empty surfaces, group boundaries, missing group-start anchors, corrections,
point order, refreshed extraction after integration, RGB alignment and depth limits.
The golden lane and full room rebuild check unchanged counts and measurements.
