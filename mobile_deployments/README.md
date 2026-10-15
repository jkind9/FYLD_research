# Mobile deployments

This is the only folder for APKs handed over for installation. APKs and private verification receipts stay local; this index is tracked in Git.

**Install FYLD capture 1.2:** [APK](capture_v1.2_20261014T210622Z_c2db5faf/fyld-capture_v1.2_20261014T210622Z.apk), or [email copy](capture_v1.2_20261014T210622Z_c2db5faf/fyld-capture_v1.2_20261014T210622Z.apk.bin). Built at 21:06:22 UTC on 14 October (22:06:22 BST).

| App | Current local folder | Version | SHA-256 |
|---|---|---|---|
| FYLD capture | [capture_v1.2_20261014T210622Z_c2db5faf](capture_v1.2_20261014T210622Z_c2db5faf/) | 1.2 (3) | `c2db5fafa5f170449d52bbff9647c7b606d552d8fbd108488960281088e2e95f` |
| Camera2 diagnostic | [camera_20261006_d7b2242e](camera_20261006_d7b2242e/) | 0.1 (10242) | `d7b2242e5e601ce73d82205f99c5884a75addbc167fdf2a2ed4135bdbe308545` |

Each folder contains an `.apk`, an identical `.apk.bin` for email transfer and installation notes. The Camera2 folder also retains its original `verification.json`. Rename the `.apk.bin` to `.apk` on the phone before opening it. Install FYLD capture as an update without uninstalling, preserving its queued data and saved computer address.

FYLD capture includes ARCore, the storage queue and PC streaming. Version 1.2 rejects invalid point projections before JSON encoding and reports serialization failures through the recording-error path. The Redmi completed a 39.88 s recording with 1,194 frames and zero reported drops; its PC replay and export have been checked. See [the measured result](../experiments/01_camera_capture_delivery/README.md#completed-redmi-session-task99). The Camera2 app is a separate capability diagnostic, with package `org.fyld.capturecheck`.

New folder names are `<app>_v<version>_<YYYYMMDDTHHMMSSZ>_<sha256-first-8>`. APK names are `fyld-<app>_v<version>_<YYYYMMDDTHHMMSSZ>.apk`, with an identical `.apk.bin`. `Z` means UTC; the version comes from the built APK. The hash distinguishes bytes even when versions are reused. The retained Camera2 bundle has only its historical build date, so its name stays as migrated. The owner requested versions and timestamps; the exact spelling was proposed by Claude, not owner-ruled. Publishers refuse to overwrite an existing bundle. Update this index when handing over a new build; the scripts print its exact path.

Build capture with `wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh`. The Camera2 export wrapper is `experiments/01_camera_capture_delivery/build/export-apk.ps1`; `RunId` remains a build/staging identifier, while the published folder uses the convention above. Both routes publish here. Gradle and cached Camera2 build outputs remain build intermediates, not installation handoffs.

On 14 October the owner chose to keep capture and the latest Camera2 diagnostic. Older smoke, phonecheck, raw-recorder and Camera2 handoffs, duplicate capture copies, abandoned staging folders and experiment APK handoffs were removed. Phone recordings and receiver logs were retained in experiment run folders.
