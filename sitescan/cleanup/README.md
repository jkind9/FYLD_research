# Cleanup

Keeps surface points supported by the depth views, then retains the largest touching
pieces. The visibility vote compares weighted support with views that see through a
point. `clean_room` returns a boolean mask in input order so points, colours and other
attributes remain aligned. These are the two adopted filters; trials live in
[`experiments/surface_cleanup`](../../experiments/surface_cleanup/README.md).

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `points` | N × 3 float array | ARCore world metres |
| `views` | Sequence of `(camera_from_world, intrinsics, depth)` | Projection transform inverse to the OpenCV camera pose; pixel intrinsics; camera-plane metres |
| `cell` | float | Connected-piece grid width in metres |
| `vote_tallies` result | Two N float64 arrays | Weighted support and see-through opposition |
| Filter result | N bool array | Input-order mask; apply to both points and RGB |

## How it works

1. Project each point into every depth view, using the existing nearest-pixel rounding rule.
2. A view supports points near its measured depth and opposes points in front of that depth; occluded and unobserved points receive no vote.
3. Weight each vote by inverse squared measured depth so nearer observations count more.
4. Keep support at least equal to opposition, including ties and points without evidence.
5. Join occupied grid cells at faces, edges and corners, then retain the largest pieces meeting the point minimum.

## Run it

Run in `.venv-sitescan` from the repository root:

```python
import numpy as np
from sitescan import session
from sitescan.cleanup import visibility_vote

frame = next(session.frames("tests/fixtures/tum_desk_20"))
k = frame.depth.camera
view = (np.linalg.inv(frame.pose), (k.fx, k.fy, k.cx, k.cy), frame.depth.depth_m)
keep = visibility_vote(frame.points_world, [view])
print(keep.shape, keep.dtype)
# (20,) bool
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| Vote share | 0.5, implemented as support ≥ opposition | Adopted visibility rule; ties keep their points | [Cleanup evidence](../../research/surface_denoising/README.md) |
| `margin_m` | 0.08 m | Four 2 cm fusion voxels | [Fusion settings](../fusion/README.md) |
| `margin_share` | 0.05 | Existing allowance for relative learned-depth error | [Cleanup evidence](../../research/surface_denoising/README.md) |
| `min_depth_m` | 0.5 m | Preserve the original cap on near-view weights | [Cleanup tests](../../tests/test_sitescan_cleanup.py) |
| Projection near depth | 0.1 m | Preserve the original point projection limit | [Fusion range](../fusion/README.md) |
| Evidence far depth | 8 m | Room callers retain see-through evidence beyond the 4 m fusion limit | [Adopted room build](../../src/live/room_build.py) |
| `cell` | 0.02 m in `clean_room`; required by `largest_pieces` | Default matches fusion voxel spacing | [Adopted chain](../../DESIGN.md#2-where-the-project-is) |
| `keep` | 50 pieces | Owner chose this in the cleanup tuner | [Adopted chain](../../DESIGN.md#2-where-the-project-is) |
| `min_points` | 5,000 | Owner's minimum piece size in the tuner | [Adopted chain](../../DESIGN.md#2-where-the-project-is) |

## Limits

The 15 October walk keeps 554,067 of 676,855 raw points. Unobserved or occluded points
survive the vote, so the largest-pieces step is still needed. Connected occupied cells
can bridge a narrow gap; their memory use grows with the surface bounding box. The
method does not fix repeated doors caused by wrong far-depth scale. `largest_pieces`
expects a nonempty cloud; `clean_room` skips it when voting leaves no points.

## Tests

`tests/test_sitescan_cleanup.py` checks vote evidence, equal votes, capped weights,
missing observations, piece size/count limits, ordered masks and empty results. Existing
cleanup, trial, attribute and viewer tests check the compatibility imports. The golden
lane and full-room rebuild check unchanged numerical outputs; Chromium checks a newly
generated offline page after the move.
