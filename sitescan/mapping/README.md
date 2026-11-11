# Mapping

Measures a plane-aligned footprint from metric surface points. `fit_dominant_plane`
finds the plane with the most sampled support, then refits it on all inliers. `footprint`
marks observed grid cells and their highest signed heights. `measure_site` adds the
existing surface thinning and camera-based height orientation used by live and room.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `points`, `surface` | N × 3 float64 array | ARCore world metres |
| `cameras` | M × 3 array or list | Camera positions in the same world |
| `Plane` | Point, unit normal, inlier fraction, source | World metres and unit direction |
| `up` | Three numbers | Direction choosing the positive side of the plane |
| `Footprint` | Plane, two basis axes, origin, observed/on-plane masks and maximum heights | Metres and square metres; grid axes follow the plane's principal spreads |
| `measure_site` result | Dict of areas, length, width, highest point and plane normal | Existing summary field names; metres and square metres |

## How it works

1. Thin the site surface at half a map cell to retain the existing live measurement cost.
2. Draw seeded three-point plane candidates and score them on at most 50,000 points.
3. Refit the best candidate using the smallest principal axis of all its inliers.
4. Orient the normal towards the camera mean, then choose in-plane axes using only points inside the plane band.
5. Mark cells containing observations and retain the highest signed height; cells without points remain unknown.

## Run it

Run in `.venv-sitescan` from the repository root:

```python
from sitescan import mapping, session

frame = next(session.frames("tests/fixtures/tum_desk_20"))
plane = mapping.fit_dominant_plane(frame.points_world)
up = frame.pose[:3, 3] - plane.point
grid = mapping.footprint(frame.points_world, plane, up)
print(plane.point.shape, grid.observed.ndim, grid.point_count)
# (3,) 2 20
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| `cell_size_m` | 0.05 m | Existing footprint resolution | [Mapping experiment](../../experiments/05_birds_eye_mapping/README.md) |
| Surface thinning | Half a map cell | Preserve the live processor's cost and point order | [Live mapping caller](../../src/live/processor.py) |
| `inlier_distance_m`, `band_m` | 0.02 m | Existing plane fit and plane-cell tolerance | [Mapping experiment](../../experiments/05_birds_eye_mapping/README.md) |
| `iterations` | 500 | Existing plane candidate count | [Mapping tests](../../experiments/05_birds_eye_mapping/tests/test_measurement.py) |
| `sample_size` | 50,000 points | Existing bound on candidate scoring cost | [Mapping tests](../../experiments/05_birds_eye_mapping/tests/test_measurement.py) |
| `seed` | 0 | Repeatable candidates and fitted plane | [Mapping tests](../../tests/test_sitescan_mapping.py) |
| `min_points` | 1,000 | Preserve the live map's minimum surface support | [Live mapping caller](../../src/live/processor.py) |
| Grid allocation limit | 16,000,000 cells | Preserve the existing bound on grid allocation | [Mapping tests](../../experiments/05_birds_eye_mapping/tests/test_measurement.py) |

## Limits

The dominant plane can be a wall; this method does not establish that it found the
floor. Camera positions choose the normal's sign, rather than a fixed gravity vector.
Areas are observed cells inside a rectangle, not a claim about unseen space. Lengths
are measured at 5 cm cell edges with the default grid. No real-site accuracy score
exists yet. The preserved 15 October room result is 6.35 × 3.30 m.

Product functions take arrays and trust their units and shape. The experiment's
`PointChunks` loaders and input checks remain in `experiments/05_birds_eye_mapping`.
Its array callers use these functions; chunk callers share candidate fitting, scatter
arithmetic and projection while retaining their bounded reading behavior.

## Tests

`tests/test_sitescan_mapping.py` checks seeded fitting, sampling, normal orientation,
unknown cells, summary fields and skipped geometry. Existing mapping tests check
dimensions, rotation, heights, chunk/array parity, allocation limits and previews.
The golden lane and full room rebuild check unchanged numerical summaries. A new
offline page is checked in headless Chromium after this move.
