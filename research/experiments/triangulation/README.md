# Triangulated depth along a known path: first trial on the TUM desk fixture

**Question.** Owner decision 10 (12 November 2026) takes ARCore out of the product. Real size must then come from depth triangulated along an open tracker's path ([project plan](../../../PROJECT_PLAN.md#the-design-the-evidence-supports)). How close does that depth come to a depth sensor, and how good is learned depth sized by it?

**Short answer, 12 November 2026.** On the 20-frame TUM desk fixture, with the motion-capture path standing in for a tracker:

- **Sparse depth works where the camera moves smoothly.** On frames 9–18 its median error against the Kinect was 1.7–4.6%. On frames 3 and 6, where the camera turns about 10° between frames, it was 11% and 21%.
- **Dense depth needs a prior.** Swept around learned depth sized by the sparse points, its median error was 1.4–6.9% on five of six frames. Without a prior it was 2.2–39% in the median, with heavy tails (90th percentile 52–246%).
- **Learned depth sized by triangulation alone** came within a median 2.2–5.1% of the Kinect on frames 9–18 when sized by dense depth on the grid, and 3.7–6.4% when sized by sparse points. A grid fitted to the Kinect itself, which is not independent, scores 0.9–1.1% on the same frames.
- **Whole rooms sized only by triangulation** sat a median 6.3–9.0 cm from the Kinect surface, against 3.0–3.2 cm for rooms sized by the Kinect, which is scored against the depth it was fitted to. The power fit, a scale that changes with distance, did better than the grid: 6.4 against 9.0 cm with sparse targets.

These numbers come from one short, fast-moving recording, with default intrinsics and no lens undistortion. They show that the components work end to end without ARCore; they do not show phone accuracy.

## Setup

| Item | Choice | Why |
|---|---|---|
| Recording | `tests/fixtures/tum_desk_20`: 20 frames, every 5th of TUM fr1 desk, about 6 cm and 5–10° apart | Committed, public (CC BY 4.0) and has a depth sensor |
| Poses | The fixture's motion-capture poses, written as a TUM trajectory in their own z-up world | Stands in for Basalt, whose world is also z-up. Exercises the reader's turn to a y-up world |
| Reference | The fixture's Kinect depth: 7 of 20 frames, 160 × 120, registered to colour | The only metric depth in the fixture. No triangulated fit sees it |
| Intrinsics | The fixture's 525 / 319.5 / 239.5 | TUM's defaults for registered images. The calibrated values differ (cy 255.3) and the lens has radial distortion (k1 0.26), which nothing here corrects |
| Depth model | Depth Anything V2 Metric Indoor Small, upright input | The adopted model |
| Code | `sitescan/triangulate`, `scale.fit_power`, `scale_sources` in both pipelines | Built on 12 November 2026 |

Run:

```text
.venv/Scripts/python.exe -B -m research.experiments.triangulation.run_fixture --label <label>
```

It takes about a minute on the desktop CPU and writes `results.json` and the trajectory it used to `outputs/tum-desk-20/triangulation-trial/<yyyymmdd-hhmm>_<label>/`. The run reported here is `outputs/tum-desk-20/triangulation-trial/20261112-1246_second`.

## Results

Per Kinect frame. Errors are relative to the Kinect: the median of |measured / Kinect − 1|, from Kinect pixels nearest each measured pixel.

| Frame | Sparse points | Sparse | Dense around prior | Dense, no prior (p50 / p90) | Learned sized by sparse, grid | by sparse, power | by dense, grid | Kinect grid (in-sample) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | none: first keyframe | none | none | none | none | none | 1.3% |
| 3 | 412 | 11.3% | 6.9% | 12.6% / 99% | 11.6% | 6.4% | 8.6% | 1.5% |
| 6 | 47 | 21.2% | 14.5% | 38.9% / 246% | 15.1% | 10.0% | 11.8% | 2.0% |
| 9 | 127 | 4.6% | 5.7% | 10.5% / 174% | 3.7% | 3.3% | 4.7% | 0.9% |
| 12 | 676 | 2.1% | 5.3% | 6.1% / 58% | 3.7% | 6.0% | 5.1% | 1.1% |
| 15 | 806 | 2.9% | 2.1% | 2.7% / 52% | 4.0% | 4.9% | 2.2% | 1.1% |
| 18 | 419 | 1.7% | 1.4% | 2.2% / 71% | 6.4% | 8.6% | 2.9% | 1.1% |

