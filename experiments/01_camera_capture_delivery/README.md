# Experiment 01: camera capture and delivery

[Task 08](../../task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md) is the early phone-feasibility check. Run it alongside supplied-input reconstruction; camera limitations do not block the dataset control. Record support before committing to handset stereo, with alternative depth inputs explicitly identified.

## The piece we are testing

Can a phone provide camera observations that another component can use, from a saved recording or a live connection? This piece owns obtaining and delivering observations. It does not estimate depth or camera movement.

The available devices are a Samsung S23 and a Redmi Note 11 Pro. Record the Redmi's exact model and 4G/5G variant before testing. Installing a native test application is acceptable. Neither device is assumed to expose a usable simultaneous rear-camera pair.

## Development inputs and references

Camera capture is developed against recordings and capability reports from the Samsung S23 and Redmi Note 11 Pro. These recordings do not exist yet; collecting them is part of this experiment. A public driving dataset cannot establish which camera combinations, timing or calibration these phones expose.

Delivery can be developed independently by replaying the acquired Middlebury quarter-resolution image pairs under `data/middlebury/dataset/MiddEval3/trainingQ/`. Compare delivered files and frame identifiers with the originals, including their file hashes, ordering and loss records. These files test delivery; their lack of capture timestamps does not test live camera synchronization. The replay bundle and interruption tests still need to be implemented. [Acquisition records](../../data/README.md).

## Input and output agreement

The output is a saved observation bundle, with an optional live delivery path producing the same format. Each image needs a camera identifier, dimensions, orientation and capture timestamp. Record timestamp units, clock origin and whether cameras share a clock. Keep delivery time separate from capture time.

Calibration describes focal lengths and principal point in pixels, distortion, and the relative camera transform with translation in metres. Declare which camera frame the transform maps from and to. Missing calibration is explicit. Preserve original images and any crop, resize or rotation description so later geometry can reproduce processing.

## Proposed steps and comparisons

### Python test app on the phones

