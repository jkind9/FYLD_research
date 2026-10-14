# Replacing ARCore with open-source or hand-built parts

Map of 14 October 2026. The owner asked what would have to be rebuilt or slotted in where ARCore is used, so the product does not depend on Google. Licences were read from each project's own licence file or GitHub's licence record on 14 October 2026. How ARCore works is in [arcore_internals.md](arcore_internals.md); its terms are in [arcore_commercial_terms.md](arcore_commercial_terms.md).

## Two rules for the open rebuild

1. **Build from published methods, not from ARCore.** The Google APIs Terms (§4) forbid reverse engineering, and the ARCore library itself (the `.aar` the app links) is not open source: the SDK's licence file puts the binaries under the ARCore Additional Terms and only the sample code under Apache-2.0.
2. **Check patents before copying a specific design.** Google holds patents on ARCore's designs, for example concurrent odometry and mapping (US 10,802,147 B2) and depth from motion (US 11,145,075 B2). Open-source licences do not grant rights to other parties' patents. Using established open methods (MSCKF-style filters, sliding-window optimisation, learned depth) is the normal route, but a product needs a freedom-to-operate check by someone qualified.

## Function-by-function map

| ARCore gives | What it does | Open replacement | Licence (checked) | Notes |
|---|---|---|---|---|
| Camera frames and timestamps | Images at 30 fps with capture times | Android Camera2 API | Android platform | The Redmi reports a realtime timestamp source (same clock as the motion sensors), from the Task08 capability report |
| Motion-sensor readings | Gyroscope and accelerometer at hundreds of Hz | Android SensorManager | Android platform | Must share the camera's clock; the time offset between them still needs calibrating |
| Calibration | Camera intrinsics, camera-to-IMU rotation and offset, time shift, sensor noise | Kalibr (offline, with a printed target) | BSD-3-Clause | Per phone model; some VIO systems refine it online |
| Pose in metres, with gravity | Visual-inertial odometry | Basalt VIO | BSD-3-Clause | Permissive; strong published accuracy on EuRoC |
| | | Kimera-VIO | BSD-2-Clause | Permissive; part of a larger mapping stack |
| | | OKVIS2 | BSD-style (3-clause text) | Permissive; keyframe-based, loop closure |
| | | OpenVINS, VINS-Mono, VINS-Fusion | GPL-3.0 | Reference only, like ORB-SLAM3 |
| Pose without motion sensors (fallback) | Visual SLAM, no size | stella_vslam | BSD-2-Clause | Measured here: 17-28 mm, 5-8 ms per frame on a desktop CPU (Task84) |
| | | ORB-SLAM3 | GPL-3.0 | Reference only; measured 12.8-26 mm (Task84) |
| Revisits (loop closure) | Recognise a place and correct the path | DBoW2 or FBoW for place recognition | DBoW2 BSD-style; FBoW MIT | Used inside ORB-SLAM3 and stella_vslam |
| Map refinement | Joint optimisation of poses and points | Ceres Solver or g2o | Ceres BSD-3-Clause; g2o BSD (some optional parts LGPL) | |
| Depth images | Depth from motion on one CPU core | Learned depth resized per frame to tracked points or to stereo-from-motion depth | Depth Anything V2 Small Apache-2.0; OpenCV (stereo matching) Apache-2.0 | Tasks 72 and 78 show resizing to tracked points works on recorded data |
| Running models on the phone | | ONNX Runtime; LiteRT | MIT; Apache-2.0 | ZipDepth's phone build already exports to ONNX (Task62) |
| Planes | Flat surfaces from feature points | RANSAC plane fit on map points | Own code (Task55) or Open3D (MIT) | |
| Anchors | Keep objects fixed when the path is corrected | Store positions relative to keyframes and re-express them after each correction | Own code | |
| Install and device check | Google Play Services for AR | Not needed | — | Works on phones without Google Play, on managed devices and in China |

## What makes the rebuild hard

- **Camera and motion-sensor timing on Android.** Visual-inertial systems need the two clocks aligned to about a millisecond. Ports of research systems name this as the main obstacle on Android.
- **Per-phone calibration.** Every phone model needs its camera-to-IMU calibration and sensor noise; ARCore ships these for supported devices.
- **Rolling shutter and autofocus.** Phone cameras read rows over time and refocus; most research VIO assumes fixed focus and handles rolling shutter partly or not at all.
- **Start-up and robustness.** ARCore starts tracking within seconds and recovers from blur and fast turns; research systems are less forgiving (OpenVINS took 35-40 s to initialise in one study).
- **Porting to the phone.** The candidates are desktop C++; each needs an Android NDK build and a sustained-speed check.

## A route that keeps ARCore as the reference

ARCore's shared-camera mode lets an app read Camera2 images while ARCore runs. A recorder that saves raw camera frames, motion-sensor readings and ARCore's poses together gives, in one walk, both the inputs an open VIO system needs and ARCore's answer to compare against. Open systems can then be run offline on these recordings (as Task84 did for stella_vslam and ORB-SLAM3) before any is ported to the phone.

Stream B started on 14 October 2026 in [experiments/open_vio/](../../experiments/open_vio/README.md). Step 1, the recorder, and what Android and ARCore promise about clocks: [../visual_inertial_odometry/phone_recording_and_clocks.md](../visual_inertial_odometry/phone_recording_and_clocks.md).

## Sources

- Licence files: [Basalt](https://gitlab.com/VladyslavUsenko/basalt/-/raw/master/LICENSE), [Kimera-VIO](https://github.com/MIT-SPARK/Kimera-VIO), [OKVIS2](https://github.com/ethz-mrl/OKVIS2), [OpenVINS](https://github.com/rpng/open_vins), [VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion), [VINS-Mono](https://github.com/HKUST-Aerial-Robotics/VINS-Mono), [stella_vslam](https://github.com/stella-cv/stella_vslam) (LICENSE.fork and LICENSE.original, both BSD-2), [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3), [Kalibr](https://github.com/ethz-asl/kalibr), [Ceres](https://github.com/ceres-solver/ceres-solver), [g2o](https://github.com/RainerKuemmerle/g2o), [DBoW2](https://github.com/dorian3d/DBoW2), [FBoW](https://github.com/stella-cv/FBoW), [Open3D](https://github.com/isl-org/Open3D), [OpenCV](https://github.com/opencv/opencv), [ONNX Runtime](https://github.com/microsoft/onnxruntime), [LiteRT](https://github.com/google-ai-edge/LiteRT), [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2), [ARCore SDK](https://github.com/google-ar/arcore-android-sdk/blob/main/LICENSE).
- Initialisation times: RD-VIO (arXiv 2310.15072), via the SLAM review of 14 October 2026.
