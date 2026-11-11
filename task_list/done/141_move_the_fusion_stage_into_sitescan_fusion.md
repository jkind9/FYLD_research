---
id: "141"
title: Move the fusion stage into sitescan/fusion
status: done
files:
  - sitescan/fusion/__init__.py
  - sitescan/fusion/fragments.py
  - sitescan/fusion/README.md
  - src/live/fragments.py
  - tests/test_sitescan_fusion.py
  - sitescan/README.md
  - DESIGN.md
created: 2026-11-09
---
# Move the fusion stage into sitescan/fusion

## Goal

Move correction-aware TSDF fragments without changing fusion, point order or colours

## Plan

1. Add failing fragment behavior tests. 2. Move and rewrite fragment state and TSDF calls with old imports forwarding. 3. Write the stage reference. 4. Check fragment callers, golden outputs, room numbers and Chromium.

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
- sitescan/README.md (+29 -0, 29 lines)
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
- src/live/fragments.py (+6 -82, 7 lines)
- src/live/orientation_control.py (+7 -27, 116 lines)
- src/live/room_build.py (+16 -48, 211 lines)
- src/live/run.py (+3 -16, 133 lines)
- src/live/sizing.py (+14 -36, 43 lines)
- src/live/stream.py (+10 -44, 14 lines)
- src/walkthrough/steps/depth.py (+15 -49, 289 lines)
- tests/test_sitescan_depth.py (+115 -0, 115 lines)
- tests/test_sitescan_fusion.py (+56 -0, 56 lines)
- tests/test_sitescan_scale.py (+83 -0, 83 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)

## Checked

- `New fusion tests -> failed on missing Fragments before move; locked pytest tests/test_sitescan_fusion.py src/live/tests/test_fragments.py -> 13 passed; locked pytest -m golden tests/golden -> 3 passed; full room_build -> full summary exact except path and timings, 676855 raw, 554067 cleaned, 6.35 x 3.30 m; regenerated capture_scene and headless Chromium -> room.html ok; ruff, duplicate check and Python review -> clean`
- cost: 5 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.16 (was 0.19); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 0 in 2896 words

## Left over

Next: cleanup, mapping, objects, then orchestrators. Full default suite last passed 1013 tests after depth; rerun after the remaining stage moves. Live replay after depth met 1.377 updates/s with objects. Locked dev extra lacks psutil, so full default suite uses system Python. Owner chose evaluation/layers and experimental sitescan/objects.
