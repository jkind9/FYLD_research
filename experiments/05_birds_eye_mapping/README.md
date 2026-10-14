# Layer 4b: bird's-eye map and area measurement

This folder is part of layer 4, environment visualisation, in the five-layer pipeline described in the [root README](../../README.md). The other part of layer 4, building the 3D surface, lives in [experiments/04_surface_reconstruction](../04_surface_reconstruction/README.md).

This folder answers: **given a 3D model of the site, can we produce a top-down map that gives correct heights, boundaries and areas in metres, and shows clearly what was never seen?** This is where the brief's "estimate the size of the worksite" becomes a number.

**Status:** the first measurement component exists and is in the six-layer walkthrough (Task55, 7 October 2026). `measure.py` fits the dominant plane, lays a 5 cm grid over it and reports seen area, area on the plane, region size, unseen area and height range. `preview.py` draws the top-down map. Known-shape tests pass. It has not been compared with a physical survey (Task53), so no real-world accuracy is claimed.

## How a bird's-eye map works

1. **Choose the ground.** Decide which way is up and where the reference plane is. "Up" can come from gravity measured by the phone's motion sensors (ARCore already reports a gravity-aligned world), from fitting a plane to the floor points, or from a person declaring it. Record which was used, because a tilted plane makes every height wrong.
2. **Lay a grid over the ground.** Pick a cell size, such as 5 cm. Every 3D point falls into one cell when viewed from above.
3. **Summarise each cell.** Choose a rule: the highest surface in the cell, the lowest, or the surfaces within a height band (a slice). Record the rule. The cell also keeps a count of how many observations it got.
4. **Mark what was seen.** A cell with no points is **unknown**, not empty ground. A blank area on the map means "never filmed", never "clear" or "safe".
5. **Measure.** Select a region and add up the area of its observed cells. Report the footprint (area on the ground), the surface area and any volume separately, and report the unknown area alongside them.

Common traps:
- A highest-surface map hides a floor under an overhang, such as a scaffold board over a trench.
- Area in square metres needs a 3D model in real metres. A model with arbitrary scale, as single-camera methods can produce, gives a picture, not an area.
- Outlier points, such as a reflection, can create false walls or false holes.

The outputs are a height map (an image where each pixel is a height), a top-down colour image (an orthographic view, with no perspective) and the observed/unknown mask, all with the cell size and the grid's position recorded.

## The first method: grid footprint