Sparse triangulation took 10–20 ms per frame; the sweep 0.1–0.3 s around a prior and 0.5–0.9 s without one (capped at 128 candidates).

Whole rooms, scored only where the Kinect frames saw (surface points that land on a valid Kinect pixel), by distance to the nearest Kinect point:

| Run | Frames fused | Scored points | Median | 90th percentile | Map length × width |
|---|---|---|---|---|---|
| Fixture's stand-in ARCore poses, Kinect scale (today's route) | 7 | 43,049 | 3.2 cm | 22.1 cm | 4.45 × 3.15 m |
| Tracker poses, Kinect scale (only the poses change) | 7 | 39,862 | 3.0 cm | 19.9 cm | 4.25 × 3.20 m |
| Tracker poses, sparse, grid | 19 | 52,203 | 9.0 cm | 33.6 cm | 3.90 × 2.95 m |
| Tracker poses, sparse, power | 19 | 48,250 | 6.4 cm | 22.8 cm | 4.05 × 3.10 m |
| Tracker poses, dense then sparse, grid | 19 | 55,540 | 8.9 cm | 32.8 cm | 4.40 × 3.10 m |
| Tracker poses, dense then sparse, power | 19 | 49,025 | 6.3 cm | 30.2 cm | 4.40 × 3.40 m |

The first two rows use the Kinect to size depth and are scored against it, so they are optimistic. Triangulated rooms fuse 19 frames rather than 7, because every posed frame after the first has measured targets; the extra frames include 3 and 6, the worst-triangulated.

## What it shows

1. **The chain runs without ARCore.** Tracker poses in a z-up world, anchors made from keyframes, depth triangulated along the path, learned depth sized by it, fusion, clean-up and mapping all ran on the fixture with no ARCore record used.
2. **The fixture's own ARCore stand-in turns images the wrong way.** It writes TUM's z-up poses into ARCore's y-up fields, so the depth model got sideways images on 6 of 7 frames (`turns_3`). Read as a tracker trajectory, the same poses are turned upright first and every frame is predicted upright (`turns_0`). With that, the 90th-percentile surface error fell from 22.1 to 19.9 cm; fusion works relative to anchors, so the world's turn changes nothing else there. The golden outputs keep the old behaviour on purpose.
3. **Recent keyframes, not wide ones, carry sparse triangulation.** Keyframes 0.3–0.4 m back kept 0–71 matches; the newest 0.05–0.1 m back kept 214–690.
4. **Dense sweeps need about one candidate per pixel of disparity.** A first version with 48 fixed candidates, and the widest keyframes, put neighbouring candidates up to about 17 px apart; its median error was 26–286%. Spacing candidates one pixel apart, choosing keyframes about a tenth of the depth away and searching near a prior fixed that.
5. **A scale that changes with distance helps on this scene.** The power fit cut the room's median surface error by about a quarter against the grid fit with either source.

## Limits

- One 3.2 s recording with fast turns; frames 3 and 6 dominate the room errors.
- TUM's default intrinsics and no undistortion: lens distortion near the image edge is several pixels, which the 4 px epipolar test partly rejects and partly absorbs as error.
- The Kinect reference is itself noisy (about 1–3% at 1 m) and sparse (160 × 120).
- The dense sweep's confidence was calibrated on this same fixture.
- Nothing here measures a tracker's own error: the poses are motion capture.

## Second trial: the 15 October Redmi walk, 12 Nov 2026

A stand-in, not a tracker result: ARCore's own camera path was written out as a TUM trajectory (779 poses) and read back as tracker poses, with ARCore's recorded intrinsics as the calibration. Depth was sized by `--scale-sources dense sparse` with the grid fit; ARCore depth was not read. The reference is the same walk built the default way (ARCore poses, sized by ARCore depth). Neither room is ground truth. The walk shows a home, so its outputs stay in the ignored `outputs/redmi-20261015-0939/` (runs `room/20261112-1341_arcore-depth`, `room/20261112-1405_sweep`, `room/20261112-1430_sweep-jump125` and their `compare/` runs).

