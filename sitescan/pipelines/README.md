# Pipelines

The two orchestrators. Each decides which frames to use, in what order the stages run,
and what to do when a frame lacks something. Neither contains a method of its own: the
depth, scale, fusion, cleanup, mapping and object steps are the stage functions in
`sitescan/`. The [walkthrough notebook](../../notebooks/00_sitescan_walkthrough.ipynb)
runs each orchestrator, then repeats its steps one stage call at a time and shows that
the result is the same.

| Orchestrator | Uses | When a frame has no ARCore depth | Clean-up | Output |
|---|---|---|---|---|
| `build_room` (offline) | Every frame whose ARCore depth is fresh (under 0.1 s old) | Skips it | Once, on the whole room | `Room`: raw and cleaned surface, per-frame timeline, summary with map |
| `LiveProcessor` (live) | The newest posed frame, once per update | Scales from tracked points, else keeps the last scale | None yet | One record per update: scale, surface size, map, counts, stage times |

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| Recording folder | Format in [session/FORMAT.md](../session/FORMAT.md) | Read with `session.read_wire_session` |
| `model` | Callable from `depth.load_model` | RGB array to depth and validity |
| `detector` | Callable from `objects.load_detector`, or `None` | RGB array to detections |
| `RoomSettings` | `far_m=4.0`, `voxel_m=0.02`, `piece_cell_m=None`, `supported_only=False` | Metres |
| `LiveSettings` | `voxel_m=0.02`, `keyframes_per_fragment=10`, `max_distance_m=0.35`, `ambiguity_margin_m=0.05` | Metres |
| `Room.summary` | dict | Frame outcomes, scale range, clean-up counts, `map` from `mapping.measure_site` |
| Live record | dict | `scale`, `scale_source`, `surface_points`, `map`, `counts`, `stage_ms`, `latency_ms` |

## How the room build works

For each frame in recording order (`fusable_frames`):

1. Keep anchor events: a new anchor starts a keyframe group; a moved anchor moves the surface fused from its group.
2. Skip frames without ARCore depth, without a pose, or whose depth is more than 0.1 s older than the image.
3. Predict depth with the image turned upright (`depth.predict`).
4. Fit an 8 × 6 grid of scales to ARCore's confident depth (`scale.depth_targets`, `scale.fit_grid`). Skip the frame if fewer than 50 pixels match.
5. Fuse metric depth up to 4 m into the keyframe's fragment (`Fragments.integrate`). Keep depth up to 8 m as see-through evidence for the vote.

Then, once:

6. Move each frame's camera by its anchor's correction since it was fused (`vote_views`).
7. Clean the room: visibility vote, then the 50 largest pieces of at least 5,000 points (`cleanup.clean_room`).
8. Measure the cleaned surface (`mapping.measure_site`).

## How a live update works

`add(frame, image_path)` runs for every received frame and only records the newest posed
one, preferring a frame with new ARCore depth. `update()` then:

1. Decodes the image and predicts depth as recorded (not turned upright; see Future work in the root README).
2. Fits one scale: ARCore depth (at least 50 pixels), else tracked points (at least 20), else the previous scale (`frame_scale`).
3. Applies anchor corrections and fuses depth in 0.1–4 m.
4. On a second thread, detects, places and counts objects (`Objects.update`).
5. Measures the whole surface (`mapping.measure_site`).

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

The command line wraps both: see [apps/README.md](../../apps/README.md).

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| Fresh depth | 0.1 s | ARCore depth older than one depth period belongs to another view | [Scale stage](../scale/README.md) |
| `far_m` | 4.0 m | Inherited fusion limit; ARCore depth, which sets the scale, rarely reaches past 2.5 m | [Surface research](../../research/surface_denoising/README.md) |
| `voxel_m` | 0.02 m | 52 mm mean surface error on the synthetic ICL control at 2 cm | [Fusion stage](../fusion/README.md) |
| Grid scale (room) | 8 × 6 cells | Held-out ARCore pixels: median AbsRel 0.044 against 0.065 with one scale, 15 October walk | [Scale stage](../scale/README.md) |
| Map settings (live) | 5 cm cells, 2 cm plane band, 500 iterations | Inherited from the mapping trial | [Mapping stage](../mapping/README.md) |

## Limits

- The room build is offline: the 15 October walk (134 fused frames) took 51 s on a 32-thread CPU with the model on 16 threads.
- Live updates meet the floor of one per second on public recordings at a 2 cm voxel (1.61–1.90 updates/s), and on the 14 October Redmi walk (1.58 updates/s). The whole-surface map grows with the room, so a large room will cross one second. Measured runs: [research/evaluation/results.md](../../research/evaluation/results.md).
- Live depth is predicted sideways on the Redmi and scaled with one factor per frame; the room uses upright images and the grid. Bringing live to the room's rules is the first behaviour change on the list.

## Tests

`python -B -m pytest -q tests/test_pipelines.py` checks that live uses the newest frame,
that a correction moves the surface and the objects, the scale fallback order, the
fresh-depth rule, the vote cameras following corrections, the run loop's files and the
command's refusal to overwrite a run. `pytest -m golden` runs both orchestrators on the
committed fixture and compares every number with the saved outputs.
