# Live SLAM on recorded data

This folder answers one question: **how accurate and how fast is an established live SLAM system on the project's recordings, when it only ever sees frames up to the current one?** The owner ruled on 14 October 2026 that the deployed system must be live (or update at least once per second), so the offline structure-from-motion path in `experiments/sfm` can only be a reference. On the phone, ARCore will track the camera; until ARCore recordings exist, this is the evidence for live tracking accuracy. Task: [84](../../task_list/open/84_live_cpu_slam_on_the_recorded_data_scored_causally.md). Background: [the SLAM review](../../research/camera_tracking_and_slam/sota_slam_review_2026-10-14.md).

## How it works

1. `run_live.py` writes the recording's frame list (time and image path, in order) and a camera file built from the system's own TUM example settings, with this recording's pinhole camera and no distortion.
2. A small native runner (`native/run_stella.cc`, `native/run_orbslam3.cc`) feeds the frames to the SLAM system one at a time, in WSL, as fast as it can process them. For every frame it writes the pose the system returned at that moment (`live.txt`), or "lost", and how long that frame took (`frame_ms.txt`). At the end it saves the system's own refined trajectory (`final_*.txt`).
3. `run_live.py` scores both with the same code as the SfM runs (`experiments/sfm/src/scoring.py`): best fit with size, rigid best fit, 1 s relative error, share of frames tracked. Images only; no depth and no ground truth reach the system.

"Live" scores use only what the system knew at each frame. "Final" scores use its refined trajectory after the whole run, which a live system would not have had at the time.

| System | Licence | Role |
|---|---|---|
| stella_vslam (fork of OpenVSLAM) | BSD-2 | Permissive candidate |
| ORB-SLAM3 | GPLv3 | Accuracy reference only (owner, 14 October 2026) |

## Setup (WSL Ubuntu 24.04)

System libraries, once (needs `sudo`):

```text
sudo apt update && sudo apt install -y libopencv-dev libeigen3-dev libyaml-cpp-dev libsuitesparse-dev libglew-dev libsqlite3-dev libgoogle-glog-dev libboost-all-dev
```

Build the systems into `~/live_slam` (outside the repository; commits are logged to `~/live_slam/BUILD.txt`):

```text
bash experiments/live_slam/native/setup_wsl.sh stella
bash experiments/live_slam/native/setup_wsl.sh orbslam3
```

Build each runner:

```text
mkdir -p ~/live_slam/runners/stella && cd ~/live_slam/runners/stella
cp <repo>/experiments/live_slam/native/run_stella.cc .. && cp <repo>/experiments/live_slam/native/stella/CMakeLists.txt .
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j 16
```

(the same for `orbslam3`). Then, from Windows in `.venv-sfm`:

```text
python -m experiments.live_slam.run_live --system stella --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_xyz_every2 --run-root experiments/live_slam/runs/stella_tum_xyz_every2
python -m pytest experiments/live_slam/tests -p no:cacheprovider --import-mode=importlib
```

Build notes: Pangolin v0.6 (needed by ORB-SLAM3) fails under GCC 13 unless `<cstdint>` and `<limits>` are force-included and its X11 window code is switched off; ORB-SLAM3 needs C++14. `setup_wsl.sh` does both.

## Results, 14 October 2026

Five repeats per setting; median with the range over repeats in brackets. "Path error" is best fit with size (the standard monocular score) on the largest map; "frames tracked" counts frames in that map. Timing is the time the system took per frame on a 32-thread desktop CPU in WSL2. From `python -m experiments.live_slam.report experiments/live_slam/runs`:

