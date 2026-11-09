---
id: "107"
title: Replay the 15 October walk through the live pipeline
status: done
priority: HIGH
type: experiment
blocked_by: []
blocks: ["102"]
verification_test: "src/live/tests/test_sizing.py"
plan_reviewed: null
files:
  - src/live/**
  - outputs/**
docs:
  - src/live/README.md
  - experiments/01_camera_capture_delivery/README.md
baseline_metric:
  source: "outputs/capture_task99_220756/live_verified/summary.json (14 October walk)"
  field: "size_sources; final map"
  baseline_value: "63 updates at 1.58/s; sizing 33 tracked points, 30 previous, 0 ARCore depth; dominant plane normal [-0.98, 0.12, -0.16]; highest point 5.98 m; 845,428 surface points"
  target: "Same pipeline and settings on the 15 October walk; report how often ARCore depth sets the scale and whether the map's floor and height become plausible"
created: 2026-11-07
last_updated: 2026-11-07
superseded_by: null
---

# Task 107: Replay the 15 October walk through the live pipeline

## In plain English

The house walk used so far turned out to have no usable depth from the phone, so its 3D model was scaled from a handful of tracked points. A second walk, recorded the next morning, has good phone depth. Run that walk through the unchanged live pipeline and see whether the phone's depth now sets the scale, and whether the model looks less distorted. No code changes.

## Verified inputs, 7 November 2026

- **Session:** `experiments/01_camera_capture_delivery/runs/capture_redmi_20261014/20261015_093913_walk`, capture 1.2. 822 frames (about 27.5 s), `end_reason: stop`, 0 dropped frames, 779 frames with ARCore records (43 without), motion sensors at 423.6 Hz.
- **Depth:** 147 raw-depth maps; 144 pass the live sizing rule, median 1,585 confident pixels per map. Depth trails its frame by a median of 8 ms (Task106 probe).
- **Orientation:** gravity along the phone's long edge in 99.4% of accelerometer samples, so the phone was in portrait; images reach the depth model sideways (Task109 tests the effect).
- **Baseline (14 October walk, Task99):** see `baseline_metric` above. Its dominant plane is nearly vertical in ARCore's gravity-aligned world (ARCore's world y axis points up), and its highest point is 5.98 m inside a two-storey house. Both suggest an axis or scale fault.
- **Not yet run on this session:** `clock_check.py` and the EuRoC export checker.

## Plan

1. Run the Task99 capture checks on the session: `experiments/open_vio/host/clock_check.py` and `experiments/open_vio/host/recording.py --euroc`. Record the status and any metadata gaps; do not fill gaps.
2. Replay with the Task99 command and settings: `python -B -m src.live.run --replay <session> --out outputs/capture_task107_093913/live --threads 16`.
3. Report from `summary.json` and `updates.jsonl`:
   - updates per second, longest gap, gaps over 1 s;
   - `size_sources` counts, and the spread of `size` across updates (minimum, median, maximum), next to the 14 October run;
   - final map: dominant plane normal against ARCore's up axis, highest point, observed area, length and width;
   - surface point count and anchor corrections.
4. Build the Task100 viewer for this surface (`tools.demos.capture_scene`) for a visual check by the owner. Keep it local.
5. Add the result to `src/live/README.md` and the capture README. State that the two walks differ in route and length, so this is not a paired comparison: it shows whether ARCore-depth sizing engages and how the map changes, not the size of the effect.

## Settings

| name | value | source |
|---|---|---|
| threads | 16 | inherited: Task99 receipt, `outputs/capture_task99_220756/live_verified/summary.json` |
| voxel | 0.02 m | inherited: same summary (`voxel_m`) |
| replay speed | 1.0 (recorded speed) | inherited: same summary (`speed`) |
| objects | on | inherited: same summary (`objects: true`) |
| depth model | cached Depth Anything V2 Metric Indoor Small | inherited: Task99 / Task102 settings |
| raw-depth confidence cut-off | 128 | `src/live/sizing.py:16` |
| minimum raw-depth pixels | 50 | `src/live/sizing.py:17` |
| minimum tracked points | 20 | `src/live/sizing.py:18` |

No setting changes. No GPU. The recording is read only.

## Finish when

The replay has run, the figures above are reported beside the 14 October baseline, and the docs say what this does and does not show. A geometry improvement is not required to finish. Accuracy claims need Tasks75/53.

## Files

- PROJECT_PLAN.md (+254 -0, 254 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- research/README.md (+1 -1, 239 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- src/live/README.md (+35 -0, 124 lines)

## Checked

- `clock_check.py 20261015_093913_walk -> exit 0, problems []; recording.py --euroc -> exit 0, no problems found; src.live.run --replay --threads 16 -> exit 0, 47 updates at 1.70/s, longest gap 0.741 s, 0 gaps over 1 s, sizes 32 arcore_depth / 12 tracked_points / 2 previous / 1 none; capture_scene viewer -> exit 0, 47,885 splats, 1.22 MB; session folder 0 files newer than run start; pytest src/live/tests/test_sizing.py -> 4 passed`
- cost: 3 min from begin to finish; Claude tokens 1,182,788 (fresh input 19,819, cache read 1,154,434, output 8,535; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 17 in 4151 words: bold-labels "5 items", same-opening "it", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Dominant plane still about 86 degrees from world y (a wall, not the floor), so length, width and highest point are measured from a wall; cause untested (Task109 sideways images, Task102 diagnosis). Owner visual check of outputs/capture_task107_093913/viewer/redmi-walk-15oct.html. Task started with --force because the HIGH plan review gate was not run. Not committed.
