# Native SLAM runners and their build

This folder builds two established live SLAM systems (systems that track the camera while frames arrive) and holds the small C++ programs that feed them recorded frames. It belongs to [live SLAM on recorded data](../README.md).

Each runner reads a frame list, passes frames to the SLAM system one at a time as fast as the system can take them, and logs the pose returned for each frame at that moment. Nothing from later frames reaches the system, so the log shows what a live system would have known.

| File | What it does |
|---|---|
| `setup_wsl.sh` | Clones, patches and builds the SLAM systems in WSL Ubuntu 24.04 under `~/live_slam` (outside the repository), and logs each built commit to `~/live_slam/BUILD.txt`. Takes `stella`, `orbslam3` or `all`. |
| `run_stella.cc` | Runner for stella_vslam (BSD-2). Usage: `run_stella <vocabulary.fbow> <config.yaml> <frames.txt> <output folder>`. |
| `run_orbslam3.cc` | Runner for ORB-SLAM3 (GPLv3, used as a reference only). Usage: `run_orbslam3 <vocabulary> <settings.yaml> <frames.txt> <output folder>`. |
| `stella/CMakeLists.txt` | Builds `run_stella` against the stella_vslam install in `~/live_slam/install`. |
| `orbslam3/CMakeLists.txt` | Builds `run_orbslam3` against the ORB-SLAM3 source tree in `~/live_slam/src/ORB_SLAM3`. |

Both runners write the same files into the output folder:

- `live.txt`: one line per frame, `time segment x y z qx qy qz qw` (camera to world, in the system's own units), or `time lost`. A segment is one map.
- `frame_ms.txt`: milliseconds the system took for each frame.
- `final_tum.txt` (stella) or `final_euroc.txt` (ORB-SLAM3): the system's refined trajectory after the whole run, which a live system would not have had at the time.

[`../src/trajectory.py`](../src/README.md) reads these files.

## How to run it

This needs WSL (Ubuntu 24.04) and, once, `sudo apt install` of the system libraries listed in the [live SLAM README](../README.md). No GPU is used. From the repository root, inside WSL:

```text
bash experiments/live_slam/native/setup_wsl.sh stella
bash experiments/live_slam/native/setup_wsl.sh orbslam3
```

Then build each runner as the live SLAM README describes: copy the `.cc` file and the `CMakeLists.txt` into `~/live_slam/runners/<system>/` and run CMake there. The runners are normally started from Windows by `../run_live.py`, which converts paths with `to_wsl` and writes the frame list.

## Where results are recorded

Accuracy and speed results are in the [live SLAM README](../README.md).
