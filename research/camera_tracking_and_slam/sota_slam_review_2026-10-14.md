# State-of-the-art SLAM: accuracy and edge latency

Review of 14 October 2026. The owner asked what the current best SLAM methods are, for accuracy and for speed on edge hardware, after ruling that the deployed system must be live (or update at least once per second) and that the GPU stays off for now. Every number here is the cited authors' claim unless it says "measured here". Different papers use different sequences, hardware and settings, so numbers from different rows are not a fair ranking.

## Short answer

1. **Most accurate on short indoor video: learned and foundation-model SLAM.** DROID-SLAM, MASt3R-SLAM and newer foundation-model systems reach about 16-20 mm on TUM RGB-D. They need a desktop or Jetson-class GPU and run at 5-15 frames per second on a desktop GPU.
2. **Fastest per watt: classic feature-based SLAM and visual-inertial odometry (VIO).** ORB-SLAM3 runs at about 30 frames per second on a desktop CPU and 6-18 ms per frame on Jetson boards, with 1.5-2.5 times the error of the best learned systems on TUM.
3. **On an Android phone, the practical state of the art is the platform's own VIO (ARCore).** Running a research SLAM system on a phone is possible (ORB-SLAM2 ports report about 30 frames per second on recent Snapdragon chips), but camera-IMU synchronisation on Android is the stated obstacle for visual-inertial versions. ARCore solves that inside the platform, gives metres and gravity, and costs the app nothing to run. Its accuracy evidence is thin: about 0.02 m/s drift for the best of four commercial trackers in a 2022 study, and over 10 cm on phones in another.
4. **For this project's recorded-data tests on the CPU: ORB-SLAM3 (GPLv3, reference only, now allowed by the owner) and stella_vslam (BSD-2).** Both run live on a desktop CPU, accept monocular or depth input, and process frames in order, so they replace the offline SfM stand-in with something causal.

## Families

| Family | Examples | Typical hardware | Accuracy on TUM (published) | Speed (published) | Licence notes |
|---|---|---|---|---|---|
| Classic feature SLAM | ORB-SLAM3, stella_vslam (OpenVSLAM fork) | CPU | ORB-SLAM3 monocular 9 mm xyz, 17 mm desk (MASt3R-SLAM paper); 38 mm mean over 8 TUM sequences in a 2026 UAV study | ~30 fps desktop CPU; 6-18 ms/frame on Jetson | ORB-SLAM3 GPLv3; stella_vslam BSD-2 from v0.3 |
| Classic VIO | VINS-Mono, OpenVINS, Basalt, OKVIS2 / OKVIS2-X | CPU; IMU required | EuRoC ATE 0.25-0.33 m (VINS-Mono, ORB-SLAM3 VI, LEVIO paper) | OpenVINS tracking ~6 ms laptop, ~14 ms Jetson; full pipeline 16 / 53 ms (ACM 2024 study, from search summary) | VINS-Mono, OpenVINS GPLv3; Basalt BSD-3 |
| GPU-accelerated classic | cuVSLAM (NVIDIA), Jetson-ORB-SLAM3, GLidE-SLAM | NVIDIA GPU (cuVSLAM, Jetson); OpenGL ES (GLidE) | cuVSLAM: TUM RGB-D (mono + depth) RMSE APE 0.065 against ORB-SLAM3 0.067 | cuVSLAM mono 0.9 ms desktop, 2.7 ms Jetson AGX Orin per frame; Jetson-ORB-SLAM3 32 fps on Orin Nano; GLidE up to 9 times a CPU baseline | cuVSLAM is CUDA-only, licence to check; GLidE code not published |
| Learned SLAM / VO | DROID-SLAM, DPVO / DPV-SLAM | GPU | DROID 16 mm, DPVO 32 mm mean over 8 TUM sequences (2026 UAV study) | Desktop GPU 13 and 19 fps; Orin NX 68 and 29 ms/frame; DROID out of memory on a 2 GB Jetson Nano | BSD-3 / MIT |
| Foundation-model SLAM | MASt3R-SLAM, VGGT-SLAM 2.0, FoundationSLAM, AIM-SLAM, CUT3R (streaming reconstruction) | Large GPU | MASt3R-SLAM 16 mm desk, 9 mm xyz; FoundationSLAM claims first on 7 of 9 TUM sequences | MASt3R-SLAM ~15 fps RTX 4090, 5-7 fps RTX 3080 Ti; VGGT-SLAM 2.0 ~3.9 fps, 6.5 GB; CUT3R ~30 fps, 3.2 GB | Mostly non-commercial weights |
| Microcontroller VIO | LEVIO | GAP9 microcontroller, under 100 mW | EuRoC machine hall ATE average 3.46 m (ORB-SLAM3 0.25 m) | 20 fps, under 1 MB memory | Open source; licence to check |
| Platform VIO | ARCore (Android), ARKit (iOS) | The phone, built in | No TUM numbers. Best of four commercial trackers about 0.02 m/s drift (Kim et al. 2022); phones over 10 cm position error in a markerless AR study | Live at camera rate, no app compute | Google / Apple terms |

## Accuracy and speed from one comparison

