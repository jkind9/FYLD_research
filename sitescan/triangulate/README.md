# Triangulate

Measures depth from the camera's own motion, given its poses. `Triangulator.sparse` matches
a frame's corner features with recent keyframes and triangulates them, giving metric depth
and its standard error at a few hundred pixels. `Triangulator.dense` sweeps candidate depths
through two keyframes and returns a measured depth map with a confidence, in the same record
as ARCore's raw depth. Both feed the scale stage, so learned depth can be sized without ARCore.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `grey` | H × W uint8 | The recording's lossless grey image (`frame.grey`, recording v2) |
| `camera` | `Camera` | Pinhole intrinsics of that image, in pixels |
| `pose` | 4 × 4 float64 `world_from_camera` | Metres; OpenCV camera axes; any world, as long as all poses share it |
| `SparseDepth` | `uv` N × 2, `depth_m` N, `sigma_m` N, `index` N | Frame pixels; camera-plane metres; standard error in metres; feature number |
| `MeasuredDepth` (dense) | h × w float32 depth, uint8 confidence, own `Camera`, `source="sweep"` | Camera-plane metres at half the image size; confidence 0–255, 0 where unmeasured |
| `prior` (optional) | H × W float | Metres: learned depth already sized, to search around |

## How it works

Sparse, per frame:

1. Detect up to 2,000 ORB corners, because they are fast and their binary descriptors match in microseconds.
2. Take the three newest keyframes 5 cm to 1 m away and facing within 30°, because recent views share most of the scene.
3. Keep mutual best matches that beat the second best by a ratio of 0.8, to drop repeated texture.
4. Drop matches more than 4 px from the epipolar line the poses predict (hloc's rule), so the poses vet the matches.
5. Triangulate each pair at the midpoint of its two rays; keep points in front of both cameras, reprojecting within 2 px, crossing at 1° or more.
6. Give each point the error z · σ / (f · sin parallax) with σ = 1 px, and drop points worse than 10% of their depth.
7. Average a feature's depths from several keyframes by inverse variance.
8. Add the frame to the window of 8 keyframes once it has moved 10 cm or turned 15°.

Dense, per frame:

1. Choose two keyframes whose baseline is nearest a tenth of the typical depth (about 6° of parallax).
2. Halve the images. Test candidate depths: evenly spaced in inverse depth from 0.3 to 10 m, or within ±30% (e^±0.3) of a prior.
3. Use as many candidates as put neighbours about one pixel of disparity apart in the wider keyframe (16 to 128).
4. Cost each candidate by the Census distance (5 × 5 window, 24 bits) between the pixel and where it lands in each keyframe.
5. Smooth the costs with semi-global matching along four scan lines (P1 = 1, P2 = 6 bits), so neighbours agree on surfaces.
6. Take the cheapest candidate, refine between its neighbours, and set confidence from its margin over the next-cheapest non-neighbour.
7. Give zero confidence at the first and last candidates, where the true depth may lie outside the range.

## Run it

From the repository root, in the locked environment:

```python
import numpy as np
from sitescan import session
from sitescan.session.wire_v1 import world_from_camera_cv
from sitescan.triangulate import Triangulator

triangulator = Triangulator()
for frame in session.read_wire_session("tests/fixtures/tum_desk_20"):
    camera, pose = session.camera(frame), world_from_camera_cv(frame.pose)
    sparse = triangulator.sparse(frame.grey, camera, pose)
dense = triangulator.dense(frame.grey, camera, pose, frame.t_ns)
print(len(sparse.depth_m), round(float(np.median(sparse.depth_m)), 2), len(triangulator.window))
print(dense.depth_m.shape, dense.source, round(float((dense.confidence >= 128).mean()), 2))
# 407 0.98 8
# (240, 320) sweep 0.28
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| `FEATURES` | 2,000 | Hundreds of matches survive per frame on the fixture | [Fixture trial](../../research/experiments/triangulation/README.md) |
| `MAX_EPIPOLAR_PX` | 4 px | hloc's check of matches against known poses | [Parts review](../../research/visual_inertial_odometry/depth_without_arcore_2026-11-12.md#step-1-sparse-triangulation-along-the-path) |
| `MAX_REPROJECTION_PX` | 2 px | Rejects matches the midpoint cannot explain in both views | [Stage tests](../../tests/test_sitescan_triangulate.py) |
| `MIN_PARALLAX_DEG` | 1° | Below it one pixel of error is more than 11% of the depth at f = 525 px | [Stage tests](../../tests/test_sitescan_triangulate.py) |
| `MAX_RELATIVE_SIGMA` | 10% | Keeps points that can size learned depth, whose own shape error is 8–16 cm | [Project plan](../../PROJECT_PLAN.md#the-design-the-evidence-supports) |
| Sparse references | 3 newest usable | Keyframes 0.3–0.4 m back kept 0–71 matches; the newest kept 214–690 | [Fixture trial](../../research/experiments/triangulation/README.md) |
| Keyframe step | 10 cm or 15° | The window of 8 then spans about 0.8 m | [Fixture trial](../../research/experiments/triangulation/README.md) |
| `DENSE_BASELINE_PER_M` | 0.1 | About 6° of parallax: enough precision, little change in appearance | [Fixture trial](../../research/experiments/triangulation/README.md) |
| `PLANE_STEP_PX` | 1 px | Wider spacing quantised a rendered wall to one candidate | [Fixture trial](../../research/experiments/triangulation/README.md) |
| `PRIOR_BAND` | 0.3 (±30%) | Learned depth sized by sparse points had a median error of 4–15% on the fixture | [Fixture trial](../../research/experiments/triangulation/README.md) |
| `FULL_CONFIDENCE_MARGIN` | 0.6 | Confidence 128 then marks a 30% margin, where the median error fell to 3–5% | [Fixture trial](../../research/experiments/triangulation/README.md) |

## Limits

- Pinhole only. A calibration's distortion is carried but not applied; phone lenses need undistorted feature positions before triangulation.
- Census costs are sampled at the nearest pixel, so a candidate's neighbours cost the same and refinement rarely helps. Depth is quantised to half a pixel of disparity: under 2% of depth at the chosen baseline.
- On the TUM desk fixture, with default intrinsics and no undistortion, sparse depth was within a median 2–5% of the Kinect on frames 9–18, but 11–21% off on fast-turning early frames. Dense depth around a prior was within a median 1.4–6.9% on five of six frames, and 14.5% on the sixth.
- Plane sweep takes 0.1–0.3 s per frame around a prior and up to 0.9 s without, on the desktop CPU, in Python; too slow for every live update.
- Moving objects break the static-scene assumption of both; nothing masks them yet.
- Only one confidence check (the cost margin). A cross-view consistency check is not built.

## Tests

`python -B -m pytest -q tests/test_sitescan_triangulate.py` checks triangulation of
projected points, the stereo error rule, epipolar distances, feature matching on identical
images, sparse depth on a rendered wall, rejection under a wrong pose, inverse-variance
merging, keyframe choice and window rules, Census bits, candidate spacing with and without
a prior, plane counts, semi-global smoothing, refinement and range ends, and a sweep that
finds a rendered wall within one candidate.
