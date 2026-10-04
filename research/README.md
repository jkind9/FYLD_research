# Research evidence

Original source review: 1 October 2026. [Recovered Claude research](session_recovery/README.md), added on 2 October, records missing edge SLAM sources, phone capture requirements, source corrections and unresolved leads. It also preserves the supplied trace. Read that addendum alongside the older tables; their unknown fields have not all been revised. Paper results are publisher claims, not results reproduced by this project.

Start with the [reading guide and 21 individual source summaries](sources/README.md). The [background explanation](sources/00_start_here.md) introduces depth, camera movement, reconstruction and the different measurements needed to assess a site map.

The current [six-piece experiment plan](../experiments/README.md) connects research to independent tests. Start with verified geometry and supplied-input reconstruction; inspect phones alongside this work. The new [object recognition and persistent counting plan](../experiments/06_object_recognition/README.md) relates the supplied recognition papers to multi-view labels, moving-feature removal and revisit identities. Its ScienceDirect source remains unverified. The [dataset guide](../experiments/datasets/README.md) explains reference inputs for each stage. Earlier implementation and local outputs are preserved in [the prototype archive](../archive/task00_prototype/README.md).

| File | Purpose |
| --- | --- |
| [edge_products/README.md](edge_products/README.md) | Commercial stereo/edge mapping routes, actual map-rate evidence and a shared approach to worksite measurement and distinct-object counting |
| [orb_slam/README.md](orb_slam/README.md) | ORB-SLAM3 as a central tracking reference, current alternatives, 2026 edge implementations and fair benchmark comparisons |
| [session_recovery/README.md](session_recovery/README.md) | Findings recovered from the interrupted Claude session, evidence status, experiment connections and original trace |
| [literature_review.md](literature_review.md) | Primary sources and what they establish |
| [papers.csv](papers.csv) | Searchable evidence table; unknown fields stay explicit |
| [sources.bib](sources.bib) | Verified bibliographic fields |
| [method_comparison.md](method_comparison.md) | Input requirements and evaluation choices |
| [licences.md](licences.md) | Separate code, weight and dataset permissions |
| [dataset_catalog.md](dataset_catalog.md) | Calibration, ground truth and dataset suitability |
| [roadmap.md](roadmap.md) | Later experiments and completion evidence |
| [limitations.md](limitations.md) | Boundaries of the present demonstration |
| [repositories.json](repositories.json) | Pinned reference checkouts and execution status |

Historical prototype results used TUM supplied depth for scale and an image-only branch with arbitrary scale. Current bounded controls and desk replay are recorded in the root and experiment READMEs. Their receipts do not establish full pipeline or site validation; do not substitute paper benchmarks for local measurements.

The proposed area output describes observed surfaces. Unseen space remains unknown. It does not establish safe clearance, hidden utilities, structural condition or whether a person can safely enter an area.

## Task16 shortlist and experiment protocol

