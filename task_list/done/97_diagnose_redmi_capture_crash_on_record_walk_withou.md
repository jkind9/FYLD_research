---
id: "97"
title: Diagnose Redmi capture crash on Record walk without USB
status: done
files:
  - experiments/01_camera_capture_delivery/capture/**
  - experiments/01_camera_capture_delivery/README.md
  - learning/08_phone_and_deployment.md
  - research/phone_ar_platforms/android_testing_and_crash_reports.md
  - README.md
  - learning/12_rebuilding_arcore.md
  - experiments/open_vio/README.md
created: 2026-10-14
---
# Diagnose Redmi capture crash on Record walk without USB

## Goal

Preserve the Redmi's uncaught exception and Android process-exit diagnostics and send them to the existing PC receiver after reopening, so the Record walk crash can be identified without USB or a SIM

## Plan

1. Check received attempts and recording startup; tests first for crash persistence, original-handler delegation and sending to the existing report receiver. 2. Add app crash diagnostics, bump APK version, and report previous exits on restart. 3. Build in WSL with JVM tests, stage a separately named diagnostic APK and document verified evidence and AVD limits. 4. Review, finish with owner reproduction left over, commit and push.

## Files

- README.md (+2 -0, 417 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -2, 365 lines)
- experiments/01_camera_capture_delivery/capture/app/build.gradle (+2 -2, 28 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CaptureActivity.java (+4 -1, 743 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CrashDiagnostics.java (+68 -0, 68 lines)
- experiments/01_camera_capture_delivery/capture/app/src/main/java/org/fyld/capture/CrashReport.java (+79 -0, 79 lines)
- experiments/open_vio/README.md (+2 -2, 161 lines)
- learning/08_phone_and_deployment.md (+7 -1, 95 lines)
- learning/12_rebuilding_arcore.md (+1 -1, 97 lines)
- mobile_deployments/.staging-smoke_20261004_b-5ed74fb9cbd244209ffd4e82559bf89e/README.md (+7 -0, 7 lines)
- mobile_deployments/.staging-smoke_20261004_b-5ed74fb9cbd244209ffd4e82559bf89e/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/camera_20261004_camera_redmi_run6/README.md (+7 -0, 7 lines)
- mobile_deployments/camera_20261004_camera_redmi_run6/test1_mobile.apk (+0 -0, 0 lines)
- mobile_deployments/camera_task52_camera_java_review_20261006_02/README.md (+7 -0, 7 lines)
- mobile_deployments/camera_task52_camera_java_review_20261006_02/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_accuracy_20261014/README.md (+9 -0, 9 lines)
- mobile_deployments/phonecheck_accuracy_20261014/fyld-phonecheck-accuracy.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk (+0 -0, 0 lines)
- mobile_deployments/phonecheck_session_v1_20261014/fyld-phonecheck-v1.apk.bin (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_archcheck/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_archcheck/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_final/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_final/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_20261004_reviewed/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_20261004_reviewed/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- mobile_deployments/smoke_smoke_20261004_c/README.md (+7 -0, 7 lines)
- mobile_deployments/smoke_smoke_20261004_c/unnamed_dist_1-debug.apk (+0 -0, 0 lines)
- research/phone_ar_platforms/android_testing_and_crash_reports.md (+23 -0, 23 lines)

## Checked

- `wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh -> 27 JVM tests passed and capture 1.1 APK built; CrashReportTest XML -> 7 tests, 0 failures; aapt dump badging -> org.fyld.capture versionCode 2, versionName 1.1, minSdk 26; pytest test_capture_receiver.py -k speed_check_and_report_connections -> 1 passed; RED checkpoints 8d0f577 and 8d3a4a1 -> missing implementation then truncated-report delivery failure reproduced; diff review -> blocker fixed, no remaining confirmed blocker; git diff --check -> clean; APK and .apk.bin hashes -> both bb4def77d56b59824f90a3fcc87b450d9e29fa43951e82878c8b7ae96cb014db`
- cost: 16 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 2 in 1941 words: same-opening "the", same-opening "the"

## Left over

The Record walk crash is not yet diagnosed or fixed. Owner must install capture 1.1 as an update from mobile deployment/capture_20261014_diagnostics, reopen on home Wi-Fi to send historical exits, and reproduce/reopen if a new Java stack is needed. Inspect reports on the running PC receiver, identify the exception, fix it and complete the short trial before the house walk and 60 s rest. Android lifecycle/exit-trace retrieval needs Redmi verification; native history may be unavailable. Android Studio/AVD was researched and recommended, not installed. Existing untracked mobile_deployments and private run data remain local and excluded from commits.
