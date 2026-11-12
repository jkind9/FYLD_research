# Camera2 diagnostic app and native build control

This folder holds the native sources for the Python-route Android builds of [experiment 01, camera capture and delivery](../README.md): a Java Camera2 diagnostic app, and a one-function C file that checks the NDK can compile.

| File | What it does |
|---|---|
| `camera/java/org/fyld/capture/CameraActivity.java` | The diagnostic app's only screen. Asks for camera permission, builds a capability report, tries a single-camera capture, and exports the session as a ZIP. |
| `camera/java/org/fyld/capture/CameraCapture.java` | Opens one camera with Camera2 and captures JPEG frames with their sensor timestamp, crop region, rotation and distortion-correction mode. |
| `camera/java/org/fyld/capture/CameraReport.java` | Builds the versioned report (`schema_version` 1): device identity, each camera's characteristics, concurrent camera sets, per-check status and per-frame records. Writes files atomically. |
| `smoke.c` | `int add(int a, int b)`. The build compiles it to prove the Android NDK toolchain works. The app does not call it. |

The three Java files are pinned by SHA-256 in [`../build/camera-profile.json`](../build/camera-profile.json), so changing one means updating that file. [`../app/capture_report.py`](../app/README.md) checks the reports they write.

This app is separate from the FYLD capture app in [`../capture/`](../capture/README.md), which uses ARCore and writes a different report.

## How to run it

Nothing here runs on its own. The Python build compiles `smoke.c` and, with `--camera`, packages the Java files into the APK:

```text
bash research/experiments/01_camera_capture_delivery/build/build-apk.sh --camera --run-id <id> --p4a-env <path> --sdk <path> --predecessor-root <path> --gradle-cache <path> --scratch <path> --output-root <path>
```

This needs WSL with the pinned Android toolchain. See [`../build/`](../build/README.md).

## Where results are recorded

The staged-APK results and the Redmi capability report are in the [experiment 01 README](../README.md). That README says the on-device single-image export of the staged APK was unverified when last recorded.
