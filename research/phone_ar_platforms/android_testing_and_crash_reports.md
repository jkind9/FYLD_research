# Android testing and crash reports

Checked 14 October 2026. Task97 follows the first Redmi capture trials: checks passed, but Record walk terminated the app. USB debugging is unavailable to the owner. The PC retained one attempt without camera frames and another with 100 frames. Neither establishes a usable house recording.

## Tests on an Android Virtual Device

An Android Virtual Device (AVD) is the Android Emulator's saved device configuration. Android documents testing across Android versions, network conditions and virtual sensors: [Android Emulator](https://developer.android.com/studio/run/emulator).

Google's [ARCore emulator instructions](https://developers.google.com/ar/develop/java/emulator) require an x86 or x86_64 image at API 27 or later, a VirtualScene rear camera, and the emulator version of Google Play Services for AR. These instructions support ARCore testing; they do not establish that this app's shared-camera and raw-depth combination works on the emulator. That combination has not been tested here.

Google's [shared-camera guide](https://developers.google.com/ar/develop/java/camera-sharing) says additional camera surfaces increase device demands and calls for testing on the devices users will use. An AVD can exercise app controls, permissions, lifecycle and transport; Redmi camera timing, sustained sensor rates, thermal behaviour and Wi-Fi speed still need device measurements.

Proposed by Claude, not owner-ruled: add an Android 13/API 33 AVD first to match the Redmi, then API 36 to check the app's target version. Keep the existing JVM tests and WSL APK build. No emulator was installed by Task97.

## Diagnostics without USB

[Thread.UncaughtExceptionHandler](https://developer.android.com/reference/java/lang/Thread.UncaughtExceptionHandler) receives an uncaught Java exception and its thread. The app can save that stack before delegating to Android's original handler. This does not catch native process crashes, forced termination or every out-of-memory failure.

[ActivityManager.getHistoricalProcessExitReasons](https://developer.android.com/reference/android/app/ActivityManager#getHistoricalProcessExitReasons(java.lang.String,%20int,%20int)) exposes recent process exits. [ApplicationExitInfo.getTraceInputStream](https://developer.android.com/reference/android/app/ApplicationExitInfo#getTraceInputStream()) can return ANR traces; API 31 and later can also return native-crash tombstones as protobuf bytes. Android may have overwritten a trace, so null is a valid result.

The diagnostic app reports its own recent exit timestamps (wall-clock milliseconds), reason codes, status and descriptions. Available trace bytes are encoded as base64 without treating a binary tombstone as text. Its saved Java exception includes the crashing version, thread, timestamp and full cause chain. On reopening, these diagnostics use the existing LAN report connection to the capture receiver. A local Java trace is retained after sending. The receiver saves reports under its output folder's `reports/` directory.

Task97 adds evidence collection. It does not claim the Record walk crash is fixed. The owner must install the diagnostic APK as an update, reproduce the failure and reopen the app to send its report. Existing Java crashes cannot acquire a retroactive Java stack from the new handler; historical system exit details may still exist.

## Received exception and Task99 fix

The local report `20261014T215846_901_2201116TG.json` contains the saved capture 1.1 exception: a `NullPointerException` in `SessionMessages.encode`, called by `DiskQueue.add` and `FrameWriter.write`. The crashing thread is `frame-writer`. Reopening uploaded the report; another reproduction was not needed.

Android's [AOSP JSONObject implementation](https://android.googlesource.com/platform/libcore/+/refs/heads/main/json/src/main/java/org/json/JSONObject.java) catches a serialization `JSONException` in the no-argument `toString()` and returns null. Its `toString(int)` overload propagates the exception. JSON number serialization rejects NaN and infinity. The received stack establishes the null serialization result; it does not identify the offending numeric field. Synthetic tests reproduce invalid point projections and overflowing pixel coordinates as a route to that failure.

Capture 1.2 filters unprojectable points and non-finite confidence values, and converts serialization exceptions into the existing queue write-error path. All 30 JVM tests pass, including the three regressions. The Redmi subsequently completed 1,194 frames over 39.88 s without a crash or reported dropped frame. This is device evidence for that recording, not a guarantee for every future session.
