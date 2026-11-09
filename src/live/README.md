# Live processing of the phone stream

This package turns the phone's stream into a surface, a top-down map and object counts while the stream runs, updating at least once per second on the CPU (the owner's floor, 14 October 2026). It reads [phone session v2](../../experiments/01_camera_capture_delivery/phone_session_v2.md) from FYLD capture and retains replay support for v1: image, ARCore pose, tracked points, raw depth when new, and pose corrections. Tasks89, 96 and 99.

## How one update works

Frames arrive about 30 times a second. `LiveProcessor.add()` only records each one: the newest posed frame (preferring one that carries new ARCore depth), the keyframe anchors and their corrections. `LiveProcessor.update()` then works on that newest frame and returns one record. Frames that arrive while an update runs are not queued, so the result never falls behind the phone.

| Stage | What it does | Code it reuses |
|---|---|---|
| Depth | Depth Anything V2 Metric Small on the CPU | `src/walkthrough/steps/depth.py` |
| Size | Multiply the learned depth by median(ARCore depth / learned depth) over raw-depth pixels with confidence at least 128 (at least 50 pixels), else over tracked points (at least 20), else keep the last size | `experiments/sfm/src/dense.fit_size` (Task72's rule) |
| Fuse | Add the sized depth to the current *fragment*: an Open3D signed-distance volume for a group of 10 keyframes, stored relative to a received anchor in that group | `fragments.py` |
| Surface | Every fragment's points, placed with its anchor's latest pose | `fragments.py` |
| Map | Dominant plane and grid footprint (Task55 settings) on the surface thinned to 2.5 cm | `experiments/05_birds_eye_mapping/measure.py` |
| Objects | YOLO26x on the frame, placed in 3D from the sized depth, counted by same-class matching within 0.35 m (ambiguity margin 0.05 m); runs on a second thread beside fusion and mapping | `experiments/06_object_recognition/pilot/` |

**Clean-up: the offline room build has it, the live processor not yet.** The live processor limits fused depth to 0.1-4.0 m and removes nothing else. The offline `room_build` rejects stale depth, can mask unsupported cells, and since Task126 runs the owner's clean-up (next paragraph). The owner's target scenes are indoor with surfaces under about 10 m (8 November 2026), so the 4.0 m limit cuts part of them; ARCore depth, which sets the size, rarely reaches past 2.5 m.

**Room clean-up: the visibility vote, then the largest pieces (owner, 8 November 2026; Task126). This is a key stage of the system.** The owner tuned every clean-up stage by eye in the Task125 tuner and found that only two changed the room. `room_build` now runs both, in order, on the fused surface:

1. **Visibility vote** (`clean.visibility_vote`): a point is dropped when the frames that see through it outweigh the frames that measure it there (a see-through share above 0.5). Each frame's vote weighs 1/depth², and see-through evidence reaches 8 m.
2. **Largest pieces** (`clean.largest_pieces`): the surface is cut into grid cells (default the 2 cm fusion voxel, `--piece-cell` to change). Filled cells that touch at a face, edge or corner form one *piece*, which is the 3D form of `cv2.connectedComponents` and behaves like splats one cell wide that touch. The 50 largest pieces with at least 5,000 points each are kept. A continuous walk joins the room into one or a few large pieces, so everything else is a floater.

Radius outliers, statistical outliers, frame counts, the spots rule and the normal rule changed nothing visible and are not run. On the 15 October walk (134 frames): 676,855 fused points, the vote removed 100,086 and pieces 22,702, leaving 554,067. The room is one piece; the next largest holds about 4,400 points. On a 32-thread desktop CPU the vote took 2.41 s and pieces 0.15 s, against 82 s for the whole build. The vote's cost grows with frames × points, so fewer, sharper frames make it cheaper. `surface.ply` is the cleaned room and `raw_surface.ply` the room before clean-up; `summary.json` records the counts and times under `clean_up`. Findings and the comparison with point-chain linking: [research/surface_denoising](../../research/surface_denoising/README.md#owners-setting-in-the-room-build-task126).

**Clean-up and far-sizing trial, Task120.** `python -B -m src.live.denoise_trial --session <v2 session> --out <folder>` fuses the `room_build` frames several ways and scores each against held-out ARCore tracked points (81 s on the CPU for the 15 October walk). The visibility vote in `clean.py` cut surface lying on sight lines ARCore saw through from 9.2% to 1.8% (under 2.5 m) and from 8.6% to 4.1% (beyond), for 0.5 points of ARCore coverage. Edge and side-on masks and near-first weights made it worse. Tracked-point sizing fixed far depth (16% too near to 5%) but, as one size per frame, pushed the near floor down. Full table: [research/surface_denoising](../../research/surface_denoising/README.md#trial-on-the-15-october-walk-8-november-2026-task120). `room_build.grid_size` gained an optional `fallback` size for cells without ARCore depth, and `Fragments.placing_anchor` returns the current pose of the anchor placing a keyframe. `python -B -m tools.demos.cleanup_scene --trial <trial folder> --session <v2 session> --out <viewer.html>` builds an offline page of the room with switches that show the vote's deletions in red or hide them, beside the results table (Task121; local only, it embeds photos). A proposed clean-up stage, with three hooks (before fusion, during fusion, at surface extraction) and the trials to run, is in [research/surface_denoising](../../research/surface_denoising/README.md). One constraint for it: the `ScalableTSDFVolume` used in `fragments.py` takes no per-pixel weights and cannot drop voxels seen only a few times; Open3D's newer `VoxelBlockGrid` can do the second.

**Spots rule and pieces by make-up, Task124.** `clean.wide_support` keeps far surface only if it was measured nearer than 2.5 m or by two more views at least 3° from the first measuring view (COLMAP's geometric filter); frames from one standing spot share one size guess, so they do not confirm each other. `clean.piece_majority` joins neighbours within 3 cm whose normals differ by under 30° (PCL's conditional clustering) and drops pieces where most points failed the rule. On the 15 October walk the rule removed 17% of points with ARCore coverage unchanged and kept the staircase, but did not remove the door echoes; the piece test added 0.3%. The trial now also scores surface behind tracked points and door and stair coverage, and `cleanup_scene --views 65 420` adds those camera bookmarks. Results: [research/surface_denoising](../../research/surface_denoising/README.md).

**Clean-up tuner, Task125.** `python -B -m src.live.cleanup_attributes --session <v2 session> --out <folder>` writes the raw fused room (`raw.ply`) and, per point, the evidence each depth-map stage tests (`attributes.npz`; from `clean.vote_tallies`, `clean.spot_evidence`, `clean.views_measuring` and nearest-neighbour distances). `python -B -m tools.demos.cleanup_tuner --attributes <folder> --session <v2 session> --out <page.html> --views 65 420` builds an offline page where every clean-up stage has an on/off tick and every parameter a slider with a description; chain linking and radius outliers run in the page. `denoise_trial.fuse` now also returns each frame's camera, fused depth and see-through evidence.

**When ARCore corrects its path**, it moves its anchors. Each fragment, and each counted object, is stored relative to a keyframe anchor, so it moves with that anchor's newest pose. Nothing is re-fused. The idea and its limits are in [research/camera_tracking_and_slam/fragments_and_anchors.md](../../research/camera_tracking_and_slam/fragments_and_anchors.md).

This replaces Tasks 76 and 77. The camera path now comes first (from ARCore, before any depth), and learned depth is sized to the tracker's depth and points. The walkthrough in `src/walkthrough` stays as the offline route for recorded files.

## Run it

```text
# live, from the capture app (Record walk; type this computer's address into the app): runs the v2 capture
# receiver on port 8766, saves the session under <out>/sessions and processes frames as they arrive
.venv-yolo\Scripts\python -m src.live.run --listen 8766 --out outputs/live/<name>

# a saved session (v2 from the capture receiver, v1 from the old receiver or the stand-in below), fed at its recorded speed
.venv-yolo\Scripts\python -m src.live.run --replay <session folder> --out outputs/live/<name>
```

Each run writes `updates.jsonl` (one line per update: frame used, delay, stage times, size and its source, map measurements, counts), `surface.ply` and `summary.json` (updates per second, longest gap between updates, median stage times). `--voxel` sets the fusion voxel (default 0.02 m), `--threads` the CPU threads for the models (default 16), `--no-objects` skips detection.

For a reference control, `python -m src.live.stand_in --recording tum:<folder> --out <session>` writes a recorded clip in the same format. It uses the clip's ground-truth poses and its depth sensor subsampled to ARCore's size, sends new depth on every 3rd frame and 20 points per frame, and starts one anchor per second. Its `session.json` says `control: reference`, so results from it are a check of the pipeline and its speed, not of ARCore.

## Redmi capture 1.2 result, Task99

The real session `20261014_220756_walk` contains 1,194 frames over 39.88 s. Its saved anchors begin at 1, so the old assumption that each group starts at anchor 0 caused `KeyError: 0`. Each fragment now binds to a received anchor and keeps that binding if an earlier anchor arrives later. The regression test verifies that corrections still move its surface.

CPU replay at recorded speed, with both cached models on 16 threads and a 2 cm voxel, received all 1,194 frames and produced 63 updates: 1.58 updates/s, longest gap 0.856 s, no gaps over 1 s, median update 619.4 ms, median latency 672.5 ms. The saved surface has 845,428 points. There were 83 anchor corrections; sizing used tracked points for 33 updates and the previous estimate for 30. Object counts remain provisional and geometry has no independent accuracy score.

Local outputs are `outputs/capture_task99_220756/live_verified/{updates.jsonl,summary.json,surface.ply}`. The first failed replay is retained separately under `live/`. [Capture metrics and limits](../../experiments/01_camera_capture_delivery/README.md#completed-redmi-session-task99).

Task100 adds an offline [interactive Gaussian viewer](../../outputs/capture_task99_220756/viewer/redmi-walk-gaussian-splats.html) for that surface. It shows 78,328 surface-derived splats with height colours, point/splat switching, top/fit controls, keyboard orbit/zoom, eight camera/photo bookmarks and a Gaussian PLY download. The HTML is 1.58 MB, embeds its photos and needs no server or network. It does not perform photographic Gaussian training. Generate a viewer with:

```text
.venv-yolo\Scripts\python -B -m tools.demos.capture_scene --surface <surface.ply> --session <v2 session folder> --out <viewer.html>
```

The renderer and its previous desk demo are reused. Twelve capture-viewer tests and the existing demo tests pass (30 total); real offline Chromium checks found no browser errors or external requests. Display grouping defaults to 6 cm, proposed by Claude, not owner-ruled. Camera bookmarks use original recorded poses, so later anchor corrections can shift the final surface relative to a photo.

## Redmi 15 October walk, Task107

The 14 October walk saved only empty phone depth maps, so its learned depth was sized from tracked points or carried over from earlier updates. The walk `20261015_093913_walk` (822 frames, 27.5 s) has 147 raw depth maps from ARCore, Google's phone tracking library. It was replayed with the Task99 command and settings unchanged: CPU only, 16 threads, 2 cm voxel, recorded speed, objects on. `clock_check.py` and `recording.py --euroc` both exited 0 and reported no problems.

The two walks follow different routes and differ in length (27.5 s against 39.9 s). This is not a paired comparison. It shows whether sizing from ARCore depth engages and how the map changes, not how large the effect is. ARCore depth is not ground truth, and nothing here measures accuracy.

"Size" is the factor that multiplies the model's depth. "Highest point" is the largest distance above the map's dominant plane, the largest flat surface the plane fit finds. ARCore's world y axis points up, so a floor would have a normal close to y.

| | 14 Oct (Task99) | 15 Oct (Task107) |
|---|---|---|
| Frames received / updates | 1,194 / 63 | 822 / 47 |
| Updates per second | 1.58 | 1.70 |
| Longest gap between updates | 0.856 s | 0.741 s |
| Gaps over 1 s | 0 | 0 |
| Median update / latency | 619.4 / 672.5 ms | 565.6 / 632.7 ms |
| Size from ARCore depth | 0 | 32 |
| Size from tracked points | 33 | 12 |
| Size carried from previous update | 30 | 2 |
| No size (update skipped) | 0 | 1 (update 1, before any source) |
| Size min / median / max | 0.267 / 0.621 / 5.845 | 0.340 / 0.776 / 1.276 |
| Dominant plane normal | [-0.98, 0.12, -0.16] | [0.40, 0.07, 0.91] |
| Angle between normal and world y | 82.9° | 86.2° |
| Highest point above that plane | 5.98 m | 3.55 m |
| Observed area / plane area | 25.26 / 5.32 m² | 15.84 / 5.37 m² |
| Length × width | 6.70 × 6.30 m | 6.35 × 3.75 m |
| Surface points | 845,428 | 578,774 |
| Anchor corrections | 83 | 47 |
| Fragments | 4 | 3 |

ARCore depth now sets the size for 32 of 47 updates (68%). Tracked points cover 12 more. The previous size was reused twice, at updates 35-36. The size stays between 0.34 and 1.28, against a 22-fold spread (0.267 to 5.845) on 14 October. ARCore-depth sizes have median 0.712; tracked-point sizes have median 0.900 on this walk.

The dominant plane is still close to vertical: its normal is 86° from up, so it is a wall, not the floor. Length, width and highest point are therefore measured on and from a wall, not the floor. The 3.55 m highest point is lower than 5.98 m, but it does not show that the height problem is fixed. Whether the floor goes missing because of the plane fit or because the images reached the depth model sideways (the phone was in portrait) is untested. Task109 covers the sideways images.

Local outputs are `outputs/capture_task107_093913/{live/{updates.jsonl,summary.json,surface.ply},euroc/,viewer/redmi-walk-15oct.html,replay.log}`. The viewer holds 47,885 splats in 1.22 MB and embeds household photos, so it stays local.

## Sideways against upright input to the depth model, Task109

The Redmi camera sensor is mounted at 90 degrees (`sensor_orientation_deg: 90`). With the phone held in portrait, every recorded image is on its side, and the live processor passes it to Depth Anything unrotated. `python -B -m src.live.orientation_control --session <v2 session> --out <folder>` runs the cached model twice on the same frames. One pass uses the image as recorded ("sideways"); the other turns it 90 degrees clockwise ("upright") and turns the predicted depth back. Both are scored on the recorded grid after one fitted size per frame (Task72's median rule). Scores are AbsRel (mean absolute relative error) and the share of pixels within 25% (delta < 1.25).

Run on `20261015_093913_walk`: 144 frames pass the sizing rule, and all 144 are portrait by the ARCore pose (the image's long axis within 45 degrees of vertical). 20 are evenly spaced among them (owner-approved settings, 7 November 2026). A saved thumbnail pair was checked by eye: the turned image is the right way up.

| Reference | Input | Median AbsRel | Median share within 25% | Fitted size min / median / max |
|---|---|---|---|---|
| ARCore raw depth | sideways | 0.080 | 93.8% | 0.41 / 0.66 / 0.92 |
| ARCore raw depth | upright | 0.058 | 98.3% | 0.43 / 0.60 / 0.73 |
| ARCore tracked points | sideways | 0.106 | 88.1% | 0.60 / 0.81 / 1.15 |
| ARCore tracked points | upright | 0.090 | 92.4% | 0.55 / 0.63 / 0.76 |

Upright input lowers median AbsRel by 27% against ARCore depth (better in 17 of 20 frames) and by 15% against tracked points (19 of 20). Both clear the 10% bar set for "clearly better". The fitted size also varies less from frame to frame: max/min falls from 2.2 to 1.7 against ARCore depth. Limits: ARCore depth and tracked points are references, not ground truth; this is 20 frames from one walk. Task112 owns turning portrait frames upright in the live processor. That change also has to turn the image intrinsics, or keep the turn inside the depth call as this check does.

Local outputs: `outputs/task109_orientation_093913/{frames.json,results.json,000042_recorded.jpg,000042_upright.jpg}`. Tests: `src/live/tests/test_orientation_control.py`.

## Offline room cloud from the ARCore-depth frames, Task113

`python -B -m src.live.room_build --session <v2 session> --out <folder> [--far 4.0]` builds one room cloud from the frames that carry ARCore raw depth. Each image is turned upright for the depth model (Task109). The predicted depth is then fitted to ARCore's confident raw depth with an 8 × 6 grid of sizes rather than one size per frame, and fused with the live fragments, so anchor corrections still apply. It is offline: it uses every depth frame, not the about 1.7 per second the live loop reaches.

The grid was chosen on held-out pixels. Each of the 144 eligible frames of `20261015_093913_walk` had its ARCore pixels split at random into halves: fit on one half, score on the other. Median AbsRel was 0.065 for one size, 0.058 for size plus offset, 0.049 for a size that tilts across the image, 0.050 for a 4 × 3 grid and 0.044 for an 8 × 6 grid.

Surfaces are compared with ARCore depth alone, fused along the same path. Its floor lies at y = -0.76 m (ARCore's y axis points up) with only a few centimetres of spread. That makes it a yardstick for the floor, not ground truth. It reaches neither the ceiling nor the far walls, so points above its top are not counted as errors here.

| Surface (15 Oct walk) | Frames | Points over 10 cm below the floor | Points within 5 cm of the floor | Dominant plane |
|---|---|---|---|---|
| ARCore depth only | 147 maps | 0.0% | 11.6% | n/a |
| Task107 live replay (sideways, 47 updates) | 47 | 7.7% | 4.0% | wall |
| All posed frames, sideways, one size | 751 | 25.0% | 3.5% | wall |
| All posed frames, upright, one size | 751 | 15.5% | 5.2% | wall |
| ARCore-depth frames, upright, one size | 144 | 5.1% | 5.1% | wall |
| Task113: ARCore-depth frames, upright, grid, 4.0 m | 144 | 5.2% | 4.8% | wall |
| Task113: same, 2.5 m | 144 | 5.4% | 4.8% | floor, 20° from up |

Turning images upright and fusing only frames with ARCore depth explain most of the change, from 25.0% to 5.1% of points below the floor. Most posed frames carry no depth map (559 of 751), and those are sized from tracked points. The grid fit lowers per-pixel error but leaves the floor figures unchanged. Capping fused depth at 2.5 m drops distant, smeared points, and the floor becomes the dominant plane. Its map then reads 14.7 m² observed, 5.0 × 4.35 m, and 2.85 m from the floor to the highest point. The floor is still a band about 30 cm thick against ARCore's few centimetres, and some walls appear twice. The "one size" rows other than Task107 come from throwaway trial runs of the unchanged `LiveProcessor` (objects off), not from `room_build.py`. Their surfaces are in `outputs/room_allframes_093913/`.

Local outputs: `outputs/capture_task113_093913/{far4.0,far2.5}/{surface.ply,summary.json}` and viewers `outputs/capture_task113_093913/viewer/redmi-room-15oct-{far2.5,far4.0}.html` (42,503 and 53,355 splats). The viewer's photos are still shown as the sensor recorded them, on their side.

## Upright export and frame-by-frame view, Task114

Orientation is now decided per frame, not assumed. `orientation_control.quarter_turns` picks the clockwise quarter turns (0-3) that bring the image's down axis closest to world down in ARCore's gravity-aligned world. `turned_camera` turns the pose, intrinsics and image size to match, and a test checks that the turned camera sees each world point at the pixel where the turned image puts it. On the 15 October walk all 144 fused frames needed one clockwise turn, so the Task113 2.5 m surface is unchanged (555,231 points).

`room_build` also writes `frames.npz`: each fused frame's camera and intrinsics, about 2,000 learned-depth points per frame (every 12th pixel) with photo colours, and every second ARCore depth point. These points use the frame's pose when it was fused, before later anchor corrections, so they show where that frame put them.

`tools.demos.capture_scene` now shows bookmark photos upright and looks from the matching upright camera. With `--frames <frames.npz>` it adds a "Frame by frame" mode: a slider and play button over the fused frames. It shows the points built so far in photo colours, the current frame's learned points in orange and ARCore points in cyan, and the camera outline and path in red, beside the upright photo. "View from camera" looks through each frame's camera.

```text
.venv-yolo\Scripts\python -B -m src.live.room_build --session <v2 session> --out <folder> --far 2.5
.venv-yolo\Scripts\python -B -m tools.demos.capture_scene --surface <folder>\surface.ply --session <v2 session> --frames <folder>\frames.npz --out <viewer.html>
```

The 15 October viewer is `outputs/capture_task114_093913/viewer/redmi-room-15oct-frames.html` (8.33 MB, local only because it embeds household photos). Headless Chromium loaded it with no console errors or network requests; the bookmark and timeline screenshots show upright photos.

### Seeing inside the room (Task 115)

`room_build` now saves the fused volume's photo colours in `surface.ply`, and the viewer shows photo colours by default (a button switches back to height colours). Each splat's normal is turned toward the nearest recorded camera, so its front is the side the phone saw. "Hide surfaces seen from behind" drops splats whose front faces away from the viewer: from outside, the near walls and the ceiling disappear. Ceiling and floor sliders hide everything above or below a height.

The 15 October room at 4.0 m far depth, shown in 3 cm cells: `outputs/capture_task115_093913/viewer/redmi-room-15oct-cutaway.html` (211,242 splats, 12.62 MB, local only). The floor is at about -0.9 m and the ceiling at about 1.6 m in ARCore height, so a ceiling slider value of 1.3 m opens the room from above. From the phone bookmarks, the stairs, TV, rug, table, sofa and window match the photos; anything within about 0.5 m of the camera smears, and walls are still wavy or doubled in places.

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
- **Why the counts are too high (Task93).** Each update now logs every detection (class, confidence, new or matched, distance to the nearest object of its class before matching), and `python -m src.live.count_report <run>/updates.jsonl` splits the new identities. Replays on 14 October:

  | | TUM xyz | TUM desk |
  |---|---:|---:|
  | New identities | 51 | 45 |
  | ... 0.35-0.7 m from an object of the same class | 23 | 21 |
  | ... 0.7-1.5 m away | 7 | 8 |
  | ... over 1.5 m away | 3 | 3 |
  | ... first of their class, or not placed | 18 | 13 |
  | ... detector confidence under 0.5 | 21 | 23 |
  | ... seen in only one update | 15 | 14 |
  | Chairs / TVs, all identities | 14 / 7 | 5 / 9 |
  | Chairs / TVs, seen in 3 or more updates | 9 / 7 | 2 / 7 |

  The main cause is position scatter: almost half the new identities appear just past the 0.35 m matching distance from an object of the same class. That distance was set for cups placed from reference depth at every frame. Chairs and screens placed from the median of learned depth inside their box move further than that between views, and live updates see each object only about twice a second. Low-confidence detections and one-off sightings add more, but dropping them is not enough: counting only identities seen 3 or more times still leaves 9 chairs and 7 TVs on xyz. Next step: a matching distance that grows with the object's size or distance from the camera, then a check against a counted inventory of a real scene (none exists for TUM).
- **No corrections were exercised on real data.** The stand-in has none; the anchor maths is covered by tests only.

## Tests

`src/live/tests` (in the default `pytest` paths): sizing from ARCore depth through both camera models, then points, then the last size; fragments joined by keyframe group and moved with their anchor; the processor on a synthetic session, including a correction that moves the surface and keeps one object as one; the stand-in read back by the host reader; the run loop end to end with fake models.
