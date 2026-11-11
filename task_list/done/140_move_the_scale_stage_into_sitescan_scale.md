---
id: "140"
title: Move the scale stage into sitescan/scale
status: done
files:
  - sitescan/scale/__init__.py
  - sitescan/scale/fit.py
  - sitescan/scale/targets.py
  - sitescan/scale/README.md
  - src/live/sizing.py
  - src/live/room_build.py
  - experiments/sfm/src/dense.py
  - tests/test_sitescan_scale.py
  - sitescan/README.md
  - DESIGN.md
created: 2026-11-09
---
# Move the scale stage into sitescan/scale

## Goal

Share single-frame and grid scale fits on arrays without changing fallback or freshness behavior

## Plan

1. Add failing scale and target behavior tests. 2. Move adopted median fits, grid fits and target projection with forwarding adapters. 3. Write the stage reference. 4. Check scale callers, golden outputs and Chromium page.

## Files

- DESIGN.md (+3 -3, 694 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+3 -3, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+3 -46, 4 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+9 -157, 10 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+4 -183, 5 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+2 -200, 3 lines)
- experiments/sfm/src/dense.py (+5 -2, 121 lines)
- experiments/shared/geometry.py (+5 -4, 117 lines)
- pytest.ini (+1 -1, 7 lines)
- sitescan/README.md (+28 -0, 28 lines)
- sitescan/depth/README.md (+71 -0, 71 lines)
- sitescan/depth/__init__.py (+5 -1, 5 lines)
- sitescan/depth/model.py (+72 -0, 72 lines)
- sitescan/depth/orientation.py (+36 -0, 36 lines)
- sitescan/scale/README.md (+77 -0, 77 lines)
- sitescan/scale/__init__.py (+15 -1, 15 lines)
- sitescan/scale/fit.py (+92 -0, 92 lines)
- sitescan/scale/targets.py (+41 -0, 41 lines)
- sitescan/session/FORMAT.md (+201 -0, 201 lines)
- sitescan/session/README.md (+70 -0, 70 lines)
- sitescan/session/__init__.py (+5 -0, 6 lines)
- sitescan/session/protocol.py (+45 -0, 45 lines)
- sitescan/session/read.py (+89 -0, 89 lines)
- sitescan/session/replay.py (+39 -0, 39 lines)
- sitescan/session/wire_v1.py (+195 -0, 195 lines)
- sitescan/session/wire_v2.py (+256 -0, 256 lines)
- sitescan/types.py (+48 -0, 48 lines)
- src/live/orientation_control.py (+7 -27, 116 lines)
- src/live/room_build.py (+16 -48, 211 lines)
- src/live/run.py (+3 -16, 133 lines)
- src/live/sizing.py (+14 -36, 43 lines)
- src/live/stream.py (+10 -44, 14 lines)
- src/walkthrough/steps/depth.py (+15 -49, 289 lines)
- tests/test_sitescan_depth.py (+115 -0, 115 lines)
- tests/test_sitescan_scale.py (+83 -0, 83 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)

## Checked

- `New scale tests -> 13 failed on missing functions before move; locked pytest on scale, sizing, room and SfM dense callers -> 37 passed; locked pytest -m golden tests/golden -> 3 passed; full 15 October room -> 676855 raw, 554067 cleaned, map 6.35 x 3.30 m, full summary exact except path and timings; regenerated capture_scene plus headless Chromium -> room.html ok; ruff and Python review -> clean, randomized old/new grids exact and point depths within 1e-14; README example -> True and (480, 640)`
- cost: 6 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.17 (was 0.2); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 0 in 2649 words

## Left over

Next: fusion, cleanup, mapping, objects, then orchestrators. Default suite last passed 1013 tests after depth; rerun after the remaining stage moves. Live fallback and freshness policy have not changed. Locked dev extra still lacks psutil; full default suite uses system Python. Owner chose evaluation/layers and experimental sitescan/objects.
