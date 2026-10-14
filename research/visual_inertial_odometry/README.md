# Visual-inertial odometry: the open-source replacement for ARCore's tracking

Visual-inertial odometry (VIO) follows a camera through space by fusing its images with gyroscope and accelerometer readings. The motion sensors give scale in metres and the direction of gravity, which images alone cannot. This folder holds the sources for Stream B: rebuilding ARCore's functions from open parts, starting 14 October 2026. The function-by-function plan with checked licences is in [../phone_ar_platforms/arcore_open_replacement.md](../phone_ar_platforms/arcore_open_replacement.md); the plain-language chapter is [learning/12_rebuilding_arcore.md](../../learning/12_rebuilding_arcore.md).

## Notes

| Note | What it covers |
|---|---|
| [calibration.md](calibration.md) | Kalibr, Basalt calibration and the Allan deviation; TUM-VI's calibration facts used as the reference; phone-specific traps (Task90) |
| [phone_recording_and_clocks.md](phone_recording_and_clocks.md) | Android camera and motion-sensor clocks, ARCore's shared-camera mode and pose conventions, published phone recorders, and how the project measures the camera-to-IMU time offset (Task88) |

## Papers

Saved locally on 14 October 2026; PDFs are not in Git. Paper results are the authors' claims.

| File | Why it is here |
|---|---|
| [mars_logger_huai_2019_2001.00470.pdf](papers/mars_logger_huai_2019_2001.00470.pdf) | MARS logger: an Android and iOS camera-plus-IMU recorder; phones showed camera-IMU time offsets up to 30 ms |
| [tumvi_schubert_2018_1804.06120.pdf](papers/tumvi_schubert_2018_1804.06120.pdf) | TUM-VI benchmark: sensors, calibration method, Allan noise values for a BMI160, tracker results; the reference for the calibration check |
| [double_sphere_usenko_2018_1807.08957.pdf](papers/double_sphere_usenko_2018_1807.08957.pdf) | The double-sphere fisheye camera model used by Basalt's calibration |
| (not saved) Kalibr, Furgale, Rehder, Siegwart, IROS 2013, pp. 1280-1286 | Continuous-time camera-IMU calibration with time offset; no open PDF found |
| (not saved) Twist-n-Sync, Sensors 21(1):68, 2021 | Gyroscope cross-correlation for clock alignment; [open access page](https://www.mdpi.com/1424-8220/21/1/68) |
