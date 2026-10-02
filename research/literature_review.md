# Literature review

## Scope and evidence

The project needs camera tracking, surface geometry, metric scale and a defensible boundary around the observed work area. A depth map alone does not provide all four. The sources below were checked against publisher pages, author university pages or official repositories on 1 October 2026. Missing runtime, hardware and code details remain unknown in [papers.csv](papers.csv).

## Phone depth

[MobiDepth](https://www.microsoft.com/en-us/research/publication/mobidepth-real-time-depth-estimation-using-on-device-dual-cameras/) appeared at ACM MobiCom 2022. It handles unequal fields of view, camera timing and mobile GPU stereo matching. Its abstract reports 22 frames per second on commodity devices. This establishes a phone stereo research route, not a portable implementation for any phone. Camera access and calibration must be tested on the selected handset.

[HiMoDepth](https://ieeexplore.ieee.org/document/10178038/) was published online on 11 July 2023 and in IEEE Transactions on Mobile Computing 23(5), pages 4648–4664, in May 2024. Its full author list is confirmed by the [Seoul National University record](https://snu.elsevierpure.com/en/publications/himodepth-efficient-training-free-high-resolution-on-device-depth/). It extends training-free dual-camera processing with hierarchical matching for high-resolution depth. The abstract discusses at least 1280×960 resolution. No numerical runtime is adopted here because its test conditions have not been extracted and reproduced.

[HyperSight](https://lion.sjtu.edu.cn/publication/publicationDetail?id=64), ACM SenSys 2019, uses phone motion to create a longer effective stereo baseline while nearby objects help track that motion. The author page reports a 6 cm mean depth error at five metres. That experiment does not establish area accuracy in a moving construction scene. It motivates testing baseline length, nearby texture and motion constraints.

[MobileStereoNet](https://openaccess.thecvf.com/content/WACV2022/html/Shamsafar_MobileStereoNet_Towards_Lightweight_Deep_Networks_for_Stereo_Matching_WACV_2022_paper.html), WACV 2022, has an [official implementation](https://github.com/cogsys-tuebingen/mobilestereonet). Its lightweight 2D and 3D variants estimate stereo disparity. The released evaluation uses Scene Flow, KITTI and DrivingStereo. Converting disparity to metres still requires a calibrated baseline and focal length; the network does not solve phone synchronization or camera pose.

[BANet](https://arxiv.org/abs/2503.03259), accepted at ICCV 2025, has an [official implementation](https://github.com/gangweix/BANet). Bilateral aggregation aims to retain boundaries and handle textureless regions with 2D convolutions. Treat its mobile speed and accuracy claims as leads for a controlled comparison. Neither BANet nor MobileStereoNet weights were run here.

[ARCore Raw Depth](https://codelabs.developers.google.com/codelabs/arcore-rawdepthapi) exposes unfiltered sparse depth for geometry analysis. The [frame API](https://developers.google.com/ar/reference/java/com/google/ar/core/Frame) specifies depth in millimetres, invalid depth as zero and a separate confidence image. Device-dependent resolution and repeated cached depth require timestamp checks. [RoomPlan](https://developer.apple.com/augmented-reality/roomplan/) uses camera and LiDAR on supported Apple devices to build a parametric room representation. Room walls and objects are useful indoors, but do not automatically describe irregular outdoor work areas.

## Tracking and reconstruction

[RTAB-Map](https://github.com/introlab/rtabmap) is a candidate for tracking with revisits and loop closure. Its selected reference checkout has not been built or executed. [COLMAP](https://colmap.github.io/) supports camera reconstruction from overlapping images and multi-view stereo. An image-only reconstruction needs independent metric scale before reporting metres or square metres. Its source checkout remains unbuilt; a separate pycolmap wheel completed a preliminary sparse CPU run. The [COLMAP source note](sources/11_colmap.md) records that run's limits.

[Open3D colour/depth integration](https://www.open3d.org/docs/release/tutorial/pipelines/rgbd_integration.html) combines calibrated frames and camera poses into a surface volume and can extract a mesh. Here, Open3D supports the permitted colour/depth baseline. A point cloud output must not be described as an executed mesh pipeline.

[MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM), CVPR 2025, combines learned reconstruction priors with tracking. Its official setup uses CUDA and reports experiments on an RTX 4090. Its code and underlying checkpoints have separate restrictions. It was not downloaded or executed, and its desktop GPU evidence does not establish on-phone throughput.

[VGGT](https://arxiv.org/abs/2503.11651), CVPR 2025, jointly predicts cameras and scene geometry from images. The [official repository](https://github.com/facebookresearch/vggt) now points to [VGGT-Ω](https://vggt-omega.github.io/), CVPR 2026. The latter page says its September 2026 replacement checkpoint should be the reference for comparisons after a reproducibility concern. [InfiniteVGGT](https://arxiv.org/abs/2601.02281), a January 2026 preprint, proposes bounded memory for streaming geometry. These are verified current leads, not evaluated or cleared deployment choices.

## Construction evidence

[Moritani and colleagues](https://www.iaarc.org/publications/fulltext/ISARC_2020_Paper_334.pdf), ISARC 2020, study smartphone capture, cloud reconstruction and guidance for additional photographs at a construction site. Their title is *Streamlining Photogrammetry-based 3D Modeling of Construction Sites using a Smartphone, Cloud Service and Best-view Guidance* (DOI 10.22260/ISARC2020/0143). The useful connection is capture feedback for poorly observed regions. This is not evidence for autonomous safety decisions.

[Pal, Lin, Hsieh and Golparvar-Fard](https://experts.illinois.edu/en/publications/activity-level-construction-progress-monitoring-through-semantic-/) study semantic segmentation of 3D-informed orthographic images for activity-level construction progress. The journal year is 2024; the DOI contains 2023 (10.1016/j.autcon.2023.105157). Its relevance is combining geometry with task meaning. Orthographic segmentation is not a validation of metric area from an uncalibrated phone capture.

## Recommendation from this evidence

Start with a repeatable metric colour/depth pipeline to isolate pose and area errors. Add native phone depth and pose capture next. Evaluate image-only reconstruction separately, including independent scale measurements. Introduce semantic work-area boundaries only after the geometry and unknown-region behaviour are measured. [The roadmap](roadmap.md) defines the required evidence for each step.
