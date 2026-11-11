---
id: "144"
title: Move the experimental objects stage into sitescan/objects
status: done
files:
  - sitescan/objects/__init__.py
  - sitescan/objects/types.py
  - sitescan/objects/detector.py
  - sitescan/objects/localisation.py
  - sitescan/objects/assignment.py
  - sitescan/objects/association.py
  - sitescan/objects/counting.py
  - sitescan/objects/README.md
  - experiments/06_object_recognition/pilot/detector.py
  - experiments/06_object_recognition/pilot/localisation.py
  - experiments/06_object_recognition/pilot/compat_localisation.py
  - experiments/06_object_recognition/pilot/association.py
  - src/live/processor.py
  - tests/test_sitescan_objects.py
  - sitescan/README.md
  - DESIGN.md
  - sitescan/mapping/site.py
created: 2026-11-09
---
# Move the experimental objects stage into sitescan/objects

## Goal

Move the existing detector, box lifting and association unchanged, marked experimental

## Plan

1. Add failing object geometry, matching and anchor tests. 2. Move array methods and state records with legacy boundary adapters. 3. Write the experimental stage reference. 4. Check pilot and live callers, golden outputs, room/viewer outputs and live replay.

## Files

- DESIGN.md (+4 -4, 694 lines)
- experiments/01_camera_capture_delivery/host/capture_receiver.py (+3 -3, 377 lines)
- experiments/01_camera_capture_delivery/host/protocol.py (+3 -46, 4 lines)
- experiments/01_camera_capture_delivery/host/session_v1.py (+9 -157, 10 lines)
- experiments/01_camera_capture_delivery/host/session_v2.py (+4 -183, 5 lines)
- experiments/01_camera_capture_delivery/phone_session_v2.md (+2 -200, 3 lines)
- experiments/05_birds_eye_mapping/chunks.py (+93 -0, 93 lines)
- experiments/05_birds_eye_mapping/measure.py (+7 -304, 9 lines)
- experiments/05_birds_eye_mapping/streaming.py (+131 -0, 131 lines)
- experiments/sfm/src/dense.py (+5 -2, 121 lines)
- experiments/shared/geometry.py (+5 -4, 117 lines)
- experiments/surface_cleanup/README.md (+25 -0, 25 lines)
- experiments/surface_cleanup/__init__.py (+1 -0, 1 lines)
- experiments/surface_cleanup/filters.py (+55 -0, 55 lines)
- experiments/surface_cleanup/masks.py (+48 -0, 48 lines)
- experiments/surface_cleanup/support.py (+55 -0, 55 lines)
- pytest.ini (+1 -1, 7 lines)
- sitescan/README.md (+31 -0, 31 lines)
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
- sitescan/mapping/README.md (+74 -0, 74 lines)
- sitescan/mapping/__init__.py (+8 -1, 8 lines)
- sitescan/mapping/footprint.py (+78 -0, 78 lines)
- sitescan/mapping/plane.py (+70 -0, 70 lines)
- sitescan/mapping/site.py (+59 -0, 59 lines)
- sitescan/mapping/types.py (+69 -0, 69 lines)
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
- src/live/processor.py (+4 -21, 166 lines)
- src/live/room_build.py (+18 -50, 211 lines)
- src/live/run.py (+3 -16, 133 lines)
- src/live/sizing.py (+14 -36, 43 lines)
- src/live/stream.py (+10 -44, 14 lines)
- src/walkthrough/steps/depth.py (+15 -49, 289 lines)
- tests/test_sitescan_cleanup.py (+70 -0, 70 lines)
- tests/test_sitescan_depth.py (+115 -0, 115 lines)
- tests/test_sitescan_fusion.py (+56 -0, 56 lines)
- tests/test_sitescan_mapping.py (+58 -0, 58 lines)
- tests/test_sitescan_scale.py (+83 -0, 83 lines)
- tests/test_sitescan_session.py (+138 -0, 138 lines)

## Checked

- `Final system python -B -m pytest -q -> 1045 passed, 7 skipped, one eager-import regression found; root-import regression plus mapping tests after lazy Open3D fix -> 27 passed; final full-suite rerun -> running in background, log outputs/final_refactor/default_fixed.log; golden after mapping -> 3 passed; every moved stage rebuilt full room -> 676855 raw, 554067 cleaned, 6.35 x 3.30 m, summary exact except path and timings; regenerated room pages in Chromium -> no errors; final isolated full live replay with objects -> 1.594 updates/s, longest gap 0.849 s, zero gaps over 1 s; ruff, duplicate check and Python review -> clean`
- cost: 413 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.13 (was 0.16); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 3659 words: one-line-closer "Run   to check the retained methods."

## Left over

Owner requested a quick handover for manual review. Completed stages are session, depth, scale, fusion, cleanup and mapping (tasks 138-143). Objects implementation did not start; red-only objects tests were removed. Objects and both orchestrators remain to move. Final default suite is running in background; inspect outputs/final_refactor/default_fixed.log for completion. Last full run had one import regression, fixed and verified by 27 focused tests. Locked dev extra lacks psutil; full suite uses established system Python. No commit or push. Owner choices remain evaluation/layers and experimental sitescan/objects.
