# Dataset catalog

## Selection

TUM provides metric depth and independently recorded camera motion, so it isolates tracking and fusion without requiring a model download. It is an indoor Kinect benchmark, not a smartphone or construction-site validation. Dataset choice and licence choice are separate checks.

| Dataset | Input and reference measurements | Relevant test | Licence/status | Primary source |
| --- | --- | --- | --- | --- |
| TUM colour/depth | Kinect colour/depth, camera calibration and motion-capture trajectory | Tracking with supplied metric depth; oracle pose fusion | CC BY 4.0; Freiburg1 xyz downloaded and first 120 matched frames used | [Publisher](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) |
| EuRoC MAV | Synchronized monochrome stereo and inertial measurements; calibration; motion/structure reference | Stereo/inertial tracking and scale consistency | Permission unresolved; not downloaded | [Current ASL page](https://projects.asl.ethz.ch/datasets/euroc-mav/), [data DOI](https://doi.org/10.3929/ethz-b-000690084) |
| ETH3D | Separate stereo and colour/depth SLAM benchmarks | Dense geometry and tracking on varied scenes | CC BY-NC-SA 4.0; blocked for company use without permission; no downloads | [Current publisher](https://eth3d.ethz.ch/) |
| ICL-NUIM | Synthetic colour/depth, reference poses and surface geometry; clean/noisy variants | Surface reconstruction errors against an independent mesh | CC BY 3.0; optional, not downloaded | [Publisher](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html) |
| Consented project capture | Phone images, native depth where supported, poses, inertial data and independent dimensions | Outdoor work-area measurements and phone resource use | Not collected; define consent, ownership and retention first | Project-owned future data |

The current EuRoC index links the ETH Research Collection through DOI `10.3929/ethz-b-000690084`. The DOI fetch failed in this browsing session. The current download location is identified by the publisher, but a functioning archive URL and its terms remain unverified. Avoid obsolete ASL download paths.

## TUM ingest contract

The acquired Freiburg1 xyz archive is 448,204,271 bytes; acquisition checksums and timestamps belong in the dataset receipt. Colour and depth frames are paired within 20 ms. The used colour images are 640×480. Depth integers divide by 5000 to obtain metres, with zero treated as invalid. Pose translations are metres, quaternions are `qx qy qz qw`, and timestamps are Unix seconds. See the publisher's [formats and calibration](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

The baseline uses the publisher's recommended registered-image camera parameters: `fx=525`, `fy=525`, `cx=319.5`, `cy=239.5`. The Freiburg1 depth correction factor of 1.035 was already applied by the publisher and must not be applied again. Its [camera parameter page](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats#intrinsic_camera_calibration_of_the_kinect) explains the registration caveat.

An explicit world-up transform is not proof of measured gravity. The present run labels that distinction. Future phone captures must record camera calibration, pose direction, depth units, confidence, frame timestamps, display rotation and gravity alignment in a manifest. Independently measured dimensions must remain outside the estimation inputs when they are used for validation.
