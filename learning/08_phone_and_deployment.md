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

> **Project status (14 October 2026).** Two partial apps exist: the check app (colour, ARCore outputs, no motion sensors, live stream) and the raw recorder (lossless grey, motion sensors, ARCore poses, no depth). Task95 merges them into one capture app. The first test walk goes through a house, down and back up the stairs, which is a known hard case for ARCore (chapter 11).

## What is still unmeasured

- ARCore's pose, depth and point accuracy on the Redmi (Tasks 52 and 75).
- Any model's speed, memory, heat and battery on the phone (Task57).
- Whether a real site walk (sunlight, mud, moving people, repeated textures) tracks as well as the indoor benchmarks.

## Try it

`experiments/01_camera_capture_delivery/README.md` describes the Android capability export that has run on the Redmi, and what a usable phone recording must contain (images, calibration, clocks, depth, motion data).

## Further reading

- [research/phone_ar_platforms](../research/phone_ar_platforms/README.md): ARCore notes, raw depth, Apple RoomPlan, the RealityCheck drift paper.
- [research/camera_tracking_and_slam/orb_slam/android](../research/camera_tracking_and_slam/orb_slam/android/README.md): why most Android SLAM ports are not ready to use.
