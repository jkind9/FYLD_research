# FYLD capture app (Gradle project)

This Android project is the phone-side recorder for [experiment 01, camera capture and delivery](../README.md). It records every camera image, the camera's capture settings, ARCore's tracking record and the motion sensors into a queue on the phone's storage, and a sender drains that queue to the PC. The wire format is "phone session v2", defined in [`../phone_session_v2.md`](../phone_session_v2.md).

The project is `capture/` with one module, `app/` (package `org.fyld.capture`, version 1.2, minimum Android API 26, ARCore SDK 1.56.0). The Java sources are in `app/src/main/java/org/fyld/capture/`.

## Source files

| File | What it does |
|---|---|
| `CaptureActivity.java` | The only screen. Has three actions: record a walk, record motion sensors only (the rest recording used for calibration), and run all checks (ARCore set-up, a 15 s tracking run, link speed). |
| `SharedCameraRig.java` | Opens Camera2 through ARCore's shared-camera mode, so ARCore tracks while the app also receives every image. |
| `FrameCapture.java` | Reads ARCore's record for each new camera image: pose, tracking state, points, new raw depth, anchors and their corrections. Runs on the GL thread (the graphics thread). |
| `FrameAssembler.java` | Joins the image, its capture result and ARCore's record. Releases frames in image order, or after a fixed wait with whatever has arrived. |
| `FrameWriter.java` | Encodes each released frame (grey plane, colour JPEG, ARCore record) and writes it to the queue. |
| `SessionFrame.java`, `SessionMessages.java`, `ArcoreRecord.java`, `RecordingMeta.java` | Plain-Java encoders for the session v2 frame and the other messages. They hold no Android types, so the JVM can test them. |
| `ImuLogger.java` | Logs accelerometer and gyroscope readings with Android's bias estimates. |
| `DiskQueue.java` | The on-phone queue. Messages are numbered with no gaps and deleted only when the PC acknowledges them. |
| `Uploader.java` | Sends the queue over TCP and resumes after a dropped connection without loss or repeats. |
| `Report.java`, `TrackingStats.java` | The check report (schema 1) and the per-frame ARCore statistics for the tracking run. |
| `CrashReport.java`, `CrashDiagnostics.java` | Save Java crashes and Android's exit history, and send them on the next launch. |
| `CameraPreview.java` | Draws ARCore's camera image full screen. |

Tests are in `app/src/test/java/org/fyld/capture/`. `SessionV2Test` encodes the shared fixture in `app/src/test/resources/session_v2/`. `SendingTest` covers the queue, assembler and resumable sender. `FrameJsonTest` covers point projection. `CrashReportTest` covers crash persistence.

## How to run it

Build and test in WSL (Ubuntu with the Android SDK and Gradle 8.14.3), from the repository root:

```text
wsl -d Ubuntu -- bash research/experiments/01_camera_capture_delivery/build/build-capture.sh
```

The script runs `testDebugUnitTest assembleDebug` and stages the APK in [`mobile_deployments/`](../../../../mobile_deployments/README.md). See [`build/`](../build/README.md).

On the PC, the capture receiver now lives in `apps/receiver/` and the session readers in [`sitescan/session/`](../../../../sitescan/session/README.md).

## Where results are recorded

Capture runs on the Redmi, with frame counts, drops and limits, are in the [experiment 01 README](../README.md) and [`../phone_session_v2.md`](../phone_session_v2.md).
