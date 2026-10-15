# 8. The phone

The owner ruled on 7 October 2026 that the system must be deployed on a phone, and that any method slower than one frame per second is not worth using. On 14 October 2026 the owner added that processing must be live, or update at least once per second, even on a server: no method may wait for the whole walk to be captured. This chapter covers what a phone can supply, how that changes the design, and what is still unmeasured.

## What ARCore gives an Android app

ARCore is Google's augmented-reality library. On a supported phone it provides, live, for every camera frame:

- **Camera pose in metres**, from visual-inertial odometry (chapter 3): camera features plus the IMU. It has metric size and knows which way gravity points.
- **Intrinsics** for the current image (chapter 1).
- **Tracked feature points** in 3D: the same kind of sparse points SfM produces (chapter 4).
- **Depth images** from motion (or a time-of-flight sensor if the phone has one). *Raw depth* is a 16-bit image in millimetres, typically about 160 × 120 pixels, with a separate confidence image; zero means no reading. Google lists it as most accurate at 0.5-5 m and poor on blank surfaces.
- **Planes**: detected floors and walls.

Its accuracy depends on the phone and the walk. Published tests range from about 1.5 cm drift on short indoor sessions (RealityCheck) to over 10 cm on harder walks; one study of four commercial trackers measured final drift of 0.07-0.12 m on corridors and campus walks, and much more in a car. ARCore has not been measured on the project's Redmi phone yet (Task75).

**Using ARCore in a product.** It is free for the on-device features used here and allowed commercially. An app must tell users it runs on Google Play Services for AR, governed by Google's Privacy Policy. Google's general API terms forbid uses where failure could cause death or injury, and let Google change or discontinue the service. Only phones on Google's supported list with Google Play can run it. Details: [research/phone_ar_platforms/arcore_commercial_terms.md](../research/phone_ar_platforms/arcore_commercial_terms.md).

> **Project result: ARCore works on the project's Redmi.** A 15 s walk tracked on 100% of 891 frames, 4.9 ms per update; raw depth is 160 x 90 from motion (the phone's depth sensor is not used), and the phone streamed 29 frames per second with their poses to a computer over Wi-Fi (Task85).

How ARCore works inside is explained in [chapter 11](11_inside_arcore.md).

## Hosted against on the phone

- **Hosted**: the phone records; a server with a GPU does the heavy work after upload. Most accurate methods (multi-view stereo, large learned models, offline SfM) live here.
- **On the phone**: runs on the handset with no network, for quick checks on site. Needs small models (a few million to tens of millions of parameters) through a mobile runtime such as LiteRT, ONNX Runtime Mobile or ExecuTorch.

Which parts run where is still an open owner decision (Task61). Either way, results must update live, at least once per second.

## The design the results point to

Putting chapters 2-5 together:

| Need | Source on the phone | Evidence from recorded data |
|---|---|---|
| Camera path | ARCore's own tracking, not a depth-based tracker | Image-feature tracking with refinement (SfM) is 3-5 times more accurate than the old depth-based tracker (chapter 3) |
| Real-world size | ARCore's metric tracking, or about 20 depth readings at tracked points | 20 readings give a path within 1.15 times the best possible (chapter 4) |
| Dense surfaces | A small learned depth model, resized each frame to ARCore's tracked points | Within 8-27 mm of the true-path ceiling on recorded data (chapter 5) |
| Better surfaces, if needed | Multi-view stereo on recent frames, on a server that updates at least once per second | Not yet run (needs GPU permission) |

The small depth model candidates measured so far: ZipDepth's phone build (6.1M parameters, shape AbsRel 0.07, 24 ms per frame on a desktop CPU, exported to ONNX; its TFLite conversion failed) and Depth Anything V2 Small (25M parameters, 218-318 ms per frame on a desktop CPU). Neither has run on the phone yet (Task57).

## Capture first, phone later

On 14 October 2026 the owner set the order of work: first capture on the phone and do everything else on the PC, then move what works onto the phone.

The reason is that the methods are not chosen yet. Six ways of building a 3D model are on the table: ARCore's own path with learned depth, ARCore's raw depth alone, an open visual-inertial tracker (Basalt), an image-only tracker (stella_vslam), offline structure from motion (COLMAP) as a reference, and feed-forward 3D models. To compare them fairly, they must all see the *same* walk. A phone can only run one of them at a time, and a slow one would hold the others back; a PC can replay one recording through all six.

What a recording must therefore hold:

- **Every camera frame, none dropped.** Trackers follow features from one frame to the next; a gap of several frames can lose track. Wi-Fi drops frames when it slows, so the phone writes every frame to its own storage first and sends the files afterwards.
- **Grey images without compression loss** for the trackers, which follow small image patches that JPEG blurs, and **colour images** for the depth and detection models, which were trained on colour.
- **The gyroscope and accelerometer**, uncorrected, as fast as the phone allows, on the same clock as the camera (chapter 12 explains why a few milliseconds matter).
- **Everything ARCore says** about each frame: its pose, whether it is tracking, its tracked points, its raw depth and confidence, and its later corrections. This is the ARCore method's input and everyone else's reference.
- **The camera's settings per frame** (exposure, readout time, focus), which the trackers need to model a rolling-shutter phone camera.

