# Mobile deployments

This is the only folder for APKs handed over for installation. APKs and private verification receipts stay local; this index is tracked in Git.

| App | Current local folder | Version | SHA-256 |
|---|---|---|---|
| FYLD capture | [capture_20261014_bb4def77](capture_20261014_bb4def77/) | 1.1 (2) | `bb4def77d56b59824f90a3fcc87b450d9e29fa43951e82878c8b7ae96cb014db` |
| Camera2 diagnostic | [camera_20261006_d7b2242e](camera_20261006_d7b2242e/) | 0.1 (10242) | `d7b2242e5e601ce73d82205f99c5884a75addbc167fdf2a2ed4135bdbe308545` |

Each folder contains an `.apk`, an identical `.apk.bin` for email transfer and installation notes. The Camera2 folder also retains its original `verification.json`. Rename the `.apk.bin` to `.apk` on the phone before opening it. Install FYLD capture as an update without uninstalling, preserving its queued data and saved computer address.

FYLD capture includes ARCore, the storage queue and PC streaming. Version 1.1 adds crash reports; Record walk still crashes on the Redmi and is under diagnosis. Reopen it on home Wi-Fi after a crash to send the saved report. The Camera2 app is a separate capability diagnostic, with package `org.fyld.capturecheck`.

Folder names are `<app>_<YYYYMMDD>_<sha256-first-8>`, where `capture` and `camera` identify the apps. The date is the UTC publication date; the migrated Camera2 bundle retains its original 6 October date. The hash identifies the exact APK even when its version number is reused. This convention was proposed by Claude, not owner-ruled. Publishers refuse to overwrite an existing bundle.

Build capture with `wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh`. The Camera2 export wrapper is `experiments/01_camera_capture_delivery/build/export-apk.ps1`; `RunId` remains a build/staging identifier, while the published folder uses the convention above. Both routes publish here. Gradle and cached Camera2 build outputs remain build intermediates, not installation handoffs.

On 14 October the owner chose to keep capture and the latest Camera2 diagnostic. Older smoke, phonecheck, raw-recorder and Camera2 handoffs, duplicate capture copies, abandoned staging folders and experiment APK handoffs were removed. Phone recordings and receiver logs were retained in experiment run folders.
