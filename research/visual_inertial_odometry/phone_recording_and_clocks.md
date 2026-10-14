# Recording camera and motion sensors on one clock on Android

Notes of 14 October 2026 for Task88, the raw recorder that feeds the open-source replacement of ARCore (Stream B). A visual-inertial tracker fuses camera images with gyroscope and accelerometer readings, so it needs every reading's time on one clock, to about a millisecond. This note records what Android and ARCore promise about those clocks, what published phone recorders found, and how the project measures the offset that is left.

## What Android and ARCore promise

| Fact | Exact wording or value | Source |
|---|---|---|
| Motion-sensor timestamps | "The time in nanoseconds at which the event happened. For a given sensor, each new sensor event should be monotonically increasing using the same time base as SystemClock.elapsedRealtimeNanos()." | Android `SensorEvent.timestamp` (AOSP source, frameworks/base, `core/java/android/hardware/SensorEvent.java`, read 14 October 2026) |
| Camera timestamps, REALTIME source | Camera timestamps "are in the same timebase as SystemClock.elapsedRealtimeNanos, and they can be compared to other timestamps using that base" | Android `CameraMetadata.SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME` (AOSP source) |
| Camera timestamps, UNKNOWN source | Monotonic nanoseconds that "can not be compared to timestamps from other subsystems (e.g. accelerometer, gyro etc.)"; roughly the `uptimeMillis` base | same |
| What a camera timestamp marks | "the time at start of exposure of first row of the image sensor active array" | Android `CaptureResult.SENSOR_TIMESTAMP`, quoted in the MARS logger paper |
| Uncalibrated gyroscope | rad/s; "No gyro-drift compensation is performed. Factory calibration and temperature compensation is still applied"; values[3..5] are the drift estimate | Android `SensorEvent` documentation for `TYPE_GYROSCOPE_UNCALIBRATED` |
| Uncalibrated accelerometer | m/s^2; values[0..2] "without bias compensation"; values[3..5] are the bias estimate | Android `SensorEvent` documentation for `TYPE_ACCELEROMETER_UNCALIBRATED` |
| Rates above 200 Hz | Apps must declare the `HIGH_SAMPLING_RATE_SENSORS` permission to read sensors faster than 200 Hz | Android `SensorManager` class documentation (AOSP source) |
| The Redmi's camera clock | Rear and front cameras report the REALTIME timestamp source | Task08 capability report, experiments/01_camera_capture_delivery/README.md |
| ARCore shared camera | Session created with `Session.Feature.SHARED_CAMERA`; the app's own `ImageReader` is added with `setAppSurfaces` "to receive additional images when ARCore is active"; camera opened with ARCore's wrapped callbacks; ARCore resumed in the capture session's `onActive`; the app must not issue its own repeating request while ARCore is active | [ARCore camera sharing guide](https://developers.google.com/ar/develop/java/camera-sharing); [SharedCamera reference](https://developers.google.com/ar/reference/java/com/google/ar/core/SharedCamera) |
| ARCore default streams | One YUV CPU stream, "currently always 640x480", and one GPU stream, typically 1920x1080; mid-tier phones support either two YUV streams plus a GPU stream, or one YUV stream, a GPU stream and an occasional still | ARCore camera sharing guide |
| ARCore's camera pose | "OpenGL camera pose with +X pointing right, +Y pointing up, and -Z pointing in the direction the camera is looking"; "the camera pose at the center of exposure of the center row of the image" | [ARCore Camera.getPose()](https://developers.google.com/ar/reference/java/com/google/ar/core/Camera) |
| ARCore's frame timestamps | `getAndroidCameraTimestamp()` returns "the (Android Camera timestamp) of the image"; `getAndroidSensorPose()` returns "the pose of the Android Sensor Coordinate System in the world coordinate space for this frame" | [ARCore Frame reference](https://developers.google.com/ar/reference/java/com/google/ar/core/Frame) |
| ARCore focus | Default focus mode on supported devices is currently FIXED | [ARCore Config.FocusMode](https://developers.google.com/ar/reference/java/com/google/ar/core/Config.FocusMode) |

Consequence: on a phone whose camera reports REALTIME, camera and motion-sensor timestamps share a clock base, but a camera timestamp marks the start of exposure of the first row while the image is centred later. ARCore's pose is placed at the centre of exposure of the middle row. For a perfectly aligned phone the two therefore differ by half the exposure time plus half the rolling-shutter readout time (the time the sensor takes to read all rows).

## What published phone recorders found

| Source | Finding | Relevance |
|---|---|---|
| Huai, Zhang, Yilmaz, "The Mobile AR Sensor Logger for Android and iOS Devices", arXiv 2001.00470 (2019, submitted to IEEE Sensors 2019). Saved: [papers/mars_logger_huai_2019_2001.00470.pdf](papers/mars_logger_huai_2019_2001.00470.pdf) (local only) | Records Camera2 frames at about 30 Hz with focus distance, exposure and rolling-shutter skew per frame, IMU at 50-100 Hz, accelerometer interpolated at gyroscope times. If the camera clock is not the boot clock, records `System.nanoTime()` and `elapsedRealtimeNanos()` at start and end to convert. Online calibration (VINS-Mono, MSCKF) on five phones found camera-IMU time offsets "up to 30 ms" and frame readout times of about 5-30 ms, before allowing for start-of-exposure stamps and rolling shutter | Same recording design as Task88, independently built. The 30 ms figure is why the offset is measured, not assumed. The app's code is GPL-3.0 (F-Droid listing), so Task88 does not copy it |
| Faizullin, Kornilova, Akhmetyanov, Ferrer, "Twist-n-Sync: Software Clock Synchronization with Microseconds Accuracy Using MEMS-Gyroscopes", Sensors 21(1):68, 2021, doi 10.3390/s21010068 ([open access](https://www.mdpi.com/1424-8220/21/1/68); PDF not saved: the publisher refuses scripted downloads) | Two rigidly joined phones are twisted for a few seconds; the time offset is found by cross-correlating their gyroscope signals, then refined; the authors report microsecond-level accuracy | The method family used by Task88's clock check, here between the gyroscope and the rotation ARCore sees through the camera |
| OpenCamera Sensors, Skoltech ([GitHub](https://github.com/MobileRoboticsSkoltech/OpenCamera-Sensors)) | Android recorder of video with synchronised IMU, from the same group | An existing alternative recorder; not used, because ARCore poses must be recorded alongside |

## How Task88 measures the offset

1. **Same clock base.** The app stores `elapsedRealtimeNanos()` and `System.nanoTime()` when recording starts and stops. The first camera, gyroscope and accelerometer stamps must lie within 1 s of the start stamp. A camera on the `uptimeMillis` base would sit away from it by the time the phone has slept since boot.
2. **ARCore saw the same images.** Each ARCore row stores `getAndroidCameraTimestamp()`. On one shared capture session every buffer of a capture carries the same timestamp, so these must equal saved image stamps exactly.
3. **Offset.** ARCore's camera rotation between consecutive frames gives an angular speed at each frame-pair midpoint. The gyroscope's angular speed, averaged over one frame interval, is compared at lags from -200 to +200 ms in 1 ms steps; the best normalised correlation, refined with a parabola, is the offset (positive: the gyroscope stamps a motion later than the camera). Subtracting half the exposure and half the readout leaves the camera-to-IMU clock offset. Tests recover synthetic shifts of +12 and -20 ms to within 1 ms.

ARCore's own pose already depends on its internal calibration, so this is a check, not a calibration. Kalibr measures the offset independently in the calibration task.

## Patent note

Nothing here comes from inside ARCore: only Android and ARCore public interfaces and published papers. Recording ARCore's output as a reference does not copy its design. No design here touches the two Google patents named in [../phone_ar_platforms/arcore_open_replacement.md](../phone_ar_platforms/arcore_open_replacement.md) (US 10,802,147 concurrent odometry and mapping; US 11,145,075 depth from motion).