The user selected [python-for-android](https://github.com/kivy/python-for-android) as the planned packaging route. It can bundle Python and its dependencies into an installable Android package (APK). The first deliverable is a small foreground test app that runs Python experiments and saves results, rather than the full mapping pipeline.

Use Python for test sequencing, result recording and optional delivery. Access Android camera APIs through the Java bridge [PyJNIus](https://python-for-android.readthedocs.io/en/latest/apis.html), adding a small Java helper if camera callbacks or lifecycle handling require it. This bridge is a proposed implementation route, not a tested dual-camera wrapper. Packaging Python does not bypass the handset's camera restrictions.

The first app should enumerate camera identities and capabilities, save that report, obtain camera permission, record a single-camera control and then attempt a supported pair. Save original images and capture metadata locally before adding stream delivery. If using a small Kivy interface, keep it limited to starting tests, showing status and exporting results. Native libraries such as OpenCV require a supported cross-compilation recipe; verify dependency support before adding them. The backend receiver can use desktop OpenCV independently.

On this Windows workstation, plan a verified Linux build environment with Android SDK/NDK and Java. The [official quickstart](https://python-for-android.readthedocs.io/en/latest/quickstart.html) directs Windows users to a Linux virtual machine. WSL is a possible environment to investigate, but an installed executable does not establish a usable distribution or build toolchain. Pin the packaging and SDK versions after checking their compatibility; the quickstart contains examples from different tool versions, so do not copy those numbers blindly.

The p4a repository identifies its code licence as MIT. Dependencies, copied Android samples and helper code need their own licence records. No build environment, APK or phone test has been completed in this plan.

### Alternative implementation routes

The user is open to alternatives to Python packaging. [Chaquopy](https://chaquo.com/chaquopy/doc/current/android.html) embeds Python in a standard Android Gradle application and documents Windows build-host configuration. A small native Camera2 layer could capture original images while Python coordinates tests. Compared with p4a, this is a useful build-environment alternative; it still needs camera lifecycle handling and separately verified package support. Review exact plugin/SDK compatibility and code terms before selecting a revision. Nothing has been installed.

A minimal native Kotlin/Java test app based on [Android's camera APIs](https://developer.android.com/media/camera/camera2/multi-camera), with all analysis in desktop Python, is another option. This avoids packaging numerical libraries on the phone for the capture-only experiment. It is my proposed first fallback if p4a's bridge or build setup becomes the main obstacle. Keep saved observations identical whichever app route supplies them.

OpenCV receiving is a separate choice. Two readable stream URLs can feed separate desktop readers, but do not establish synchronization, calibration or physical-camera availability. The Android/native bridge question must be verified on the actual phones before committing to a streaming implementation.

### Capture and delivery controls

1. Identify both phones and inspect accessible camera combinations through native APIs.
2. Save a single-camera control recording. Attempt simultaneous rear-camera capture.
3. Check view overlap, timing differences and whether focus, zoom or stabilization changes geometry.
4. Save dual-camera observations locally before attempting live delivery to a PC or hosted endpoint.
5. Compare saved and delivered observations. Attribute losses and image changes to the correct stage.

## Measurements, failures and decision

Report accessible pairs, calibration availability, capture rate, timing differences, missing frames, payload sizes and capture-to-receipt delay. Record sustained behaviour and device configuration. Strong connectivity does not settle synchronization or camera availability.

Test denied permission, disconnection, interrupted recording, restart and unsupported camera pairs. Failure must leave an identifiable incomplete session.

Decide which device and capture route supplies reproducible inputs. Agree numeric acceptance limits before running trials. Recorded capture may be usable while live delivery needs further work.

## Research and reuse

[MobiDepth](../../research/sources/01_mobidepth.md) and [HiMoDepth](../../research/sources/02_himodepth.md) explain lens and timing differences. They do not establish support on these phones. [Construction capture guidance](../../research/sources/19_construction_capture_guidance.md) motivates overlapping views from approved safe positions.

## Camera and streaming leads supplied during planning

The simplest receiving experiment can open two supported stream URLs in separate OpenCV readers. [VideoCapture's official reference](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html) supports video stream URLs with suitable installed backends. This requires a phone application or service to publish each stream first. Two readers do not synchronize capture; preserve capture timestamps and pair images by those timestamps, not PC read order.

| Lead | What it helps investigate | What remains unproven |
|---|---|---|
| [Official Android camera samples](https://github.com/android/camera-samples) | Current camera API examples, including a concurrent front/back preview | Usable simultaneous rear-camera stereo on either phone; stream publishing and calibration |
| [Front/rear Camera2 article](https://medium.com/better-programming/simultaneous-front-and-rear-camera-preview-in-android-using-camera2-api-d9f2eb9af6b5) | User-supplied implementation lead | Article content was unavailable in this review; no technical claims adopted |
| [libuvc discussion](https://stackoverflow.com/questions/42849639/merging-multiple-camera-streams-on-android-using-libuvc) | Discussion of two external USB cameras and combining frames | Built-in phone camera access; the question is not a demonstrated solution for these devices |
| [ADB/OpenCV article](https://medium.com/@alessandroroat/extending-opencv-videocapture-a-seamless-approach-to-android-video-streaming-via-adb-faffb6e8403c) and [author source](https://github.com/alexroat/opencv-adbvideocapture/blob/main/ADBVideoCapture.py) | Screen-video delivery into OpenCV through Android Debug Bridge (ADB) | Original dual-camera observations: the source runs screenrecord and captures the display |
| [scrcpy camera documentation](https://github.com/Genymobile/scrcpy/blob/master/doc/camera.md) | A separate direct-camera mirroring lead with camera selection | Concurrent usable stereo, capture metadata export and a compatible OpenCV receiving adapter |

Keep original camera images separate from display previews. Front/back views, stitched previews and screenshots do not become calibrated overlapping stereo merely because they arrive together. No linked sample has been installed or executed on either handset. Check the exact revision and code terms before reuse; article access does not establish a code licence.

Promote the observation format and reader when another experiment consumes them unchanged. Keep phone and network adapters separate. This is the device-dependent piece; the other pieces can start with datasets or analytic fixtures without these phones. See the [dataset plan](../datasets/README.md) and [experiment guide](../README.md). This plan has not been executed.