| Setting | Repeats | Frames tracked (largest map) | Maps | Live path error | Final path error | ms per frame, median | ms per frame, 95th pct |
|---|---:|---:|---:|---|---|---:|---:|
| stella_vslam, TUM xyz, every 2nd frame | 5 | 97.5% | 1 | 17.1 mm (15.3-56.5) | 15.8 mm (14.9-42.2) | 8.3 | 18.4 |
| stella_vslam, TUM xyz, every frame | 5 | 99.5% | 1 | 18.8 mm (13.6-57.7) | 15.8 mm (13.4-39.4) | 8.4 | 18.1 |
| stella_vslam, TUM desk, every 2nd frame | 5 | 90.6% | 1 | 28.3 mm (24.0-30.3) | 23.9 mm (22.7-25.6) | 8.4 | 16.5 |
| stella_vslam, TUM desk, every frame | 5 | 87.8% | 1 | 25.7 mm (24.7-30.7) | 23.6 mm (22.4-28.6) | 7.2 | 16.7 |
| stella_vslam, ICL, every 2nd frame | 5 | 96.6% | 1 | 38.1 mm (23.7-39.7) | 36.9 mm (19.3-38.1) | 4.7 | 9.9 |
| ORB-SLAM3, TUM xyz, every 2nd frame | 5 | 99.2% | 1 | 12.8 mm (12.5-13.0) | 12.3 mm (12.2-12.6) | 11.5 | 28.2 |
| ORB-SLAM3, TUM xyz, every frame | 5 | 99.7% | 1 | 12.9 mm (12.5-13.1) | 12.2 mm (11.8-12.5) | 12.3 | 25.2 |
| ORB-SLAM3, TUM desk, every 2nd frame | 5 | 73.5% | 2 | 384.7 mm (29.5-527.9) | 47.5 mm (21.3-528.7) | 9.9 | 22.3 |
| ORB-SLAM3, TUM desk, every frame | 5 | 97.1% | 1 | 25.8 mm (24.6-52.5) | 23.0 mm (21.6-39.0) | 10.9 | 20.5 |
| ORB-SLAM3, ICL, every 2nd frame | 5 | 97.7% | 1 | 39.1 mm (27.8-53.1) | 29.2 mm (19.6-45.9) | 7.7 | 18.5 |

For comparison (best fit with size): offline SfM on the same every-2nd-frame clips 11.9 mm (xyz), 21.5-24 mm (desk), 34.1 mm (ICL); the old walkthrough tracker with Kinect depth 34 mm (xyz) and 112 mm (desk); ORB-SLAM3 monocular as published, every frame, 9 mm (xyz) and 17 mm (desk).

What this shows:

- **Live tracking from images alone works on a CPU, fast.** Both systems take 5-12 ms per frame (median), 16-28 ms at the 95th percentile: 35-200 frames per second on this desktop, far above the 1 fps floor.
- **Live accuracy is close to the offline stand-in.** On xyz, ORB-SLAM3 is 12.8 mm live against SfM's 11.9 mm; stella_vslam 17.1 mm. On desk both are about 26-28 mm live against SfM's 21.5-24 mm. On ICL 38-39 mm against 34 mm. Both beat the old walkthrough tracker fed with the Kinect's own depth (34 and 112 mm) by 2-4 times.
- **The live pose is only slightly worse than the system's own refined path** (final): 1-5 mm on TUM. Refinement after the fact adds little here.
- **Robustness is the weak point.** stella_vslam keeps only 88-91% of desk frames (it loses track on the fast turns and relocalises), and on xyz its worst repeat reaches 57 mm. ORB-SLAM3 on desk at every 2nd frame lost track and started a second map in some repeats, so its largest map holds 73.5% of frames with a 385 mm median error; at full frame rate it holds 97% at 26 mm. Halving the frame rate makes fast motion harder.
- **Task84 target** (at least 95% tracked at 30 ms per frame or less, path error within 2 times SfM on xyz and desk): met on xyz by both systems and on full-rate desk by ORB-SLAM3; not met on desk by stella_vslam (88-91% tracked) or by ORB-SLAM3 at every 2nd frame.
- **For the phone:** ARCore adds the phone's motion sensors, which are what usually carry tracking through fast turns; whether it does better than these image-only results on our phone is untested (Task75). stella_vslam is the permissive option if a non-ARCore tracker is ever needed (hosted, or another device).

Timing caveat: the stella_vslam runs overlapped the ORB-SLAM3 compile, and some ORB-SLAM3 runs overlapped a low-priority APK build; the medians are robust to that, the 95th percentiles may be slightly high.

## Status and handover, 14 October 2026

- Done (Task84): both systems built and run live, 5 repeats per setting; results above. Build commits: stella_vslam `e445b54`, g2o `e8df200`, FBoW `c6e3c29`, ORB-SLAM3 `4452a3c`, Pangolin `dd801d2` (v0.6).
- Next: export the 3D points each system tracks in each frame (stella_vslam's frame publisher has `get_keypoints_and_landmarks()`), then rerun the Task72/78 surface pipeline on the live poses and points, so the whole chain is causal.
