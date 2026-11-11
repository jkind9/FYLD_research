---
id: "142"
title: Move the cleanup stage into sitescan/cleanup
status: done
files:
  - sitescan/cleanup/__init__.py
  - sitescan/cleanup/vote.py
  - sitescan/cleanup/pieces.py
  - sitescan/cleanup/README.md
  - experiments/surface_cleanup/__init__.py
  - experiments/surface_cleanup/masks.py
  - experiments/surface_cleanup/filters.py
  - experiments/surface_cleanup/support.py
  - experiments/surface_cleanup/README.md
  - src/live/clean.py
  - tests/test_sitescan_cleanup.py
  - sitescan/README.md
  - DESIGN.md
created: 2026-11-09
---
# Move the cleanup stage into sitescan/cleanup

## Goal

Keep adopted visibility voting and largest pieces in the product and preserve rejected filters in experiments

## Plan

1. Add failing cleanup behavior tests. 2. Move adopted vote and component functions, move trial filters to experiments, forward old imports. 3. Write references. 4. Check cleanup and viewer callers, golden outputs, full room and Chromium.

## Files

- DESIGN.md (+3 -3, 694 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+3 -3, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+3 -46, 4 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+9 -157, 10 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+4 -183, 5 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+2 -200, 3 lines)
- experiments/sfm/src/dense.py (+5 -2, 121 lines)
- experiments/shared/geometry.py (+5 -4, 117 lines)
- experiments/surface_cleanup/README.md (+25 -0, 25 lines)
- experiments/surface_cleanup/__init__.py (+1 -0, 1 lines)
- experiments/surface_cleanup/filters.py (+55 -0, 55 lines)
- experiments/surface_cleanup/masks.py (+48 -0, 48 lines)
- experiments/surface_cleanup/support.py (+55 -0, 55 lines)
- pytest.ini (+1 -1, 7 lines)
- sitescan/README.md (+30 -0, 30 lines)
- sitescan/cleanup/README.md (+72 -0, 72 lines)
- sitescan/cleanup/__init__.py (+23 -1, 23 lines)
- sitescan/cleanup/pieces.py (+24 -0, 24 lines)
- sitescan/cleanup/vote.py (+55 -0, 55 lines)
- sitescan/depth/README.md (+71 -0, 71 lines)
- sitescan/depth/__init__.py (+5 -1, 5 lines)
- sitescan/depth/model.py (+72 -0, 72 lines)
- sitescan/depth/orientation.py (+36 -0, 36 lines)
- sitescan/fusion/README.md (+69 -0, 69 lines)
- sitescan/fusion/__init__.py (+5 -1, 5 lines)
- sitescan/fusion/fragments.py (+103 -0, 103 lines)
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
- src/live/clean.py (+13 -204, 14 lines)
- src/live/fragments.py (+6 -82, 7 lines)
- src/live/orientation_control.py (+7 -27, 116 lines)
- src/live/room_build.py (+16 -48, 211 lines)
- src/live/run.py (+3 -16, 133 lines)
- src/live/sizing.py (+14 -36, 43 lines)
- src/live/stream.py (+10 -44, 14 lines)
- src/walkthrough/steps/depth.py (+15 -49, 289 lines)
- tests/test_sitescan_cleanup.py (+70 -0, 70 lines)
- tests/test_sitescan_depth.py (+115 -0, 115 lines)
- tests/test_sitescan_fusion.py (+56 -0, 56 lines)
- tests/test_sitescan_scale.py (+83 -0, 83 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)

## Checked

- `New cleanup tests -> failed on missing functions before move; locked pytest cleanup, trial, attributes, scene and tuner callers -> 31 passed; locked pytest -m golden tests/golden -> 3 passed; full room_build -> summary exact except path and timings, 676855 raw, 554067 cleaned, 6.35 x 3.30 m; regenerated capture_scene and headless Chromium -> room.html ok; ruff, duplicate check and Python review -> clean, ten randomized old/new comparisons exact; README example -> (20,) bool`
- cost: 9 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.16 (was 0.18); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 3290 words: one-line-closer "Run   to check the retained methods."

## Left over

Next: mapping, objects, then orchestrators. Default suite last passed 1013 tests after depth; rerun after the remaining stage moves. Locked dev extra lacks psutil; full default suite uses system Python. Owner chose evaluation/layers for walkthrough tests and experimental sitescan/objects. Live behavior, viewer formats and experimental filters are preserved.
