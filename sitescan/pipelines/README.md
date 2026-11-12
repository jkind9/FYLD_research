# Pipelines

The two orchestrators. Each decides which frames to use, in what order the stages run,
and what to do when a frame lacks something. Neither contains a method of its own: the
depth, scale, fusion, cleanup, mapping and object steps are the stage functions in
`sitescan/`. The [walkthrough notebook](../../notebooks/00_sitescan_walkthrough.ipynb)
runs each orchestrator, then repeats its steps one stage call at a time and shows that
the result is the same.

| Orchestrator | Uses | When a frame has none of its scale sources | Clean-up | Output |
|---|---|---|---|---|
| `build_room` (offline) | Every posed frame with a scale source; by default, fresh ARCore depth (under 0.1 s old) | Skips it | Once, on the whole room | `Room`: raw and cleaned surface, per-frame timeline, summary with map |
| `LiveProcessor` (live) | The newest posed frame, once per update | Keeps the last scale | None yet | One record per update: scale, surface size, map, counts, stage times |

Both read poses from ARCore by default, or from an open tracker's trajectory and the
phone's calibration (`session.read_tum`, `session.read_calibration`). Both choose scale
targets by name, in order, from the same list in [targets.py](targets.py):

| Scale source | Targets | Needs |
|---|---|---|
| `arcore_depth` | ARCore's confident raw depth | ARCore recording |
| `tracked_points` | The record's 3D points (ARCore's) | ARCore recording |
| `sparse` | Features triangulated against recent keyframes, weighted by their error | Poses, grey images (v2) |
| `dense` | Plane-sweep depth between keyframes, searched around learned depth sized by `sparse` | Poses, grey images (v2) |

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| Recording folder | Format in [session/FORMAT.md](../session/FORMAT.md) | Read with `session.read_wire_session` |
| `model` | Callable from `depth.load_model` | RGB array to depth and validity |
| `detector` | Callable from `objects.load_detector`, or `None` | RGB array to detections |
| `trajectory`, `calibration` | Optional `Trajectory` and `Calibration` from `session` | Tracker poses in a y-up world; the phone's camera |
| `RoomSettings` | `far_m=4.0`, `voxel_m=0.02`, `piece_cell_m=None`, `supported_only=False`, `scale_sources=("arcore_depth",)`, `scale_fit="grid"`, `max_scale_jump=None` | Metres; source names above; `"grid"` or `"power"`; a factor such as 1.25, or off |
| `LiveSettings` | `voxel_m=0.02`, `keyframes_per_fragment=10`, `max_distance_m=0.35`, `ambiguity_margin_m=0.05`, `scale_sources=("arcore_depth", "tracked_points")` | Metres; source names above |
| `Room.summary` | dict | Frame outcomes, `pose_source`, `scale` (sources, fit, frames per source), scale range, clean-up counts, `map` from `mapping.measure_site` |
| Live record | dict | `scale`, `scale_source`, `surface_points`, `map`, `counts`, `stage_ms`, `latency_ms` |

## How the room build works

For each frame in recording order (`fusable_frames`):

1. Keep anchor events: a new anchor starts a keyframe group; a moved anchor moves the surface fused from its group. A tracker's anchors are one a second and never move.
2. Skip frames without a pose. With a triangulated source, triangulate every posed frame against the keyframe window (`Triangulator.sparse`), so the window keeps up.
3. Try each scale source in order (`scaled_frame`). ARCore depth more than 0.1 s older than the image counts as stale. A source with too few targets (50 depth pixels, 20 points) is counted and the next is tried.
4. Predict depth with the image turned upright (`depth.predict`), once, when a source first has enough targets; `dense` needs it earlier, to search around.
5. Fit the scale: an 8 × 6 grid (`scale.fit_grid`) or a curve in distance (`scale.fit_power`), weighted for `sparse`. Skip the frame if no source fits.
6. Fuse metric depth up to 4 m into the keyframe's fragment (`Fragments.integrate`). Keep depth up to 8 m as see-through evidence for the vote.

Then, once:

7. Move each frame's camera by its anchor's correction since it was fused (`vote_views`).
8. Clean the room: visibility vote, then the 50 largest pieces of at least 5,000 points (`cleanup.clean_room`).
9. Measure the cleaned surface (`mapping.measure_site`).

## How a live update works

`add(frame, image_path)` runs for every received frame and only records the newest posed
one, preferring a frame with new ARCore depth. `update()` then:

