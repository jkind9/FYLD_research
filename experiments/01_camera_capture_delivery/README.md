# Layer 1: camera capture and delivery

This folder (experiment 01) is layer 1 of the five-layer pipeline described in the [root README](../../README.md). It answers: **can a phone record what the other layers need, and get it to wherever those layers run?** It does not compute depth, camera position or objects. It supplies the raw material for all of them, so its mistakes, such as wrong timestamps or missing calibration, show up as errors in every later layer.

**Status:** the WSL Android build route produced a verified arm64 print-only smoke APK and a separate native Camera2 APK handoff. The Redmi app has now run and returned a valid capability report. It exposes one rear camera and one front camera, with no advertised simultaneous-camera sets. The received session has no image captures; a separate rear-camera control export is still needed. Other layers use public benchmark recordings as a stand-in.

## How capture works

A useful capture is more than a video file. Each frame needs:

| Item | What it is | Why later layers need it |
|---|---|---|
| Image | The original frame, uncompressed or lightly compressed | Everything starts here. Heavy video compression smears edges that depth and tracking rely on. |
| Capture time | When the sensor took the frame, with its clock source and units | Depth, motion sensors and a second camera are paired by time. Arrival time on a server is a different number and must be kept separately. |
| Calibration | Focal length and image centre in pixels, lens distortion, and for two lenses the offset between them in metres | Turns pixels into directions and distances. Calibration is only valid for the image size it was measured at, so crops and resizes must be recorded. |
| Motion sensors (IMU) | Accelerometer and gyroscope readings, typically 100–500 per second | Help the camera tracker through fast turns and blur, and give the direction of gravity. |
| Phone's own estimates | ARCore's camera position, depth and confidence for each frame, if used | A ready-made stand-in for layers 2 and 3 on the phone, and a comparison for our own methods. |

Phones change images in ways that matter for measurement. Autofocus changes the focal length slightly. Image stabilisation shifts the picture. Most phone sensors read out row by row (rolling shutter), so fast motion bends straight lines. For measurement, lock focus and exposure and turn stabilisation off where the phone allows it, and record the settings used.

**Using two lenses at once.** Android groups physical lenses behind a "logical" camera. Whether an app may stream two rear lenses at the same moment is decided by the manufacturer for each phone. Android's [multi-camera API](https://developer.android.com/media/camera/camera2/multi-camera) reports it. Having three rear lenses does not mean stereo is available, so this must be checked on both phones before stereo depth is planned around them.

