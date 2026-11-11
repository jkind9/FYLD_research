# APK build and export scripts

This folder builds the Android packages for [experiment 01, camera capture and delivery](../README.md), checks the finished APK bytes, and copies the APK into the repository's handoff folder, [`mobile_deployments/`](../../../mobile_deployments/README.md).

There are two build routes:

- the Python route (python-for-android, "p4a") packages [`../app/main.py`](../app/README.md) and the Camera2 diagnostic sources in `../native/`;
- the Gradle route builds the FYLD capture app in [`../capture/`](../capture/README.md).

| File | What it does |
|---|---|
| `build-capture.sh` | Runs the capture app's JVM tests, builds its debug APK with Gradle, then calls `deployment.py`. Prints the APK's SHA-256 and the output folder. |
| `deployment.py` | Reads the APK's version with `aapt`, then calls `export.publish_capture` to stage `.apk` and `.apk.bin` copies plus a short README in `mobile_deployments/capture_v<version>_<UTC time>_<hash8>/`. |
| `build-apk.sh` | Thin wrapper that runs `warm.py`. |
| `warm.py` | Reproduces the cached p4a build into a scratch folder without touching the existing installation. `--camera` builds the Camera2 profile from `camera-profile.json`. Main functions: `preflight`, `prepare`, `run`. |
| `recipe.py` | The pinned toolchain versions (`PINS`), settings validation and `sha256`. |
| `verify.py` | `verify_apk` checks the signature, manifest, native libraries and embedded Python bundle of a finished APK with the installed Android tools. |
| `verify_bytecode.py` | Compares the Python bytecode inside the APK with `app/main.py`. It runs only under the recovered Python 3.14.2 (`require_python` refuses anything else). |
| `export.py` | `publish_bundle` verifies an APK against its receipt and publishes a dated folder; `publish_capture` does the lighter capture-app version. |
| `export-apk.ps1` | PowerShell wrapper that runs `export.py` in WSL for a verified APK and a `verification.json` receipt. |
| `toolchain.json` | The pinned versions of Ubuntu, Python, Java, p4a, NDK, Gradle and the smoke app. |
| `camera-profile.json` | The pinned package name, permissions and Java source hashes for the Camera2 diagnostic profile. |
| `container-readiness.json` | A record of which Docker images were checked on 4 October 2026 for a clean container build. None was compatible. |

## How to run it

Both routes need WSL (Ubuntu) with the Android SDK, Java 17 and Gradle 8.14.3 installed under the home folder. No GPU is used.

Capture app, from the repository root:

```text
wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh
```

Gradle downloads the ARCore library from Google's Maven repository on the first build. The script builds in `~/capture-build` (set `CAPTURE_WORK` to change it) because Gradle is slow on `/mnt/c`.

Python route: `build-apk.sh` takes `--p4a-env`, `--sdk`, `--predecessor-root`, `--gradle-cache`, `--scratch`, `--output-root` and `--run-id`, all of which depend on the local WSL layout. See `warm.py` for the full list.

Tests, which need no Android tools:

```text
.venv/Scripts/python.exe -m pytest experiments/01_camera_capture_delivery/tests/test_build_recipe.py experiments/01_camera_capture_delivery/tests/test_warm_build.py experiments/01_camera_capture_delivery/tests/test_deployment.py
```

## Where results are recorded

Build results, APK hashes and the warm-build run are in the [experiment 01 README](../README.md). Current installable APKs are listed in [`mobile_deployments/README.md`](../../../mobile_deployments/README.md).
