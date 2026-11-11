# Scale

Fits learned depth to measured camera-plane distances. `fit_one` gives one median
factor for an image; `fit_grid` fits cell medians in log space and blends them into
a per-pixel factor. ARCore depth and tracked points supply the measured targets.
Choosing a source, borrowing an earlier scale and selecting frames remain pipeline decisions.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| Learned depth and validity | H × W float array and bool array | Recorded colour grid; learned camera-plane metres |
| `ArcoreDepth`, `Camera` | Shared records | Depth metres, confidence 0–255, intrinsics in pixels |
| Target `uv`, `target` | N × 2 and N float64 arrays | Colour pixels and measured camera-plane metres |
| Tracked world points and pose | N × 3 points, 4 × 4 `world_from_camera` | Metres; OpenCV camera axes in ARCore world |
| `fit_one` result | float or None | Multiplicative scale |
| `fit_grid` result | H × W float array or None | Multiplicative scale on the recorded grid |
| `fallback` | Optional float | Natural logarithm of a scale, used by unsupported grid cells |
| Freshness inputs | Two integers | Depth and camera timestamps, in nanoseconds |

## How it works

1. Keep positive ARCore depth with confidence at least 128 and project it through both cameras onto the colour grid.
2. Transform tracked world points into OpenCV camera axes and retain their positive camera-plane distances.
3. For one scale, take the median measured-to-learned ratio after the required valid support is present.
4. For a grid, take the median log ratio in each supported cell and fill unsupported cells from the frame or supplied log scale.
5. Resize the log-scale grid with bilinear interpolation, then exponentiate, preserving the adopted room fit.

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
# True
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

## Limits

ARCore depth reaches about 2.5 m on these recordings; a fit there does not establish
far-depth accuracy. Grid cells with fewer than 20 targets borrow a scale rather than
measure one. Both fits clip target pixel indices as the original implementation did.
The freshness helper retains the existing one-sided age check, including timestamps
ahead of the camera clock. It is not a clock alignment or scale-expiry rule.

Live tries raw depth, tracked points, then its last scale (`frame_scale` in the live
pipeline). Room chooses fresh depth and a grid fit. These choices belong to the
orchestrators, not this stage. The optional
scale-and-shift experiment remains in `experiments/sfm`.

## Tests

`python -B -m pytest -q tests/test_sitescan_scale.py tests/test_pipelines.py
experiments/sfm/tests/test_dense.py` checks confidence,
camera projection, image bounds, point depth, invalid pairs, support thresholds, grid
blending and fallback, source fallback, freshness and the retained shift experiment.
Golden room and live outputs check the combined numerical result.
