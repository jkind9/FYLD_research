# Camera tracking and its independent scorer

This folder tracks the camera frame to frame from supplied colour and depth images, then scores the path against a separate reference. It belongs to [experiment 03, camera pose estimation](../README.md).

The tracker is Open3D's hybrid odometry on the CPU. Each new frame is matched to the previous one, and the matches are chained into one path. A failed match starts a new path segment with its own origin, so a failure is recorded instead of hidden.

| File | What it does |
|---|---|
| `run.py` | Entry point. `execute(root, run_root, count, ...)` reads frames, tracks, scores and publishes a run folder with receipts. `validate_outputs` checks a finished run. |
| `supervisor.py` | `supervise(...)` runs one worker process under a hard memory limit and a wall-clock limit, and keeps the run's receipts if the worker is killed. `RunRootLock` stops two runs sharing a folder. |
| `memory_limits.py` | `WindowsProcessMemoryLimit` is a Windows Job Object (an operating-system limit on a process) with a per-process memory cap. `direct_interpreter()` starts Python without the venv launcher so the cap applies to the real process. |
| `dataset.py` | Reads the TUM RGB-D layout with no poses. `associations(root, count)` pairs colour and depth images by time (within 0.02 s, one to one). `load_frame` returns an `RGBDFrame` with depth in metres. |
| `backend.py` | `CPUOdometry` is the Open3D adapter. `cpu_build()` refuses to start if the installed Open3D has CUDA or SYCL, so no GPU is used by accident. |
| `tracking.py` | `track(frames, backend)` returns one `Record` per frame: status, pose or none, and a reason. |
| `evaluation.py` | `read_references(path)` loads motion-capture poses. `evaluate(records, references)` aligns each segment at its first matched pose with scale one (`position_rmse_m`). It also reports a best-fit rigid error (`ate_rigid_rmse_m`), a best-fit error with one size per segment (`ate_scaled_rmse_m`) and a one-second relative error (`rpe_1s_*`). References are read only after tracking. |
| `reporting.py` | `thumbnail` and `report` write the colour and depth previews and an HTML page. They do not change the estimated path. |
| `validation/__init__.py` | Public entry to the scorer: re-exports `evaluate` and `read_references`. |

Other experiments reuse the scorer. `research/experiments/open_vio/vio/score.py` and `research/experiments/sfm/src/scoring.py` call `evaluate`, and `research/evaluation/stage_report/stages/camera.py` re-scores saved runs with it.

## How to run it

Run from the repository root on Windows, CPU only. The memory limit needs Windows Job Objects, and the Open3D CPU wheel (version 0.19.0) must be installed:

```text
.venv/Scripts/python.exe -B -m research.experiments.03_camera_pose_estimation.src.run --dataset data/tum/rgbd_dataset_freiburg1_xyz --frames 30
```

`--dataset` is a TUM sequence folder, `--frames` is how many associated frames to use (default 30), and `--runs` changes where run folders are written (default `../runs`). Tests:

```text
.venv/Scripts/python.exe -B tools/check.py -q research/experiments/03_camera_pose_estimation/tests
```

## Where results are recorded

Error figures, timings and memory use are in the [experiment 03 README](../README.md). Run folders are in [`../runs/`](../runs).
