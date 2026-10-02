# Research recovered from the interrupted Claude session

Recovered on 2 October 2026. Claude found useful material that had not reached the research files. The largest gap was methods that split camera tracking and mapping between a device and a nearby server. This page records the findings, their sources and how they could be tested within the five existing experiments.

The follow-up [ORB-SLAM and current tracking review](../orb_slam/README.md) checks ORB-SLAM3, leading comparisons and newer 2026 edge implementations in response to the user's priority.

## What was preserved

The raw trace, original logs and downloaded PDFs below are local evidence and are excluded from Git. A fresh clone contains this reviewed summary, the URL inventory and hash manifest. Local artifact links require the original workspace; retrieve primary publications using the source links for a fresh review.

The published URL inventory omits one token-bearing coverage-badge URL; the original local trace is unchanged. It contains 327 URL rows rather than the original mechanically extracted 328.

| Artifact | Purpose |
| --- | --- |
| [Supplied trace](claude_trace_2026-10-02.txt) | Unedited copy of the user's attachment, including commands, printed results, research requests and interrupted lookups |
| [Source URL inventory](source_urls.csv) | 328 distinct URL strings extracted mechanically, with first trace line and occurrence count |
| [Original evidence manifest](evidence_manifest.csv) | Original paths, saved paths, sizes and SHA-256 hashes for 17 recovered artifacts |
| [Main session log](raw/9b29fa07-f009-4a1c-9e5f-1b27b25a2b79.jsonl) and five agent logs in `raw/` | Original tool-result summaries and requests omitted from the pasted trace, with agent metadata |
| Four PDFs in `raw/` | MobiDepth paper, ScanNet++ terms, SLAM-Share slides and SLAM-Share full paper |

The trace has 3,712 lines. Its SHA-256 is `92f35d2760a7fc949ad6ffc8613413c926da788c4c9771c09beb864ac26004e2`; the attachment and saved copy match. Line references below refer to that copy. The URL inventory includes badges, search noise and shell placeholders such as `$u`. An entry is not proof that a page exists or that its claims were checked.

The pasted trace contains five research-agent requests but no completed research reports. The original logs confirm that all five agents stopped at the weekly limit. Their omitted tool-result summaries were recovered separately. Those summaries are generated descriptions of fetched pages, not original webpage text, and contain contradictions. Printed primary-source excerpts support recovered findings; summaries and requested investigations keep their evidence labels. Selected important sources were reopened during recovery, as marked below. No algorithms or phone captures were run during this recovery.

