# SLAM file exchange

This folder converts between the files the native SLAM runners read and write, and the per-frame rows that [`research/experiments/sfm/src/scoring.py`](../../sfm/src/README.md) scores. It belongs to [live SLAM on recorded data](../README.md).

| File | What it does |
|---|---|
| `trajectory.py` | `frame_list(times, images)` writes the runner's input, one `time path` line per frame in order, with Windows paths converted by `to_wsl`. `read_poses(path)` parses a runner's `live.txt` into `(time, segment, camera-to-world matrix)`, with `None` for a lost frame. `read_trajectory(path, time_scale=...)` parses a system's own final trajectory (`time x y z qx qy qz qw`) into the same form. `rows(frame_ids, times, poses, tolerance_s=0.001)` matches poses to input frames by time and returns scoring rows, leaving unmatched frames unplaced. |

A segment is one map. A SLAM system that loses tracking and restarts begins a new segment with its own origin, and the scorer aligns each segment separately.

## How to run it

Nothing here is a script. [`../run_live.py`](../README.md) imports it. Test it from the repository root:

```text
.venv/Scripts/python.exe -m pytest research/experiments/live_slam/tests -p no:cacheprovider --import-mode=importlib
```

## Where results are recorded

Accuracy and speed results are in the [live SLAM README](../README.md). The runner programs that write these files are in [`../native/`](../native/README.md).
