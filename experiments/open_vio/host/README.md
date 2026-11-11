# Recording reader and clock check

This folder reads a session recorded by the FYLD capture app, checks it, and converts it for the open tracking and calibration tools. It belongs to the [open visual-inertial tracking experiment](../README.md).

A recording is a phone session v2 folder, as written by the PC capture receiver (now in `apps/receiver/`; the readers for the same format are in [`sitescan/session/`](../../../sitescan/session/README.md)). Every camera and motion-sensor time is an integer in nanoseconds on the phone's `elapsedRealtime` clock.

| File | What it does |
|---|---|
| `recording.py` | `load(root)` reads a session into a `Recording`. `problems(rec)` lists faults: missing files, timestamps that do not increase, a stream on another clock, images without metadata, ARCore frames that match no image, a recording that did not stop cleanly. `to_euroc(rec, out)` writes the EuRoC/ASL layout (`mav0/cam0`, `mav0/imu0`) that Basalt, Kimera-VIO, OKVIS2 and Kalibr read, plus `arcore_camera_tum.txt`, ARCore's camera path in OpenCV axes. `tracking_poses` and `arcore_match_fraction` are helpers. |
| `clock_check.py` | `report(rec)` checks that the camera, gyroscope and accelerometer share one clock and measures the camera-to-gyroscope offset. It cross-correlates the gyroscope's angular speed with the angular speed of ARCore's camera rotation. `estimate_offset` does the correlation. |

The offset in `camera_imu_clock_offset_ms` is what remains after removing half the exposure and half the readout time, because ARCore stamps the middle of the exposure and Camera2 stamps the start of the first row.

## How to run it

Run from the repository root with the project environment. CPU only, no phone needed once a session folder exists.

```text
.venv/Scripts/python.exe experiments/open_vio/host/recording.py <session folder> [--euroc <output folder>]
.venv/Scripts/python.exe experiments/open_vio/host/clock_check.py <session folder>
```

`recording.py` prints the problems it finds and exits with status 1 when there are any. `clock_check.py` writes `clock_check.json` into the session folder. The calibration scripts in [`../calibration/`](../calibration/README.md) import `recording.py` from here.

## Where results are recorded

Clock-check results, the Redmi walk and the host-tool descriptions are in the [open_vio README](../README.md).
