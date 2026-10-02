# ORB-SLAM and current tracking research

Primary sources checked on 2 October 2026. ORB-SLAM3 should be a central reference for this project. It provides camera tracking, map reuse and recovery across several sensor configurations. Current research also includes learned trackers, dense image-only mapping and hardware acceleration. None of the checked sources establishes a single best method across accuracy, recovery, surface quality and phone runtime.

This review extends the [recovered Claude research](../session_recovery/README.md). It does not report a local algorithm comparison. No listed method was installed, downloaded or reproduced in this review. Published rates and errors below are author results under their stated conditions.

The [eight user-supplied sources](user_sources/README.md) cover lighting-based reconstruction, learned depth, dynamic scenes and Android demonstrations. The [dedicated Android review](android/README.md) separates native tracking from phone recording followed by desktop processing.

## The ORB-SLAM reference

[ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) is the official upstream implementation. Its [latest tagged release](https://github.com/UZ-SLAMLab/ORB_SLAM3/releases) remains `v1.0-release`, dated 22 December 2021, short commit `0df83dd`. That is a release identity, not a claim that the current default branch is unchanged. The [paper](https://arxiv.org/abs/2007.11898) appeared in IEEE Transactions on Robotics 37(6), pages 1874–1890, in 2021. A recently published fork is not automatically an official successor.

The system extracts repeatable image features (ORB features), tracks the camera against mapped landmarks, adjusts nearby camera poses and landmarks, detects revisits (loop closure), and maintains multiple maps when tracking cannot continue. The supported configurations include monocular, stereo and RGB-D cameras, with visual-inertial configurations and pinhole/fisheye models. These capabilities make it relevant to independently testing camera tracking before dense reconstruction. [Official implementation and paper](https://github.com/UZ-SLAMLab/ORB_SLAM3).

Camera-only monocular reconstruction does not independently establish metres. Calibrated stereo or metric depth supplies a scale route; camera-plus-IMU tracking requires correct calibration, timing and successful inertial initialization. Sparse landmarks are not a dense surface or an area measurement. The official setup recommends a powerful desktop CPU; it does not establish Android S23/Redmi performance. These limitations determine what to measure in the tracking and reconstruction experiments. [Paper](https://arxiv.org/abs/2007.11898), [official requirements](https://github.com/UZ-SLAMLab/ORB_SLAM3).

Code is GPLv3. The authors offer contact for a separately negotiated closed-source commercial version. GPL permits commercial activity subject to its conditions; it is not a noncommercial restriction. Distribution, dependencies and linking still require their own review. A Python wrapper does not alter those terms. [Licence section](https://github.com/UZ-SLAMLab/ORB_SLAM3#1-license).

## Relevant current alternatives

The comparison below separates estimating camera movement from producing dense geometry. A method that wins one question may be unsuitable for another.

| Method and primary sources | Input and output | Why include it | Compute and permission limits |
| --- | --- | --- | --- |
| ORB-SLAM3, [paper](https://arxiv.org/abs/2007.11898), [code](https://github.com/UZ-SLAMLab/ORB_SLAM3) | Calibrated images, optional depth/IMU; trajectory and sparse maps | Main classical tracking, recovery and revisit reference | C++/CPU upstream; GPLv3; no target-phone rate measured |
| OpenVINS, [documentation](https://docs.openvins.com/), [code](https://github.com/rpng/open_vins) | Camera/IMU; sparse tracks and visual-inertial odometry | Calibration, timing, initialization and uncertainty comparison | GPLv3. Standard estimator is odometry; optional loosely coupled loop closure does not update its underlying odometry state. No target-phone rate verified |
| Basalt, [code](https://gitlab.com/VladyslavUsenko/basalt), [tags](https://gitlab.com/VladyslavUsenko/basalt/-/tags) | Camera/IMU; odometry/mapping and calibration | Traditional visual-inertial alternative with permissive code terms | BSD-3 plus dependency terms. Current tag 0.1.7, 21 March 2026; no Android result verified |
| DROID-SLAM, NeurIPS 2021, [paper](https://arxiv.org/abs/2108.10869), [code](https://github.com/princeton-vl/DROID-SLAM) | Calibrated monocular/stereo/RGB-D; poses and dense depth | Strong learned tracking comparison | CUDA; README states at least 11 GB GPU memory for demos and 24 GB for some evaluations. BSD-3 code; weights/data separate. Monocular scale requires independent validation |
| DPVO / DPV-SLAM / DPV-SLAM++, [paper](https://arxiv.org/abs/2408.01654), [code](https://github.com/princeton-vl/DPVO) | Calibrated monocular images; tracked patches and trajectory | Learned tracking with lower-memory variants; distinguish odometry from enabled loop-closure SLAM | CUDA; MIT code, but loop dependencies and weights separate. Camera-only metric scale not established |
| MASt3R-SLAM, CVPR 2025 Highlight, [paper](https://arxiv.org/abs/2412.12392), [code](https://github.com/rmurai0610/MASt3R-SLAM) | RGB, optional calibration; dense geometry and poses | Learned reconstruction prior with tracking and loop closure | Paper 15 FPS; repository experiments RTX 4090 and release differences. CC BY-NC-SA 4.0 code plus separate checkpoint restrictions |
| VGGT-SLAM 2.0, [January 2026 paper](https://arxiv.org/abs/2601.19887), [code](https://github.com/MIT-SPARK/VGGT-SLAM) | Uncalibrated RGB; dense submaps and optimized trajectory | Current dense feed-forward comparison; official README reports RSS 2026 acceptance and June live-code release | Paper reports 8.4 unique keyframes/s on RTX 3090 with 16-frame submaps, without semantic inference; 3.5 keyframes/s on Jetson Thor with 4-frame submaps. These are not incoming camera rates. BSD-2 wrapper; [live script](https://github.com/MIT-SPARK/VGGT-SLAM/blob/main/main_realtime.py) uses original noncommercial VGGT-1B weights |

Learned geometry can help tracking without proving physical dimensions. Consistent submap alignment also does not establish independent metric scale. The listed learned methods need a known dimension, calibrated stereo/depth, or another verified scale source before supporting metres or square metres. This is a project evaluation requirement, not a claim that every method has the same scale behavior.

## New ORB-SLAM edge implementations

[Jetson-ORB-SLAM3](https://arxiv.org/abs/2608.17874), submitted 18 August 2026, is a particularly relevant new preprint. It accelerates the ORB front end on Jetson Orin Nano while keeping mapping/optimization on the CPU. The authors report 32 FPS mean over the eleven EuRoC sequences in monocular-inertial mode on a 7 W device, with mean trajectory errors within 0.10 cm between their four CPU/GPU/hardware configurations. These are author results and an accuracy-preservation claim, not proof that it beats all trackers or runs on a phone.

The [author repository](https://github.com/ClarityLab-Org/Jetson-ORB-SLAM3) exists and declares GPLv3, JetPack 6/Orin requirements and optional CosPlace/TensorRT loop closure. Its run script can automatically download EuRoC and use supplied binaries. Data permission and exact implementation version must therefore be checked before running it here. A Jetson is a nearby-server/embedded option; CUDA acceleration does not transfer directly to Android GPU hardware.

[FastTrack](https://arxiv.org/abs/2509.10757), IROS 2025 with a July 2026 arXiv revision, accelerates ORB-SLAM3 tracking with CUDA. Its abstract reports up to 2.8× improvement on desktop and Jetson Xavier NX in stereo-inertial tests on EuRoC and TUM-VI. Keep this as a hardware-optimization lead; code availability, terms and full accuracy/runtime conditions were not established in this review.

For splitting work across a network, the [recovery review](../session_recovery/README.md) covers Edge-SLAM, AdaptSLAM, COVINS-G and SwarmMap. These are distinct from accelerating one device's computation. ORB-SLAM2/3 underpins several of those systems, which strengthens its value as a common experimental reference.

## What the benchmark evidence actually supports

Two comparisons from the same papers are useful because their conditions are stated together. They should not be combined into a cross-paper league table.

| Source and comparison scope | Author-reported result | Interpretation |
| --- | --- | --- |
| [DPV-SLAM Table 1](https://arxiv.org/html/2408.01654v1), full Freiburg1 monocular TUM set, median of five trials; runtime on RTX 3090 | Mean trajectory error: DROID 0.038 m, DPV 0.076 m, DPV++ 0.054 m. GPU memory: 8.5/4/6 GB respectively; listed rates 30 FPS. | Memory/accuracy trade-off. ORB's failed sequences must remain failures; averaging only successful runs would favor a method unfairly. These aligned errors do not independently validate metric scale. |
| [VGGT-SLAM 2.0 Table I](https://arxiv.org/html/2601.19887v1), TUM, 32-frame VGGT submaps, separated by calibration availability | Calibrated: MASt3R 0.030 m, DROID 0.038 m. Uncalibrated: MASt3R 0.060 m, VGGT-SLAM 1.0 SL(4) 0.053 m, VGGT-SLAM 2.0 0.041 m. | VGGT 2.0's strongest accuracy claim belongs to the uncalibrated comparison. Supplying calibration changes the question and ranking. Timing above used different submap sizes. |

The original [ORB-SLAM3 paper](https://arxiv.org/abs/2007.11898) reports 3.6 cm stereo-inertial accuracy on EuRoC and 9 mm in TUM-VI handheld room sequences. Preserve these as historical author results with their sensor/scene conditions, not outdoor phone expectations.

For more realistic motion and scale, [LaMAria](https://arxiv.org/abs/2509.26639), ICCV 2025, provides a newer egocentric benchmark. The [official repository](https://github.com/cvg/lamaria) describes approximately 22 hours and 70 km of trajectories with survey-grade control points; it declares CC BY 4.0 for data/documentation and MIT for code. Head-mounted motions, lighting changes, dynamic environments and moving platforms make it useful beyond short indoor examples. Full reference coverage and method-specific failures must be read before an evaluation. The CVF PDF fetch returned 403 during this review; the arXiv and author repository were accessible. No numerical ranking is copied from search snippets.

## Candidate comparison plan for this project

This is an evidence-based ordering for later experiments, not a claim that these controls have passed.

1. Use ORB-SLAM3 as the primary calibrated tracking reference alongside the simpler supplied-depth control already planned. Keep reference poses out of algorithm inputs and score tracking loss as well as error.
2. Add OpenVINS or Basalt when recorded camera/IMU timing and calibration have been verified. Check initialization failures and metric-scale drift explicitly.
3. Compare DROID and DPV variants on the same calibrated image sequence if exact weight terms and GPU resources permit. Preserve differences in loop closure and final optimization.
4. Evaluate MASt3R-SLAM and VGGT-SLAM 2.0 as separate dense image-only routes when permissions permit. Test physical dimensions and surface accuracy in addition to pose error.
5. Compare Jetson acceleration or an edge split only after the recorded-input reference works. Measure complete processing latency, transfer volume, energy/thermal behavior and disconnection recovery on the intended hardware.

Every comparison should record input modality, supplied calibration, image size/crop, clock relationship, scale source, reference alignment, completed-frame fraction, initialization failures, tracking loss, relocalization, loop closure, memory, hardware and included runtime stages. Ground-truth-fitted scale must be reported separately from accuracy in metres. Numeric acceptance limits and tunable settings remain undecided.

The user prefers Python and accepts other languages where needed. Python can own dataset conversion, experiment orchestration and evaluation while a C++ implementation supplies tracking through a defined interface. The first test must verify pose direction, timestamps, units and map-segment identity. Dense fusion remains an independently tested consumer; a corrected trajectory may require reintegrating or updating earlier geometry.

## Coverage and remaining uncertainty

This review checks the official ORB release and a focused set of leading relevant alternatives, plus 2025–2026 edge and benchmark work. It is not an exhaustive survey of every proposed SLAM system. The evidence supports a comparison shortlist, not a universal SOTA designation. Dynamic-scene handling, long-term maps, rolling shutter and construction-site conditions need their own evaluations. Baseline indoor success cannot establish those capabilities.

The strongest next evidence is matched-input local results, including failures. No current source establishes accuracy, sustained runtime or camera support on the available Samsung S23 or Redmi Note 11 Pro.