1. Decodes the image and predicts depth as recorded (not turned upright; see [Plan](../../README.md#plan) in the root README).
2. With a triangulated source, triangulates the frame against the keyframe window (logged as stage `triangulate`).
3. Fits one scale from the first source with enough targets: by default ARCore depth (at least 50 pixels), else tracked points (at least 20), else the previous scale (`frame_scale`).
4. Applies anchor corrections and fuses depth in 0.1–4 m.
5. On a second thread, detects, places and counts objects (`Objects.update`).
6. Measures the whole surface (`mapping.measure_site`).

`run_live(processor, feed, out, about)` feeds frames on one thread and calls `update()` as
often as it can on another, writing `updates.jsonl`, `surface.ply` and `summary.json`.
Frames that arrive during an update are not queued, so results never fall behind.

## Run it

From the repository root, with the local depth weights:

```python
from sitescan.depth import load_model
from sitescan.pipelines import DEPTH_MODEL, build_room

room = build_room("tests/fixtures/tum_desk_20", load_model(DEPTH_MODEL))
print(room.summary["surface_points"], room.summary["map"]["length_m"])
# 51962 4.45
```

On tracker poses, sized only by depth triangulated along them:

```text
.venv/Scripts/python.exe -B -m apps.cli room --session <recording> --label <label> --trajectory <basalt trajectory> --calibration <phone calibration JSON> --scale-sources dense sparse
```

`save_room` writes `surface.ply` (cleaned), `raw_surface.ply` (fused), `voted_surface.ply` (after the vote, before the piece rule), `frames.npz` and `summary.json`. A viewer built from `voted_surface.ply` with `tools.demos.capture_scene` has sliders for the piece rule; at the room build's values it shows `surface.ply`.

The command line wraps both: see [apps/README.md](../../apps/README.md).

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| Fresh depth | 0.1 s | ARCore depth older than one depth period belongs to another view | [Scale stage](../scale/README.md) |
| `far_m` | 4.0 m | Inherited fusion limit; ARCore depth, which sets the scale, rarely reaches past 2.5 m | [Surface research](../../research/surface_denoising/README.md) |
| `voxel_m` | 0.02 m | 52 mm mean surface error on the synthetic ICL control at 2 cm | [Fusion stage](../fusion/README.md) |
| Grid scale (room) | 8 × 6 cells | Held-out ARCore pixels: median AbsRel 0.044 against 0.065 with one scale, 15 October walk | [Scale stage](../scale/README.md) |
| Map settings (live) | 5 cm cells, 2 cm plane band, 500 iterations | Inherited from the mapping trial | [Mapping stage](../mapping/README.md) |
| `max_scale_jump` (room) | Off; trial value 1.25 against the median of the last 15 fused frames, from the 5th fused frame on | A wrongly sized run of frames builds a copy of the room too large for the piece-size rule: on the 15 October walk sized by plane sweep, 7 frames at 2.6 times ARCore's scale made a 113,716-point piece. With ARCore depth the check skips 5 of 134 frames | [Triangulation trial](../../research/experiments/triangulation/README.md) |

## Limits

- The room build is offline: the 15 October walk (134 fused frames) took 51 s on a 32-thread CPU with the model on 16 threads.
- Live updates meet the floor of one per second on public recordings at a 2 cm voxel (1.61–1.90 updates/s), and on the 14 October Redmi walk (1.58 updates/s). The whole-surface map grows with the room, so a large room will cross one second. Measured runs: [research/evaluation/results.md](../../research/evaluation/results.md).
- Live depth is predicted sideways on the Redmi and scaled with one factor per frame; the room uses upright images and the grid. Bringing live to the room's rules is the first behaviour change on the list.
- Without a trajectory, both pipelines take poses and anchors from ARCore's records, so a recording without ARCore and without a trajectory fuses nothing.
- The tracker runs outside the package; only its trajectory file comes in. Its anchors are never corrected, so drift stays in the surface.
- With `dense`, a room build takes about 0.5 s per frame on the desktop CPU, twice the `sparse` build; live updates with `dense` will not meet one per second.
- On the TUM desk fixture, rooms sized only by triangulated depth sat a median 6–9 cm from the Kinect surface, against 3 cm for rooms sized by the Kinect itself ([fixture trial](../../research/experiments/triangulation/README.md)). On the 15 October Redmi walk, with ARCore's path standing in for a tracker, plane-sweep sizing agreed with ARCore depth within 20% on 91% of shared frames; the rest built surface copies the clean-up keeps, which `max_scale_jump` removes in part.

## Tests

`python -B -m pytest -q tests/test_pipelines.py` checks that live uses the newest frame,
that a correction moves the surface and the objects, the scale fallback order, the
fresh-depth rule, the vote cameras following corrections, the run loop's files and the
command's refusal to overwrite a run. On the committed fixture with its poses given as a
z-up tracker trajectory, it checks rooms sized only by `sparse` and by `dense` then
`sparse`, live updates scaled by `sparse`, and the weighting of sparse targets. `pytest -m golden` runs both orchestrators on the
committed fixture and compares every number with the saved outputs.