The most direct same-protocol comparison found is a 2026 UAV deployment study ([arXiv 2605.03678](https://arxiv.org/abs/2605.03678)): five systems, the same 8 TUM RGB-D and 6 EuRoC sequences, desktop and four Jetson boards. Its tables have internal inconsistencies (for example DPVO is 18.6 fps in one table and 5.1 ms per frame on the same GPU in another), so treat it as indicative.

| | ORB-SLAM3 | DPVO | DROID-SLAM | DUSt3R | MASt3R |
|---|---:|---:|---:|---:|---:|
| TUM RGB-D ATE, mean of 8 (mm) | 38 | 32 | 16 | 21 | 18 |
| EuRoC ATE, mean of 6 (mm) | 87 | 38 | 20 | 24 | 19 |
| Desktop frames per second (RTX 3090; ORB-SLAM3 on CPU) | 28 | 19 | 13 | 9 | 6 |
| Jetson Nano 2 GB, ms per frame | 18 | 125 | out of memory | out of memory | out of memory |
| Jetson Orin NX, ms per frame | 8 | 29 | 68 | 95 | 143 |

The same study finds ORB-SLAM3 the only option without a GPU, but the least robust in degraded conditions (62% of runs tracked overall, 0% in dense haze).

## What it means for this project

| Question | Answer | Evidence |
|---|---|---|
| What tracks the camera on the phone? | ARCore's own VIO. Running our own SLAM on the phone would duplicate it, and visual-inertial research systems are hard to synchronise on Android. | Android ORB-SLAM2 port notes; ARCore feature inventory in [phone_ar_platforms/arcore](../phone_ar_platforms/arcore/README.md) |
| How good is ARCore? | Unknown on our handset; published evidence is thin and old. Measuring it is the most important open number. | Task75; Kim et al. 2022; RealityCheck 2021 |
| What replaces SfM on recorded data? | A live CPU SLAM run frame by frame: ORB-SLAM3 as the accuracy reference, stella_vslam as the permissive option. Monocular on TUM and ICL, scored causally. | This review; owner ruling 14 October 2026 |
| Is there a better live method if the GPU is allowed later? | DROID-SLAM or DPVO on a server GPU, or MASt3R-SLAM for dense output (non-commercial). cuVSLAM if NVIDIA hardware is used. | Tables above |
| Does a foundation model help on a phone? | Not now: the smallest still need GBs of GPU memory and run under 30 fps on desktop GPUs. | Table above |

## Gaps in the evidence

- No published head-to-head of ARCore against research SLAM on the same walk.
- No published per-frame timing of ORB-SLAM3, OpenVINS or Basalt on a Snapdragon phone; the closest are Jetson numbers.
- Most learned-SLAM speed numbers come from desktop GPUs; few report CPU or phone runs.

## Papers saved (local only, not in Git)

| File | Why |
|---|---|
| `papers/uav_vslam_multi_paradigm_deployment_2605.03678.pdf` | Same-protocol accuracy and Jetson latency for five systems |
| `papers/cuvslam_2506.04359.pdf` | GPU-accelerated classic SLAM; per-frame timing on desktop and Jetson |
| `papers/levio_embedded_vio_2602.03294.pdf` | VIO on a microcontroller; shows the accuracy cost of extreme efficiency |
| `papers/foundationslam_2512.25008.pdf` | Foundation-model SLAM claiming best TUM accuracy |
| `papers/glide_slam_gl_embedded_2607.16897.pdf` | Direct tracking on OpenGL ES compute shaders for embedded GPUs |

## Sources

- [Robust Visual SLAM for UAV Navigation: a multi-paradigm evaluation and deployment study (arXiv 2605.03678)](https://arxiv.org/abs/2605.03678)
- [cuVSLAM: CUDA accelerated visual odometry and mapping (arXiv 2506.04359)](https://arxiv.org/abs/2506.04359)
- [LEVIO: Lightweight Embedded Visual Inertial Odometry (arXiv 2602.03294)](https://arxiv.org/abs/2602.03294)
- [FoundationSLAM (arXiv 2512.25008)](https://arxiv.org/abs/2512.25008)
- [AIM-SLAM (arXiv 2603.05097)](https://arxiv.org/abs/2603.05097)
- [GLidE-SLAM (arXiv 2607.16897)](https://arxiv.org/abs/2607.16897)
- [Jetson-ORB-SLAM3 (arXiv 2608.17874)](https://arxiv.org/abs/2608.17874)
- [MASt3R-SLAM, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Murai_MASt3R-SLAM_Real-Time_Dense_SLAM_with_3D_Reconstruction_Priors_CVPR_2025_paper.pdf)
- [F2SLAM, runtime appendix for VGGT-SLAM 2.0 (arXiv 2610.05207)](https://arxiv.org/html/2610.05207) and [Geometric Context Transformer, CUT3R comparison (arXiv 2604.14141)](https://arxiv.org/html/2604.14141v1)
- [A Comprehensive Study of Systems Challenges in Visual SLAM Systems, ACM 2024](https://dl.acm.org/doi/10.1145/3677317) (numbers from the search summary; the page refused direct access)
- [XR-VIO (arXiv 2502.01297)](https://arxiv.org/abs/2502.01297) and [RD-VIO (arXiv 2310.15072)](https://arxiv.org/abs/2310.15072): initialisation times
- [Android ORB-SLAM2s](https://github.com/Olsc/Android_ORB-SLAM2s) (author's frame rates, unverified)
- [stella_vslam documentation](https://stella-cv.readthedocs.io/en/latest/overview.html)
- [Kim et al., A Benchmark Comparison of Four Off-the-Shelf Proprietary Visual-Inertial Odometry Systems, Sensors 2022](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9785098/)
- [Markerless AR tracking accuracy across phones (NSF PAR)](https://par.nsf.gov/servlets/purl/10358173)