The PDF `webfetch-1790926819286-pby67m.pdf` identifies itself as the SLAM-Share paper through embedded title `Multi_User_SLAM_CoNext_Camera.pdf`. It likely came from the final [NSF manuscript request](https://par.nsf.gov/servlets/purl/10388651); that association is inferred, and the log returned a usage-limit error. The other filenames are mapped in their original logs. All 17 artifact copies were checked against their source hashes.

## Missing edge and collaborative tracking sources

Tracking camera movement while building a map is called simultaneous localization and mapping (SLAM). Tracking with both images and motion sensors is visual-inertial odometry (VIO). Edge processing means using a nearby server for part of the work. These methods directly address the original question about established AR/VR approaches.

| Source | Evidence and useful result | Fit to this project |
| --- | --- | --- |
| [Edge-SLAM](https://github.com/droneslab/edgeslam), MobiSys 2020 | Reopened official repository. Built on ORB-SLAM2; offloads expensive modules. Documented Linux/ROS setup, separate frame, keyframe and map-update TCP connections; GPLv3. Trace 602–603 only showed a fetch. | Capture/delivery and tracking: compare local processing with a split process using identical recorded inputs. It is a C++ integration lead, not a ready Python phone package. |
| [AdaptSLAM paper](https://arxiv.org/abs/2301.04620), INFOCOM 2023; [repository](https://github.com/i3tyc/AdaptSLAM) | Reopened paper and repository. Selects representative frames (keyframes) under communication/computation limits; integrates with ORB-SLAM3. Abstract reports 62% lower tracking error than its best baseline under constrained bandwidth. Repository permission terms were not established. Trace 1885–1910, 2381–2382. | Delivery and tracking: compare frame-selection policies at the same transfer budget. The paper's percentage does not set our acceptance limit. |
| [SwarmMap](https://www.usenix.org/conference/nsdi22/presentation/xu), NSDI 2022; [repository](https://github.com/MobiSense/SwarmMap) | Reopened publisher and repository. Uses change logs, priority scheduling and compact maps. Publisher reports >20 agents, 2× agent capacity at the same resource overhead, and 38 cm mean trajectory error in its evaluation. Repository says GPLv3 and “Under Construction.” Trace 2574–2596, 2753–2754. | Later multi-phone delivery and mapping: measure redundant transfer, scheduling and map consistency. Multi-agent paper results do not establish single-phone outdoor accuracy. |
| [COVINS / COVINS-G](https://github.com/v4rl-ucy/covins), ISMAR 2021 / ICRA 2023 | Reopened repository; former VIS4ROB-lab URL redirects here. Central collaborative backend; generic VIO/tracking front-end wrapper and VINS-Fusion support. GPLv3. Trace 1219–1220; [COVINS-G paper](https://arxiv.org/abs/2301.07147), trace 1859–1860. | Tracking: investigate whether an existing camera/IMU front end can feed server-side map optimization. Interface compatibility still needs testing. |
| [SLAM-Share DOI](https://dl.acm.org/doi/10.1145/3555050.3569142), CoNEXT 2022; [author slides](https://jiasi.engin.umich.edu/wp-content/uploads/sites/81/2023/03/SLAMshare-conext22-slides.pdf) | Trace search summary describes IMU/GPU-assisted offloading, map merging and shared memory. No code repository found in the trace; full paper extraction stopped at the usage limit. Trace 2845–2857, 3155–3169, 3296–3298. Unconfirmed here. | Delivery/tracking lead for offloading placement and multi-user latency; inspect primary paper before adopting performance claims. |

[ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) was also reopened. It supports monocular, stereo, RGB-D and inertial configurations; code is GPLv3, with an author contact for closed-source commercial licensing. GPLv3 is not a noncommercial licence. Distribution and integration obligations need a separate decision; this recovery grants no blanket permission. A Python wrapper does not change underlying terms.

The architectural implication is a proposed experiment, not a selected implementation: keep timely pose estimation near capture where needed, send selected observations to a server, and measure whether map corrections improve results within a transfer budget. Dense surfaces remain a separate reconstruction question. Shared anchors or visual positioning services should not be assumed to provide dense metric geometry.

## Phone capture facts recovered from Android references

The trace printed primary Android reference passages at 2225–2235, 2485–2504 and 2841–2844. References: [CameraCharacteristics](https://developer.android.com/reference/android/hardware/camera2/CameraCharacteristics), [CaptureResult](https://developer.android.com/reference/android/hardware/camera2/CaptureResult), [CameraMetadata](https://developer.android.com/reference/android/hardware/camera2/CameraMetadata), [SensorEvent](https://developer.android.com/reference/android/hardware/SensorEvent), [CameraManager](https://developer.android.com/reference/android/hardware/camera2/CameraManager). CameraCharacteristics was reopened during recovery. These are API meanings, not measured S23 or Redmi capabilities.

| Recovered requirement | Consequence for experiment 01 and the observation contract |
| --- | --- |
| Intrinsics are `[fx, fy, cx, cy, skew]` in pre-correction active-array pixels; metadata can be absent. | Record array, crop, output size and distortion handling. Convert calibration to actual delivered images; do not copy sensor intrinsics unchanged. |
| Pose rotation is `(x,y,z,w)`; translation is optical-center position in metres relative to the reported pose reference. An undefined reference supplies defaults. | Record axes and reference identity. Do not treat this vector directly as a world-to-camera translation or accept defaults as stereo calibration. |
| Camera timestamps mark first-row exposure start in nanoseconds. `REALTIME` shares the `elapsedRealtimeNanos()` base; `UNKNOWN` does not establish comparison with IMU or other cameras. Motion sensor timestamps use that real-time base. | Save capture times separately from arrival times. Verify clock compatibility before associating image and IMU samples. |
| Both calibrated and approximate logical-camera synchronization can assign equal request timestamps despite differing physical exposure starts. | Equal timestamps do not prove synchronized stereo. Query synchronization type and test temporal misalignment. |
| Rolling-shutter skew describes row timing; crop affects the covered interval. Optional optical stabilization samples describe timestamped pixel shifts. | Retain exposure/skew and stabilization metadata where available; investigate their effect on matching and motion estimation. |
| Logical physical-camera access and concurrent device access are different mechanisms. Hidden physical IDs may still have queryable characteristics; supported stream/session combinations must be tested. | Probe both handsets, record exact model/firmware and open/configure the actual stream combination. Lens count does not prove usable stereo. |

Further details preserved in the trace include Brown–Conrady distortion coefficients and the deprecated radial-distortion normalization issue, camera pose references to primary camera/gyroscope, pixel centers at `(x+0.5,y+0.5)`, the 20 ms motion-tracking exposure intent, Android 11 rolling-shutter wording changes and API 34 readout timestamps. These need full API/version checks when implementing a recorder.

## Corrections and added detail for existing sources

| Existing gap | Recovered evidence | Status and action |
| --- | --- | --- |
| MobiDepth hardware and input resolution left unknown | Extracted [paper PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/09/mobicom22-final138.pdf), trace 2241–2300: 22 FPS / 45 ms on Huawei Mate40 Pro; stereo input 640×480, disparity level 64, four aggregation paths. Other devices: Huawei P30 and Pixel 6 Pro. | Primary text printed in trace. Preserve paper conditions; no S23/Redmi performance claim. |
| MobiDepth accuracy conditions missing | Same excerpt: stationary objects at 0.5–5 m, mean depth error 1.1–10.4%; moving-object experiment on P30 at 1 m and 30–80 cm/s reports 8.7%, versus 43.5% for its ARCore comparison. A RealSense D435i was used for reference. | Author results, not local measurements. Paper-era ARCore comparison does not establish current ARCore limitations. |
| MobiDepth implementation detail only partly extracted | Trace 2092–2095 mentions 30 FPS capture, Java/C++ implementation and 0.2 px calibration reprojection rejection. Mate40 Pro speedups: 1.66× AnyNet and 12.13× MADNet without online adaptation, trace 2254–2256. | Preserve as partial extraction; read surrounding paper before reproducing parameters. No official code release established. |
| MASt3R-SLAM CSV runtime unknown | [Paper](https://arxiv.org/abs/2412.12392) abstract printed at 3688–3700 reports 15 FPS. [Repository](https://github.com/rmurai0610/MASt3R-SLAM) excerpt 3558–3560 specifies RTX 4090 and differences in multiprocessing release. | Already present in source note, missing in CSV. Rate is a paper claim; exact timing/resolution still unresolved. |
| COLMAP main licence URL returned 404 | Trace 2423–2428 shows `COPYING.txt` renamed to `LICENSE` on main; BSD-3 remains. [Current file](https://github.com/colmap/colmap/blob/main/LICENSE). | Pinned 3.12.6 `COPYING.txt` stays appropriate. Trace reports release 4.2.1 on 29 September 2026; RTAB-Map 0.23.8 on 5 July. These are trace snapshots, not upgrade decisions. |
| EuRoC licence unresolved | DataCite output 3134–3139 for [data DOI](https://doi.org/10.3929/ethz-b-000690084) explicitly says “In Copyright - Non-Commercial Use Permitted”; deposit year 2024. [2016 paper DOI](https://doi.org/10.1177/0278364915620033) is separate. | Printed metadata, not a Creative Commons grant or company clearance. Landing page hit HTTP 429; recovery web-tool retry of DataCite failed. |
| VGGT family permissions grouped as unknown | Reopened [VGGT repository](https://github.com/facebookresearch/vggt) and [licence](https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt): commercial code under custom terms; original VGGT-1B weights remain noncommercial. Separate [VGGT-1B-Commercial](https://huggingface.co/facebook/VGGT-1B-Commercial) requires application and its own terms. | Correction to the blanket unknown. No model downloaded or execution permission decision made. Default quick-start uses the original model. |
| VGGT-Ω replacement checkpoint name absent | Trace 3233–3236 names [vggt_omega_1b_416_reproduce.pt](https://huggingface.co/facebook/VGGT-Omega/blob/main/vggt_omega_1b_416_reproduce.pt), dated 18 September 2026. | Existing note already records replacement warning; exact file newly preserved. Omega terms are separate from VGGT-1B-Commercial. |
| Older ICL notes say not acquired | Local folders contain acquired ICL archives, reference surface and extraction receipts. Task 02 was initially active during this recovery; its status changed independently while recovery was underway. | Consult current Task 02 receipts for readiness. This research recovery does not validate the acquisition implementation or scoring geometry. |

VGGT-Ω abstract excerpts also report 30% of predecessor training GPU memory, 15× supervised data and 77% improvement in its Sintel camera test (trace 3320). InfiniteVGGT's printed abstract describes bounded rolling memory and approximately 10,000-frame Long3D evaluation (3355). Cache similarity/first-frame anchoring details came from a search summary, and conference acceptance remained unconfirmed. These are model-specific research claims, not deployment guarantees.

## Additional code, model and data permission evidence

This table records what Claude actually obtained. It is not an execution-clearance list. A repository licence does not automatically cover pretrained weights or source datasets, and a model-hosting tag can conflict with the author's explicit terms.

| Asset | Recovered statement and primary link | Trace lines / limitation |
| --- | --- | --- |
| Pi3 / Pi3X | [Official README](https://github.com/yyfz/Pi3#-license): BSD-3 code, CC BY-NC 4.0 weights. | 3180–3187. Conflicts with the queried Pi3 hosting tag of BSD-2 at 3124; use explicit component terms. |
| MapAnything | [Repository](https://github.com/facebookresearch/map-anything): Apache code. Default model tag is CC BY-NC 4.0; separate [map-anything-apache](https://huggingface.co/facebook/map-anything-apache) model. | 3119–3121, 3199–3225. Record the exact checkpoint before any evaluation. |
| Depth Anything V2 | [README](https://github.com/DepthAnything/Depth-Anything-V2): Small Apache-2.0; Base/Large/Giant CC BY-NC 4.0. | 2958–2959. Do not apply code terms to every model size. |
| Prompt Depth Anything | [Repository](https://github.com/DepthAnything/PromptDA); Small/Large model-card tags Apache-2.0. Uses sparse depth prompting; demonstrated iPhone LiDAR route. | 3111–3112, 3265–3294. Model terms need full reading; sparse depth must exist first. |
| FoundationStereo | [Repository licence](https://github.com/NVlabs/FoundationStereo/blob/master/LICENSE) has research terms; README points to separate [NVIDIA TAO offering](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tao/models/foundationstereo). | 2680–2697. Partial excerpt; commercial offering does not clear research weights. |
| Depth Pro | [Apple licence](https://github.com/apple/ml-depth-pro/blob/main/LICENSE), README says shared by code and weights. | 2963–2965, 3101–3107. Partial grant printed; full conditions still need review. |
| Metric3D / UniDepth / MoGe | [Metric3D](https://github.com/YvanYin/Metric3D): BSD-2 code, queried weight tag absent. [UniDepth](https://github.com/lpiccinelli-eth/UniDepth): CC BY-NC 4.0 repository, queried weight tag absent. [MoGe](https://github.com/microsoft/MoGe): MIT code; DINOv2 component Apache-2.0; queried model tags MIT. | 2788–2813, 2982, 3113–3117. Missing tags do not mean unrestricted use. |
| Reconstruction families | DUSt3R, MASt3R, Spann3R, CUT3R licence headers CC BY-NC-SA 4.0; Fast3R FAIR Noncommercial Research; MUSt3R custom header only; MonoGS custom licence header only. | 3394–3441, 3622–3658. Full terms/weights unresolved. Names and fetched paths retained in URL inventory. |
| Other SLAM code | Headers: VGGT-SLAM BSD-2, DROID-SLAM BSD-3, DPVO MIT, SplaTAM BSD-3, Photo-SLAM GPLv3. | 3420–3437. Headers alone do not clear inherited models or dependencies. |
| Stereo code | RAFT-Stereo MIT, CREStereo Apache-2.0, IGEV/IGEV++ MIT, OpenStereo main MIT, Selective-Stereo MIT. | 2528–2573, 2815–2820. Weight terms not established by these headers. OpenStereo v2 licence path failed. |
| Optimization dependencies | [g2o](https://github.com/RainerKuemmerle/g2o): BSD core, csparse extension LGPL-2.1+. [GTSAM](https://github.com/borglab/gtsam): simplified BSD plus separately licensed components. | 2868–2893. Review the components actually built; avoid blanket “all BSD.” |
| MASt3R checkpoint notice | [Notice](https://github.com/naver/mast3r/blob/main/CHECKPOINTS_NOTICE) includes inherited DUSt3R and training-data restrictions, including 3D Street View and IndoorVL conditions. | 3483–3539. Existing research linked notice but did not spell out inherited restrictions. |
| ARKitScenes | [Licence](https://github.com/apple/ARKitScenes/blob/main/LICENSE): noncommercial grant plus conditional commercial grant tied to a 700-million monthly-active-user threshold before August 2024. | 2357–2375; exact licence reopened during recovery and clause confirmed. Preserve condition and separate component terms. |
| Replica | [Licence](https://github.com/facebookresearch/Replica-Dataset/blob/main/LICENSE): noncommercial/not-for-profit research; commercial employees remain bound by that scope and employer conditions. | 2761–2772. Employment at a company does not itself expand allowed purposes. |
| ScanNet++ | [Terms PDF](https://kaldir.vc.in.tum.de/scannetpp/static/scannetpp-terms-of-use.pdf) excerpt restricts to noncommercial research/education. | 2024. Remainder truncated; full agreement still needs reading. |

PromptDA's model card additionally records up-to-4K LiDAR-prompted output, 340-million-parameter Large and 25.1-million-parameter Small models, Large-only paper benchmarking, and a Small-Transparent variant trained for 10,000 steps on HAMMER with simulated LiDAR. Its example prompt is 192×256 in metres. These belong to a supplied-depth refinement comparison, not evidence that either Android phone has LiDAR. Trace 3265–3294.

## Additional evidence recovered from the original agent logs

The following useful details were absent from the pasted trace. They are retained as original tool-generated summaries, pending primary text checks. Each log contains the cited URL and its returned description.

| Agent log | Additional evidence and limitations |
| --- | --- |
| [Edge research](raw/agent-a73995957a1f2525c.jsonl) | AdaptSLAM summary describes feature-point uplink and optimized pose/feature downlink; local map times 162.8 ± 68.9 ms versus 556.4 ± 113.7 ms using a Ryzen 7 4800H/GTX 1660 Ti laptop and four-core/8 GB VM, not a phone. An inconsistent “3.7×” summary is not adopted. COVINS-G summaries describe keyframes/landmarks sent to the backend and optional returned map updates; ARCore/ARKit compatibility is unverified. SLAM-Share DOI returned 403 and slide extraction failed, but PDFs survived. |
| [Datasets and models](raw/agent-af3fcb9f68faa206a.jsonl) | Hilti 2022 official-page summary: CC BY-NC-SA 3.0, five global-shutter cameras plus LiDAR/IMU, surveyed reference in IMU frame. ConSLAM repository summary: custom academic-use-only terms. ADVIO summary: CC BY-NC 4.0 and reference from IMU/manual fixation points. TUM VI summary: CC BY 4.0 data/BSD-2 code, stereo 20 Hz, IMU 200 Hz, reference 120 Hz; full room reference but start/end-only reference elsewhere. ARKitScenes IMU availability was guessed and remains unconfirmed. |
| [Sources 01–10](raw/agent-a0c9d0ab22347a1e0.jsonl) | VGGT-Ω licence/model-card summaries: FAIR Noncommercial Research terms; A100 memory 6.02/13.37/43.15 GB for 1/100/500 frames at 624×416. Repository names `VGGT-Omega-1B-416-Reproduction` with an 8 September update, differing from the project's 18 September date. InfiniteVGGT summary: Apache-2.0 code using StreamVGGT weights, whose terms remain unresolved. Raw Depth codelab reportedly archived 13 February 2026, Apache-2.0. HyperSight URLs returned 404; HiMoDepth IEEE returned empty content. |
| [Sources 11–21](raw/agent-af75e4e8914c004d1.jsonl) | RTAB-Map documentation summary warns about SURF/nonfree OpenCV; SIFT patent expiry is a separate issue. EuRoC landing page failed. COLMAP release-summary dates saying 2024 conflict with the printed 2026 output and are rejected. |
| [Phone capture](raw/agent-a4a916059db9e13a9.jsonl) | Camera2 fetch summaries returned navigation rather than definitions. Useful API meanings above come from subsequent printed primary-text extraction. S23 database lacks timestamp source, stereo synchronization, calibration and firmware metadata. |

These logs preserve partial work, not five completed validations. Full raw evidence remains available if a condensed row proves insufficient.

## Leads that were requested or searched, but not resolved

Preserve these for continuation without presenting them as checked recommendations. The complete requests are in trace 510–586; URLs that actually appeared are in the inventory.

| Area | Unfinished leads |
| --- | --- |
| Edge and multi-user systems | C2TAM, CloudSLAM, CCM-SLAM, Kimera-Multi, maplab 2.0, Swarm-SLAM; incidental Map++ (`arxiv:2411.02553`), edge-assisted multi-robot VIO (`2603.11085`), SHARE (`2607.23901`) and multi-user occlusion (`2411.10940`) search hits |
| AR/VR services and runtimes | ARCore Cloud Anchors/Geospatial, Lightship VPS, Immersal, Magic Leap, Quest/HoloLens, Monado/Basalt; Azure Spatial Anchors retirement check was requested but not established |
| Tracking and calibration tools | OpenVINS, Basalt, VINS, Kimera-VIO, DPV-SLAM, pySLAM, stella_vslam, MAC-VO, Kalibr, OpenCV calibration, evo, RPG trajectory evaluation; ARCore Recording & Playback and sensor loggers |
| Android inference | LiteRT/TFLite, ONNX Runtime Mobile, ExecuTorch, NCNN; no deployment comparison completed |
| Additional depth/reconstruction | LightStereo, HITNet, Metric3D v2, UniDepth v2, MoGe-2, MASt3R-SfM, MUSt3R, Fast3R, Spann3R, CUT3R and learned/Gaussian mapping families; licence snippets above are not full method validation |
| Dataset alternatives | [Hilti](https://hilti-challenge.com/dataset-2022.html), [ConSLAM](https://github.com/mac137/ConSLAM), [ADVIO](https://github.com/AaltoVision/ADVIO), [TUM VI](https://cvg.cit.tum.de/data/datasets/visual-inertial-dataset), OpenLORIS, 7-Scenes, ARKitScenes, ScanNet++, Replica |
| Map evaluation | CloudCompare/Open3D surface accuracy, completeness and F-score; elevation mapping, grid_map, OpenDroneMap orthophotos and excavation cut/fill measurements |

Hilti 2021/2023 noncommercial licence statements were search summaries drawing partly on third-party catalogues (604–624). ConSLAM searches returned conflicting “N/A”, “All Rights Reserved” and “other” records (1008–1025). Dataset and paper permissions may differ. Both remain unresolved here. ConSLAM's construction-site imagery, LiDAR, motion-sensor and professional reference-scan description is a useful search lead, not a verified input contract.

The original validation requests also named TartanAir/TartanGround, KITTI and Scene Flow terms; TUM registered-image calibration versus nominal intrinsics; ICL ray-range depth and negative vertical focal length; and Middlebury's principal-point offset in disparity-to-depth conversion. Existing dataset notes cover several of these. No completed agent report establishes that every requested check was done.

## How to test the useful ideas independently

These are candidate follow-ups. No frame budget, threshold or tunable value is selected by this document.

| Existing experiment | Isolated test suggested by the recovered research | Evidence to record |
| --- | --- | --- |
| 01: capture and delivery | Probe each handset; record calibration, timing and stabilization. Separately replay known observations through a network with controlled delay, loss and disconnection. Compare images, features and selected frames as payloads. | Supported stream combination, capture-versus-arrival time, transferred bytes, backlog and recovery. Save original observations for replay. |
| 02: stereo depth | Compare a permitted simple matcher with selected model candidates on identical calibrated pairs. Check timing/crop changes separately from matching changes. | Disparity and metric-depth error, invalid coverage, runtime and hardware. Use MobiDepth settings only as cited paper conditions until locally chosen. |
| 03: camera tracking | Compare recorded local tracking with edge-assisted corrections or VIO, while holding observations constant. Test loss of network, tracking loss, relocalization and separate map origins. | Absolute and relative trajectory errors, drift, time until pose available, lost segments and correction behavior. Alignment for scoring must not disguise unknown metric scale. |
| 04: reconstruction | Keep supplied depth and poses as the independent control; replace one input at a time with tracker/depth outputs. Compare geometry rather than rendered appearance. | Surface accuracy/completeness, observed support, memory and failure regions against independent geometry. Shared sparse maps do not establish a dense surface. |
| 05: bird's-eye mapping | Continue exact-shape tests before site data; later investigate height/elevation and cut/fill questions separately. | Declared plane, units, visible coverage, unknown cells and independently known areas/heights. No safety or clearance inference. |

Python can own recorded-data adapters and evaluation. Existing C++/ROS systems can be wrapped or called as separate processes if their inputs, outputs, build requirements and terms fit. No wrapper or new implementation was created during recovery.

## Failed lookups and unsupported handset claims

The trace's Camera FV-5 [S23 entry](https://www.camerafv5.com/devices/manufacturers/samsung/sm-s911b_dm1q_0/) lists camera settings, but is third-party and cannot establish simultaneous streams, synchronization or current firmware behavior (3393). Redmi 4G `viva` and other regional/5G IDs were located but not individually validated (3567–3614). The search summary's “10 MP front camera” statement is unsupported and is not adopted here.

Initial Camera2 string searches missed the definitions; later extraction recovered them. Windows text-encoding errors affected SensorEvent and Crossref, then UTF-8 corrected relevant output. EuRoC landing-page rate limits did not invalidate the successful DataCite rights output. Several licence 404s were filename/branch mistakes: MASt3R-SLAM and MonoGS use `.md`, VGGT uses `.txt`, COLMAP main uses `LICENSE`. HITNet and full MonoGS/MUSt3R terms remain unresolved. Repeated weekly-limit messages explain why the investigations stopped; no final research synthesis or research-file write appears in the supplied trace.

Older source notes, CSV and BibTeX remain historical evidence. This addendum supplies missing detail without inventing bibliography fields for unconfirmed leads or silently changing existing execution decisions.