| Room | Fused frames | Scale, min / median / max | Surface points |
|---|---|---|---|
| ARCore depth | 134 | 0.45 / 0.60 / 0.80 | 554,065 |
| Plane sweep, then sparse | 762 | 0.39 / 0.62 / 1.99 | 1,270,715 |

The triangulated room fuses every posed frame; the ARCore room only the 134 that carried ARCore depth. Dense depth sized all 762; 18 more frames had neither dense depth nor enough sparse points.

- **Scale on the same frames.** Both rooms share camera poses (to 5 × 10⁻¹⁰ m) and learned depth, so on the 134 frames both fused, the ratio of median point distances is the ratio of their scales: median 1.03, 10th–90th percentile 0.95–1.19. 49% of frames agree within 5%, 69% within 10%, 91% within 20%.
- **Surfaces.** ARCore-room points lie a median 3.3 cm (90th percentile 15.6 cm) from the triangulated surface. Triangulated points lie a median 10 cm (90th percentile 67 cm) from the ARCore surface within 2.5 m of a camera, partly because they cover more of the room.
- **What it looks like.** From above, the ARCore room is one room box; the triangulated room is the same room with walls smeared outwards and one piece detached. Frames whose scale is off put the same wall at different distances.

The fixture's 1.4–6.9% dense error does not carry over to every frame of a real walk: one frame in eleven is more than 20% off ARCore's scale.

**Why the clean-up left clutter.** The clean-up ran (vote −198,858 points, pieces −36,395), but its size rule keeps any piece of at least 5,000 points. Besides the room it kept a 113,716-point piece (4.2 × 4.4 × 3.4 m, 0.95 m from the room) and a 5,219-point piece. The large one came from 7 frames (seq 565–572) sized about 2.6 times too large: a second, bigger copy of part of the room. With ARCore depth, the room is one piece of 553,514 points plus fragments under 130 points.

**Skipping frames whose scale jumps** (`--max-scale-jump 1.25`: a frame whose median scale is more than 1.25 times off the median of the last 15 fused frames is not fused):

| Room | Fused | Skipped | Scale, min / median / max | Second-largest piece | Points over 2.5 m from a camera, median gap to ARCore surface |
|---|---|---|---|---|---|
| Plane sweep, no check | 762 | — | 0.39 / 0.62 / 1.99 | 113,716 | 160,637, 1.94 m |
| Plane sweep, check 1.25 | 725 | 37 | 0.47 / 0.62 / 0.88 | 599 | 42,101, 0.59 m |
| ARCore depth, check 1.25 | 129 | 5 of 134 | 0.45 / 0.59 / 0.76 | — | — |

On the 124 frames both rooms fused, 74% agree with ARCore's scale within 10% and 95% within 20% (69% and 91% without the check). The check removed both detached pieces. Seen from above, the room still has streaks and smeared walls joined to it, which no piece-size rule can remove: they come from frames, or grid cells within a frame, sized 10–25% off. The frame-by-frame view now leaves out points the clean-up removed (24.6% of the ARCore room's saved frame points).

## Next

1. Calibrate the Redmi ([Task103](../../../task_list/open/103_measure_redmi_camera_and_imu_calibration_from_owne.md)) and run Basalt on the recorded walks ([Task104](../../../task_list/open/104_compare_open_trackers_and_surfaces_on_the_same_red.md)); then rerun the 15 October room above with Basalt's poses in place of ARCore's path. Before that, find why some frames' plane-sweep scale is 20% or more off, and try the power fit there.
2. Undistort feature positions with the calibration before triangulating.
3. A public visual-inertial recording with a scanned room (for example EuRoC's Vicon rooms) would score the same chain at room scale and far depth; its download and terms are not yet checked ([decision 9](../../../PROJECT_PLAN.md#decisions-needed)).