[Task16](../task_list/pending_review/16_research_segmentation_recognition_and_camera_corre.md) records the source review and draft protocol for Tasks17–22 and 25. The owner later clarified that exploratory replay and association trials do not approve this broader protocol, so Task16 remains pending review. Each experiment records its own authorised settings and limits. The [stage06 plan](../experiments/06_object_recognition/README.md#proposed-comparison-protocol) holds the proposed protocol. Keep the existing YOLO26x checkpoint for the first detection comparison. Other learned models remain research candidates; no new models or weights are downloaded.

The requested [Kuey survey](https://kuey.net/index.php/kuey/article/download/2260/1290/13992) separates boundary methods, such as edge detection, from region methods. It reviews algorithms; it is not a current device benchmark or a runnable object inventory. A Canny contour is a boundary control. GrabCut with a checked rectangle prompt is a classical mask-producing control. Neither supplies an object class or instance identity. OpenCV's [marker watershed guide](https://docs.opencv.org/4.12.0/d3/db4/tutorial_py_watershed.html) describes a seeded region method that can test touching objects.

### Ranked shortlist

| Rank | Candidate | Version and availability | Licence and qualified performance evidence | Input and role |
|---|---|---|---|---|
| 1 | RF-DETR Nano | Package 1.11.0, released 24 September 2026. Official code and public COCO checkpoints are available. | Core Nano–Large code/models Apache-2.0. Vendor reports 2.3 ms at 384×384 on NVIDIA T4, TensorRT FP16, batch 1. Not a phone or project result. [Release](https://github.com/roboflow/rf-detr/releases) · [benchmark method](https://github.com/roboflow/rf-detr/blob/develop/docs/learn/run/detection.md) | RGB image to COCO boxes, labels and scores; no prompt. Preferred automatic detector control. COCO coverage may not include the owner's chosen objects. |
| 2 | YOLO26n | Model released January 2026; Ultralytics package 8.4.164 was the latest release checked on 3 October 2026. COCO checkpoint and code are available. | AGPL-3.0 or separate Enterprise terms. Vendor reports 1.7 ms for the nano model at T4 TensorRT and up to 43% faster CPU ONNX inference than YOLO11n on an Intel Xeon 2.00 GHz. These claims do not predict S23, Redmi or project performance. [Model and measurements](https://docs.ultralytics.com/models/yolo26) · [licensing](https://docs.ultralytics.com/) | RGB image to boxes, labels and scores; no prompt. Include only if licence terms are acceptable. yolo26n-seg.pt is a separate automatic instance-mask comparison. |
| 1, mask-only | OpenCV GrabCut plus Canny/contour | Available in OpenCV 4.x; no learned weights. OpenCV 4.x uses [Apache-2.0 terms](https://github.com/opencv/opencv/blob/4.12.0/LICENSE). Freeze the exact package version before a run. | No device speed claim is used. OpenCV's [GrabCut guide](https://docs.opencv.org/4.12.0/d8/d83/tutorial_py_grabcut.html) requires a rectangle enclosing the foreground. Canny yields edges; contour closing/filling are extra steps and must be frozen. | RGB crop and same box prompt for GrabCut; RGB crop for contour control. Boundary results are not object proposals or semantic labels. |
| 2, prompted mask | MobileSAM ViT-T | Official code and mobile_sam.pt checkpoint are listed. ONNX export is available. | Apache-2.0 repository. Authors report about 3 seconds on a Mac i5 CPU. This is not Android timing. [Official repository](https://github.com/ChaoningZhang/MobileSAM) | RGB image plus point or box prompt; no class label. Preferred permissive prompted-model baseline. |
| 3, prompted mask | EdgeSAM / EdgeSAM-3x | Official PyTorch code, weights and exported formats are listed. Save the exact source commit and checkpoint hashes before selection. | NTU S-Lab License 1.0; owner review is needed before reuse. Authors report 38.7 FPS on iPhone 14 with CoreML, 1024×1024 input, encoder plus decoder, one prompt. COCO mask results use ViTDet-provided box prompts. [Code, terms and benchmark details](https://github.com/chongzhou96/EdgeSAM) | RGB image plus point or box prompt. Strong mobile comparison if licence and runtime fit the intended device. |
| 4, prompted mask | EfficientSAM-Ti | Official code, checkpoints and ONNX example are available. | Apache-2.0. The paper reports 19 ms on NVIDIA A100 for its prompted evaluation. This is not a mobile result. [Repository](https://github.com/yformer/EfficientSAM) · [paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Xiong_EfficientSAM_Leveraged_Masked_Image_Pretraining_for_Efficient_Segment_Anything_CVPR_2024_paper.pdf) | RGB image plus point or box prompt. Keep as an alternate if the first two prompted models do not fit terms or quality needs. |
| Not runnable | SqueezeSAM, arXiv v3 | The paper reports 300 ms on iPhone 14 CPU at 1024×1024 and 8 ms on A100. Its comparisons use ViTDet boxes or points sampled from reference masks. The public [repository](https://github.com/balakv504/squeeze_sam) currently has one README and no implementation, checkpoint or licence. | No runnable artefact or terms could be verified. Do not select until a usable, licensed implementation and weights are supplied. The paper's saliency grouping may combine related objects, so instance separation needs its own score. [Paper](https://arxiv.org/html/2312.06736v3) | RGB image plus point or box prompt. The paper result is not an Android or project benchmark. |

The dated shortlist below contains candidate methods and a temporary-tracking reference. Task20 measured ZNCC, ORB/SIFT availability and existing YOLO26x features; DINO and ResNet50 have not been tested.

| Method | Code/weights and input | Expected strengths and limits |
|---|---|---|
| Masked ZNCC | OpenCV 4.13 matchTemplate, TM_CCOEFF_NORMED, with a mask over resized object crops; no learned weights. [Formula and mask support](https://docs.opencv.org/4.13.0/df/dfb/group__imgproc__object.html) | Interpretable crop-matching baseline. Same-size patch comparison tolerates some brightness/contrast change. It does not handle arbitrary rotation, perspective or scale by itself. |
| ORB and SIFT | OpenCV descriptors and matchers in OpenCV 4.x; no model weights. OpenCV terms are [Apache-2.0](https://github.com/opencv/opencv/blob/4.12.0/LICENSE). Keep descriptor matches inside the object mask and reject matches without geometric support. [OpenCV feature matching](https://docs.opencv.org/4.x/d1/de0/tutorial_py_feature_homography.html) | ORB is a fast local-feature baseline. Its paper reports rotation invariance and two orders of magnitude more speed than SIFT on its tested applications; this is not a current-phone measurement. Both can fail on textureless, repetitive, symmetric, occluded or strongly changed views. [ORB paper](https://ieeexplore.ieee.org/document/6126544/) |
| DINOv2 ViT-S/14 | Frozen 21M-parameter encoder, official code and weights available under Apache-2.0. Use masked-crop embeddings; no fine-tuning in the initial comparison. [Official source and model table](https://github.com/facebookresearch/dinov2) | Learned appearance baseline. ImageNet classification scores do not establish instance re-identification. Same-category instances may look alike; masking/background handling and viewpoint robustness must be measured locally. |
| DeepSORT | The paper describes a temporary tracking method whose common appearance model is trained for pedestrian re-identification. No versioned implementation, checkpoint and licence are pinned for this project, so it is not in the runnable shortlist. [Paper](https://arxiv.org/abs/1703.07402) | A conceptual temporary video-track control for frame-to-frame association and short occlusion. It is not evidence of persistent object identity after leaving and returning. |

### Camera correction shortlist

Rank 1 is feature-seeded Open3D 0.19.0 as the local extension: official code is already used by this project under Apache-2.0 terms, and its RGB-D odometry API returns a metric rigid transform and information matrix for registered color/depth pairs. Seed it with calibrated, depth-backed feature matches and compare against the current identity-initialised path on the same pairs. Open3D multiway registration supplies pose-graph mechanics, not a complete place-retrieval system. [Open3D 0.19.0 licence](https://github.com/isl-org/Open3D/blob/v0.19.0/LICENSE) · [odometry API](https://www.open3d.org/docs/0.19.0/python_api/open3d.pipelines.odometry.compute_rgbd_odometry.html) · [pose graph guide](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/multiway_registration.html)

Rank 2 is RTAB-Map 0.22.1, whose public source provides RGB-D place retrieval, loop detection and graph correction under BSD-3-Clause. Pin a release/build configuration; check whether enabled OpenCV nonfree/SURF components change licence obligations. Rank 3 is ORB-SLAM3 v1.0-release, with RGB-D tracking, relocalisation and loop closure under GPLv3; include only if its licence and build fit the intended use. [RTAB-Map tagged source](https://github.com/introlab/rtabmap/tree/0.22.1) · [ORB-SLAM3 tagged source and licence](https://github.com/UZ-SLAMLab/ORB_SLAM3/tree/v1.0-release) No comparable source timing claim is used because included stages and tested hardware differ. None of these candidate loop routes has a local project result or approved numeric gate.

For each retrieved keyframe candidate, require calibrated correspondences, valid depth, robust metric SE(3), inlier counts/rate, reprojection and 3D residuals, overlap, uncertainty/information, reverse/cycle consistency and graph residual checks. Reject weak-parallax/degenerate geometry, dynamic-only matches and inconsistent transforms. Appearance similarity nominates a pair only; it cannot establish camera translation or rotation. A correction creates a new pose revision and requires downstream geometry to be recomputed or invalidated as one committed generation. The stage03 experiment README records the proposed measurements and owner choices.

A similarity score can nominate a keyframe pair but cannot provide camera position or orientation. Before accepting a loop edge, retain calibrated correspondences with valid depth, robust metric transform, inlier counts, reprojection and 3D residuals, overlap, uncertainty/information and a rejection reason. Reject degenerate geometry, dynamic-only matches, inconsistent reverse/cycle transforms and implausible graph residuals. Reference poses are for evaluation only.

### Five-experiment protocol

The [stage06 plan](../experiments/06_object_recognition/README.md#proposed-comparison-protocol) specifies the experiment boundaries, split rules, negative cases and processing-cost ledger. It keeps evaluator-only masks, object IDs and reference poses out of method input except explicitly named reference controls. Task17's inventory found a desk cup return and distinct monitors, with missing or unusable cases recorded separately. Preserve Task13's desk hold-out and frozen settings. No model, checkpoint or GPU run was performed for Task16.

The earlier bounded trials recorded delegated numerical choices in their own receipts. New comparisons require their own reviewed settings, references and execution authorisation. Unsupported footage scenarios remain gaps; contract controls cannot replace recorded evidence. Desktop results do not establish phone performance.

## Research agenda, 4 October 2026

This review uses primary documentation and papers. Proposed comparisons below are unperformed. Local results and their source artifacts are summarized in the [object experiment README](../experiments/06_object_recognition/README.md); vendor/paper results remain external evidence. Task16's broader protocol remains pending review.

### A. Observation IDs, provisional identities and duplicates

[Task31](../task_list/open/31_compare_provisional_object_ids_and_duplicate_relationships.md) follows the existing checked store and bounded association trials. Every detection needs its own observation ID. Unmatched candidates may acquire provisional object IDs; confirmed inventory and rejected detections remain distinct. Preserve source histories and aliases when identities are unified. A confident returning observation retains its ID; missing depth records unknown position.

[Linear assignment documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html) describes one-to-one minimum-cost assignment, including rectangular problems. It supplies a solver, not an object identity policy; eligibility, unmatched options, birth, duplicate and confirmation decisions still need definition. [Deep SORT](https://arxiv.org/abs/1703.07402) combines motion and learned pedestrian appearance for time-local tracking. Its results do not establish persistent identity for cups/books in disjoint views.

Compare the existing restrictive class-birth rule with provisional births and explicit duplicate links on fixed cached detections. Independently checked co-visible foreground objects constrain distinct identities; duplicate detector boxes require separate rejection/consolidation evidence. For identical objects only seen in separate views, measure retained ambiguity as well as wrong merges/splits. Do not force a unique answer where the references themselves cannot establish identity.

### B. Spatial supports and calibrated uncertainty

[Task32](../task_list/open/32_investigate_spatial_support_and_position_uncertainty.md) investigates matching spatial distributions or occupied supports rather than point centres. Keep three quantities separate: uncertainty about a defined object anchor, measured visible-surface geometry, and hypotheses about full dimensions. A visible-surface centroid can move with viewpoint even when the object is stationary.

[Extended-object tracking review](https://arxiv.org/abs/1604.00970) treats objects that generate multiple measurements and models extent separately from motion state. [Kendall and Gal](https://proceedings.neurips.cc/paper/2017/hash/2650d6089a6d640c5e85b2b88265dc2b-Abstract.html) distinguish observation noise from model uncertainty in depth/segmentation tasks. These motivate the design; neither provides a calibrated model for this project.

Compare the current point gate with simple uncertainty regions, empirical depth supports and multiple foreground/background hypotheses. Isolate box-boundary shifts, foreground selection, depth confidence/holes, object extent, calibration and camera-pose perturbations. A multimodal depth mixture need not be represented by one Gaussian around background-contaminated samples.

[Confidence calibration research](https://proceedings.mlr.press/v70/guo17a.html) addresses whether predicted classification probabilities agree with empirical correctness. It does not justify interpreting detector scores, cosine similarity or point-cloud spread as spatial probability. Using independent surveyed anchors/surfaces and held-out recordings, compare claimed region coverage with observed inclusion, region volume/sharpness, residuals by range/view and proper scores for actual distributions. Calibrate same-object probabilities separately against independently labelled pairs. Record uncertain reference measurements and failures; never calibrate/test on the same nearby frames.

### C. Appearance and spatial association

[Task33](../task_list/open/33_compare_object_appearance_context_and_spatial_association.md) retains Task20's tested ZNCC and existing YOLO26x pooled features as baselines. [ResNet research](https://arxiv.org/abs/1512.03385) establishes an image-recognition architecture; proposed ResNet50 embeddings do not yet establish instance re-identification here. [DINOv2 source](https://github.com/facebookresearch/dinov2) remains a separate contextual-feature candidate from Task16. No new weights were acquired.

Hold crop/support, gallery and split fixed while comparing ZNCC, current YOLO features and an authorised ResNet50/context candidate. Compare object-only pixels with fixed surrounding context and context-only controls; repeated backgrounds may help within-session matching yet leak scene identity. Then compare appearance-only, spatial-only and combined costs on the same observations. Include similar co-visible neighbours and identical objects seen only separately.

Report pair rankings, false accepts/rejects, mistaken merges, splits, unresolved cases and full extraction/association runtime. Plot the distance/similarity trade-off without calling exploratory gates validated rules. Fix any operating rule on separate validation data before held-out testing. Geometry-only and combined rules both resolved the current eleven observations, so both inputs being universally necessary is not established.

### D. Segmentation, position and dimensions

[Task34](../task_list/open/34_evaluate_segmentation_for_position_and_observed_dimensions.md) extends Task19 through new independent references; it does not reopen or rewrite that completed control. [OpenCV GrabCut](https://docs.opencv.org/4.x/d8/d83/tutorial_py_grabcut.html) requires foreground/background initialization; a filled contour is only a boundary-derived control. Neither gives a semantic object identity or complete-object shape.

On identical boxes/depth/poses, compare rectangle supports, existing classical masks and independently checked foreground masks supplied as a named oracle control. Only then add an authorised learned method. Keep prompt quality separate. Score contamination against checked visible foreground, per-view position/surface repeatability against independent references, and absolute error against a declared physical anchor. Exact visible-mask scoring needs human-checked pixel masks, not Task17's coarse polygons.

Measure observed dimensions in a declared frame, coverage, boundary/mask error, empty/unavailable cases, split/merge and full cost. Full-object size needs surveyed dimensions and views covering the required surfaces or explicitly tested completion assumptions. Mask-induced coordinate changes alone cannot prove improvement.

### E. Error propagation and sequential improvement

[Task35](../task_list/open/35_measure_error_propagation_and_sequential_fusion.md) traces pixels/masks -> depth -> camera coordinates -> camera poses -> world coordinates -> association -> object/surface fusion. First perturb one source at a time against analytic geometry or independent references, then combine perturbations on matching inputs.

Compare individual measurements with last-view, equal-weight and robust estimates as more independently acquired viewpoints arrive. Test adjacent correlated frames, reused/reprojected depth, bias, outliers, wrong associations and pose drift separately. More frames may average independent noise yet reinforce persistent bias or duplicate evidence. Report error/coverage and wrong-identity contamination as functions of independent views and elapsed time; do not assume a reduction proportional to the square root of frame count.

[ElasticFusion](https://thomaswhelan.ie/Whelan16ijrr.pdf) demonstrates RGB-D surface fusion with correction of drift through loop closures/deformation. [ARCore Raw Depth](https://developers.google.com/ar/develop/java/depth/raw-depth) explicitly distinguishes new depth from reprojected observations by timestamp. Proposed transfer: retain observation lineage and rebuild or invalidate old derived geometry after revised poses. Task25 owns camera-correction production; Task35 evaluates downstream effects without using a match's own correction as independent confirmation.

### F. Surface visualization and realistic environments

[Task36](../task_list/open/36_compare_surface_representations_and_visual_realism.md) separates geometry measurement from appearance and navigability.

| Representation and primary source | Capture/coverage requirement and limitation | Cost and export questions |
|---|---|---|
| Denser depth points | Fixed registered depth/poses; denser display reveals existing samples but does not acquire hidden surfaces | Rendering memory/time; PLY/other point formats and source-pixel provenance |
| Oriented patches: [ElasticFusion](https://thomaswhelan.ie/Whelan16ijrr.pdf) | Repeated RGB-D surface observations; patch orientation and fusion can reduce visual gaps but require alignment | Fusion/correction cost; patch export support; false bridges and holes |
| Depth-fused mesh: [KinectFusion](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/ismar2011.pdf) and [Open3D integration](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_integration.html) | Registered metric depth and poses; unobserved surfaces remain unsupported; integration settings influence smoothing | Voxel/memory/time trade-off; PLY/OBJ/glTF compatibility to assess |
| Photogrammetry/textured mesh: [COLMAP](https://colmap.github.io/tutorial) | Static overlapping RGB with translated viewpoints, calibration and independent metric scale; weak texture and lighting changes are capture risks | Reconstruction/texture labour, memory, processing, mesh/texture exports |
| Gaussian splatting: [original author project](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) | Posed multi-view images for novel views; Gaussian support is rendering geometry, not calibrated anchor uncertainty | Optimisation/rendering cost, scene format/player compatibility, behaviour outside coverage |
| Neural radiance fields: [NeRF](https://arxiv.org/abs/2003.08934) | Posed images optimize density and view-dependent colour; rendering realism does not prove dimensions | Training/rendering memory/time, checkpoints versus extracted meshes and downstream tooling |

Start with fixed supplied depth/poses and points versus patches/mesh before adding RGB-only reconstruction or optimised novel-view methods. Independently score surface distance, coverage, boundary preservation and missing/false surfaces. Score withheld-view appearance and review usability separately. Use the same capture for comparisons and retain unseen-region labels.

The supplied [Alpha3D article](https://www.alpha3d.io/kb/metaverse/convert-normal-video-to-vr/) returned a generic landing shell when checked; its article claims could not be verified. It remains an unavailable starting pointer. Stereo video conversion creates eye-specific imagery; panorama viewing lets a user rotate around a viewing location. Neither alone establishes a metric environment that supports translated movement and correct parallax. Those require independently checked 3D geometry/scale and sufficient capture coverage.

### G. Dedicated AR/VR room mapping

[Task37](../task_list/open/37_research_arcore_arkit_and_roomplan_mapping.md) is a dedicated platform/data investigation. No Apple or Android capability is inferred from a brand name alone.

| Primary source | Accessible API capability | Limits and proposed transfer |
|---|---|---|
| [ARCore fundamentals](https://developers.google.com/ar/develop/fundamentals), [Frame](https://developers.google.com/ar/reference/java/com/google/ar/core/Frame) | Visual/inertial tracking, plane information, camera/time/coordinate APIs and depth where supported | Verify exact phone support and captured metadata. Tracking/planes do not establish independent metric accuracy. |
| [Raw Depth guide](https://developers.google.com/ar/develop/java/depth/raw-depth) and [codelab](https://codelabs.developers.google.com/codelabs/arcore-rawdepthapi) | Sparse depth plus confidence; original depth timestamps distinguish new observations from reprojection; depth sensor optional on supported devices | Confidence bytes are not a calibrated error distribution. Tutorial filters are example choices. Full depth may smooth/interpolate. Record new/reused depth lineage. |
| [ARCore anchors](https://developers.google.com/ar/develop/anchors) | Anchor poses adapt as the world estimate changes | Nearby content sharing an anchor retains relative relationships better than separately anchored content; evaluate corrections/revisits rather than freezing exported coordinates forever. |
| [ARKit world tracking](https://developer.apple.com/documentation/arkit/understanding-world-tracking), [scene reconstruction](https://developer.apple.com/documentation/arkit/arworldtrackingconfiguration/scenereconstruction), [depth](https://developer.apple.com/documentation/arkit/ardepthdata) | Visual-inertial tracking; supported LiDAR devices expose scene depth/confidence and environment mesh | Apple LiDAR depth/reconstruction does not apply to S23/Redmi. Inspect device support; distinguish planes, mesh and parametric objects. |
| [ARKit saved world data](https://developer.apple.com/documentation/arkit/saving-and-loading-world-data) | Saved maps/anchors and attempted relocalisation | Revisit coverage and changed scenes affect recovery; repeated scans need independently checked alignment. |
| [RoomPlan overview](https://developer.apple.com/augmented-reality/roomplan/) | Swift API using camera and LiDAR, scan coaching, parametric rooms/furniture and USD/USDZ export | Requires supported Apple hardware. Parametric boxes are not detailed visible surfaces or verified arbitrary-object measurements. |
| [RoomPlan research](https://machinelearning.apple.com/research/roomplan) | Paper describes semantic point-cloud accumulation, local/global detection, temporal aggregation and box fusion | Internal networks/fusion are research-described techniques, not exposed interchangeable APIs. Its static-room laser-scan references do not validate this project. |

Transferable investigations: scan guidance for missing coverage, depth lineage/confidence, local observations retained before global refinement, planes/surfaces separated from object boxes, anchors/correction-aware geometry, relocalisation, and repeated-observation handling. Compare Android API exports with required project records first; an Apple scan is a separate hardware/control acquisition. Costs include hardware access, capture labour, export fidelity, processing, energy and independent room measurements.

ARCore's depth storage range is not an accuracy guarantee. Its current documentation gives range-dependent behaviour; this project has no phone result and still excludes depth at/beyond 4 m.

### H. Autonomous driving and longer range

[Task38](../task_list/open/38_research_long_range_fusion_and_driving_evaluation.md) separates stationary inventory from moving-object tracking and evaluates data suitability without downloading datasets.

[The supplied probabilistic detection review](https://arxiv.org/abs/2011.10671) discusses observation/model uncertainty, calibration and proper scoring; its comparative experiments concern primarily 2D probabilistic detection. It is not proof of a locally calibrated 3D distribution. [LaserNet](https://openaccess.thecvf.com/content_CVPR_2019/papers/Meyer_LaserNet_An_Efficient_Probabilistic_3D_Object_Detector_for_Autonomous_Driving_CVPR_2019_paper.pdf) predicts distributions over LiDAR-based 3D boxes. [BEVFusion](https://arxiv.org/abs/2205.13542) combines camera/LiDAR features in an overhead representation. Neither has been run here.

[OctoMap](https://octomap.github.io/octomap/doc/index.html) represents occupied, free and unknown regions; occupancy does not by itself supply instance identity. [Occupancy Flow Fields](https://arxiv.org/abs/2203.03875) adds motion to occupancy for dynamic agents and notes loss of agent identities in occupancy grids. These motivate separating extents/space from identity and separating ego-motion from object motion.

| Candidate evaluation data | References and useful evidence | Suitability and acquisition gaps |
|---|---|---|
| [KITTI raw](https://www.cvlibs.net/datasets/kitti/raw_data.php) and [tracking](https://www.cvlibs.net/datasets/kitti/eval_tracking.php) | Stereo, LiDAR, GPS/IMU, timestamps/calibration and tracklet/track annotations depending on selected subset | Confirm subset, label convention, visibility, terms and storage. Standard tracking scores do not replace full 3D absolute location error. Car-mounted geometry does not prove phone/site suitability. |
| [nuScenes paper](https://arxiv.org/abs/1903.11027), [schema](https://github.com/nutonomy/nuscenes-devkit/blob/master/docs/schema_nuscenes.md), [detection scoring](https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/nuscenes/eval/detection/README.md) and [tracking scoring](https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/nuscenes/eval/tracking/README.md) | Multi-sensor timestamps/calibration/ego poses, 3D boxes and identity annotations; translation/scale/orientation/velocity and association measures | Ego poses and box annotations have uncertainty. Box centre differs from visible-surface anchor. Detection translation scoring uses ground-plane centre distance; add declared full 3D errors when appropriate. Registration, terms, storage and subset authorisation remain open. |

First check coordinate/time conventions and stationary references; then compare camera/stereo/LiDAR on matching observations with supplied ego poses. Stratify absolute error and repeatability separately by range, viewpoint, visibility and neighbour separation. Perturb timing, calibration and ego pose separately before combined tests. Add moving objects only after ego-motion compensation is independently checked, preserving velocities and time-local identities.

Report extent error only with compatible box/physical references; evaluate uncertainty coverage, association errors, unresolved cases, runtime/memory and sensor/acquisition costs. No street-scale threshold or acquisition is selected here.

### I. Future review and measurement requirements

[Task39](../task_list/open/39_record_future_3d_review_and_measurement_requirements.md) records a future requirement, not an application implementation for this session. A picked 3D object should expose every source frame/crop, accepted/rejected observations, provisional IDs and duplicate links, individual positions and fused estimates, with pose revisions and depth lineage. A surface selection should show endpoint provenance, distances, observed dimensions and uncertainty.

Review usability must be measured separately from metric accuracy. Unknown surfaces, complete-size assumptions, rejected matches and incompatible coordinate frames need visible explanations. Existing Task22/23 review scopes remain bounded; this requirement does not silently expand them.

### Practical order and authorisation gaps

[Task40](../task_list/open/40_plan_independent_references_and_hard_case_acquisition.md) owns the shared reference-acquisition protocol: independent human identity/mask review, surveyed anchor/extent/surface definitions, uncertainty of reference instruments, representative hard cases and session-disjoint splits. Begin with an inventory of usable existing evidence, then request only missing capture/reference access. Raw data acquisition, packages/weights, learned-model execution and phone/Apple hardware trials are not authorised by Task30.

After a reviewed reference plan: Task31 policy comparison can start on cached proposals; Task34 rectangle/classical/oracle mask comparison isolates contamination; Task32 support/distribution comparison isolates spatial uncertainty; Task33 appearance/context and combined association follows fixed supports; Task35 sequential/error tests follow defined anchors and support. Task36 points/patch/mesh display can be scoped independently, with geometric claims waiting for references. Task37 and Task38 platform/dataset research can proceed independently; their acquisitions need separate approval. Task13 and Task25 remain a separate frozen camera stream.

Targets are questions/measurements, not invented success thresholds. Each owning task must record settings, costs, acquisition permissions and a decision rule before execution. A negative or inconclusive outcome is useful if the limitations and failure causes are measured.
