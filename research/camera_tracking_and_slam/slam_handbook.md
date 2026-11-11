# SLAM Handbook (Carlone, Kim, Barfoot, Cremers, Dellaert, eds.)

Read 7 November 2026. The owner judged it essential reading for this project. This note records what it covers, what it changes for the project and what it cannot answer.

## Source

- **Repository:** [SLAM-Handbook-contributors/slam-handbook-public-release](https://github.com/SLAM-Handbook-contributors/slam-handbook-public-release). The whole book is one PDF, `main.pdf`, 669 pages.
- **Status:** a pre-publication draft for Cambridge University Press, released in parts for public feedback (Part 1 November 2024, Part 2 March 2025, Part 3 May 2025). No licence is stated on the repository page.
- **Local copy:** `papers/slam_handbook_2026.pdf`, downloaded 7 November 2026. It is gitignored like every third-party PDF in this repository.
- **Page numbers below** are the book's printed page numbers. The PDF page is the printed page plus 16.

## Chapters and their use here

| Chapter | Topic | Use in this project | Read |
|---|---|---|---|
| 1 | Factor graphs | The common language of every later chapter | Background |
| 3 | Robustness to incorrect data association and outliers | Deciding which object a new sighting belongs to: the cause of the live overcount | **Before any counting redesign; not yet read** |
| 5 | Dense map representations | Surface fusion; TSDF against points and meshes; observed against unobserved space | Section 5.5 read |
| 7 | Visual SLAM | Monocular tracking, metric scale, combining vision with an IMU | Section 7.8 read |
| 11 | Inertial odometry | Visual-inertial odometry (VIO), calibration, clock alignment, motions where scale is lost | Section 11.4 and Table 11.1 read |
| 13 | Boosting SLAM with deep learning | DROID-SLAM and feed-forward 3D models (GPU, so not usable now) | Later |
| 14 | Differentiable volume rendering maps | NeRF and Gaussian splatting | Later, for display work |
| 15 | Dynamic and deformable SLAM | Moving people and vehicles on site | Section 15.2 opening read |
| 16 | Metric-semantic SLAM | Objects as landmarks in the map; 3D scene graphs | Sections 16.1-16.2 opening read |
| 17 | Open-world spatial AI | Objects named in plain text ("traffic cone") | Later, for counting |
| 18 | Computational structure of spatial AI (Davison) | Mapping the workload onto phone and edge hardware | Later, for on-phone work |
| 8-10, 12 | Lidar, radar, event cameras, legged robots | Not relevant to a phone | Skip |

## What it confirms

1. **Camera plus motion sensors is the standard design.** A single camera cannot recover real-world scale. An IMU (gyroscope and accelerometer) supplies scale and the direction of gravity, so only 4 unknowns remain (x, y, z and heading) instead of 7 (section 7.8, p. 220-221). ARCore and Basalt both work this way; Basalt and OKVIS2 are among the systems named.
2. **TSDF fusion suits noisy depth.** A TSDF (truncated signed distance field) stores each surface as a distance on a voxel grid. Section 5.5 (p. 146) says it fuses noisy depth better than points or meshes, which are "more sensitive to the quality of the depth measurements". The project's live fusion already uses Open3D's TSDF volume (`sitescan/fusion/fragments.py`).
3. **Matching objects after tracking is one recognised approach.** Chapter 16 describes the alternative: objects become landmarks with a class, pose, scale and shape, optimised together with the camera path (Definition 16.1, p. 456).

## What it changes for the project

1. **A published drift benchmark.** "A good VIO system has a drift below 1% of the distance traveled ... and in some cases the drift can be as low as 0.1%" (section 11.4.1, p. 327-328). On a 50 m site walk, 1% is 0.5 m. This gives the accuracy-target discussion (Task61) and the tape-measured ARCore walks (Task75) a reference point.
2. **Motions that hide scale.** Table 11.1 (p. 326) lists motions where a single camera with an IMU cannot recover some quantities. Constant acceleration hides the overall scale. Pure rotation, and moving straight towards a point, hide the distance to that point. The capture guide should ask walkers to vary their motion and avoid turning on the spot. Task110 checks the recorded walks for these motions.
3. **Calibration does not scale to field workers.** Calibration with a printed target is the more accurate method, but "can be cumbersome and undesirable in some scenarios where the final system is expected to be used at large scale by non-experts" (section 11.4.2, p. 329). Calibration estimated while the system runs avoids the procedure but "can be less accurate". This is a risk for the open-source route, which needs a calibration per phone.
4. **Clock alignment after the fact is the weaker method.** Stamping each sensor's data and aligning the times afterwards "is generally less accurate and robust" than hardware or protocol sync. Online systems can instead estimate the time offset as a state (section 11.4.3, p. 329-330). The project's -2.67 ms camera-to-IMU offset came from after-the-fact alignment, with peak correlation 0.62.
5. **Moving objects.** IMU data is not fooled by motion in the scene, so it helps separate the phone's motion from moving objects. Robust estimation and segmentation masks are the other defences (section 15.2.1, p. 424-425). Every project recording so far is of a static scene.

## What it cannot answer

- **Phones.** A full-text search of all 669 pages finds zero mentions of "smartphone", "ARCore" or "ARKit". The book assumes dedicated sensors and, where possible, hardware clock sync.
- **This project's defects.** Why the 14 October house-walk reconstruction looks distorted is a question about this project's data and code. The 7 November probes (Task106) found that the walk's ARCore depth maps are all empty and that the phone was held in portrait throughout. No textbook can find those.
- **Constraints and goals.** CPU only, at least one update per second, worksite accuracy targets and street-works objects are outside its scope.

## Follow-up

- Read chapter 3 (data association) and the rest of chapter 16 before changing the counting rule.
- Read chapter 18 before any on-phone port (Task57).
