# 12. Rebuilding ARCore from open parts

Chapter 11 explained what ARCore does inside. This chapter follows the project's second development stream (Stream B, started 14 October 2026): replacing each of ARCore's functions with open-source or hand-built parts, so the product does not depend on Google. It starts with the part everything else rests on: getting camera images and motion-sensor readings onto one clock. Sources are in [research/visual_inertial_odometry/](../research/visual_inertial_odometry/README.md); the code is [experiments/open_vio/](../experiments/open_vio/README.md).

## What has to be rebuilt

| ARCore function | Open replacement | Section |
|---|---|---|
| Camera images and motion-sensor readings on one clock | Android's camera (Camera2) and sensor interfaces, recorded by the project's own app | below |
| Calibration of camera and motion sensors | Kalibr with a printed target | "Calibration" |
| Camera path in metres with gravity | An open visual-inertial odometry system: Basalt, Kimera-VIO or OKVIS2 | "Choosing a tracker" |
| Depth images | Learned depth resized to the tracker's points (chapter 5) | later |

Visual-inertial odometry (VIO) means tracking with camera and motion sensors together; chapter 11 explains why the two complement each other. Licences matter: anything that ships must have a permissive licence (BSD, MIT, Apache). GPL systems such as OpenVINS and ORB-SLAM3 are used only to compare against. The rebuild must come from published methods. Taking ARCore apart is forbidden by its terms, and Google holds patents on some of its designs, so any design that resembles them is noted for a patent check before launch.

## Why clocks matter so much

A VIO system predicts the camera's motion between two frames from the gyroscope and accelerometer, then checks that prediction against what the camera sees. If the motion-sensor readings are stamped 10 ms late compared with the images, the system compares the image with the wrong motion. Turning the phone at 90 degrees per second, 10 ms is 0.9 degrees, which at 640 pixels across a 65-degree view is about 9 pixels. Feature tracks are matched to about one pixel, so a 10 ms error is far larger than the measurement noise. Research systems want the two streams aligned to about a millisecond.

### What Android promises

- **Motion sensors** stamp every reading in nanoseconds on the `elapsedRealtimeNanos` clock (time since the phone booted, including sleep).
- **Cameras** report a *timestamp source*. REALTIME means the camera uses the same `elapsedRealtimeNanos` clock; UNKNOWN means a different clock that "can not be compared" with the sensors. The project's Redmi reports REALTIME for both cameras.
- **What a camera timestamp marks:** the start of exposure of the image's first row.

So on the Redmi the clocks share a base. That does not make them agree to the millisecond. The MARS logger study (Huai et al. 2019), which recorded five phones the same way, measured camera-to-motion-sensor offsets of up to 30 ms.

### Two effects that look like a clock offset

1. **Exposure.** The picture is collected over the exposure time (often 5-20 ms indoors). Its timestamp marks the start; the "average" moment of the picture is half an exposure later.
2. **Rolling shutter.** A phone sensor reads its rows one after another; the last row is read 10-30 ms after the first (the *readout time*, which Android reports as rolling-shutter skew). The middle row, where most of the picture's content sits on average, is half a readout later.

ARCore states its camera pose at "the centre of exposure of the centre row". So if the camera and gyroscope clocks agreed perfectly, ARCore's pose would still appear half an exposure plus half a readout later than the image timestamp. The project subtracts this to get the true clock offset.

## The raw recorder

The project's recorder app (Task88) saves, during one walk:

- every camera frame's grey image, 640 x 480, lossless, named by its timestamp;
- per frame: exposure time, readout time, focus distance, sensitivity and stabilisation mode;
- the gyroscope and accelerometer at the fastest rate the phone allows, in their *uncalibrated* form (Android's own bias correction can jump mid-walk, which a tracker would read as motion);
- ARCore's camera pose for each frame, as the reference answer.

ARCore and the app share the camera through ARCore's *shared-camera mode*: ARCore runs normally, and the same capture session sends a copy of every image to the app. The recording therefore holds both the inputs an open tracker needs and ARCore's answer for the same walk, without any extra equipment. A second mode records the motion sensors alone with the phone at rest, for calibration.

### Measuring the offset

The gyroscope measures how fast the phone turns. ARCore's poses also show how fast it turns: the rotation between two consecutive poses divided by the time between them. Both are curves of turning speed over time. Slide one curve along the other in 1 ms steps; the shift where they match best is the offset. This is the idea behind Twist-n-Sync (Faizullin et al. 2021), which aligns the clocks of two phones by shaking them together and matching their gyroscopes. The project's tests make a synthetic walk with a known 12 ms shift and check that the method finds 12 ms to within 1 ms.

Because ARCore's pose already depends on ARCore's own internal calibration, this measurement is a check, not the final number. Kalibr (next section) measures the offset independently, from the camera images and the gyroscope alone.

> **Project result (14 October 2026).** The recorder app builds and its host tools pass 19 tests on synthetic recordings. The first Redmi recording, with measured rates and offset, waits for the owner to install the app.

## Calibration

*Planned (step 2 of Stream B).* Kalibr (BSD-3) estimates, from a video of a printed grid of AprilTag markers, the camera's focal length, image centre and lens distortion; the rotation and offset between the camera and the motion sensors; and the time offset between them. It also needs each sensor's noise level and how fast its bias wanders, which come from a long recording with the phone at rest. ARCore ships these numbers for every supported phone; an open rebuild has to measure them per phone model.

## Choosing a tracker

*Planned (step 3).* Basalt (BSD-3), Kimera-VIO (BSD-2) and OKVIS2 (BSD-style) will run offline on the Redmi recordings, with OpenVINS (GPL-3.0) as a reference. Each is scored the way chapter 9 describes, against ARCore's poses and tape-measured distances, and timed per frame. The best is then ported to the phone.

## Try it

```text
python -m pytest experiments/open_vio/tests
python experiments/open_vio/host/clock_check.py <recording folder>
python experiments/open_vio/host/recording.py <recording folder> --euroc <output folder>
```

## Further reading

- [research/visual_inertial_odometry/phone_recording_and_clocks.md](../research/visual_inertial_odometry/phone_recording_and_clocks.md): exact Android and ARCore wording, the MARS logger and Twist-n-Sync papers.
- [research/phone_ar_platforms/arcore_open_replacement.md](../research/phone_ar_platforms/arcore_open_replacement.md): the function-by-function map with checked licences.
- Chapter 11 (inside ARCore) and chapter 3 (tracking and SLAM).
