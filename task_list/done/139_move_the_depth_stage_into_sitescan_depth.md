---
id: "139"
title: Move the depth stage into sitescan/depth
status: done
files:
  - sitescan/depth/__init__.py
  - sitescan/depth/model.py
  - sitescan/depth/orientation.py
  - sitescan/depth/README.md
  - src/live/run.py
  - src/live/orientation_control.py
  - src/live/room_build.py
  - src/walkthrough/steps/depth.py
  - experiments/shared/geometry.py
  - tests/test_sitescan_depth.py
  - DESIGN.md
  - sitescan/README.md
created: 2026-11-09
---
# Move the depth stage into sitescan/depth

## Goal

Load learned depth once and predict from RGB arrays while preserving recorded and upright behavior

## Plan

1. Add failing depth and orientation behavior tests. 2. Move model inference and image orientation, keeping adapters for old callers. 3. Write the stage reference. 4. Check focused tests, default suite, golden outputs and a regenerated room page.

## Files

- DESIGN.md (+3 -3, 694 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+3 -3, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+3 -46, 4 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+9 -157, 10 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+4 -183, 5 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+2 -200, 3 lines)
- experiments/shared/geometry.py (+5 -4, 117 lines)
- pytest.ini (+1 -1, 7 lines)
- sitescan/README.md (+27 -0, 27 lines)
- sitescan/depth/README.md (+71 -0, 71 lines)
- sitescan/depth/__init__.py (+5 -1, 5 lines)
- sitescan/depth/model.py (+72 -0, 72 lines)
- sitescan/depth/orientation.py (+36 -0, 36 lines)
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
- src/live/room_build.py (+4 -2, 245 lines)
- src/live/run.py (+3 -16, 133 lines)
- src/live/stream.py (+10 -44, 14 lines)
- src/walkthrough/steps/depth.py (+15 -49, 289 lines)
- tests/test_sitescan_depth.py (+115 -0, 115 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)

## Checked

- `Depth tests failed on missing new module, then python -B -m pytest -q tests/test_sitescan_depth.py src/live/tests/test_orientation_control.py -> 20 passed; system python -B -m pytest -q -> 1013 passed, 7 skipped, 3 deselected; locked python -B -m pytest -m golden tests/golden -> 3 passed; full room_build -> all summary values exact except path and timings, 676855 raw and 554067 cleaned, 6.35 x 3.30 m; capture_scene plus screenshot -> Chromium room.html ok; full live replay with objects on CPU -> 1.377 updates/s, longest gap 0.866 s, none over 1 s; ruff and Python review -> clean`
- cost: 10 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.19 (was 0.21); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 0 in 2337 words

## Left over

Next: scale, fusion, cleanup, mapping, objects, then orchestrators. Owner decisions are recorded in DESIGN section 13: walkthrough tests to evaluation/layers and object pilot to sitescan/objects, experimental. Full default suite uses system Python because locked dev extra lacks psutil. Live and room frame choice, scale fallback and freshness behavior remain unchanged.
