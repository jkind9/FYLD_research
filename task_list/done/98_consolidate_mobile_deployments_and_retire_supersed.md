---
id: "98"
title: Consolidate mobile deployments and retire superseded APKs
status: done
files:
  - .gitignore
  - README.md
  - mobile_deployments/README.md
  - experiments/01_camera_capture_delivery/build/deployment.py
  - experiments/01_camera_capture_delivery/build/export.py
  - experiments/01_camera_capture_delivery/build/export-apk.ps1
  - experiments/01_camera_capture_delivery/build/build-capture.sh
  - experiments/01_camera_capture_delivery/tests/test_deployment.py
  - experiments/01_camera_capture_delivery/tests/test_build_recipe.py
  - experiments/01_camera_capture_delivery/README.md
  - experiments/01_camera_capture_delivery/field_accuracy.md
  - experiments/open_vio/README.md
  - learning/08_phone_and_deployment.md
  - learning/12_open_vio.md
  - learning/12_rebuilding_arcore.md
created: 2026-10-14
---
# Consolidate mobile deployments and retire superseded APKs

## Goal

Keep the latest capture and Camera2 diagnostic APKs in one named deployment folder and route future builds there.

## Plan

1. Test deployment naming and publication before changing code. 2. Update publishers and docs. 3. Verify retained APK hashes, remove obsolete bundles, finish, commit and push.

## Files

- .gitignore (+2 -1, 109 lines)
- README.md (+1 -1, 417 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -14, 367 lines)
- experiments/01_camera_capture_delivery/build/build-capture.sh (+3 -7, 21 lines)
- experiments/01_camera_capture_delivery/build/deployment.py (+18 -0, 18 lines)
- experiments/01_camera_capture_delivery/build/export-apk.ps1 (+1 -1, 35 lines)
- experiments/01_camera_capture_delivery/build/export.py (+38 -5, 267 lines)
- experiments/01_camera_capture_delivery/field_accuracy.md (+2 -2, 79 lines)
- experiments/open_vio/README.md (+1 -1, 161 lines)
- learning/08_phone_and_deployment.md (+2 -0, 97 lines)
- learning/12_rebuilding_arcore.md (+2 -0, 99 lines)
- mobile_deployments/README.md (+18 -0, 18 lines)

## Checked

- `pytest deployment/build_recipe/warm_build -> 128 passed; WSL build-capture.sh -> 27 JVM tests passed and APK published only in mobile_deployments; SHA256 both APK/email pairs -> matched retained receipt/build; git diff --check -> clean`
- cost: 6 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.69 (was 0.78); approximate (python could not start)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 1 in 1251 words: same-opening "the"
- folders that could not be read, skipped: experiments/02_stereo_depth/tests/.test-marigold-temp/tmpby3p9_1j, experiments/02_stereo_depth/tests/.test-marigold-temp/tmpdpztkok_, experiments/02_stereo_depth/tests/tmphix76bln, experiments/02_stereo_depth/tests/tmpx6_7h35w

## Left over

Record walk crash still needs the new saved report: reopen capture 1.1 on home Wi-Fi. Latest PC diagnostic is 21:48:45 with old exits and no Java stack. Receiver remains running. Full house walk, 60 s rest, replay and EuRoC export remain unperformed. AVD not installed.
