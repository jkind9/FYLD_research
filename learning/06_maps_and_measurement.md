# 6. Maps and measurement

A 3D surface in metres (chapter 5) is not yet a measurement. Someone has to say which way is up, where the ground is, what region counts, and what was never seen. This chapter covers the top-down map the project builds and the traps in reading areas off it.

## Five steps to a top-down map

1. **Choose the ground.** Decide which way is up and where the reference plane is. "Up" can come from gravity (the phone's IMU; ARCore already reports a gravity-aligned world), from fitting a plane to the floor points, or from a person declaring it. Record which was used: a tilted plane makes every height wrong.
2. **Lay a grid over the ground.** Pick a cell size, such as 5 cm. Every 3D point falls into one cell when viewed from above.
3. **Summarise each cell.** Choose a rule (highest surface, lowest surface, or a height band) and record it. Keep a count of observations per cell.
4. **Mark what was seen.** A cell with no points is **unknown**, not empty. A blank area on the map means "never filmed", never "clear" or "safe".
5. **Measure.** Add up the area of observed cells in a selected region. Report footprint, plane area and the unknown area together.

Viewed straight down with no perspective, the result is an *orthographic* map: a height image, a colour image and an observed/unknown mask, with the cell size and grid position recorded.

## How the project's method works

`experiments/05_birds_eye_mapping/measure.py`, `GridFootprint` in the walkthrough:

- **Ground plane by RANSAC**: try 500 random three-point planes on a 50,000-point sample, keep the one with the most points within 2 cm, then refit by least squares on all points near it.
- **Grid axes from the plane's own points**, so furniture standing on it cannot rotate the grid.
- **5 cm cells**, highest point above the plane per cell, seen if it holds at least one point.
- **Outputs**: seen footprint, area on the plane itself, the rectangle around all seen cells, the unknown area inside that rectangle, and the height range.

It is checked against 20 shapes with answers written from the shape definitions: a 2 × 3 m rectangle gives 6.00 m²; with a 1 × 1 m hole it gives 5.00 m² seen and 1.00 m² unknown; tilted and turned it stays within one perimeter-times-cell-size of 6.00 m².

## Traps

- **Overhangs hide floors.** A highest-surface map shows a scaffold board, not the trench under it.
- **Area needs real metres.** A model with arbitrary scale (chapter 4) gives a picture, not an area.
- **Wrong depth size inflates area by the square.** A depth 1.4 times too far makes a surface 1.4 times wider and 1.4 times longer: about 2 times the area, before any other error.
- **Outlier points** (a reflection, a mismatched feature) can create false walls or holes.
- **The fitted plane may not be the floor.** On a desk recording it is the desk top.

> **Project result: learned depth inflates areas three to four times.** On 30 frames of TUM xyz, the desk-top plane measured 2.21 m² with Kinect depth and 7.44 m² with Depth Anything; the seen footprint 4.09 against 16.37 m². Neither is checked against a tape measure yet. Only 17% of Depth Anything's points lay on the plane, against 51% for the Kinect, because the wrong per-frame size smears the desk into a thick slab. (`experiments/05_birds_eye_mapping/README.md`.)

This is why chapters 2-5 matter: area is the end of a chain, and every error upstream reaches it, multiplied.

## Try it

```text
python -m pytest experiments/05_birds_eye_mapping/tests -q
```

Each test builds a known shape and checks the measured area, unknown area and rectangle against hand-written answers.

## Further reading

- [Construction progress from top-down images](../research/construction_site_context/construction_orthographic_progress.md): how a top-down map is used on site, and why interpretation differs from geometric accuracy.
- `research/start_here.md`, "From a scene to a top-down map".
