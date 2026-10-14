---
id: "92"
title: Prepare Stream A field accuracy checks and ARCore notice
status: done
files:
  - experiments/01_camera_capture_delivery/host/accuracy.py
  - experiments/01_camera_capture_delivery/tests/test_accuracy.py
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/java/org/fyld/phonecheck/CheckActivity.java
  - experiments/01_camera_capture_delivery/phonecheck/app/src/main/res/values/strings.xml
  - experiments/01_camera_capture_delivery/field_accuracy.md
  - experiments/01_camera_capture_delivery/README.md
  - research/phone_ar_platforms/arcore_commercial_terms.md
  - README.md
  - mobile deployment/phonecheck_accuracy_20261014/README.md
created: 2026-10-14
---
# Prepare Stream A field accuracy checks and ARCore notice

## Goal

Make Stream A step 3 ready for measured phone walks without claiming handset accuracy before capture

## Plan

1. Test scoring of loop closure, tape distances, missing tracking and invalid annotations. 2. Add a session v1 scorer and capture protocol for indoor, stairs and outdoor walks. 3. Show the ARCore notice and links in the app; rebuild and verify the APK. 4. Run host checks, review the diff, finish the record and push Stream A work.

## Files

- README.md (+1 -1, 399 lines)
- experiments/01_camera_capture_delivery/README.md (+8 -0, 308 lines)
- experiments/01_camera_capture_delivery/field_accuracy.md (+79 -0, 79 lines)
- experiments/01_camera_capture_delivery/host/accuracy.py (+5 -5, 107 lines)
- experiments/01_camera_capture_delivery/phonecheck/app/src/main/res/values/strings.xml (+1 -1, 4 lines)
- experiments/01_camera_capture_delivery/tests/test_accuracy.py (+32 -4, 183 lines)
- research/phone_ar_platforms/arcore_commercial_terms.md (+1 -1, 52 lines)

## Checked

- `.venv-yolo/Scripts/python.exe -B -m pytest -q src/live/tests experiments/01_camera_capture_delivery/tests --basetemp outputs/task92_pytest_final_01 --cov=accuracy --cov-branch --cov-report=term-missing -rs -> 199 passed, 1 skipped (Windows symlink privilege), scorer coverage 98%; python -m ruff check accuracy.py test_accuracy.py -> passed; WSL build-phonecheck.sh -> APK built, 4 JVM tests passed; apksigner verify -> v2 signature valid; aapt dump --values resources -> required notice and quoted privacy/terms links packaged; Get-FileHash -> staged APK 5680c2836c62734fe387cd0317e0b5cd3256bf5f3c84ee5b847ddebcf5d0d751; git diff --check -> passed`
- cost: 13 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.23 (was 0.25); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 1295 words: same-opening "the"
- folders that could not be read, skipped: experiments/02_stereo_depth/tests/.test-marigold-temp/tmpby3p9_1j, experiments/02_stereo_depth/tests/.test-marigold-temp/tmpdpztkok_, experiments/02_stereo_depth/tests/tmphix76bln, experiments/02_stereo_depth/tests/tmpx6_7h35w

## Left over

Owner: install mobile deployment/phonecheck_accuracy_20261014/fyld-phonecheck-accuracy.apk, inspect the notice and links, and capture tape-measured indoor, stair and outdoor loops using field_accuracy.md. Task75 stays open for measured results and the phone-session COLMAP adapter/comparison; Task61 needs owner acceptance limits. Task89 object overcounting and the narrow ICL speed margin remain. No ADB handset was attached; no real phone accuracy is claimed.
