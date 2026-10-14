---
id: "84"
title: Live CPU SLAM on the recorded data, scored causally
status: done
priority: HIGH
type: experiment
approval_status: owner 2026-10-14 - deployment must be live (or update at >= 1 fps); GPU not allowed; GPLv3 ORB-SLAM3 allowed as an accuracy reference; system libraries installed in WSL by the owner. Settings marked proposed by Claude are not owner-ruled.
blocked_by: []
blocks: ["76"]
verification_test: "experiments/live_slam/tests/test_trajectory.py"
plan_reviewed: null
files:
  - experiments/live_slam/**
docs:
  - experiments/live_slam/README.md
  - experiments/README.md
  - learning/03_camera_tracking_and_slam.md
baseline_metric:
  source: "Task67 offline SfM (COLMAP) on the same clips; walkthrough tracker (Task70 rescoring); published monocular SLAM (MASt3R-SLAM paper Table 1)"
  field: "camera path best fit with size (mm), frames tracked, relative error over 1 s, milliseconds per frame on the CPU"
  baseline_value: "SfM xyz 11.9 mm, desk 21.5-24 mm, ICL 34.1 mm; walkthrough tracker with Kinect depth xyz 34 mm, desk 112 mm; published ORB-SLAM3 monocular xyz 9 mm, desk 17 mm (every frame)"
  target: "proposed by Claude 2026-10-14, not owner-ruled: a live CPU system tracks at least 95% of frames at 30 ms per frame or less, with best-fit-with-size error within 2 times the SfM stand-in on TUM xyz and desk"
created: 2026-10-14
last_updated: 2026-10-14
superseded_by: null
---

# Task 84 — Live CPU SLAM on the recorded data, scored causally

## In plain English

The camera path used so far in the experiments came from software that looks at the whole video after it has been recorded. The owner has ruled that the real system must work live. This task runs two established live tracking programs on the same recordings, one frame at a time, as if the video were arriving from a camera. It records the camera position each program reports at the moment each frame arrives, scores those positions against the true camera path, and measures how long each frame takes on an ordinary computer processor.

## What

1. **Build** in WSL Ubuntu 24.04, outside the repository, from pinned commits: stella_vslam (BSD-2) with g2o and FBoW, and ORB-SLAM3 (GPLv3, reference only) with Pangolin. No viewer.
2. **One small runner per system** (`experiments/live_slam/native/`): reads a frame list (time, image path) and a camera file, feeds frames in order, and writes for every frame the pose the system returned at that moment (camera-to-world, TUM format) or "lost", the time that frame took, and at the end the system's final, refined trajectory. Monocular only: the images, no depth, no ground truth.
3. **Recordings**, the same as the SfM stand-in: TUM fr1/xyz and fr1/desk every-2nd-frame clips, ICL living room 2 every 2nd frame. Also full-rate TUM xyz and desk (every frame), to compare with published numbers.
4. **Scores** (Python, `experiments/live_slam/score.py`, reusing `experiments/sfm/src/scoring.py`): best fit with size, best fit rigid, 1 s relative error, frames tracked, segments (resets); for the live poses and the final trajectory separately; milliseconds per frame (median, 95th percentile). Five repeats per setting, because multi-threaded SLAM is not deterministic; report the median and range.
5. **README** in `experiments/live_slam/` with the build commands, results beside SfM and the walkthrough tracker, and what it means for the phone.

Out of scope here (next task if this works): exporting each frame's tracked 3D points for the Task72/78 surface pipeline.

## Why

The owner ruled on 14 October 2026 that offline methods cannot be deployed. The SfM stand-in proved the design, but it used future frames. This measures what a live tracker achieves on the same data, and how fast, on a CPU. On the phone ARCore will do this job; until ARCore recordings exist, this is the best available evidence of live accuracy.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Recording readers (frames, times, camera, ground truth, ICL axis flip) | `experiments/sfm/src/sequences.py` | SfM runs | experiments/sfm/src/sequences.py:99-133 |
| Camera-path scores from per-frame rows (best fit with size, rigid, 1 s) | `scoring.score`, `scoring.records` | `run_sfm.py` | experiments/sfm/src/scoring.py:21-56 |
| Sealed run folders with settings, timing and manifest | `experiments.shared.runs.Run` | every experiment | experiments/sfm/run_dense.py:276 |
| SLAM survey and candidate choice | SOTA review | this task | research/camera_tracking_and_slam/sota_slam_review_2026-10-14.md |
| Nothing comparable exists for live SLAM in the repo | searched experiments/ and src/ for "orb_slam", "stella", "SLAM runner" | — | none found |

### Plan

1. Tests first for `src/trajectory.py`: reading a TUM-format pose file into the per-frame rows `scoring` expects (lost frames, missing frames, timestamps matched within 1 ms), and writing the frame list.
2. `native/setup_wsl.sh`: clone and build the dependencies and both systems at pinned commits into `~/live_slam` in WSL, logging the commits.
3. `native/run_stella.cc`, `native/run_orbslam3.cc` with one CMake file each.
4. `run_live.py`: writes the frame list and camera file, runs the native runner through `wsl`, copies its outputs into a sealed run folder, scores.
5. One background queue for all runs, START/END log; README tables.

## Hyperparameters

| name | value | source |
|---|---|---|
| systems | stella_vslam (BSD-2), ORB-SLAM3 (GPLv3, reference) | SOTA review 2026-10-14; owner allowed GPLv3 as reference 2026-10-14 |
| mode | monocular, images only | owner live ruling; matches the SfM stand-in |
| camera | TUM default pinhole 525, 525, 319.5, 239.5, no distortion; ICL 481.2, 480, 319.5, 239.5 | inherited experiments/sfm/src/sequences.py |
| frames | every-2nd clips (as Task67); full-rate TUM for the published comparison | inherited Task67; full rate proposed by Claude 2026-10-14 |
| features | each system's default monocular TUM settings (ORB, 1000-2000 features, 8 levels, scale 1.2) | system defaults |
| vocabulary | each system's published ORB vocabulary | system defaults |
| repeats | 5 per setting, median and range | proposed by Claude 2026-10-14, not owner-ruled |
| pose reported | live: the pose returned for that frame; final: the system's saved trajectory after the run | proposed by Claude 2026-10-14, not owner-ruled |
| frame pacing | as fast as the system processes (no waiting for real time); per-frame time recorded | proposed by Claude 2026-10-14, not owner-ruled |
| devices | CPU only, WSL2, 32 threads | owner 2026-10-14 (no GPU) |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Built systems | `native/setup_wsl.sh` | runners | `~/live_slam` in WSL, commits logged to `~/live_slam/BUILD.txt` | yes; rebuilding is the script |
| Frame list and camera file | `run_live.py` | native runner | text: `time path` per line; YAML camera | written into the run folder `input/` |
| Live and final poses, timings | native runner | `score.py` | TUM format camera-to-world in the system's own units; `frame_ms.txt` | copied into the sealed run folder |
| Scores | `score.py` | README | JSON as Task67's `scores.json` | sealed |

- **Source of truth:** the recordings and the ground-truth files; ground truth enters only scoring.
- **Process boundary:** Windows Python calls `wsl -d Ubuntu -- <runner> <args>`; paths are translated to `/mnt/c/...`; text files cross it.
- **Failure after each step:** a crashed runner leaves an incomplete run folder that the report skips; the queue log records the exit code.
- **Backward compatibility:** no existing file changes.

## Verification

- `experiments/live_slam/tests/test_trajectory.py`: a pose file with 3 tracked frames, 1 "lost" line and 1 frame missing gives rows with `model_id` 0, None, None in the right order; timestamps 1 ms apart match, 30 ms apart do not; a camera-to-world pose survives the round trip; the frame list has one line per frame with WSL paths.
- Red first: run the tests before the module exists.
- Before/after: the baseline numbers above against the measured rows in the README.
- Plan review: no independent reviewer (the owner has not asked for agents); started with `task.js start 84 --force`.

## Receipts

| field | value |
|---|---|
| closing commit | pushed with the follow-up commit (owner asked to keep the repo current) |
| files changed | experiments/live_slam/ (new: README, run_live.py, report.py, src/trajectory.py, native runners and setup_wsl.sh, tests); experiments/README.md; learning/03, learning/10 |
| test | experiments/live_slam/tests 6 passed; ruff clean; 50 runs completed (2 x 5 settings x 5 repeats) |
| before / after | Offline SfM stand-in xyz 11.9, desk 21.5-24, ICL 34.1 mm. Live (median of 5): ORB-SLAM3 xyz 12.8, desk 25.8 (full rate), ICL 39.1 mm; stella_vslam xyz 17.1, desk 28.3, ICL 38.1 mm; 4.7-12.3 ms per frame median |
| result | Target met on xyz by both and on full-rate desk by ORB-SLAM3; not met on desk by stella_vslam (88-91% tracked) or ORB-SLAM3 at half frame rate (second map in some repeats) |

Notes / caveats / follow-ups:

- Full-rate TUM desk sits one folder deeper (data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk); the first three stella runs used the wrong path and were rerun.
- Timing overlaps: stella runs overlapped the ORB-SLAM3 compile; some ORB-SLAM3 runs overlapped a low-priority APK build (Task85).
- Task lock was handed to Task85 while runs continued (journaled), then taken back with --take --force.
- Next: per-frame tracked points export and the causal surface pipeline.

## Files

- experiments/01_camera_capture_delivery/README.md (+27 -0, 269 lines)
- experiments/01_camera_capture_delivery/build/build-phonecheck.sh (+21 -0, 21 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+46 -0, 46 lines)
- experiments/01_camera_capture_delivery/host/receiver.py (+74 -0, 74 lines)
- experiments/01_camera_capture_delivery/host/report.py (+49 -0, 49 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/build.gradle (+25 -0, 25 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/AndroidManifest.xml (+22 -0, 22 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CheckActivity.java (+377 -0, 377 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/HostStream.java (+145 -0, 145 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/Report.java (+54 -0, 54 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/TrackingStats.java (+135 -0, 135 lines)
- experiments/01_camera_capture_delivery/phonecheck/build.gradle (+3 -0, 3 lines)
- experiments/01_camera_capture_delivery/phonecheck/gradle.properties (+2 -0, 2 lines)
- experiments/01_camera_capture_delivery/phonecheck/settings.gradle (+8 -0, 8 lines)
- experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py (+74 -0, 74 lines)
- experiments/README.md (+1 -0, 258 lines)
- experiments/live_slam/README.md (+83 -0, 83 lines)
- experiments/live_slam/native/orbslam3/CMakeLists.txt (+16 -0, 16 lines)
- experiments/live_slam/native/run_orbslam3.cc (+69 -0, 69 lines)
- experiments/live_slam/native/run_stella.cc (+75 -0, 75 lines)
- experiments/live_slam/native/setup_wsl.sh (+72 -0, 72 lines)
- experiments/live_slam/native/stella/CMakeLists.txt (+12 -0, 12 lines)
- experiments/live_slam/report.py (+58 -0, 58 lines)
- experiments/live_slam/run_live.py (+111 -0, 111 lines)
- experiments/live_slam/src/trajectory.py (+66 -0, 66 lines)
- experiments/live_slam/tests/test_trajectory.py (+73 -0, 73 lines)
- learning/03_camera_tracking_and_slam.md (+2 -0, 95 lines)
- learning/10_findings_timeline.md (+2 -0, 50 lines)

## Checked

- `.venv-sfm pytest experiments/live_slam/tests -> 6 passed; ruff clean; report.py over 50 runs -> table in experiments/live_slam/README.md`
- cost: 14 min from begin to finish; Claude tokens 20,135,545 (fresh input 76,560, cache read 20,003,181, output 55,804; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.1 (was n/a (no functions))
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 3 in 2008 words: bold-labels "5 items", bold-labels "4 items", bold-labels "6 items"

## Left over

Per-frame tracked points export and causal surface pipeline (next task); timing rerun on an idle machine optional
