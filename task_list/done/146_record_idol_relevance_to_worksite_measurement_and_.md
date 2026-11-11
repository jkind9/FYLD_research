---
id: "146"
title: Record Idol relevance to worksite measurement and counting
status: done
files:
  - research/gaussian_splatting/idol.md
  - research/gaussian_splatting/README.md
created: 2026-11-10
---
# Record Idol relevance to worksite measurement and counting

## Goal

Save the sourced Idol assessment beside related splatting research

## Plan

1. Write the model facts, project fit and limits. 2. Link the note from the splatting index. 3. Check local links and finish the record.

## Files

- DESIGN.md (+57 -4, 747 lines)
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
- pyproject.toml (+16 -1, 72 lines)
- pytest.ini (+1 -1, 7 lines)
- research/gaussian_splatting/README.md (+1 -0, 42 lines)
- research/gaussian_splatting/idol.md (+39 -0, 39 lines)
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
- uv.lock (+92 -8, 1581 lines)

## Checked

- `git diff --check -> passed; PowerShell local Markdown link check -> all 29 targets exist; read-back -> sourced facts and project assessments are separate`
- cost: 1 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.13 (was 0.16); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 4502 words: one-line-closer "Run   to check the retained methods."

## Left over

None for this research note. Idol remains reference only; no inference or integration was attempted.