`measure.py` follows the five steps above with these settings (Task55, chosen under the owner's delegation on 7 October 2026):

| Step | What the code does | Setting |
|---|---|---|
| Choose the ground | `fit_dominant_plane`: RANSAC on a seeded random sample, then a least-squares refit on all points near the winning plane. "Up" is passed in by the caller; the walkthrough points it towards the cameras. | inlier distance 0.02 m, 500 tries, 50,000-point sample, seed 0 |
| Lay a grid | Axes are the two main directions of the points lying on the plane, so furniture standing on it cannot turn the grid. The grid starts at the lowest coordinate on each axis. | 5 cm cells |
| Summarise each cell | Highest point above the plane | — |
| Mark what was seen | A cell with at least one point is seen; every other cell is unknown | at least 1 point |
| Measure | Seen footprint, area on the plane itself (points within 0.02 m of it), the region rectangle around all seen cells (length along the plane's longest direction, width across it, measured on cell edges), the unknown area inside that rectangle, and the highest and lowest cell tops | metres and square metres |

The region rectangle is only the box around what was seen. Space outside it is not claimed either way.

Points can be passed as one array or as `PointChunks`, one chunk per frame. Chunks are read one at a time on each of three passes (grid axes, grid extent, cell contents), so memory stays at about one frame plus the grid however long the recording; the result is identical to passing one array. A grid that would need more than 16,000,000 cells (200 m x 200 m at 5 cm, usually caused by stray far points) is refused with the span it would have covered. In the walkthrough, an origin that cannot be measured (too few points, points on a line, no plane) is skipped with its reason saved, and the other origins are still measured.

`preview.py` draws one grid as a top-down picture: blue at the plane to yellow at the highest cell, purple where a cell's top is more than 2 cm below the plane (for example floor beside a desk-top plane), grey where nothing was seen. The footer gives the size, cell size and colour scale.

### Known-shape tests

`tests/test_measurement.py` (20 tests) checks answers written from the shape definitions, never from the projection code. Every shape has one point at its corner and all others at 0.005 + 0.01k m, so no point sits on a cell edge.

| Shape | Expected and checked |
|---|---|
| Flat 2 m x 3 m rectangle | 6.00 m² seen and on the plane, 0 unknown, 3.00 m x 2.00 m |
| Same with a 1 m x 1 m hole | 5.00 m² seen, 1.00 m² unknown, region still 3.00 m x 2.00 m |
| Rectangle turned 30° and tilted 20°, plane found by RANSAC | area within 0.50 m² (perimeter x cell) of 6.00 m², sides within 0.10 m |
| 0.5 m board 0.8 m above the centre or a corner | area unchanged at 6.00 m², grid not turned, highest point 0.80 m |
| Noisy floor (2 mm) with 30% clutter | normal within 1°, identical for the same seed |
| Empty, non-finite, wrong-shape or non-metre input; bad cell size | refused with a clear error |

Run them with `python -m pytest experiments/05_birds_eye_mapping/tests -q`.

### First real runs

The walkthrough's `GridFootprint` method measured 30 frames of TUM `freiburg1_xyz`. The dominant plane is the desk top. Results with the two depth sources ([walkthrough README](../../src/walkthrough/README.md#first-real-method-runs-7-october-2026)):

| Depth source | Points on the plane | Desk-plane area | Seen footprint | Region | Unknown inside region |
|---|---|---|---|---|---|
| Kinect sensor depth | 51% | 2.21 m² | 4.09 m² | 4.40 x 3.10 m | 9.56 m² |
| Depth Anything V2 Metric Small | 17% | 7.44 m² | 16.37 m² | 5.25 x 5.85 m | 14.35 m² |

Learned depth inflates every area three to four times. The desk has no tape-measured size yet, so neither row is checked against reality.

## Methods: hosted and on the phone

| Method | Route | What it does | Notes |
|---|---|---|---|
| Plane fitting with [Open3D](https://www.open3d.org/docs/0.19.0/tutorial/geometry/pointcloud.html#Plane-segmentation) (RANSAC) | Either | Finds the ground plane in a point cloud | MIT licence. The planned first step for the hosted route. |
| Grid projection in NumPy, or [PDAL](https://pdal.io/) for large clouds | Hosted | Turns points into height maps and top-down images | Simple, inspectable code is the planned baseline. |
| [OpenDroneMap](https://opendronemap.org/) or [COLMAP](https://colmap.github.io/) | Hosted | Builds a true top-down photo (orthomosaic) from overlapping images | Needs good overlap and an independent scale. |
| Elevation mapping ([ANYbotics elevation_mapping](https://github.com/ANYbotics/elevation_mapping)) | Hosted or edge | Height map that carries uncertainty from the camera position | Robotics method; useful for uneven ground and trenches. |
| [OctoMap](https://octomap.github.io/) | Hosted or edge | 3D grid that marks space as occupied, free or unknown | Keeps "never seen" separate from "empty". |
| [ARCore planes](https://developers.google.com/ar/reference/java/com/google/ar/core/Plane) | On the phone | ARCore detects floor and wall planes live and gives each floor plane an outline | Gives a rough footprint and area on site with no server. Accuracy on these phones is unmeasured. |
| [RTAB-Map for Android](https://github.com/introlab/rtabmap) | On the phone | Builds a live 2D occupancy map and mesh using ARCore's camera position | BSD-3 core licence. Useful for a coverage-gap view on site. |

## Top 5 sources

| Source | What it is | Why it matters here |
|---|---|---|
| [Construction progress from top-down images](../../research/construction_site_context/construction_orthographic_progress.md) | Research using orthographic views to track construction work | Shows top-down views are useful on real sites. Its completion results do not measure geometry accuracy. |
| [OctoMap](https://octomap.github.io/octomap/doc/index.html) | A widely used 3D mapping library | Its occupied, free and unknown states are the model for keeping unseen areas visible. |
| [ANYbotics elevation_mapping](https://github.com/ANYbotics/elevation_mapping) | Height mapping for walking robots | Handles uneven ground and carries position uncertainty into heights. |
| [ARCore planes](https://developers.google.com/ar/reference/java/com/google/ar/core/Plane) | Android's live plane detection | The cheapest on-phone area estimate on both test phones. |
| [Apple RoomPlan](../../research/phone_ar_platforms/apple_roomplan.md) | Apple's room-scanning API | Shows a finished floor-plan product. It needs Apple hardware with a laser sensor, which our phones lack, and it models rooms as boxes rather than measured surfaces. |

## How this layer will be tested

### Test shapes with known answers

The first tests use simple made-up shapes defined in advance: a flat plane, steps, a rectangular pit, holes and an overhang. Their true dimensions, heights, areas and visibility masks come from the shape definitions, written separately from the projection code. This way a bug in the projection cannot also produce the "expected" answer. Record dimensions, coordinate frames and grid settings before generating them. No download is needed.

The real ICL-NUIM living-room model at `data/icl_nuim/reference_surface/living-room.ply` can be used later as a realistic input. It cannot replace the test shapes, because its true floor areas and heights are not independently given. [ICL acquisition record](../../data/README.md#icl-acquisition-and-verified-contents). After that come reconstructed surfaces from layer 4 and then phone captures.

### Inputs and outputs

- **Input:** 3D geometry with declared units and coordinate frame, a reference plane and an up direction. Record where the plane and up direction came from: a measured site marker, gravity, a fitted plane or a person's declaration. Unverified choices stay visible in the output metadata.
- **Output:** a grid or orthographic image with cell size, extent, origin and orientation in the input's units. Observed and unknown masks. The height rule used for each cell. Colour and observation counts are descriptive only; they are not confidence values or evidence of free space.

### Steps

1. Project test shapes containing a plane, steps, holes, objects and an overhang.
2. Check axes, heights, boundaries and cell assignment against the known shapes.
3. Compare highest-surface maps with labelled height slices.
4. Vary cell size and measure how detail and observed area change.
5. Apply the checked projection to reconstructed surfaces, then to repeated phone captures.

### Measurements and failure cases

Measure height error, boundary error, dimensions, observed area and agreement between repeated captures. Always report unknown area next to measured area. Agree numeric limits for the first real output before claiming success.

Test empty input, invalid coordinates, wrong units, a tilted reference plane, outliers and overlapping surfaces. Bad input must stop with a clear error rather than produce a misleading map. With an uncertain reference plane, a labelled overview is possible but heights and areas are not established.

Recognising whether work is finished is a separate task. It needs its own definitions and evidence beyond a top-down image.

## What can be improved

- **Survey a real floor.** The known-shape tests pass, but no real area has been checked against a tape measure (Task53).
- **Choose the plane deliberately.** The dominant plane is whatever surface holds most points (the desk top on TUM). A site floor needs gravity from the phone or a declared marker.
- **Score ARCore plane areas on both phones** against a tape-measured floor. If close enough, this becomes the on-site size check.
- **Carry uncertainty into area.** Camera drift and depth noise both blur boundaries. Report an area range, not just a single number.
- **Handle multi-level sites**, such as trenches and stacked materials, with height slices rather than one highest surface.
- **Combine repeated visits.** Align maps from different days only after their coordinate frames are linked by a checked transform.

Projection code will move to [experiments/shared](../shared/README.md) once its tests pass, so any geometry source can use it. See the [experiment guide](../README.md) for how the layers connect.

## Current delivery ownership, 7 October 2026

[Task55](../../task_list/closed/55_implement_site_dimensions_and_area_measurement.md) built the first dimensions/area component, its known-shape tests and its walkthrough method. [Task56](../../task_list/open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md) owns the complete walkthrough benchmark. [Task53](../../task_list/open/53_collect_independent_scene_measurements_and_object_.md) supplies the physical reference measurements that real areas still need.

## Walkthrough measurement boundary

Step 5 of the walkthrough uses `GridFootprint` (`src/walkthrough/steps/mapping.py`) when `--mapping grid-footprint` is passed. It measures each tracking origin separately, never joining separate worlds, saves each origin's grids under `output/predictions/mapping/`, and the visual index shows one top-down map per origin. It does not infer area from sampled viewer points or fill unseen space. See [the six-step runner](../../src/walkthrough/README.md).
