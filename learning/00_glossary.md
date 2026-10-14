# Glossary

Terms used across the learning chapters, in alphabetical order. Each entry says what the term means and, where useful, where it shows up in this project.

| Term | Meaning |
|---|---|
| **Absolute trajectory error (ATE)** | How far each estimated camera position is from the true one, summarised as a root-mean-square error in metres. Computed after lining the two paths up (see *best fit*). |
| **AbsRel** | Absolute relative depth error: the mean of `|predicted − true| / true` over pixels. 0.07 means depth is off by 7% on average. |
| **ARCore** | Google's augmented-reality library on Android. Gives the phone's camera pose in metres (from camera plus motion sensors), depth images, and tracked 3D points. |
| **Baseline (stereo)** | The distance between two cameras, or between two positions of one camera, that see the same point. Longer baselines give better depth at range. |
| **Best fit (alignment)** | Rotating and shifting an estimated camera path so it lines up with the true path as closely as possible before measuring error. *Best fit with size* also fits one overall scale factor; it is the standard score for camera-only methods, which have no real-world size. |
| **Bundle adjustment** | Solving all camera poses and all 3D points together so that every point projects back onto the pixels where it was seen. The core of structure from motion and of most SLAM systems. |
| **Calibration (intrinsics)** | The numbers that describe a camera's lens and sensor: focal lengths `fx, fy` and image centre `cx, cy` in pixels, plus lens distortion. Needed to turn pixels into directions. |
| **Camera pose (extrinsics)** | Where a camera is (position) and which way it points (orientation) for one frame. Stored as a 4 × 4 matrix. *Camera-to-world* moves points from the camera's frame into the world; *world-to-camera* is its inverse. |
| **Coverage (surface)** | The share of a reference surface that has a reconstructed point nearby (5 cm in this project). Reported with accuracy because a small, accurate patch can hide a mostly missing room. |
| **Depth** | Distance from the camera to the surface seen at a pixel, measured along the camera's forward axis, in metres. |
| **Depth Anything** | A family of learned depth models. V2 Metric Small (25M parameters) is the project's main single-image depth model; Depth Anything 3 takes several images and optional camera poses. |
| **Disparity** | How far a point shifts sideways, in pixels, between two views. Depth = focal length × baseline ÷ disparity. |
| **Drift** | Slowly growing error in a camera path, because each small step's error adds to the last. |
| **Feature (keypoint)** | A distinctive, findable spot in an image, such as a corner, with a descriptor that lets it be recognised in another image. SIFT and ORB are classic types; ALIKED is learned. |
| **Frame** | One image from a video. Also used for a coordinate system ("camera frame", "world frame"); the meaning is clear from context. |
| **Fusion (TSDF)** | Combining many depth images into one surface. A truncated signed distance function (TSDF) stores, in each small cube of space (voxel), the averaged distance to the nearest surface. |
| **Global mapper (GLOMAP)** | A structure-from-motion method that solves all camera rotations, then all positions, then refines once. Faster than the incremental mapper on large sets. |
| **Ground truth / reference** | Independently measured answers used only to score a method: motion-capture camera paths, Kinect depth, a surveyed surface. Never fed to the method being tested. |
| **IMU** | Inertial measurement unit: the phone's gyroscope and accelerometer. Measures rotation and acceleration hundreds of times a second and gives the direction of gravity. |
| **Incremental mapper** | A structure-from-motion method that adds one image at a time and refines often. COLMAP's classic mapper. |
| **Loop closure** | Recognising that the camera has returned to a place it saw before, and correcting the whole path so both visits agree. Removes accumulated drift. |
| **Metric depth** | Depth in real metres. *Relative depth* has the right shape but an unknown size (and sometimes an unknown offset). |
| **Multi-view stereo (MVS)** | Computing dense depth for each frame by matching it against neighbouring frames whose poses are known. The step after structure from motion. |
| **Odometry (visual odometry)** | Working out how the camera moved between consecutive frames, frame by frame. Has no map and no loop closure, so it drifts. |
| **Point cloud** | A set of 3D points. *Sparse* (a few thousand tracked features) or *dense* (every pixel). |
| **Pose graph** | A graph whose nodes are camera poses and whose edges are measured motions between them. Optimising it spreads a loop-closure correction along the path. |
| **Relative pose error (RPE)** | Error of the motion over a short window (1 s here), which shows drift independently of where the path started. |
| **Reprojection error** | Distance in pixels between where a 3D point projects into an image and where it was actually seen. Bundle adjustment minimises it. |
| **Rolling shutter** | A camera sensor that reads its rows one after another rather than all at once. The last row is read 10-30 ms after the first on a phone (the *readout time*, reported by Android as rolling-shutter skew), so fast motion bends straight lines and each row has its own capture time. |
| **Scale ambiguity** | From images alone, a scene and every camera position can be made twice as large and still match the photos. Real size must come from somewhere else: a depth sensor, a known distance, or the IMU. |
| **Shared camera (ARCore)** | An ARCore mode in which ARCore tracks as usual while the app receives its own copy of every camera image from the same capture session. The project's raw recorder uses it to save images and ARCore's poses together. |
| **SfM (structure from motion)** | Recovering camera poses and 3D points together from overlapping images. Usually offline over all images at once. COLMAP is the standard tool. |
| **SLAM** | Simultaneous localisation and mapping: tracking the camera while building a map, usually live, with loop closure. |
| **TUM RGB-D** | A benchmark of Kinect colour-and-depth recordings with motion-capture camera paths. The project uses its `freiburg1_xyz` and `freiburg1_desk` recordings. |
| **ICL-NUIM** | A synthetic benchmark (rendered images) of a living room with exact camera paths and an exact 3D surface model. The project uses living room trajectory 2. |
| **Time offset (camera to IMU)** | How much later (or earlier) the motion sensors stamp a motion than the camera does. Visual-inertial trackers need it to about a millisecond; phones have shown up to 30 ms. Measured by matching turning speed seen by the gyroscope and by the camera. |
| **Timestamp source (Android camera)** | Which clock a phone camera stamps its images on. REALTIME is the same clock as the motion sensors (`elapsedRealtimeNanos`); UNKNOWN is a clock that cannot be compared with them. |
| **Triangulation** | Finding a 3D point from its pixel positions in two or more views with known poses. |
| **VIO (visual-inertial odometry)** | Tracking that combines camera images with the IMU. Gives metric size and gravity. ARCore works this way. |
| **Voxel** | A small cube of 3D space, the 3D version of a pixel. |
