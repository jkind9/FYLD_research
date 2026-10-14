---
id: "89"
title: Live host processing of the phone session stream at 1 update per second or faster on CPU
status: done
files:
  - src/live/__init__.py
  - src/live/README.md
  - src/live/stream.py
  - src/live/stand_in.py
  - src/live/sizing.py
  - src/live/fragments.py
  - src/live/processor.py
  - src/live/run.py
  - src/live/tests/test_sizing.py
  - src/live/tests/test_fragments.py
  - src/live/tests/test_processor.py
  - src/live/tests/test_stand_in.py
  - experiments/01_camera_capture_delivery/host/receiver.py
  - experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py
  - pytest.ini
  - README.md
  - learning/05_dense_surfaces.md
  - learning/11_inside_arcore.md
  - src/live/score.py
  - research/camera_tracking_and_slam/fragments_and_anchors.md
  - research/camera_tracking_and_slam/README.md
  - research/phone_ar_platforms/arcore_raw_depth.md
created: 2026-10-14
---
# Live host processing of the phone session stream at 1 update per second or faster on CPU

## Goal

One entry point (src/live/run.py) reads a phone session v1 stream, live from the receiver or replayed from a saved session at its recorded speed, and updates the surface, the top-down map and the object counts at least once per second on the CPU, moving fused content when ARCore corrects its poses; absorbs Tasks 76 and 77 (camera path before depth, depth sized to the tracker's points)

## Plan

1. Tests first (src/live/tests): sizing picks ARCore depth pixels with confidence >= 128 (at least 50) and maps them into the image through both intrinsics, falls back to tracked points (at least 20), then to the last size; fragments: a frame is fused in the fragment of its keyframe group (10 keyframes), and moving that group's anchor moves its surface points by the same transform without refusing; processor: on a synthetic session with a fake depth model and fake detector, updates come from the newest frame with new depth, counts and map appear, a correction moves object positions; stand-in: a TUM clip becomes a valid v1 session (session_v1.read_session reads it back) with labelled control. See them fail. 2. stand_in.py: recording (tum:/icl:) to a v1 session folder: ground-truth pose turned into ARCore axes, sensor depth subsampled to 160x120 as raw depth every 3rd frame (10 per second), 20 tracked points per frame from sensor depth, one anchor per second, no corrections; session.json says control=reference so no result is mistaken for ARCore. 3. sizing.py, fragments.py (Open3D ScalableTSDFVolume per fragment in its anchor's frame, voxel 2 cm (TUM) / 1 cm (ICL), truncation 4 voxels, depth 0.1-4 m; surface = each fragment's points moved by its anchor's latest pose, voxel-thinned), processor.py (Depth Anything V2 Metric Small, CPU, sized; mapping by experiment 05 plane + footprint with Task55 settings; YOLO26x detection on the saved JPEG, placed by experiment 06 localisation, counted by associate_frame with 0.35 m / 0.05 m; object positions kept relative to their keyframe anchor). 4. run.py: --replay <session> (frames fed at recorded speed by a thread) or --listen <port> (receiver with an on_frame callback; receiver.py gains that callback), --out; writes updates.jsonl (per update: frame used, latency, stage times, surface points, measurements, counts), surface.ply, summary.json with update rate. Torch threads set explicitly (16). 5. Background queue (START/END log): stand-in sessions for TUM xyz and desk and ICL; replay each through run.py; score ICL surface against the ICL reference with experiment 04's scorer and compare with Task72's 93 mm. 6. README for src/live, root README Stream A step 2, learning chapter 5/11 note on anchors and fragments; close Tasks 76/77 as absorbed; finish; commit only this task's files; push.

## Files

- README.md (+1 -1, 399 lines)
- experiments/01_camera_capture_delivery/host/receiver.py (+5 -1, 94 lines)
- experiments/01_camera_capture_delivery/tests/test_phonecheck_host.py (+7 -0, 124 lines)
- learning/05_dense_surfaces.md (+10 -0, 102 lines)
- learning/11_inside_arcore.md (+1 -1, 118 lines)
- pytest.ini (+1 -1, 5 lines)
- research/camera_tracking_and_slam/README.md (+2 -0, 42 lines)
- research/camera_tracking_and_slam/fragments_and_anchors.md (+27 -0, 27 lines)
- research/phone_ar_platforms/arcore_raw_depth.md (+9 -0, 46 lines)
- src/live/README.md (+57 -0, 57 lines)
- src/live/fragments.py (+66 -0, 66 lines)
- src/live/processor.py (+171 -0, 171 lines)
- src/live/run.py (+145 -0, 145 lines)
- src/live/score.py (+38 -0, 38 lines)
- src/live/sizing.py (+65 -0, 65 lines)
- src/live/stand_in.py (+118 -0, 118 lines)
- src/live/stream.py (+36 -0, 36 lines)
- src/live/tests/test_fragments.py (+38 -0, 38 lines)
- src/live/tests/test_processor.py (+81 -0, 81 lines)
- src/live/tests/test_sizing.py (+50 -0, 50 lines)
- src/live/tests/test_stand_in.py (+41 -0, 41 lines)

## Checked

- `python -m src.live.run --replay (stand-in sessions, recorded speed) -> TUM xyz 1.90, TUM desk 1.61, ICL 2 cm 1.22 updates/s, no gap over 1 s; ICL 1 cm 0.89 (misses); ICL surface 52 mm mean at 2 cm, 22% covered`
- cost: 32 min from begin to finish; Claude tokens 79,624,729 (fresh input 360,539, cache read 79,067,484, output 196,706; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.14 (was 0)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 2 in 2051 words: bold-labels "4 items", bold-labels "5 items"

## Left over

Live object counts far too high (15 chairs on TUM xyz): needs its own task. ICL margin thin (0.98 s longest gap): keep finished fragments' thinned points. Corrections not yet seen on real ARCore data: first --listen run needs the v1 APK installed on the Redmi (owner). Tasks 76/77 moved to stale as absorbed