**ARCore.** Google's augmented-reality toolkit can track the phone and provide depth on supported devices. Its [Recording and Playback API](https://developers.google.com/ar/develop/recording-and-playback) records camera video and motion-sensor data in an MP4. It does not guarantee that every API output, such as depth maps or camera poses, is stored automatically. The default CPU image used for tracking is 640×480; the high-resolution GPU display texture is not recorded. A recorder must explicitly save any additional fields needed for later replay and check that they survive playback. Google's current [supported-device table](https://developers.google.com/ar/devices) lists Redmi Note 11 Pro with Depth API support. Xiaomi's [official device guide](https://alsgp0.fds.api.xiaomi.com/xiaomi-b2c-i18n-upload/user-guides/1c100fb724c5e54a94ff40e423c5d7ef.pdf) identifies the supplied Redmi code `2201116TG` as Redmi Note 11 Pro. This makes ARCore a supported-device candidate, not a runtime or measurement result. The Samsung handset is not confirmed available, and the received Redmi APK did not include ARCore. See the [24-row API inventory](../../research/arcore/README.md). No project phone has produced an ARCore measurement.

**Delivery.** The safest pattern is save first, upload later: record to the phone, check the file, then upload over Wi-Fi with file hashes so losses are detected. Live streaming is a separate, harder condition. It adds dropped frames and delay, and needs capture time kept apart from arrival time.

**Capture technique.** Walk slowly, overlap views, film the same spot from different positions, and return to the start at the end. Revisits let the tracker correct drift. [Construction capture guidance](../../research/sources/19_construction_capture_guidance.md) covers this for real sites.

## Methods: hosted and on the phone

In the **hosted** route the phone only records and uploads; everything else runs on a server. In the **on-phone** route the phone also runs quick offline checks. Capture itself always happens on the phone.

| Method | Route | What it gives | Notes |
|---|---|---|---|
| ARCore recorder app (Kotlin) using [Recording and Playback](https://developers.google.com/ar/develop/recording-and-playback) | Both | Camera video, IMU and explicitly saved ARCore fields | Possible future recorder. It needs the SDK, owner approval and a separate scoped task. The default recording does not guarantee saved depth or pose; replay and field persistence must be verified. |
| [Camera2](https://developer.android.com/media/camera/camera2) or [CameraX](https://developer.android.com/media/camera/camerax) native app | Both | Full-resolution frames, manual focus and exposure, choice of physical lens, two-lens attempts | Needed for stereo and for high-resolution captures. |
| [OpenCamera Sensors](https://github.com/MobileRoboticsSkoltech/OpenCamera-Sensors) | Both | Research recorder that saves video with synchronised IMU readings | Existing open-source option to compare against; check its licence and current Android support. |
| [python-for-android](https://github.com/kivy/python-for-android) app with a native Java Camera2 Activity (current build route) | On the phone | Camera capability checks, single-camera control, advertised concurrent-set attempts and ZIP export | Warm-built arm64 APK verified and staged. A Redmi capability report exists, but the staged APK's on-device single-image export and the clean/container builds remain unverified. [Chaquopy](https://chaquo.com/chaquopy/doc/current/android.html) is the main alternative for Python inside a normal Android app. |
| Upload to a server, for example behind FYLD's existing [BentoML](https://docs.bentoml.com/) serving | Hosted | Resumable upload of recordings with hashes | Keep capture time and upload time separate. |
| Live streaming ([WebRTC](https://webrtc.org/), RTSP) | Hosted | Frames arrive while filming | Later condition; measure loss and delay separately from algorithm time. |
| Calibration with [Kalibr](https://github.com/ethz-asl/kalibr) or OpenCV ChArUco boards | Setup step | Measured lens and lens-to-IMU calibration for each phone | Checks the calibration the phone reports. |

## Top 5 sources

| Source | What it is | Why it matters here |
|---|---|---|
| [ARCore Recording and Playback](https://developers.google.com/ar/develop/recording-and-playback) | Google's API for saving and replaying an ARCore session | One file holds images, IMU, camera position and depth from the phone. |
| [Android multi-camera API](https://developer.android.com/media/camera/camera2/multi-camera) | Official documentation for using several lenses | Decides whether phone stereo is possible on each handset. |
| [ARCore supported devices](https://developers.google.com/ar/devices) | Google's list of phones and their ARCore features | Both test phones are listed with depth support. |
| [MobiDepth](../../research/sources/01_mobidepth.md) | Research on stereo depth from two phone cameras | Explains lens differences and timing problems on real phones. |
| [Construction capture guidance](../../research/sources/19_construction_capture_guidance.md) | Evidence about taking useful site photos | How to film a site so later layers can reconstruct it. |

## What can be improved

- **Write a capability report for both phones**: exact model and variant, camera IDs, which lens pairs can stream together, ARCore depth availability and supported image sizes.
- **Build the ARCore recorder first.** It is the quickest way to get real phone data with depth and camera position into layers 2 to 5.
- **Calibrate each phone** with a ChArUco board or Kalibr, and compare against the calibration the phone reports.
- **Measure timing**: the offset between camera and IMU clocks, frame drops, and the gap between two lenses if stereo is possible.
- **Add on-site capture checks**: warnings for blur, dark frames, fast motion, tracking loss and unfilmed areas.
- **Make upload robust**: resumable transfer, hashes on both ends, and a clear record of anything lost.

The sections below are the detailed experiment record: the test plan, the Android build environment and the build handover.

## Experiment record

[Task 08](../../task_list/archive/08_check_phone_capture_feasibility_alongside_reconstr.md) is the early phone-feasibility check. Run it alongside supplied-input reconstruction; camera limitations do not block the dataset control. Record support before committing to handset stereo, with alternative depth inputs explicitly identified.

## The piece we are testing

Can a phone provide camera observations that another component can use, from a saved recording or a live connection? This piece owns obtaining and delivering observations. It does not estimate depth or camera movement.

The confirmed phone is a Redmi Note 11 Pro 4G, model 2201116TG, running Android 13 with 6 GB RAM and a Helio G96 processor. Its exported report confirms model 2201116TG and Android 13; RAM and processor are owner-reported. USB debugging and file transfer were enabled, but Xiaomi's Install via USB setting required a SIM and workstation USB transfer was not verified. The Samsung S23 is not confirmed available. The Redmi's reported camera inventory provides no advertised simultaneous-camera set.

## Development inputs and references

The Redmi capability report is available in the local session below. A verified original image capture is still missing from the received evidence. The Samsung S23 is a separate possible test device, but its availability is unconfirmed. A public driving dataset cannot establish which camera combinations, timing or calibration the Redmi exposes.

Delivery can be developed independently by replaying the acquired Middlebury quarter-resolution image pairs under `data/middlebury/dataset/MiddEval3/trainingQ/`. Compare delivered files and frame identifiers with the originals, including their file hashes, ordering and loss records. These files test delivery; their lack of capture timestamps does not test live camera synchronization. The replay bundle and interruption tests still need to be implemented. [Acquisition records](../../data/README.md).

## Input and output agreement

The output is a saved observation bundle, with an optional live delivery path producing the same format. Each image needs a camera identifier, dimensions, orientation and capture timestamp. Record timestamp units, clock origin and whether cameras share a clock. Keep delivery time separate from capture time.

Calibration describes focal lengths and principal point in pixels, distortion, and the relative camera transform with translation in metres. Declare which camera frame the transform maps from and to. Missing calibration is explicit. Preserve original images and any crop, resize or rotation description so later geometry can reproduce processing.

The existing `validate_export` remains able to read capability-only reports with
no images. `validate_phone_session_export` is stricter: it requires a real image
and a passing single-camera check whose frame details match the exported files.
The shared phone-session reader checks the image bytes and reported size, then
keeps the camera intrinsics with the sensor grid, crop, rotation and capture
time. Android's distortion-correction mode changes which active array defines
crop coordinates. When that mode is ON or unavailable, the reader preserves the
raw calibration but marks it not ready for metric geometry. Missing depth and
pose stay explicit. The tests use generated images; they do not prove that the
Redmi has produced a valid recording.

## Proposed steps and comparisons

### Python test app on the phones

The user selected [python-for-android](https://github.com/kivy/python-for-android) as the planned packaging route. It can bundle Python and its dependencies into an installable Android package (APK). The first deliverable is a small foreground test app that runs Python experiments and saves results, rather than the full mapping pipeline.

Use Python for workstation build checks, test sequencing and result review. The current camera prototype uses a custom Java Activity at `native/camera/java/org/fyld/capture/CameraActivity.java` and calls Camera2 directly. Its pinned profile is `build/camera-profile.json`; it adds only camera permission and does not include PyJNIus or ARCore. A Redmi capability report has been returned, but the current staged APK's rear-camera still export has not been verified on a phone. The report contains no captured images. On 6 October 2026, the Windows check found no ADB command, no `ANDROID_HOME` or `ANDROID_SDK_ROOT`, and no ADB executable in the usual per-user SDK location. The pinned WSL SDK does include ADB at `/home/jkind/Android/Sdk/platform-tools/adb`, but `adb devices -l` returned no devices and `usbipd list` showed no Android handset. The SDK has no emulator binary or configured virtual device. The phone is not attached to this test path now; its ability to connect and capture remains unknown. Packaging Python does not bypass the handset's camera restrictions.

The first app should enumerate camera identities and capabilities, save that report, obtain camera permission, record a single-camera control and then attempt a supported pair. Save original images and capture metadata locally before adding stream delivery. If using a small Kivy interface, keep it limited to starting tests, showing status and exporting results. Native libraries such as OpenCV require a supported cross-compilation recipe; verify dependency support before adding them. The backend receiver can use desktop OpenCV independently.

### Workstation build environment

The selected build route now runs in Ubuntu 24.04.4 on WSL2. This prepares the workstation for APK builds, but does not prove either phone exposes compatible cameras.

| Tool | Installed version | Check |
|---|---|---|
| Host Python | 3.12.3 | p4a installed in an isolated virtual environment |
| python-for-android | 2026.05.09, release commit `58d21141f17c889bf8585f5665921d72028f8831` | GitHub release marks the commit signature verified; PyPI wheel SHA-256 `79a58606a78ed3cec1aba110876a414d4aa988f082385d68393e208d009e1e94` |
| OpenJDK | 17.0.20.1 | From Ubuntu's signed package repositories; required by Android Gradle Plugin 8.11.0 |
| Android command-line tools | revision 15859902 | Publisher SHA-256 `4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583` |
| Android SDK platform | API 36 | Installed from Google's SDK repository |
| Android build-tools | 35.0.0 | Installed from Google's SDK repository |
| Android platform-tools | 37.0.1 | Installed from Google's SDK repository |
| Android NDK | r28c, `28.2.13676358` | Publisher SHA-1 `a7b54a5de87fecd125a17d54f73c446199e72a64`; API 24 compile target |
| Gradle wrapper | 8.14.3 | p4a release template pairs it with Android Gradle Plugin 8.11.0, which requires Gradle 8.13 or newer; wrapper archive SHA-256 `ed1a8d686605fd7c23bdf62c7fc7add1c5b23b2bbc3721e661934ef4a4911d7c` |
| Android Python recipe | 3.14.2 | Version pinned by the selected p4a release; distinct from host Python 3.12.3 |

The command-line tools and NDK archives, both Gradle archives, and the p4a wheel were checked against publisher values before extraction or installation. The SDK manager installed API 36, build-tools 35.0.0 and platform-tools from Google's repository. The p4a release template uses Android Gradle Plugin 8.11.0 and Gradle 8.14.3. Android's compatibility table lists Gradle 8.13 as the minimum for plugin 8.11, so the selected wrapper is compatible.

Two no-device checks passed. NDK clang compiled an ELF64 AArch64 Android shared library for API 24. p4a built a minimal debug APK for `arm64-v8a`; APK signature verification passed, and its manifest reports min API 24 and target API 36. The smoke APK and build files are kept in the WSL home directory. No emulator or GPU was used.

The p4a repository identifies its code licence as MIT. Dependencies, copied Android samples and helper code need their own licence records. The smoke APK confirms workstation packaging only. It contains no camera implementation, and neither target phone has been connected or tested. Google's current command-line tools report that `sdkmanager` is deprecated and recommend `android sdk` for future SDK maintenance.

### Alternative implementation routes

The user is open to alternatives to Python packaging. [Chaquopy](https://chaquo.com/chaquopy/doc/current/android.html) embeds Python in a standard Android Gradle application and documents Windows build-host configuration. A small native Camera2 layer could capture original images while Python coordinates tests. Compared with p4a, this is a useful build-environment alternative; it still needs camera lifecycle handling and separately verified package support. Review exact plugin/SDK compatibility and code terms before selecting a revision. Nothing has been installed.

A minimal native Kotlin/Java test app based on [Android's camera APIs](https://developer.android.com/media/camera/camera2/multi-camera), with all analysis in desktop Python, is another option. This avoids packaging numerical libraries on the phone for the capture-only experiment. It is my proposed first fallback if p4a's bridge or build setup becomes the main obstacle. Keep saved observations identical whichever app route supplies them.

OpenCV receiving is a separate choice. Two readable stream URLs can feed separate desktop readers, but do not establish synchronization, calibration or physical-camera availability. The Android/native bridge question must be verified on the actual phones before committing to a streaming implementation.

### Capture and delivery controls

A local browser page can provide an earlier check of camera permission, preview, lens selection and sending video to a workstation. Camera access in the browser requires a secure page; a phone opening a workstation's LAN address needs HTTPS with a certificate the phone trusts. The page can stream through WebRTC or send recorded chunks to a local service. This does not report Camera2 concurrent-camera sets or the sensor and calibration fields required here, so it cannot establish stereo feasibility. See [MDN's camera API](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) for the browser security requirement and [CameraManager](https://developer.android.com/reference/android/hardware/camera2/CameraManager#getConcurrentCameraIds()) for native concurrent-camera support.

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

## Android package build and offline handoff

[Task24](../../task_list/closed/24_recover_and_reproduce_android_apk_build_inside_cap.md) owns the first-party p4a build and export helpers in `build/`, the package-only app in `app/main.py`, the native compile control in `native/smoke.c`, and build checks in `tests/`. Its cached WSL packaging route passed; clean dependency and container builds remain follow-ups. The app only prints `42`. It requests no camera permission and does not inspect camera or depth APIs. Task08 owns the separate capability and capture app.

The reproduced route reused Android libraries already built on this workstation (a warm build). It uses Ubuntu 24.04.4, host Python 3.12.3, Java 17.0.20.1, python-for-android (p4a) `2026.05.09`, Android SDK API 36, build tools 35.0.0, NDK `28.2.13676358` and Gradle 8.14.3. The APK verifies as package `org.fyld.toolchainsmoke`, version `0.1` (10241), minimum Android API 24, target API 36, and 64-bit ARM (`arm64`) only. The final run took 27.34 seconds. Its SHA-256 is `2a1f1f821408d637cbb8416e465b273245c5813013a73684f7f70dab45fc26e5`; the packaged source matches `app/main.py` SHA-256 `58a44735ffdfa6b14977516ad6e6e642d477999cd361537028f2d6b99e07ad68`; the debug certificate SHA-256 is `45e634374292b269842a381e50dc1bb08d6b30db388ed4572a880d9b1670e1c3`. Signature, package metadata, arm64 native libraries and the 68-entry compressed Python bundle passed verification.

This workstation's inputs are `/home/jkind/.venvs/p4a-2026.05.09` (p4a environment), `/home/jkind/Android/Sdk` (SDK and NDK), `/home/jkind/android-prep` (read-only predecessor source/distribution), and `/home/jkind/.gradle` (read-only Gradle cache copied into scratch). The successful run used `/tmp/fyld-task24-20261004-reviewed` for scratch and wrote its local handoff to `/mnt/c/Users/jkind/Documents/02_Work/01_fyld/mobile_depth_estimation_tracking/mobile deployment/smoke_20261004_reviewed/`.

The command for that run was:

```sh
wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-apk.sh \
  --p4a-env /home/jkind/.venvs/p4a-2026.05.09 \
  --sdk /home/jkind/Android/Sdk \
  --predecessor-root /home/jkind/android-prep \
  --gradle-cache /home/jkind/.gradle \
  --scratch /tmp/fyld-task24-20261004-reviewed \
  --output-root '/mnt/c/Users/jkind/Documents/02_Work/01_fyld/mobile_depth_estimation_tracking/mobile deployment' \
  --run-id 20261004_reviewed --mode warm
```

The exact verifier commands and their outputs are preserved in the handoff's `verification.json`. The debug APK is signed for testing, not for release.

The local offline handoff is in `mobile deployment/smoke_20261004_reviewed/`. It contains the APK, `verification.json` and installation notes. The directory is ignored by Git so generated APKs and signing material are not committed. Transfer the APK to the handset, install it, and open it to check the package launch; this is only a packaging smoke test, not a camera test.

The separate fresh dependency build, limited to already-cached downloads, stopped because the `sdl2_image` recipe lacks its JPEG source archive and attempted a network clone. The build blocked network access, so no source was downloaded. Docker was available, but no local image matched Ubuntu 24.04.4, Python 3.12.3 and Java 17.0.20.1; no image was downloaded and no container build was claimed. Task24 remains in review with the container route as an explicit follow-up. Task08 can use the verified cached route meanwhile.

Task08's native Camera2 APK was built from the pinned Java source with that cached WSL toolchain. The offline bundle is `mobile deployment/camera_20261004_camera_redmi_run6/`. Its APK is `unnamed_dist_1-debug.apk`, SHA-256 `35e2c420e38d3b857747ac255a1fd7f81791959c3e44d0a99911913af149c29a`; the receipt verifies package `org.fyld.capturecheck`, version `0.1` (10242), minimum API 24, target API 36, arm64 only, the CAMERA permission and launcher `org.fyld.capture.CameraActivity`. This is a warm cached build, not a clean dependency or container build. The Redmi was not connected during packaging. Its later on-device capability export is recorded below; the report does not attest the installed APK's version or binary hash.

### Task52 camera-source build, 6 October 2026

The first warm build stopped at Java compilation because `CameraReport.java` declared `rect(Rect)` twice. The duplicate was removed and that source's profile hash was updated. The second warm build passed in WSL in 29.00 seconds. Its bundle is `mobile deployment/camera_task52_camera_java_review_20261006_02/`. The APK SHA-256 is `d7b2242e5e601ce73d82205f99c5884a75addbc167fdf2a2ed4135bdbe308545`. `verification.json` reports a verified build, package `org.fyld.capturecheck`, version `0.1` (10242), minimum API 24, target API 36, arm64 only, and the CAMERA permission. It confirms the Java source hashes match `build/camera-profile.json`. This verifies packaging only; installation, capture, report recovery and physical image export remain unverified.

All 110 Task24 tests passed in WSL. Branch coverage across the five build modules was 82%, and Ruff passed. Run project tests through `python -B tools/check.py ...`; it checks that `task_list/` contains only task records before starting pytest, then removes its temporary test directory on exit. All test paths in `pytest.ini` are included. `.gitignore` also catches accidental pytest scratch folders. The separate Task13 scratch directory is retained as historical evidence.

## Redmi device result, 5 October 2026

The supplied folder `session-1791186245035_f881c553` was moved unchanged into [the local capture run](runs/redmi/session-1791186245035_f881c553/report.json). Generated runs stay outside Git. The phone records creation at 07:44:05.030 UTC and export at 07:44:27.522 UTC; its wall clock was not independently checked. The existing `app/capture_report.py` export validator passes, and the device, camera inventory and concurrent-set fields agree between the two JSON files.

| Evidence | Result |
|---|---|
| Handset | Xiaomi/Redmi 2201116TG, device `viva`, product `viva_eea`, Android 13/API 33, build `TP1A.220624.014` |
| Checks | Camera inventory, concurrent-camera inventory and permission PASS; advertised-pair attempt SKIPPED because no sets are advertised; ARCore depth/pose SKIPPED because this APK lacks the SDK |
| Exposed cameras | ID `0` rear and ID `1` front, both FULL hardware level with realtime timestamp source; neither exposes physical-camera IDs or synchronization metadata |
| Streams | RAW_SENSOR, JPEG, PRIVATE, YUV_420_888 and numeric format `842094169` (unidentified by the app); no DEPTH16 stream advertised |
| Rear calibration fields | Intrinsics `[2872.360595703125, 2872.361083984375, 2000, 1500, 0]`; zero distortion and translation; rotation `[1, 0, 0, 0]`. These are reported characteristics, not independent calibration or a stereo baseline |
| Front calibration fields | Intrinsics, distortion and lens pose unavailable |
| Capture evidence | `captures` is empty and no `single_camera_control` check appears; the only declared payload is `capabilities.json` |

| File | Bytes | SHA-256 |
|---|---|---|
| `capabilities.json` | 39,856 | `523aea34acef64831bc46f8325e4179ee0ee4077d97fb4390342c0ccd5961cdd` |
| `report.json` | 86,469 | `af98ca47aade243ec4fde470f930932cc096da623aae3ae24be1fe649fab9a27` |

The capabilities file matches its report-declared hash and size. The report hash above was computed at workstation intake; the report has no separate signature. A completed session means the selected operation finished and saved, including a skipped pair attempt. It does not mean the full capture task passed. This result establishes no advertised concurrent route through this app's Camera2 inventory; it does not prove every vendor camera route or ARCore depth is unavailable.

For the next check, press **Capture one rear-camera control**, then immediately **Export latest session**. The app starts a new session for each capture action and exports only the latest one, so export each result separately. Return that bundle with its JPEG and sensor metadata for integrity validation. Keep this capability/pair-attempt report. Measured frame timing, original image quality, independent calibration, sustained recording and Samsung checks remain outstanding. ARCore runtime depth, confidence and pose need a separately approved SDK-enabled test.

## Current delivery ownership, 6 October 2026

[Task52](../../task_list/open/52_build_and_verify_a_usable_phone_recording.md) owns a usable phone recording with images, calibration, timestamps and explicit available/missing depth and motion data. [Task57](../../task_list/open/57_deploy_and_measure_the_useful_edge_workload.md) owns early device feasibility and the sustained useful workload. Task08 capability evidence and Task24 smoke packaging remain bounded groundwork, not completed deployment. [Task51](../../task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md) records the hardware, workload and acceptance limits before execution.

Xiaomi's official guide identifies model `2201116TG` as Redmi Note 11 Pro, and Google's current ARCore supported-device list marks Redmi Note 11 Pro as supporting the Depth API. Together these sources make ARCore depth worth testing on the reported phone, but they do not prove that ARCore installs, starts or returns usable depth on its current software. The existing Camera2 APK does not include ARCore. A read-only WSL check found no cached `com.google.ar` dependency, attached ADB device, emulator or AVD; USB passthrough also showed no Android phone. The absence of a Camera2 `DEPTH16` stream does not test ARCore's motion-based depth path.

## Walkthrough input boundary

Step 1 of the canonical runner uses `experiments.shared.phone_session.read_phone_session` with `app.capture_report.validate_phone_session_export`. It validates recorded images, hashes, calibration and clocks while preserving absent depth and pose. Capture/readiness remains Task52 work. See [the six-step runner](../../src/walkthrough/README.md) for saved-input lifetimes and failure behavior.
