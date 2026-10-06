# Layer 4b: bird's-eye map and area measurement

This folder is part of layer 4, environment visualisation, in the five-layer pipeline described in the [root README](../../README.md). The other part of layer 4, building the 3D surface, lives in [experiments/04_surface_reconstruction](../04_surface_reconstruction/README.md).

This folder answers: **given a 3D model of the site, can we produce a top-down map that gives correct heights, boundaries and areas in metres, and shows clearly what was never seen?** This is where the brief's "estimate the size of the worksite" becomes a number.

**Status:** planned. No code or test shapes exist yet.

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
| [Construction progress from top-down images](../../research/sources/20_construction_orthographic_progress.md) | Research using orthographic views to track construction work | Shows top-down views are useful on real sites. Its completion results do not measure geometry accuracy. |
| [OctoMap](https://octomap.github.io/octomap/doc/index.html) | A widely used 3D mapping library | Its occupied, free and unknown states are the model for keeping unseen areas visible. |
| [ANYbotics elevation_mapping](https://github.com/ANYbotics/elevation_mapping) | Height mapping for walking robots | Handles uneven ground and carries position uncertainty into heights. |
| [ARCore planes](https://developers.google.com/ar/reference/java/com/google/ar/core/Plane) | Android's live plane detection | The cheapest on-phone area estimate on both test phones. |
| [Apple RoomPlan](../../research/sources/07_apple_roomplan.md) | Apple's room-scanning API | Shows a finished floor-plan product. It needs Apple hardware with a laser sensor, which our phones lack, and it models rooms as boxes rather than measured surfaces. |

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

- **Build the test shapes and projection first.** This layer has no measured result yet; the known-shape tests are the cheapest way to get one.
- **Score ARCore plane areas on both phones** against a tape-measured floor. If close enough, this becomes the on-site size check.
- **Carry uncertainty into area.** Camera drift and depth noise both blur boundaries. Report an area range, not just a single number.
- **Handle multi-level sites**, such as trenches and stacked materials, with height slices rather than one highest surface.
- **Combine repeated visits.** Align maps from different days only after their coordinate frames are linked by a checked transform.

Projection code will move to [experiments/shared](../shared/README.md) once its tests pass, so any geometry source can use it. See the [experiment guide](../README.md) for how the layers connect.

## Current delivery ownership, 6 October 2026

[Task55](../../task_list/open/55_implement_site_dimensions_and_area_measurement.md) owns the first dimensions/area component and independent known-shape tests. [Task56](../../task_list/open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md) integrates its outputs into the complete walkthrough benchmark. [Task53](../../task_list/open/53_collect_independent_scene_measurements_and_object_.md) supplies physical reference measurements. This remains planned work; a surface viewer is not a measured area result.

## Walkthrough measurement boundary

Step 5 is explicitly unavailable. Task55 must supply real mapping, dimensions, a defined area method and independent error analysis. The canonical runner records this absence; it does not infer area from sampled viewer points or fill unseen space. Deterministic mapping controls stay in root tests. See [the six-step runner](../../src/walkthrough/README.md).
