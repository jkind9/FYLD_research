# Scale

Fits learned depth to measured camera-plane distances. `fit_one` gives one median
factor for an image; `fit_grid` fits cell medians in log space and blends them into
a per-pixel factor; `fit_power` fits a factor that changes with distance. Any measured
depth map (ARCore's or a plane sweep's), tracked points or triangulated points supply the
targets, optionally with weights. Choosing a source, borrowing an earlier scale and
selecting frames remain pipeline decisions.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| Learned depth and validity | H × W float array and bool array | Recorded colour grid; learned camera-plane metres |
| `MeasuredDepth`, `Camera` | Shared records | Depth metres, confidence 0–255, intrinsics in pixels |
| `weight` (optional) | N float64 | Relative trust in each target; `target_weights` gives 1 / (variance in log depth) |
| Target `uv`, `target` | N × 2 and N float64 arrays | Colour pixels and measured camera-plane metres |
| Tracked world points and pose | N × 3 points, 4 × 4 `world_from_camera` | Metres; OpenCV camera axes in ARCore world |
| `fit_one` result | float or None | Multiplicative scale |
| `fit_grid`, `fit_power` result | H × W float array or None | Multiplicative scale on the recorded grid |
| `fallback` | Optional float | Natural logarithm of a scale, used by unsupported grid cells |
| Freshness inputs | Two integers | Depth and camera timestamps, in nanoseconds |

## How it works

1. Keep positive ARCore depth with confidence at least 128 and project it through both cameras onto the colour grid.
2. Transform tracked world points into OpenCV camera axes and retain their positive camera-plane distances.
3. For one scale, take the median measured-to-learned ratio after the required valid support is present.
4. For a grid, take the median log ratio in each supported cell and fill unsupported cells from the frame or supplied log scale.
5. Resize the log-scale grid with bilinear interpolation, then exponentiate, preserving the adopted room fit.
6. With weights, every median above is a weighted median: the value where the sorted weights reach half their sum.
7. Weight a triangulated target by 1 / (0.05² + (σ / depth)²), so far points from short baselines count less, but no single precise point outweighs the learned depth's own 5% error.
8. For `fit_power`, drop targets more than 3 robust standard deviations off a Theil–Sen line of log ratio against log learned depth, then fit a weighted least-squares line: scale = e^a · learned^b.
9. Keep b within ±0.5, set b = 0 when the targets span less than a factor of 1.5 in learned depth, and hold the scale at its end values beyond the targets' range, so the fit never extrapolates.

## Run it

Run from the repository root with `.venv/Scripts/python.exe`:

```python
import numpy as np
from sitescan import scale, session

frame = next(session.frames("tests/fixtures/tum_desk_20"))
uv, target = scale.depth_targets(frame.depth, frame.camera)
learned = np.full(frame.image.shape[:2], 2.)
valid = np.ones_like(learned, bool)
print(scale.fit_one(learned, valid, uv, target) > 0)
print(scale.fit_grid(learned, valid, uv, target).shape)
print(scale.fit_power(learned, valid, uv, target).shape)
# True
# (480, 640)
# (480, 640)
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| `min_confidence` | 128 | Adopted confidence cutoff on ARCore's 0–255 scale | [Scale tests](../../tests/test_sitescan_scale.py) |
| `minimum` | 50 pixels | Required support for the adopted raw-depth fit | [Pipeline tests](../../tests/test_pipelines.py) |
| Tracked-point minimum | 20 points | Existing live source requirement, passed by its caller | [Pipeline tests](../../tests/test_pipelines.py) |
| `cells` | 8 × 6 | Held-out AbsRel 0.044 against 0.065 for one scale per frame | [Adopted chain](../../DESIGN.md#2-where-the-project-is) |
| `min_cell_pixels` | 20 pixels | Existing support rule for each grid cell | [Scale tests](../../tests/test_sitescan_scale.py) |
| `fallback` | None | Use the frame's median log ratio in unsupported cells | [Scale tests](../../tests/test_sitescan_scale.py) |
| `max_age_s` | 0.1 s | Exclude repeated old depth from room reconstruction | [Freshness evidence](../../DESIGN.md#713-learning-from-sceneview-and-open3dmap) |
| `LEARNED_LOG_SIGMA` | 0.05 | Learned depth's typical relative error once sized; caps any one target's weight | [Parts review](../../research/visual_inertial_odometry/depth_without_arcore_2026-11-12.md#step-2-sizing-learned-depth-with-the-measured-points) |
| `MAD_K` | 3 | Robust outlier test from the MRAC rule | [Parts review](../../research/visual_inertial_odometry/depth_without_arcore_2026-11-12.md#step-2-sizing-learned-depth-with-the-measured-points) |
| `MIN_LOG_SPAN` | log 1.5 | Too little spread in depth cannot fix a slope | [Scale tests](../../tests/test_sitescan_scale.py) |
| `MAX_SLOPE` | 0.5 | The far-depth error seen (about 15% too near beyond 3 m) needs a slope near 0.14 | [Project plan](../../PROJECT_PLAN.md#status-at-a-glance) |

## Limits

ARCore depth reaches about 2.5 m on these recordings; a fit there does not establish
far-depth accuracy. Grid cells with fewer than 20 targets borrow a scale rather than
measure one. Both fits clip target pixel indices as the original implementation did.
The freshness helper retains the existing one-sided age check, including timestamps
ahead of the camera clock. It is not a clock alignment or scale-expiry rule.

Live tries raw depth, tracked points, then its last scale (`frame_scale` in the live
pipeline). Room chooses fresh depth and a grid fit. These choices belong to the
orchestrators, not this stage. The optional
scale-and-shift experiment remains in `research/experiments/sfm`.

The fits take any `(pixels, metres)` targets; `depth_targets` reads any `MeasuredDepth`,
whether ARCore's or a plane sweep's. `fit_power` is a two-number curve: it corrects a size
that drifts with distance, not shape errors within one distance. On the TUM desk fixture it
cut the room's median surface error from 9.0 to 6.4 cm against the grid fit with sparse
targets, and from 8.9 to 6.3 cm with dense ones; one fixture, so not yet a default
([fixture trial](../../research/experiments/triangulation/README.md)).

## Tests

`python -B -m pytest -q tests/test_sitescan_scale.py tests/test_pipelines.py
research/experiments/sfm/tests/test_dense.py` checks confidence,
camera projection, image bounds, point depth, invalid pairs, support thresholds, grid
blending and fallback, source fallback, freshness and the retained shift experiment;
weighted medians in both fits, target weights, outlier rejection, a power law recovered
through 20% outliers, the clamp outside the targets' range, and the single-scale case.
Golden room and live outputs check the combined numerical result.
