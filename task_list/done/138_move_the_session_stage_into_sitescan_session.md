---
id: "138"
title: Move the session stage into sitescan/session
status: done
files:
  - sitescan/types.py
  - sitescan/session/__init__.py
  - sitescan/session/read.py
  - sitescan/session/replay.py
  - sitescan/session/wire_v1.py
  - sitescan/session/wire_v2.py
  - sitescan/session/protocol.py
  - sitescan/session/README.md
  - sitescan/session/FORMAT.md
  - experiments/01_camera_capture_delivery/host/session_v1.py
  - experiments/01_camera_capture_delivery/host/session_v2.py
  - experiments/01_camera_capture_delivery/host/protocol.py
  - experiments/01_camera_capture_delivery/phone_session_v2.md
  - src/live/stream.py
  - tests/test_sitescan_session.py
  - experiments/01_camera_capture_delivery/host/capture_receiver.py
  - DESIGN.md
  - pytest.ini
created: 2026-11-09
---
# Move the session stage into sitescan/session

## Goal

Read saved recordings through one session stage with OpenCV matrix poses while preserving old callers and outputs

## Plan

1. Add failing reader and replay behaviour tests. 2. Move parsers and protocol, share folder reading, add canonical records and compatibility exports. 3. Document format and stage. 4. Check tests, golden outputs, full room and Chromium page.

## Files

- DESIGN.md (+3 -3, 694 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+3 -3, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+3 -46, 4 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+9 -157, 10 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+4 -183, 5 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+2 -200, 3 lines)
- pytest.ini (+1 -1, 7 lines)
- sitescan/session/FORMAT.md (+201 -0, 201 lines)
- sitescan/session/README.md (+70 -0, 70 lines)
- sitescan/session/__init__.py (+5 -0, 6 lines)
- sitescan/session/protocol.py (+45 -0, 45 lines)
- sitescan/session/read.py (+89 -0, 89 lines)
- sitescan/session/replay.py (+39 -0, 39 lines)
- sitescan/session/wire_v1.py (+195 -0, 195 lines)
- sitescan/session/wire_v2.py (+256 -0, 256 lines)
- sitescan/types.py (+48 -0, 48 lines)
- src/live/stream.py (+10 -44, 14 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)

## Checked

- `Session tests failed on missing new module, then phone and session tests -> 256 passed, 1 skipped; system python -B -m pytest -q -> 1005 passed, 7 skipped, 3 deselected; locked python -B -m pytest -m golden tests/golden -> 3 passed; full room_build -> 676855 raw, 554067 cleaned, map 6.35 x 3.30 m, summary exact except path and timings; capture_scene plus tools.demos.screenshot -> room.html ok in headless Chromium; ruff on moved code -> clean, capture_receiver retains two pre-existing UP037 findings; Python review -> no blocking defect`
- cost: 21 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.09 (was 0.11); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 0 in 1990 words

## Left over

Next stages: depth, scale, fusion, cleanup, mapping, objects, then orchestrators. Owner chose evaluation/layers for walkthrough tests and experimental sitescan/objects for the pilot. Locked dev environment lacks psutil for the full experiment suite; default suite used established system Python. Live full-walk replay with objects remains to be checked. V1 compatibility stays until old callers move.