ARCore's *shared-camera mode* makes this possible on one phone: ARCore tracks as usual and the same camera session also hands every image to the app.

### Getting every frame to the PC

Lossless 640 x 480 grey at 30 frames a second is 9.2 MB/s, and the colour JPEG adds roughly 2 MB/s. The older 0.70 MB/s phone-to-PC measurement waited for the PC to confirm each frame before sending the next (*stop-and-wait*), leaving the link idle between answers. At that rate a 2-minute walk of about 1.3 GB would take about 32 minutes to send. With windowed sending, the later link-only check measured 33.4 MB/s and the completed capture 1.2 session received 10.22 MB/s while recording, finishing its queue just after Stop.

The capture app therefore separates capturing from sending:

- **A queue on the phone's storage.** Every message (a frame, a batch of motion-sensor readings, a telemetry line) is numbered and written to a file at once. Capture never waits for the network; a slow link only makes the queue longer.
- **A window.** The sender keeps up to 64 messages on the way without waiting for confirmation, so the link stays busy.
- **Cumulative acknowledgements.** The PC answers with one number: the highest message it holds with no gap below it. One answer confirms everything before it, and the phone deletes those files.
- **Resume.** After a dropped connection the phone reconnects and asks where to start; the PC answers with that same number, and the phone resends from the next message. Nothing is lost and nothing is stored twice. A connection that stops moving for 20 s is treated as dropped, because a write to a PC that has gone out of Wi-Fi range can otherwise hang for minutes.
- **Sending after Stop.** The queue keeps draining after the walk ends; the screen shows what is left and an estimated time.

The same ideas run inside TCP itself and most file-transfer tools; the app repeats them one level up because a TCP connection does not survive the phone dropping off Wi-Fi.

> **Project status (15 October 2026).** Capture 1.2 (Task99) completed the Redmi recording `20261014_220756_walk`: 1,194 frames over 39.88 s at 29.92 fps, zero reported drops or missing frame numbers, motion sensors at 423.54 Hz, and 10.22 MB/s received. Sending finished 0.058 s after Stop; lossless PNGs and other session files occupy 225 MB on the PC. All images parsed and CPU replay produced 1.58 updates/s with no gap over one second. The earlier link-only check measured 33.4 MB/s and chose raw grey. The recording has 17 frames without ARCore records, one final frame without camera settings and 44 new depth maps. These limits remain visible in the checks; the 60 s rest and calibration recordings are still needed. [Measured result](../experiments/01_camera_capture_delivery/README.md#completed-redmi-session-task99).

### Testing the Android app

Current APKs live only in [mobile_deployments](../mobile_deployments/README.md), with app version, full UTC timestamp and APK hash in new folder names. APK filenames also include the version and time. The owner chose to retain FYLD capture and the latest Camera2 diagnostic. Old smoke, phonecheck and raw-recorder handoffs were removed; recordings stay in the experiment run folders.

JVM tests check the message encoder, queue and sender, but they do not execute Android's camera driver or app lifecycle. An Android Virtual Device (AVD) runs Android itself and can test controls, permissions, pauses and network handling. Google documents ARCore with an x86/x86_64 emulator and a VirtualScene camera. This app's shared-camera and raw-depth combination still needs checking on an emulator; Redmi timing, heat and sensor rates need the actual phone. Proposed by Claude, not owner-ruled: start with an Android 13 AVD matching the Redmi, then test API 36. No AVD has been installed yet.

With USB debugging unavailable, the diagnostic app saves Java exceptions before Android handles the crash, then sends the saved stack after the app is reopened. It also asks Android for recent exits and any available native crash traces. A native crash does not pass through the Java handler, and Android may no longer hold its trace, so the two sources complement each other. Sources and limits: [Android testing and crash reports](../research/phone_ar_platforms/android_testing_and_crash_reports.md).

That report exposed a frame-encoding exception. Android's JSON serializer can return null for invalid numeric values; synthetic tests reproduced non-finite point projections and overflow. Capture 1.2 filters those points and routes serialization errors through the existing recording-error message. It passes 30 JVM tests and completed the Redmi walk without a crash. The received stack did not identify which individual value caused the earlier failure.

## What is still unmeasured

- ARCore's pose, depth and point accuracy on the Redmi (Tasks 52 and 75).
- Any model's speed, memory, heat and battery on the phone (Task57).
- Whether a real site walk (sunlight, mud, moving people, repeated textures) tracks as well as the indoor benchmarks.

## Try it

`experiments/01_camera_capture_delivery/README.md` describes the Android capability export that has run on the Redmi, and what a usable phone recording must contain (images, calibration, clocks, depth, motion data).

## Further reading

- [research/phone_ar_platforms](../research/phone_ar_platforms/README.md): ARCore notes, raw depth, Apple RoomPlan, the RealityCheck drift paper.
- [research/visual_inertial_odometry/phone_recording_and_clocks.md](../research/visual_inertial_odometry/phone_recording_and_clocks.md): camera and motion-sensor clocks, ARCore's shared-camera mode, and the Android interfaces the capture app uses for telemetry, storage and compression.
- [research/camera_tracking_and_slam/orb_slam/android](../research/camera_tracking_and_slam/orb_slam/android/README.md): why most Android SLAM ports are not ready to use.
