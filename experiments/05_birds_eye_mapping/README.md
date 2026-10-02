# Experiment 05: bird's-eye mapping

## The piece we are testing

Can supplied three-dimensional geometry produce a top-down representation preserving dimensions, heights and unknown regions? This piece owns projection and interpretation. It does not reconstruct surfaces or estimate camera poses.

Start with analytically defined known geometry, generated independently of any reconstruction implementation. This needs no phone or preceding piece. A projection error should be diagnosable independently of capture and tracking. Experiment 04's surface can later replace the fixture through the same agreement. See the [dataset and fixture plan](../datasets/README.md).

## Development fixtures and reference

Develop against independently specified shapes: a plane, steps, a rectangular depression, holes and overhanging surfaces. Their definitions must provide expected dimensions, heights, areas and observation masks separately from the projection implementation. Record dimensions, coordinate frames and grid settings before generating them. These fixtures do not exist yet; creating them with independent expected answers is the first implementation step. No public dataset download is needed.

The acquired ICL living-room reference point cloud at `data/icl_nuim/reference_surface/living-room.ply` is available for later realistic geometry input. Its projection does not supply independent expected map measurements, so it cannot replace the known-shape fixtures. Reconstructed ICL surfaces and phone captures are later inputs after the projection checks pass. [Available reference geometry](../../data/README.md#icl-acquisition-and-verified-contents).

## Input and output agreement

Input is geometry with declared units and frame, plus a reference plane and up direction. Record their origin: measured site control, gravity observations, fitted plane or user declaration. Unverified declarations remain visible in metadata.

Output is a grid or orthographic image with cell size and extents in supplied units. Preserve observed and unknown masks. Declare the height rule for each observed cell, such as highest observed surface above the plane. Optional colour and observation counts are descriptive, not confidence probabilities or evidence of free space.

Define grid orientation, origin and coordinate-to-cell mapping. Metric dimensions and area require established metric scale. Arbitrary-scale geometry supports a visual map, not square metres.

## Proposed steps and comparisons

1. Project fixtures containing a plane, steps, holes, objects and overhanging surfaces.
2. Check axes, heights, boundaries and cell assignment against known geometry.
3. Compare highest-surface projection with explicitly labelled height slices.
4. Vary cell size to measure detail and observed information per cell.
5. Apply validated projection to controlled reconstruction, then repeated phone captures when available.

Keep activity recognition separate. Identifying completed work requires additional definitions and evidence beyond a top-down image.

## Measurements, failures and decision

Measure height error, boundary error, dimensions, observed area and repeated-capture agreement. Report unknown area separately. Agree numeric limits for the intended first output before claiming success.

Test empty input, invalid coordinates, wrong units, tilted reference plane, outliers and overlapping surfaces. Highest-surface views can hide a floor beneath an overhang. Blank cells mean unobserved, not clear or safe ground. Invalid-data and bounds checks must prevent misleading maps.

Decide which views support inspection and which explanations accompany them. An uncertain plane permits a labelled overview without established height or area accuracy.

## Research and reuse

[Orthographic construction progress](../../research/sources/20_construction_orthographic_progress.md) motivates useful viewing directions; its completion result is not geometry accuracy. [RoomPlan](../../research/sources/07_apple_roomplan.md) illustrates a different indoor semantic output. [FYLD public context](../../research/sources/21_fyld_public_context.md) frames inspection needs, not thresholds.

Promote projection utilities after fixture tests and interpretation rules pass. They consume geometry independently of its origin. This plan has not been executed. See the [experiment guide](../README.md).
