# Live processing of the phone stream

This package turns the phone's stream into a surface, a top-down map and object counts while the stream runs, updating at least once per second on the CPU (the owner's floor, 14 October 2026). It reads the per-frame format in [phone_session_v1.md](../../experiments/01_camera_capture_delivery/phone_session_v1.md): image, ARCore pose, tracked points, raw depth when new, and pose corrections. Task89.

## How one update works

Frames arrive about 30 times a second. `LiveProcessor.add()` only records each one: the newest posed frame (preferring one that carries new ARCore depth), the keyframe anchors and their corrections. `LiveProcessor.update()` then works on that newest frame and returns one record. Frames that arrive while an update runs are not queued, so the result never falls behind the phone.

| Stage | What it does | Code it reuses |
|---|---|---|
| Depth | Depth Anything V2 Metric Small on the CPU | `src/walkthrough/steps/depth.py` |
| Size | Multiply the learned depth by median(ARCore depth / learned depth) over raw-depth pixels with confidence at least 128 (at least 50 pixels), else over tracked points (at least 20), else keep the last size | `experiments/sfm/src/dense.fit_size` (Task72's rule) |
| Fuse | Add the sized depth to the current *fragment*: an Open3D signed-distance volume for a group of 10 keyframes, stored relative to the group's first anchor | `fragments.py` |
| Surface | Every fragment's points, placed with its anchor's latest pose | `fragments.py` |
| Map | Dominant plane and grid footprint (Task55 settings) on the surface thinned to 2.5 cm | `experiments/05_birds_eye_mapping/measure.py` |
| Objects | YOLO26x on the frame, placed in 3D from the sized depth, counted by same-class matching within 0.35 m (ambiguity margin 0.05 m); runs on a second thread beside fusion and mapping | `experiments/06_object_recognition/pilot/` |

**When ARCore corrects its path**, it moves its anchors. Each fragment, and each counted object, is stored relative to a keyframe anchor, so it moves with that anchor's newest pose. Nothing is re-fused. The idea and its limits are in [research/camera_tracking_and_slam/fragments_and_anchors.md](../../research/camera_tracking_and_slam/fragments_and_anchors.md).

This replaces Tasks 76 and 77. The camera path now comes first (from ARCore, before any depth), and learned depth is sized to the tracker's depth and points. The walkthrough in `src/walkthrough` stays as the offline route for recorded files.

## Run it

```text
# live, from the phone (the app's "Stream to computer" button; type this computer's address into the app)
.venv-yolo\Scripts\python -m src.live.run --listen 8765 --out outputs/live/<name>

# a saved session (from the receiver or the stand-in below), fed at its recorded speed
.venv-yolo\Scripts\python -m src.live.run --replay <session folder> --out outputs/live/<name>
```

Each run writes `updates.jsonl` (one line per update: frame used, delay, stage times, size and its source, map measurements, counts), `surface.ply` and `summary.json` (updates per second, longest gap between updates, median stage times). `--voxel` sets the fusion voxel (default 0.02 m), `--threads` the CPU threads for the models (default 16), `--no-objects` skips detection.

**Until ARCore recordings exist**, `python -m src.live.stand_in --recording tum:<folder> --out <session>` writes a recorded clip in the same format. It uses the clip's ground-truth poses and its depth sensor subsampled to ARCore's size, sends new depth on every 3rd frame and 20 points per frame, and starts one anchor per second. Its `session.json` says `control: reference`, so results from it are a check of the pipeline and its speed, not of ARCore.

`python -m src.live.score --run <run> --icl data/icl_nuim` scores an ICL run's surface against the published model, as `experiments/sfm/run_dense.py` does.

## Results, 14 October 2026 (stand-in sessions, replayed at recorded speed, 32-thread desktop CPU, models on 16 threads)

| Recording | Frames received | Updates | Updates per second | Longest gap | Update time, median | Delay, frame to result |
|---|---:|---:|---:|---:|---:|---:|
| TUM fr1 xyz, 2 cm voxel | 796 | 51 | 1.90 | 0.61 s | 526 ms | 585 ms |
| TUM fr1 desk, 2 cm voxel | 596 | 33 | 1.61 | 0.72 s | 621 ms | 661 ms |
| ICL living room, 1 cm voxel | 880 | 28 | 0.89 | 1.47 s | 1,149 ms | 1,170 ms |
| ICL living room, 2 cm voxel | 880 | 37 | 1.22 | 0.98 s | 821 ms | 855 ms |

Median stage times on TUM xyz: depth model 250 ms, map 200 ms, surface 35 ms, fusion 6 ms; detection 274 ms on its own thread.

- **TUM meets the floor** with no gap over 1 s. The depth model and the map take most of the time.
- **ICL at Task72's 1 cm voxel does not; at 2 cm it just does.** At 1 cm, extracting and thinning 2.6 million surface points costs about 670 ms per update. At 2 cm the longest gap is 0.98 s, and the map (360 ms) is the largest stage, so a bigger room would cross 1 s. Next speed-up: keep each finished fragment's thinned points instead of re-thinning the whole surface every update.
- **ICL surface accuracy** (`src.live.score`, true path and rendered depth standing in for ARCore): 46 mm mean distance at 1 cm and 52 mm at 2 cm; 71% and 69% of points within 5 cm; 22% of the room covered. Only 28-37 frames were fused, about one a second, so this is not comparable with Task72's every-frame 93 mm.
- **Object counts are far too high.** TUM xyz ends with 15 chairs, 7 TVs and 6 people. Live updates see each object about twice a second, through learned depth, so a sighting often lands more than 0.35 m from the last one and starts a new object. The counting rule was tuned on reference depth at every frame (Task46). It needs its own task.
- **No corrections were exercised on real data.** The stand-in has none; the anchor maths is covered by tests only.

## Tests

`src/live/tests` (in the default `pytest` paths): sizing from ARCore depth through both camera models, then points, then the last size; fragments joined by keyframe group and moved with their anchor; the processor on a synthetic session, including a correction that moves the surface and keeps one object as one; the stand-in read back by the host reader; the run loop end to end with fake models.
